import aiohttp
from bs4 import BeautifulSoup

QUERIES = [
    "ctf competition India 2026",
    "hackathon India upcoming",
    "coding competition India students"
]

async def google_dork_events():
    events = []

    async with aiohttp.ClientSession() as session:
        for q in QUERIES:
            url = f"https://www.bing.com/search?q={q}"

            async with session.get(url) as res:
                html = await res.text()

            soup = BeautifulSoup(html, "html.parser")

            for a in soup.find_all("a", href=True):
                text = a.text.strip()
                link = a["href"]

                if len(text) > 30 and link.startswith("http"):
                    events.append({
                        "name": text[:100],
                        "platform": "Search",
                        "location": "India",
                        "date": "Check Link",
                        "type": "coding",
                        "link": link
                    })

    return events