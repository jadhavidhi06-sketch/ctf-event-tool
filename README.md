
# 🔐 CTFForge CLI v3.0

An interactive, command-line CTF event aggregator heavily optimized and focused on the Indian cybersecurity ecosystem. `CTFForge CLI` concurrently scrapes upcoming and ongoing Capture The Flag competitions from multiple open intelligence platforms, filters them based on geographic location, and runs a custom scoring algorithm to rank the best events for you.

Developed by **[VRJ](https://github.com/jadhavidhi06-sketch)**.

---

## 🚀 Features

* **Multi-Source Aggregation:** Concurrently scrapes event data using the CTFtime API, live CTFtime HTML parsing (via Playwright), and the CTF Hunt API.
* **Smart AI Ranking:** Automatically ranks events based on proximity to start date, participant weight, prize availability, and localized relevance.
* **Geo-Targeted Filtering:** Easily filter offline/on-site events across 36 Indian States and Union Territories while ensuring online events remain visible.
* **Beautiful Terminal UI:** Styled entirely with `rich` panels, progress bars, tables, and color-coded competition weights.
* **Clickable Links:** Generates fully interactive terminal links to immediately open CTF landing pages right from your CLI shell.
* **Data Export:** Seamlessly dump your filtered CTF matching matrix into clean, formatted `.json` or `.csv` files for external analysis.

---

## 🛠️ Prerequisites & Installation

Make sure you have **Python 3.8+** installed on your system. 

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/jadhavidhi06-sketch/ctf-event-tool.git](https://github.com/jadhavidhi06-sketch/ctf-event-tool.git)
   cd ctf-event-tool



2. **Install Required Packages:**
Install the structural dependencies using `requirements.txt`:
```bash
pip install -r requirements.txt

```


*(Note: Essential dependencies include `httpx`, `playwright`, and `rich`)*
3. **Install Playwright Chromium Browser:**
The tool utilizes a headless browser instances to scrape supplementary details dynamically. Run the following setup command:
```bash
playwright install chromium

```



---

## 🖥️ Usage

Fire up the interactive CLI by running the script directly:

```bash
python eventforge.py

```

### Interactive Steps:

1. **State Selection:** Choose whether you want to filter for specific Indian states (supports choosing single states, comma-separated combinations, or typing `all`).
2. **Event Filtering:** Filter down the parsed timeline:
* `1` - All CTF Events
* `2` - Only Upcoming CTF Events
* `3` - Only Ongoing CTF Events
* `4` - Only Offline CTF Events
* `5` - Only High Weight CTF Events (>50)


3. **Sorting Parameters:** Choose your viewport priority: **AI Ranked (Recommended)**, Start Date, Participants Count, or CTF Weight.
4. **Inspect & Save:** Inspect detailed records directly in the terminal, then opt-in to instantly export data records to `.json` or `.csv`.

---

## 📊 AI Scoring Metrics

The algorithm evaluates and assigns a score up to `200.0` points per event using these parameters:

* **Base Value:** Begins at `100.0` points.
* **Urgency:** Penalizes `-6` points for every day remaining until the launch window (incentivizes closer events).
* **Location Boost:** Grants an immediate `+45` points if located in an Indian region and `+15` if it features an offline footprint.
* **Activity & Incentives:** Scales exponentially based on active participant pools, rewards a `+20` booster for prize pools, and multipliers based on official CTFtime weight.

---

## 🤝 Connect

* **GitHub:** [@jadhavidhi06-sketch](https://github.com/jadhavidhi06-sketch)
* **LinkedIn:** [vidhi-jadhav](https://www.google.com/search?q=https://linkedin.com/in/vidhi-jadhav)

Happy Hacking! 🎉

Made with Love For Indian CTF Players !!!!
