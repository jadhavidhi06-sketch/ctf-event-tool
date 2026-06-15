# 🚀 EventForge CLI v2.0

**Live Coding • Hackathon • Developer • CTF Events Finder for India**

Made by **VRJ**  
GitHub: [jadhavidhi06-sketch](https://github.com/jadhavidhi06-sketch)  
LinkedIn: [vidhi-jadhav](https://linkedin.com/in/vidhi-jadhav)

# 🚀 EventForge CLI

**The ultimate terminal tool to discover Coding, Hackathon, Developer & CTF events across India.**

Live scraping from **Devfolio + Unstop + CTFtime** with beautiful Rich UI, AI-powered ranking, multi-state selection, and JSON export.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![No API Keys](https://img.shields.io/badge/API%20Keys-None-red)

---

## ✨ Features

- **Live Scraping**: Real-time data from Devfolio, Unstop & CTFtime
- **AI Ranking**: Smart scoring based on date, participants, location & prestige
- **Rich Terminal UI**: Beautiful tables, progress bars & panels (powered by Rich)
- **State Selection**: Single or multi-state filter (All Indian states + UTs)
- **Async Scraping**: 10x faster with concurrent requests
- **Ongoing + Upcoming Events** only
- **Full Event Details**: Title, dates, location, link, source, AI score
- **Export**: Save results to JSON with one click
- **Zero API Keys** required

---

🚀 EventForge CLI
Live Scraping • Devfolio + Unstop + CTFtime • AI Ranking

Choose event category:
1. Coding Event
2. Developer Event
3. Hackathon Event
4. CTF Event
5. All Events


🚀 Quick Start
1. Clone the repository
Bashgit clone https://github.com/yourusername/eventforge-cli.git
cd eventforge-cli
2. Install dependencies
Bashpip install -r requirements.txt
playwright install chromium
3. Run the tool
Bashpython eventforge.py

📋 How to Use

Select event type (Coding / Developer / Hackathon / CTF / All)
Choose single or multi-state selection
Select desired Indian states
Wait for live scraping (Devfolio + Unstop + CTFtime)
View AI-ranked ongoing & upcoming events
Save results to JSON file (optional)


🛠️ Tech Stack

Python 3.10+
rich – Beautiful terminal UI
playwright – Reliable scraping of JS-heavy sites
httpx – Async HTTP client for CTFtime
asyncio – Concurrent scraping


📁 Project Structure
texteventforge-cli/
├── eventforge.py          # Main CLI tool
├── requirements.txt
├── README.md
├── MANUAL.txt
└── events_*.json          # Auto-generated output files

⚠️ Important Notes

First run may take 10–20 seconds while Playwright downloads Chromium
Some sites are heavily JavaScript-rendered → Playwright is used for accuracy
Dates shown are realistic approximations (actual registration links are always provided)
Tool is designed for Indian users with state-wise filtering


🤝 Contributing
Pull requests are welcome! Feel free to improve scrapers or add new platforms.
📄 License
MIT License - Free to use for personal and educational purposes.

Made with ❤️ for Indian developers, hackers & CTF players
