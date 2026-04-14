import asyncio
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from async_scraper import scrape_all
from ai_ranker import rank_events
from exporter import export_json, export_csv
from utils import multi_select_states

console = Console()

EVENT_TYPES = {
    "1": "coding",
    "2": "developer",
    "3": "hackathon",
    "4": "ctf",
    "5": "all"
}

def display_events(events):
    table = Table(title="🔥 Elite Event Intelligence Feed")

    table.add_column("Name", style="cyan")
    table.add_column("Platform", style="magenta")
    table.add_column("Location", style="green")
    table.add_column("Date", style="yellow")
    table.add_column("Score", style="red")
    table.add_column("Link", style="blue")

    for e in events:
        table.add_row(
            e["name"],
            e["platform"],
            e["location"],
            e["date"],
            str(e["score"]),
            e.get("link", "N/A")
        )

    console.print(table)

async def main():
    console.print("\n🚀 [bold cyan]CTF / Hackathon OSINT Tool[/bold cyan]\n")

    console.print("""
1. Coding Events
2. Developer Events
3. Hackathon Events
4. CTF Events
5. All Events
""")

    choice = Prompt.ask("Select event type", choices=list(EVENT_TYPES.keys()))
    event_type = EVENT_TYPES[choice]

    states = multi_select_states()

    console.print("\n⚡ Gathering intelligence (async scraping)...\n")

    events = await scrape_all(event_type, states)

    ranked = rank_events(events)

    display_events(ranked)

    if Prompt.ask("\n💾 Save results? (y/n)", default="y") == "y":
        export_json(ranked)
        export_csv(ranked)
        console.print("✅ Saved successfully")

if __name__ == "__main__":
    asyncio.run(main())