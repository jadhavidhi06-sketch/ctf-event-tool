import aiohttp

async def fetch_ctftime():
    url = "https://ctftime.org/api/v1/events/"

    events = []

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            data = await res.json()

            for e in data[:20]:
                events.append({
                    "name": e.get("title"),
                    "platform": "CTFtime",
                    "location": e.get("location", "Online"),
                    "date": e.get("start", "")[:10],
                    "type": "ctf",
                    "link": e.get("url")
                })

    return events