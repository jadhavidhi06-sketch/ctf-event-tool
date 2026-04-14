import requests
from bs4 import BeautifulSoup

def scrape_devfolio():
    url = "https://devfolio.co/hackathons"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    events = []

    cards = soup.find_all("div", class_="hackathon-card")

    for c in cards[:10]:
        try:
            name = c.text.strip()
            events.append({
                "name": name,
                "platform": "Devfolio",
                "location": "India",
                "date": "Upcoming",
                "type": "hackathon"
            })
        except:
            continue

    return events


def scrape_unstop():
    url = "https://unstop.com/hackathons"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    events = []

    cards = soup.find_all("div")

    for c in cards[:15]:
        text = c.text.strip()
        if len(text) > 40:
            events.append({
                "name": text[:80],
                "platform": "Unstop",
                "location": "India",
                "date": "Ongoing",
                "type": "hackathon"
            })

    return events


def scrape_events(event_type, states):
    events = []

    devfolio = scrape_devfolio()
    unstop = scrape_unstop()

    events.extend(devfolio)
    events.extend(unstop)

    # Filter by type
    if event_type != "all":
        events = [e for e in events if event_type in e["type"]]

    # Filter by states (basic keyword match)
    if states:
        filtered = []
        for e in events:
            for s in states:
                if s.lower() in e["location"].lower():
                    filtered.append(e)
        if filtered:
            events = filtered

    return events