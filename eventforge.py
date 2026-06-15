import asyncio
import json
import re
from datetime import datetime, timezone, timedelta
from typing import List, Optional

import httpx
from playwright.async_api import async_playwright, TimeoutError
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich import box

console = Console()

# ==================== CREDITS & VERSION ====================
__author__ = "VRJ"
__github__ = "jadhavidhi06-sketch"
__linkedin__ = "vidhi-jadhav"
__version__ = "3.0"
__tool_name__ = "CTFForge CLI"

# ==================== INDIAN STATES + UTs ====================
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry", "Chandigarh",
    "Andaman and Nicobar Islands", "Dadra and Nagar Haveli and Daman and Diu", "Lakshadweep"
]

# ==================== EVENT CLASS ====================
class CTFEvent:
    def __init__(self, title: str, start: datetime, end: datetime, location: str,
                 link: str, description: str, source: str, participants: int = 0,
                 event_type: str = "CTF", prizes: str = "N/A", format_type: str = "N/A",
                 status: str = "Open", weight: int = 0, organizer: str = "Unknown"):
        self.title = title.strip()
        self.start = start
        self.end = end
        self.location = (location.strip() or "🌐 Online / Remote").replace("Online", "🌐 Online").replace("Offline", "📍 Offline")
        self.link = link
        clean_desc = (description or "No description available").strip()
        self.description = clean_desc[:280] + ("..." if len(clean_desc) > 280 else "")
        self.source = source
        self.participants = participants
        self.event_type = event_type
        self.prizes = prizes
        self.format_type = format_type
        self.status = status
        self.weight = weight
        self.organizer = organizer
        self.ai_score = 0.0

    def to_dict(self):
        return {
            "title": self.title,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "location": self.location,
            "link": self.link,
            "description": self.description,
            "source": self.source,
            "participants": self.participants,
            "event_type": self.event_type,
            "prizes": self.prizes,
            "format": self.format_type,
            "status": self.status,
            "weight": self.weight,
            "organizer": self.organizer,
            "ai_score": round(self.ai_score, 2)
        }


# ==================== AI RANKING ====================
def ai_rank_events(events: List[CTFEvent]) -> List[CTFEvent]:
    now = datetime.now(timezone.utc)
    for e in events:
        score = 100.0
        days_to_start = max(0, (e.start - now).days)
        score -= days_to_start * 6
        score += min(e.participants / 8, 90)
        if any(s.lower() in e.location.lower() for s in INDIAN_STATES):
            score += 45
        if e.start <= now <= e.end:
            score += 70
        if e.weight > 0:
            score += e.weight * 2
        if e.prizes.lower() != "n/a":
            score += 20
        if "offline" in e.location.lower():
            score += 15
        e.ai_score = max(10.0, min(200.0, score))
    return sorted(events, key=lambda x: x.ai_score, reverse=True)


# ==================== DATE PARSER ====================
def parse_date(date_text: str) -> datetime:
    try:
        text = (date_text or "").strip()
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2})(?!\d)', text)
        if match:
            day, month, year = match.groups()
            return datetime(2000 + int(year), int(month), int(day), tzinfo=timezone.utc)

        candidates = re.findall(
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{4}\b|\b[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b",
            text
        )
        for candidate in candidates + [text]:
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y", "%d %b %Y", "%d %B %Y", "%b %d %Y", "%B %d %Y", "%Y-%m-%d"):
                try:
                    sanitized = candidate.replace(",", "").strip()
                    return datetime.strptime(sanitized, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
    except Exception:
        pass
    return datetime.now(timezone.utc) + timedelta(days=5)


async def _first_text(node, selectors: List[str]) -> Optional[str]:
    for selector in selectors:
        try:
            el = await node.query_selector(selector)
            if not el:
                continue
            txt = (await el.inner_text() or "").strip()
            if txt:
                return txt
        except Exception:
            continue
    return None


async def _first_attr(node, selectors: List[str], attr: str) -> Optional[str]:
    for selector in selectors:
        try:
            el = await node.query_selector(selector)
            if not el:
                continue
            val = await el.get_attribute(attr)
            if val and val.strip():
                return val.strip()
        except Exception:
            continue
    return None


# ==================== CTFTIME SCRAPER (ENHANCED) ====================
async def scrape_ctftime() -> List[CTFEvent]:
    events = []
    try:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        url = f"https://ctftime.org/api/v1/events/?limit=150&start={now_ts-86400}&finish={now_ts+120*86400}"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers={"User-Agent": f"{__tool_name__}/{__version__}"})
            data = r.json()
        
        for item in data:
            try:
                start = datetime.fromisoformat(item["start"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(item["finish"].replace("Z", "+00:00"))
                
                # Get organizer info
                organizer = "Unknown"
                if "organizer" in item and item["organizer"]:
                    organizer = item["organizer"].get("name", "Unknown")
                
                ev = CTFEvent(
                    title=item["title"],
                    start=start,
                    end=end,
                    location="🌐 Online" if not item.get("onsite") else f"📍 {item.get('location', 'TBD')}",
                    link=item.get("url") or item.get("ctftime_url", "https://ctftime.org"),
                    description=item.get("description", "CTF Event"),
                    source="CTFtime",
                    participants=item.get("participants", 0),
                    event_type="CTF",
                    prizes=item.get("prizes", "N/A"),
                    format_type=item.get("format", "Jeopardy/Mixed"),
                    status="Open",
                    weight=item.get("weight", 0),
                    organizer=organizer
                )
                events.append(ev)
            except:
                continue
    except Exception as e:
        console.print(f"[red]CTFtime scrape failed: {e}[/red]")
    return events


# ==================== CTF HUNT (ADDITIONAL CTF SOURCES) ====================
async def scrape_ctfhunt() -> List[CTFEvent]:
    events = []
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get("https://ctfhunt.com/api/events", 
                                headers={"User-Agent": f"{__tool_name__}/{__version__}"})
            data = r.json()
        
        for item in data:
            try:
                start = datetime.fromisoformat(item["start"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(item["end"].replace("Z", "+00:00"))
                
                ev = CTFEvent(
                    title=item["title"],
                    start=start,
                    end=end,
                    location=item.get("location", "🌐 Online"),
                    link=item.get("url", "https://ctfhunt.com"),
                    description=item.get("description", "CTF Event"),
                    source="CTF Hunt",
                    participants=item.get("participants", 0),
                    event_type="CTF",
                    prizes=item.get("prizes", "N/A"),
                    format_type=item.get("format", "Jeopardy"),
                    status="Open",
                    organizer=item.get("organizer", "Unknown")
                )
                events.append(ev)
            except:
                continue
    except:
        pass  # CTF Hunt may not always be available
    return events


# ==================== CAPTURE THE FLAG (SCRAPE CTFTIME HTML FOR MORE DETAILS) ====================
async def scrape_ctftime_html() -> List[CTFEvent]:
    events = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            console.print("[dim]→ Scraping CTFtime for detailed info...[/dim]")
            await page.goto("https://ctftime.org/event/list/upcoming", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=20000)
            await page.wait_for_timeout(3000)
            
            # Get all event rows
            rows = await page.query_selector_all('table tbody tr')
            
            for row in rows:
                try:
                    # Get title and link
                    title_el = await row.query_selector('td:nth-child(2) a')
                    if not title_el:
                        continue
                    title = (await title_el.inner_text()).strip()
                    link = await title_el.get_attribute('href')
                    if link and not link.startswith('http'):
                        link = f"https://ctftime.org{link}"
                    
                    # Get date
                    date_el = await row.query_selector('td:nth-child(1)')
                    date_text = await date_el.inner_text() if date_el else ""
                    
                    # Get location
                    loc_el = await row.query_selector('td:nth-child(4)')
                    location = await loc_el.inner_text() if loc_el else "🌐 Online"
                    
                    # Get format
                    format_el = await row.query_selector('td:nth-child(5)')
                    format_type = await format_el.inner_text() if format_el else "Jeopardy"
                    
                    # Get weight
                    weight_el = await row.query_selector('td:nth-child(6)')
                    weight_text = await weight_el.inner_text() if weight_el else "0"
                    weight = int(re.search(r'\d+', weight_text).group(0)) if re.search(r'\d+', weight_text) else 0
                    
                    start = parse_date(date_text)
                    end = start + timedelta(days=2)
                    
                    ev = CTFEvent(
                        title=title,
                        start=start,
                        end=end,
                        location=location,
                        link=link,
                        description=f"CTF from CTFtime - Format: {format_type}",
                        source="CTFtime",
                        participants=0,
                        event_type="CTF",
                        prizes="N/A",
                        format_type=format_type,
                        status="Open",
                        weight=weight
                    )
                    events.append(ev)
                except:
                    continue
                    
        except Exception as e:
            console.print(f"[yellow]CTFtime HTML scrape warning: {e}[/yellow]")
        finally:
            await browser.close()
    
    return events


# ==================== MAIN SCRAPER ====================
async def scrape_all() -> List[CTFEvent]:
    with Progress(SpinnerColumn(), TextColumn(f"[bold cyan]🔥 Scraping CTF events...[/bold cyan]"), console=console) as progress:
        task = progress.add_task("fetching", total=1)

        # Scrape from multiple sources
        results = await asyncio.gather(
            scrape_ctftime(),
            scrape_ctftime_html(),
            scrape_ctfhunt(),
            return_exceptions=True
        )
        progress.update(task, completed=1)

    all_events = []
    for res in results:
        if isinstance(res, list):
            all_events.extend(res)

    # Deduplicate
    seen = {}
    unique = []
    for e in all_events:
        key = f"{e.title.lower().strip()}|{e.source}|{e.start.date().isoformat()}"
        if key not in seen:
            seen[key] = True
            unique.append(e)
    return unique


# ==================== STATE SELECTION ====================
def select_states(multi: bool = True) -> List[str]:
    console.print(Panel.fit("[bold yellow]Select State(s) in India (Online events always included)[/bold yellow]", border_style="blue"))
    for i, s in enumerate(INDIAN_STATES, 1):
        console.print(f"  [cyan]{i:2d}.[/cyan] {s}")
    if multi:
        inp = Prompt.ask("Numbers (comma separated) or [bold]all[/bold]", default="all")
        if inp.strip().lower() == "all":
            return INDIAN_STATES.copy()
        selected = []
        for n in inp.split(","):
            try:
                idx = int(n.strip()) - 1
                if 0 <= idx < len(INDIAN_STATES):
                    selected.append(INDIAN_STATES[idx])
            except:
                pass
        return selected or INDIAN_STATES[:8]
    else:
        inp = Prompt.ask("Enter single number")
        try:
            idx = int(inp) - 1
            return [INDIAN_STATES[idx]]
        except:
            return [INDIAN_STATES[0]]


# ==================== MAIN CLI ====================
async def main():
    console.clear()
    console.print(Panel.fit(
        f"[bold cyan]🔐 {__tool_name__} v{__version__}[/bold cyan]\n"
        f"Made by [bold]VRJ[/bold] • GitHub: [link=https://github.com/{__github__}]{__github__}[/link] • LinkedIn: [link=https://linkedin.com/in/{__linkedin__}]{__linkedin__}[/link]\n"
        f"[bold green]CTF Event Aggregator - India Focused[/bold green]",
        title="Welcome", border_style="cyan", padding=(1, 2)
    ))

    # State selection
    multi = Confirm.ask("Multi-state selection? (Online + Offline both supported)", default=True)
    states = select_states(multi)
    
    console.print(f"\n[bold]Selected states:[/bold] {', '.join(states[:5])}{'...' if len(states) > 5 else ''}")

    # Filter options
    console.print("\n[bold]Filter options:[/bold]")
    console.print("1. All CTF Events")
    console.print("2. Only Upcoming CTF Events")
    console.print("3. Only Ongoing CTF Events")
    console.print("4. Only Offline CTF Events")
    console.print("5. Only High Weight CTF Events (>50)")
    filter_choice = Prompt.ask("Select filter", choices=["1","2","3","4","5"], default="1")
    
    # Sort options
    console.print("\n[bold]Sort options:[/bold]")
    console.print("1. AI Ranked (Recommended)")
    console.print("2. By Start Date")
    console.print("3. By Participants Count")
    console.print("4. By CTF Weight")
    sort_choice = Prompt.ask("Select sort", choices=["1","2","3","4"], default="1")

    console.print("\n[bold cyan]Fetching CTF events from multiple sources...[/bold cyan]")
    events = await scrape_all()

    # Apply state filter
    filtered = [e for e in events if any(s.lower() in e.location.lower() for s in states) or "online" in e.location.lower() or "remote" in e.location.lower()]

    now = datetime.now(timezone.utc)
    
    # Apply additional filters
    if filter_choice == "2":  # Only upcoming
        filtered = [e for e in filtered if e.start > now]
    elif filter_choice == "3":  # Only ongoing
        filtered = [e for e in filtered if e.start <= now <= e.end]
    elif filter_choice == "4":  # Only offline
        filtered = [e for e in filtered if "offline" in e.location.lower() or "📍" in e.location]
    elif filter_choice == "5":  # High weight
        filtered = [e for e in filtered if e.weight > 50]

    # Apply sorting
    if sort_choice == "1":  # AI Ranked
        ranked = ai_rank_events(filtered)
    elif sort_choice == "2":  # By start date
        ranked = sorted(filtered, key=lambda x: x.start)
    elif sort_choice == "3":  # By participants
        ranked = sorted(filtered, key=lambda x: x.participants, reverse=True)
    else:  # By weight
        ranked = sorted(filtered, key=lambda x: x.weight, reverse=True)

    # Display results
    if not ranked:
        console.print("[bold red]No CTF events found matching your criteria.[/bold red]")
        return

    # Create table with clickable links
    table = Table(
        title=f"🔐 {len(ranked)} CTF EVENTS FOUND",
        show_lines=True,
        box=box.ROUNDED,
        header_style="bold cyan"
    )
    table.add_column("Rank", justify="center", style="cyan", width=4)
    table.add_column("CTF Name", style="bold yellow", width=35)
    table.add_column("Dates", style="green", width=22)
    table.add_column("Location", style="magenta", width=18)
    table.add_column("Format", justify="center", width=10)
    table.add_column("Weight", justify="center", width=6)
    table.add_column("Participants", justify="right", width=8)
    table.add_column("Link", style="blue underline", width=45)

    for i, ev in enumerate(ranked[:35], 1):
        date_str = f"{ev.start.strftime('%d %b')} → {ev.end.strftime('%d %b %Y')}"
        
        # Make link clickable
        link_text = Text(ev.link[:42] + ("..." if len(ev.link) > 42 else ""))
        link_text.stylize(f"link {ev.link}")
        
        # Format weight with color
        weight_str = str(ev.weight) if ev.weight > 0 else "-"
        if ev.weight > 50:
            weight_str = f"[bold green]{ev.weight}[/bold green]"
        elif ev.weight > 25:
            weight_str = f"[yellow]{ev.weight}[/yellow]"
        
        table.add_row(
            str(i),
            ev.title[:50] + ("..." if len(ev.title) > 50 else ""),
            date_str,
            ev.location,
            ev.format_type[:8],
            weight_str,
            str(ev.participants) if ev.participants > 0 else "-",
            link_text
        )
    
    console.print(table)
    
    # Show statistics
    console.print(f"\n[bold cyan]📊 Statistics:[/bold cyan]")
    console.print(f"  • Total CTFs found: [bold]{len(ranked)}[/bold]")
    console.print(f"  • Online CTFs: [bold]{len([e for e in ranked if 'online' in e.location.lower()])}[/bold]")
    console.print(f"  • Offline CTFs: [bold]{len([e for e in ranked if 'offline' in e.location.lower()])}[/bold]")
    console.print(f"  • High weight (>50): [bold]{len([e for e in ranked if e.weight > 50])}[/bold]")
    console.print(f"  • Average participants: [bold]{sum(e.participants for e in ranked if e.participants > 0) // max(1, len([e for e in ranked if e.participants > 0]))}[/bold]")

    # Export options
    if Confirm.ask("Save all results to JSON?", default=True):
        filename = f"ctfforge_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in ranked], f, indent=2, ensure_ascii=False)
        console.print(f"[bold green]✅ Saved {len(ranked)} CTF events to {filename}[/bold green]")
    
    if Confirm.ask("Save results as CSV?", default=False):
        filename = f"ctfforge_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("Title,Start,End,Location,Format,Weight,Participants,Link\n")
            for ev in ranked:
                f.write(f'"{ev.title}","{ev.start.isoformat()}","{ev.end.isoformat()}","{ev.location}","{ev.format_type}",{ev.weight},{ev.participants},"{ev.link}"\n')
        console.print(f"[bold green]✅ Saved {len(ranked)} CTF events to {filename}[/bold green]")

    # Show detailed info for a specific CTF
    if Confirm.ask("View detailed info for a specific CTF?", default=False):
        try:
            idx = int(Prompt.ask("Enter rank number to view details")) - 1
            if 0 <= idx < len(ranked):
                ev = ranked[idx]
                console.print(Panel.fit(
                    f"[bold yellow]{ev.title}[/bold yellow]\n\n"
                    f"[bold]Date:[/bold] {ev.start.strftime('%d %b %Y')} → {ev.end.strftime('%d %b %Y')}\n"
                    f"[bold]Location:[/bold] {ev.location}\n"
                    f"[bold]Format:[/bold] {ev.format_type}\n"
                    f"[bold]Weight:[/bold] {ev.weight}\n"
                    f"[bold]Participants:[/bold] {ev.participants}\n"
                    f"[bold]Organizer:[/bold] {ev.organizer}\n"
                    f"[bold]Prizes:[/bold] {ev.prizes}\n"
                    f"[bold]Status:[/bold] {ev.status}\n\n"
                    f"[bold]Description:[/bold]\n{ev.description}\n\n"
                    f"[bold]Link:[/bold] [link={ev.link}]{ev.link}[/link]",
                    title="CTF Details", border_style="cyan"
                ))
        except:
            pass

    console.print("\n[bold cyan]🎉 Happy Hacking! All links are clickable in supporting terminals.[/bold cyan]")
    console.print("[dim]Run again anytime → python ctfforge.py[/dim]")

if __name__ == "__main__":
    asyncio.run(main())
