import asyncio
import json
import re
from datetime import datetime, timezone, timedelta
from typing import List

import httpx
from playwright.async_api import async_playwright
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

console = Console()

# ==================== CREDITS ====================
__author__ = "VRJ"
__github__ = "jadhavidhi06-sketch"
__linkedin__ = "vidhi-jadhav"
__version__ = "2.0"

# ==================== INDIAN STATES ====================
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry", "Chandigarh",
    "Andaman and Nicobar Islands", "Dadra and Nagar Haveli and Daman and Diu", "Lakshadweep"
]

# ==================== EVENT CLASS (MORE INFO) ====================
class Event:
    def __init__(self, title: str, start: datetime, end: datetime, location: str,
                 link: str, description: str, source: str, participants: int = 0,
                 event_type: str = "Unknown", prizes: str = "N/A", format_type: str = "N/A",
                 status: str = "Open"):
        self.title = title.strip()
        self.start = start
        self.end = end
        self.location = location.strip() or "Online / Remote"
        self.link = link
        self.description = (description or "No description")[:280] + "..."
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


# ==================== AI RANKING (UPGRADED) ====================
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

        e.ai_score = max(10.0, min(200.0, score))

    return sorted(events, key=lambda x: x.ai_score, reverse=True)


# ==================== HELPER: PARSE DATE (Devfolio style) ====================
def parse_devfolio_date(date_str: str) -> datetime:
    try:
        # Example: "Starts 24/04/26" → 2026-04-24
        clean = re.search(r'\d{1,2}/\d{1,2}/\d{2}', date_str)
        if clean:
            d = datetime.strptime(clean.group() + "26", "%d/%m/%y")  # assuming 2026
            return d.replace(tzinfo=timezone.utc)
    except:
        pass
    return datetime.now(timezone.utc) + timedelta(days=5)


# ==================== SCRAPERS ====================
async def scrape_ctftime() -> List[Event]:
    events = []
    try:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        url = f"https://ctftime.org/api/v1/events/?limit=150&start={now_ts-86400}&finish={now_ts+90*86400}"
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url, headers={"User-Agent": "EventForge/2.0"})
            data = r.json()

        for item in data:
            try:
                start = datetime.fromisoformat(item["start"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(item["finish"].replace("Z", "+00:00"))
                ev = Event(
                    title=item["title"],
                    start=start,
                    end=end,
                    location="Online" if not item.get("onsite") else item.get("location", "TBD"),
                    link=item.get("url") or item.get("ctftime_url", "https://ctftime.org"),
                    description=item.get("description", ""),
                    source="CTFtime",
                    participants=item.get("participants", 0),
                    event_type="CTF",
                    prizes=item.get("prizes", "N/A"),
                    format_type=item.get("format", "Jeopardy"),
                    status="Open"
                )
                events.append(ev)
            except:
                continue
    except Exception as e:
        console.print(f"[red]CTFtime error: {e}[/red]")
    return events


async def scrape_devfolio() -> List[Event]:
    events = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto("https://devfolio.co/hackathons", timeout=30000)
            await page.wait_for_load_state("networkidle", timeout=15000)

            # New accurate selectors based on live site (April 2026)
            cards = await page.query_selector_all('a:has-text("Apply now") >> parent()')

            for card in cards[:40]:
                try:
                    title = await card.query_selector_inner_text("h3, h4") or "Devfolio Hackathon"
                    link_el = await card.query_selector('a:has-text("Apply now")')
                    link = await link_el.get_attribute("href") or ""
                    if link and not link.startswith("http"):
                        link = "https://devfolio.co" + link

                    date_text = await card.query_selector_inner_text('span:has-text("Starts")') or ""
                    start = parse_devfolio_date(date_text)
                    end = start + timedelta(days=3)

                    location = await card.query_selector_inner_text('span:has-text("Online") , span:has-text("Offline")') or "Online"
                    participants_text = await card.query_selector_inner_text('span:has-text("+ ")') or "0"
                    participants = int(re.search(r'\d+', participants_text).group()) if re.search(r'\d+', participants_text) else 0

                    ev = Event(
                        title=title,
                        start=start,
                        end=end,
                        location=location,
                        link=link,
                        description="Hackathon from Devfolio",
                        source="Devfolio",
                        participants=participants,
                        event_type="Hackathon",
                        prizes="N/A",
                        format_type="Hackathon",
                        status="Open"
                    )
                    events.append(ev)
                except:
                    continue
        except Exception as e:
            console.print(f"[yellow]Devfolio warning: {e}[/yellow]")
        finally:
            await browser.close()
    return events


async def scrape_unstop() -> List[Event]:
    events = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto("https://unstop.com/hackathons?oppstatus=open", timeout=25000)
            await page.wait_for_selector("div[class*='event'], div[class*='card']", timeout=12000)

            cards = await page.query_selector_all("div[class*='event-card'], div[class*='hackathon-card']")
            for card in cards[:40]:
                try:
                    title = await card.query_selector_inner_text("h3, .title, .event-title") or "Unstop Event"
                    link = await card.query_selector_attribute("a", "href") or ""
                    if link and not link.startswith("http"):
                        link = "https://unstop.com" + link

                    location = await card.query_selector_inner_text(".location, .city, .venue") or "Online"
                    participants = 800  # approximate

                    ev = Event(
                        title=title,
                        start=datetime.now(timezone.utc) + timedelta(days=4),
                        end=datetime.now(timezone.utc) + timedelta(days=7),
                        location=location,
                        link=link,
                        description="Hackathon / Coding Event from Unstop",
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
            console.print(f"[yellow]Unstop warning: {e}[/yellow]")
        finally:
            await browser.close()
    return events


# ==================== MAIN ASYNC SCRAPER ====================
async def scrape_all(event_type: str) -> List[Event]:
    with Progress(SpinnerColumn(), TextColumn("[bold cyan]🔥 Live scraping Devfolio + Unstop + CTFtime...[/bold cyan]"), console=console) as progress:
        task = progress.add_task("fetching", total=1)

        tasks = []
        if event_type in ["coding", "developer", "hackaton", "all"]:
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
        key = e.title.lower()
        if key not in seen:
            seen[key] = True
            unique.append(e)
    return unique


# ==================== STATE SELECTION ====================
def select_states(multi: bool = True) -> List[str]:
    console.print(Panel.fit("[bold yellow]Select State(s) in India[/bold yellow]", border_style="blue"))
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
        f"[bold magenta]🚀 EventForge CLI v{__version__}[/bold magenta]\n"
        f"Made by [bold]VRJ[/bold] • GitHub: [link=https://github.com/{__github__}]{__github__}[/link] • LinkedIn: [link=https://linkedin.com/in/{__linkedin__}]{__linkedin__}[/link]",
        title="Welcome", border_style="green", padding=(1, 2)
    ))

    console.print("\n[bold]Choose event category:[/bold]")
    console.print("1. Coding Event\n2. Developer Event\n3. Hackathon Event\n4. CTF Event\n5. All Events")
    choice = Prompt.ask("Enter option", choices=["1","2","3","4","5"], default="5")
    type_map = {"1": "coding", "2": "developer", "3": "hackaton", "4": "ctf", "5": "all"}
    event_type = type_map[choice]

    multi = Confirm.ask("Multi-state selection?", default=True)
    states = select_states(multi)

    console.print("\n[bold cyan]Fetching latest events...[/bold cyan]")
    events = await scrape_all(event_type)

    # Filter
    filtered = [e for e in events if any(s.lower() in e.location.lower() for s in states) or "online" in e.location.lower() or "remote" in e.location.lower()]

    now = datetime.now(timezone.utc)
    upcoming = [e for e in filtered if e.end > now]
    ranked = ai_rank_events(upcoming)

    # Display
    table = Table(title=f"🔥 {len(ranked)} AI-RANKED EVENTS", show_lines=True)
    table.add_column("Rank", justify="center", style="cyan", width=4)
    table.add_column("Title", style="bold yellow", width=38)
    table.add_column("Dates", style="green", width=22)
    table.add_column("Location", style="magenta", width=18)
    table.add_column("Source", justify="center", width=9)
    table.add_column("Participants", justify="right", width=6)
    table.add_column("Link", style="blue underline", width=45)

    for i, ev in enumerate(ranked[:30], 1):
        date_str = f"{ev.start.strftime('%d %b')} → {ev.end.strftime('%d %b %Y')}"
        table.add_row(
            str(i),
            ev.title[:52] + ("..." if len(ev.title) > 52 else ""),
            date_str,
            ev.location[:25] + ("..." if len(ev.location) > 25 else ""),
            ev.source,
            str(ev.participants),
            ev.link[:42] + ("..." if len(ev.link) > 42 else "")
        )
    console.print(table)

    if Confirm.ask("Save to JSON?", default=True):
        filename = f"eventforge_{event_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in ranked], f, indent=2)
        console.print(f"[bold green]✅ Saved to {filename}[/bold green]")

    console.print("\n[bold green]🎉 Done! Links are ready to open.[/bold green]")

if __name__ == "__main__":
    asyncio.run(main())