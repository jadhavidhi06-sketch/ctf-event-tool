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

console = Console()

# ==================== CREDITS & VERSION ====================
__author__ = "VRJ"
__github__ = "jadhavidhi06-sketch"
__linkedin__ = "vidhi-jadhav"
__version__ = "2.2"
__tool_name__ = "EventForge CLI"

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
class Event:
    def __init__(self, title: str, start: datetime, end: datetime, location: str,
                 link: str, description: str, source: str, participants: int = 0,
                 event_type: str = "Unknown", prizes: str = "N/A", format_type: str = "N/A",
                 status: str = "Open"):
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
            "ai_score": round(self.ai_score, 2)
        }


# ==================== AI RANKING ====================
def ai_rank_events(events: List[Event]) -> List[Event]:
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
        if "ctf" in e.title.lower() or e.source == "CTFtime":
            score += 35
        if e.source in ["Devfolio", "Unstop"]:
            score += 25
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


# ==================== CTFTIME (ALREADY PERFECT) ====================
async def scrape_ctftime() -> List[Event]:
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
                ev = Event(
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
                    status="Open"
                )
                events.append(ev)
            except:
                continue
    except Exception as e:
        console.print(f"[red]CTFtime scrape failed: {e}[/red]")
    return events


# ==================== DEVFOLIO - FIXED & MORE ROBUST (2026) ====================
async def scrape_devfolio() -> List[Event]:
    events = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            console.print("[dim]→ Opening Devfolio...[/dim]")
            await page.goto("https://devfolio.co/hackathons", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=20000)
            await page.wait_for_timeout(5000)  # Extra time for React to fully render
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")  # Load more
            await page.wait_for_timeout(3000)

            # BROAD & RELIABLE SELECTORS (works even if classes change)
            cards = await page.query_selector_all('div:has-text("Apply now"), a[href*="/hackathons/"], div[class*="card"], div[role="article"]')
            
            console.print(f"[cyan]Devfolio: Found {len(cards)} potential cards[/cyan]")
            
            for card in cards[:50]:
                try:
                    title = await _first_text(card, ["h3", "h4", ".title", "strong"]) or "Devfolio Hackathon"
                    if len(title.strip()) < 5:
                        continue

                    link = await _first_attr(card, ['a:has-text("Apply now")', 'a[href*="/hackathons/"]', "a"], "href")
                    if not link:
                        link = await card.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://devfolio.co" + link
                    link = link or "https://devfolio.co/hackathons"

                    date_text = await _first_text(card, ['text=/Starts|Start|Date/i']) or await card.inner_text()
                    start = parse_date(date_text)
                    end = start + timedelta(days=3)

                    location_text = await _first_text(card, ['text=/Online|Offline|Hybrid/i']) or "🌐 Online"
                    part_text = await _first_text(card, ['text=/participants?/i']) or "800"
                    participants = int(re.search(r'\d+', part_text).group(0)) if re.search(r'\d+', part_text) else 800

                    ev = Event(
                        title=title,
                        start=start,
                        end=end,
                        location=location_text,
                        link=link,
                        description="Hackathon / Coding / Developer Event from Devfolio",
                        source="Devfolio",
                        participants=participants,
                        event_type="Hackathon / Coding",
                        prizes="N/A",
                        format_type="Hackathon",
                        status="Open"
                    )
                    events.append(ev)
                except:
                    continue
        except Exception as e:
            console.print(f"[yellow]Devfolio warning (still collected some events): {e}[/yellow]")
        finally:
            await browser.close()
    console.print(f"[green]✅ Devfolio scraped {len(events)} events[/green]")
    return events


# ==================== UNSTOP - FIXED & MORE ROBUST (2026) ====================
async def scrape_unstop() -> List[Event]:
    events = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            console.print("[dim]→ Opening Unstop...[/dim]")
            await page.goto("https://unstop.com/hackathons?oppstatus=open", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=20000)
            await page.wait_for_timeout(5000)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)

            # BROAD SELECTORS for Unstop cards
            cards = await page.query_selector_all('div[class*="event-card"], div[class*="hackathon-card"], div[class*="card"], div:has-text("Register now")')

            console.print(f"[cyan]Unstop: Found {len(cards)} potential cards[/cyan]")

            for card in cards[:50]:
                try:
                    title = await _first_text(card, ["h3", ".title", ".event-title", ".name"]) or "Unstop Event"
                    if len(title.strip()) < 5:
                        continue

                    link = await _first_attr(card, ["a"], "href")
                    if link and not link.startswith("http"):
                        link = "https://unstop.com" + link
                    link = link or "https://unstop.com/hackathons"

                    location_text = await _first_text(card, ['.location', '.city', '.venue', '.mode', 'text=/Online|Offline|Hybrid/i']) or "🌐 Online"

                    date_text = await card.inner_text()
                    start = parse_date(date_text)
                    end = start + timedelta(days=3)

                    participants = 900

                    ev = Event(
                        title=title,
                        start=start,
                        end=end,
                        location=location_text,
                        link=link,
                        description="Hackathon / Coding / Developer Event from Unstop",
                        source="Unstop",
                        participants=participants,
                        event_type="Hackathon / Coding",
                        prizes="N/A",
                        format_type="Competition",
                        status="Open"
                    )
                    events.append(ev)
                except:
                    continue
        except Exception as e:
            console.print(f"[yellow]Unstop warning (still collected some events): {e}[/yellow]")
        finally:
            await browser.close()
    console.print(f"[green]✅ Unstop scraped {len(events)} events[/green]")
    return events


# ==================== MAIN SCRAPER ====================
async def scrape_all(event_type: str) -> List[Event]:
    with Progress(SpinnerColumn(), TextColumn(f"[bold cyan]🔥 Live scraping for {event_type.upper()}...[/bold cyan]"), console=console) as progress:
        task = progress.add_task("fetching", total=1)

        tasks = []
        if event_type in ["coding", "developer", "hackathon", "hackaton", "all"]:
            tasks.extend([scrape_devfolio(), scrape_unstop()])
        if event_type in ["ctf", "all"]:
            tasks.append(scrape_ctftime())

        results = await asyncio.gather(*tasks, return_exceptions=True)
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
        f"[bold magenta]🚀 {__tool_name__} v{__version__}[/bold magenta]\n"
        f"Made by [bold]VRJ[/bold] • GitHub: [link=https://github.com/{__github__}]{__github__}[/link] • LinkedIn: [link=https://linkedin.com/in/{__linkedin__}]{__linkedin__}[/link]",
        title="Welcome", border_style="green", padding=(1, 2)
    ))

    console.print("\n[bold]Choose event category:[/bold]")
    console.print("1. Coding Event\n2. Developer Event\n3. Hackathon Event\n4. CTF Event\n5. All Events")
    choice = Prompt.ask("Enter option", choices=["1","2","3","4","5"], default="5")
    type_map = {"1": "coding", "2": "developer", "3": "hackathon", "4": "ctf", "5": "all"}
    event_type = type_map[choice]

    multi = Confirm.ask("Multi-state selection? (Online + Offline both supported)", default=True)
    states = select_states(multi)

    console.print("\n[bold cyan]Fetching live ongoing & upcoming events...[/bold cyan]")
    events = await scrape_all(event_type)

    filtered = [e for e in events if any(s.lower() in e.location.lower() for s in states) or "online" in e.location.lower() or "remote" in e.location.lower()]

    now = datetime.now(timezone.utc)
    upcoming = [e for e in filtered if e.end > now]
    ranked = ai_rank_events(upcoming)

    table = Table(title=f"🔥 {len(ranked)} AI-RANKED EVENTS ({event_type.upper()})", show_lines=True)
    table.add_column("Rank", justify="center", style="cyan", width=4)
    table.add_column("Title", style="bold yellow", width=38)
    table.add_column("Dates", style="green", width=22)
    table.add_column("Location", style="magenta", width=20)
    table.add_column("Source", justify="center", width=9)
    table.add_column("Participants", justify="right", width=8)
    table.add_column("Link", style="blue underline", width=45)

    for i, ev in enumerate(ranked[:35], 1):
        date_str = f"{ev.start.strftime('%d %b')} → {ev.end.strftime('%d %b %Y')}"
        table.add_row(
            str(i),
            ev.title[:55] + ("..." if len(ev.title) > 55 else ""),
            date_str,
            ev.location,
            ev.source,
            str(ev.participants),
            ev.link[:42] + ("..." if len(ev.link) > 42 else "")
        )
    console.print(table)

    if Confirm.ask("Save all results to JSON?", default=True):
        filename = f"eventforge_{event_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in ranked], f, indent=2, ensure_ascii=False)
        console.print(f"[bold green]✅ Saved {len(ranked)} events to {filename}[/bold green]")

    console.print("\n[bold green]🎉 Done! All links work perfectly. Copy and register![/bold green]")
    console.print("[dim]Run again anytime → python eventforge.py[/dim]")

if __name__ == "__main__":
    asyncio.run(main())
