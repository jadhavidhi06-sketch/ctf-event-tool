from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from scraper import scrape_events
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
    table = Table(title="🔥 Live Events")

    table.add_column("Name", style="cyan")
    table.add_column("Platform", style="magenta")
    table.add_column("Location", style="green")
    table.add_column("Date", style="yellow")
    table.add_column("Score", style="red")

    for e in events:
        table.add_row(
            e["name"],
            e["platform"],
            e["location"],
            e["date"],
            str(e["score"])
        )

    console.print(table)


def main():
    console.print("\n🚀 [bold cyan]CTF & Hackathon Finder Tool[/bold cyan]\n")

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

    console.print("\n🔎 Fetching live events...\n")

    events = scrape_events(event_type, states)

    ranked = rank_events(events)

    display_events(ranked)

    save = Prompt.ask("\n💾 Save results? (y/n)", default="y")

    if save.lower() == "y":
        export_json(ranked)
        export_csv(ranked)
        console.print("✅ Saved as JSON & CSV")

if __name__ == "__main__":
    main()