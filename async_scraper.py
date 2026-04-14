import aiohttp
import asyncio
from bs4 import BeautifulSoup
from ctftime import fetch_ctftime
from dorking import google_dork_events

HEADERS = {"User-Agent": "Mozilla/5.0"}

async def fetch(session, url):
    async with session.get(url, headers=HEADERS) as res:
        return await res.text()

async def scrape_devfolio(session):
    url = "https://devfolio.co/hackathons"
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")

    events = []

    for a in soup.find_all("a", href=True):
        text = a.text.strip()
        link = a["href"]

        if "hackathon" in link and len(text) > 10:
            if not link.startswith("http"):
                link = "https://devfolio.co" + link

            events.append({
                "name": text[:80],
                "platform": "Devfolio",
                "location": "India",
                "date": "Upcoming",
                "type": "hackathon",
                "link": link
            })

    return events

async def scrape_unstop(session):
    url = "https://unstop.com/hackathons"
    html = await fetch(session, url)
    soup = BeautifulSoup(html, "html.parser")

    events = []

    for a in soup.find_all("a", href=True):
        text = a.text.strip()
        link = a["href"]

        if len(text) > 30 and "/competition/" in link:
            if not link.startswith("http"):
                link = "https://unstop.com" + link

            events.append({
                "name": text[:80],
                "platform": "Unstop",
                "location": "India",
                "date": "Ongoing",
                "type": "hackathon",
                "link": link
            })

    return events

async def scrape_all(event_type, states):
    async with aiohttp.ClientSession() as session:

        tasks = [
            scrape_devfolio(session),
            scrape_unstop(session),
            fetch_ctftime(),
            google_dork_events()
        ]

        results = await asyncio.gather(*tasks)

    events = []
    for r in results:
        events.extend(r)

    # Filter type
    if event_type != "all":
        events = [e for e in events if event_type in e["type"]]

    # Filter states
    if states:
        filtered = []
        for e in events:
            for s in states:
                if s.lower() in e["location"].lower():
                    filtered.append(e)
        if filtered:
            events = filtered

    return events