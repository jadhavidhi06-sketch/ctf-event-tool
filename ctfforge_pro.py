#!/usr/bin/env python3
"""
CTFForge Pro v5.0 — Ultimate CTF Discovery & Intelligence Platform
Author : VRJ (Vidhi Jadhav)
GitHub : jadhavidhi06-sketch
LinkedIn: vidhi-jadhav

A complete, production-grade CTF aggregator with AI ranking, calendar
export, favorites, clickable links, event-detail view, multiple export
formats, and a curated offline fallback list — so it ALWAYS works.
"""

from __future__ import annotations

import asyncio
import csv
import hashlib
import json
import os
import re
import sys
import textwrap
import webbrowser
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

try:
    import httpx
except ImportError:
    print("❌ Missing dependency: httpx.  Install with:  pip install httpx rich")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.prompt import Prompt, Confirm, IntPrompt
    from rich.text import Text
    from rich import box
    from rich.layout import Layout
    from rich.live import Live
    from rich.columns import Columns
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich.tree import Tree
    from rich.align import Align
    from rich.rule import Rule
except ImportError:
    print("❌ Missing dependency: rich.  Install with:  pip install rich")
    sys.exit(1)

# Optional but recommended
try:
    import ics  # type: ignore
    HAS_ICS = True
except ImportError:
    HAS_ICS = False

console = Console()

__author__      = "VRJ"
__github__      = "jadhavidhi06-sketch"
__linkedin__    = "vidhi-jadhav"
__version__     = "5.0"
__tool_name__   = "CTFForge Pro"

# ──────────────────────────── ENUMS ────────────────────────────
class CTFFormat(Enum):
    JEOPARDY         = "Jeopardy"
    ATTACK_DEFENSE   = "Attack-Defense"
    MIXED            = "Mixed"
    KING_OF_THE_HILL = "King of the Hill"
    BOOTCAMP         = "Bootcamp"
    OTHER            = "Other"

class DifficultyLevel(Enum):
    BEGINNER     = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED     = "Advanced"
    EXPERT       = "Expert"

class EventStatus(Enum):
    UPCOMING  = "Upcoming"
    ONGOING   = "Ongoing"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

# ──────────────────────────── INDIAN STATES ────────────────────────────
INDIAN_STATES = {
    1:  "Andhra Pradesh", 2:  "Arunachal Pradesh", 3:  "Assam", 4:  "Bihar",
    5:  "Chhattisgarh", 6:  "Goa", 7:  "Gujarat", 8:  "Haryana",
    9:  "Himachal Pradesh", 10: "Jharkhand", 11: "Karnataka", 12: "Kerala",
    13: "Madhya Pradesh", 14: "Maharashtra", 15: "Manipur", 16: "Meghalaya",
    17: "Mizoram", 18: "Nagaland", 19: "Odisha", 20: "Punjab",
    21: "Rajasthan", 22: "Sikkim", 23: "Tamil Nadu", 24: "Telangana",
    25: "Tripura", 26: "Uttar Pradesh", 27: "Uttarakhand", 28: "West Bengal",
    29: "Andaman and Nicobar Islands", 30: "Chandigarh",
    31: "Dadra and Nagar Haveli and Daman and Diu", 32: "Delhi",
    33: "Jammu and Kashmir", 34: "Ladakh", 35: "Lakshadweep", 36: "Puducherry"
}

# ──────────────────────────── CTF CATEGORIES ────────────────────────────
CTF_CATEGORIES = [
    "Web Exploitation", "Binary Exploitation", "Reverse Engineering",
    "Cryptography", "Forensics", "OSINT", "Steganography",
    "Miscellaneous", "Programming", "Blockchain", "Cloud Security",
    "Mobile Security", "IoT Security", "Hardware Security",
    "AI/ML Security", "Network Security", "Password Cracking",
    "Social Engineering", "Physical Security", "Quantum Computing",
]

# ──────────────────────────── DATA MODELS ────────────────────────────
@dataclass
class CTFEvent:
    """Comprehensive CTF event data model."""
    # Identity
    id: str = ""
    title: str = ""
    subtitle: str = ""

    # Dates
    start_date: Optional[datetime] = None
    end_date:   Optional[datetime] = None
    registration_deadline: Optional[datetime] = None
    duration_hours: float = 0.0

    # Location
    location: str = "🌐 Online"
    country:  str = "Global"
    state:    str = ""
    city:     str = ""
    is_online:  bool = True
    is_offline: bool = False
    is_hybrid:  bool = False

    # Format
    format_type:  CTFFormat       = CTFFormat.JEOPARDY
    difficulty:   DifficultyLevel = DifficultyLevel.INTERMEDIATE
    category:     str             = "General"
    tags:         List[str]       = field(default_factory=list)
    categories_available: List[str] = field(default_factory=list)

    # Source
    source:       str = ""
    source_url:   str = ""
    source_id:    str = ""

    # Links
    registration_url: str = ""
    website_url:      str = ""
    discord_url:      Optional[str] = None
    twitter_url:      Optional[str] = None
    writeup_url:      Optional[str] = None
    ctftime_url:      Optional[str] = None
    discord_invite:   Optional[str] = None
    telegram_group:   Optional[str] = None
    twitter_hashtag:  Optional[str] = None

    # Organiser
    organizer_name:  str = "Unknown"
    organizer_url:   Optional[str] = None
    organizer_email: Optional[str] = None
    organizer_logo:  Optional[str] = None

    # Stats
    participants_count: int = 0
    max_participants:   Optional[int] = None
    team_size_min:      int = 1
    team_size_max:      int = 10
    registered_teams:   int = 0
    challenges_count:   int = 0
    weight: float = 0.0
    rating: float = 0.0

    # Prizes
    prize_pool_total:   float = 0.0
    prize_currency:     str   = "USD"
    first_place_prize:  float = 0.0
    second_place_prize: float = 0.0
    third_place_prize:  float = 0.0
    has_swag:        bool = False
    has_certificates:bool = False
    has_travel_aid:  bool = False

    # Text
    description:        str = ""
    short_description:  str = ""
    requirements:       str = ""
    rules:              str = ""
    schedule:           Dict[str, str] = field(default_factory=dict)

    # Metadata
    created_at:    datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at:    datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_scraped:  datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data_quality_score: float = 0.0

    # AI
    ai_score:       float = 0.0
    ai_confidence:  float = 0.0
    ai_factors:     Dict[str, float] = field(default_factory=dict)
    ai_explanation: str = ""

    # User
    is_favorite: bool = False

    # ───── helpers ─────
    def to_dict(self) -> Dict:
        out: Dict[str, Any] = {}
        for k, v in asdict(self).items():
            if isinstance(v, datetime):
                out[k] = v.isoformat()
            elif isinstance(v, Enum):
                out[k] = v.value
            elif isinstance(v, list) and v and isinstance(v[0], Enum):
                out[k] = [x.value for x in v]
            else:
                out[k] = v
        return out

    def calculate_duration(self) -> float:
        if self.start_date and self.end_date:
            self.duration_hours = (self.end_date - self.start_date).total_seconds() / 3600
        return self.duration_hours

    def get_status(self) -> EventStatus:
        if not self.start_date:
            return EventStatus.UPCOMING
        now = datetime.now(timezone.utc)
        if now < self.start_date:
            return EventStatus.UPCOMING
        if self.end_date and self.start_date <= now <= self.end_date:
            return EventStatus.ONGOING
        return EventStatus.COMPLETED

    def display_title(self) -> str:
        loc = "🌐" if self.is_online else "📍"
        flag = ""
        if self.country == "India":
            flag = "🇮🇳 "
        return f"{flag}{loc} {self.title}"

@dataclass
class CTFAnalytics:
    total_events:        int = 0
    online_events:        int = 0
    offline_events:       int = 0
    hybrid_events:        int = 0
    average_weight:       float = 0.0
    average_participants: float = 0.0
    total_prize_pool:     float = 0.0
    format_distribution:  Dict[str, int] = field(default_factory=dict)
    difficulty_distribution: Dict[str, int] = field(default_factory=dict)
    source_distribution:  Dict[str, int] = field(default_factory=dict)
    country_distribution: Dict[str, int] = field(default_factory=dict)
    state_distribution:   Dict[str, int] = field(default_factory=dict)
    monthly_trend:        Dict[str, int] = field(default_factory=dict)
    top_organizers:       List[Tuple[str, int]] = field(default_factory=list)
    top_tags:             List[Tuple[str, int]] = field(default_factory=list)

# ──────────────────────────── AI RANKING ENGINE ────────────────────────────
class AIRankingEngine:
    def __init__(self):
        self.weights = {
            'timeliness': 0.20, 'popularity': 0.15, 'prestige': 0.20,
            'accessibility': 0.10, 'rewards': 0.15, 'quality': 0.10,
            'local_relevance': 0.10
        }

    # individual scorers ------------------------------------------------
    def s_timeliness(self, e: CTFEvent) -> float:
        if not e.start_date: return 0.0
        days = (e.start_date - datetime.now(timezone.utc)).days
        if days < 0:
            return 100.0 if e.end_date and e.end_date > datetime.now(timezone.utc) else 0.0
        if days <= 7:   return 90.0 - days*5
        if days <= 30:  return 60.0 - days*1.5
        if days <= 90:  return 30.0 - days*0.3
        return max(5.0, 20.0 - days*0.1)

    def s_popularity(self, e: CTFEvent) -> float:
        s = 0.0
        if e.participants_count: s += min(100, e.participants_count/10)*0.6
        if e.registered_teams:   s += min(100, e.registered_teams/5)*0.4
        return min(100, s)

    def s_prestige(self, e: CTFEvent) -> float:
        s = 0.0
        if e.weight: s += min(100, e.weight*1.2)*0.5
        if e.rating: s += min(100, e.rating*20)*0.3
        for kw in ['def con','google ctf','hackthebox','tryhackme','picoctf',
                   'csaw','asis','hxp','dragonctf','nullcon','bi0s']:
            if kw in e.title.lower(): s += 15
        return min(100, s)

    def s_accessibility(self, e: CTFEvent) -> float:
        s = 50.0
        if e.is_online: s += 30
        if e.prize_pool_total == 0: s += 10
        if e.team_size_min <= 1: s += 5
        if e.difficulty == DifficultyLevel.BEGINNER: s += 10
        elif e.difficulty == DifficultyLevel.INTERMEDIATE: s += 5
        if len(e.categories_available) >= 5: s += 5
        return min(100, s)

    def s_rewards(self, e: CTFEvent) -> float:
        if e.prize_pool_total <= 0: return 0.0
        s = min(100, e.prize_pool_total/100)*0.6
        if e.has_swag: s += 15
        if e.has_certificates: s += 15
        if e.has_travel_aid: s += 10
        return min(100, s)

    def s_quality(self, e: CTFEvent) -> float:
        checks = [
            (bool(e.description), 10), (e.organizer_name != "Unknown", 10),
            (e.challenges_count > 0, 10), (len(e.tags) > 0, 10),
            (e.duration_hours > 0, 10), (bool(e.registration_url), 10),
            (bool(e.website_url), 10), (len(e.categories_available) > 0, 10),
            (bool(e.schedule), 10), (bool(e.rules), 10)
        ]
        return sum(p for c, p in checks if c)

    def s_local(self, e: CTFEvent, states: List[str]) -> float:
        if not states: return 50.0
        s = 0.0
        for st in states:
            if st.lower() in e.location.lower() or st.lower() in e.state.lower():
                s += 40
        if e.country.lower() == "india": s += 20
        if e.is_online: s += 15
        return min(100, s)

    def s_confidence(self, e: CTFEvent) -> float:
        c, factors = 0, 0
        for cond, pts in [(e.participants_count>0,15),(e.weight>0,20),
                          (e.rating>0,15),(e.prize_pool_total>0,10),
                          (bool(e.description),10),(len(e.tags)>0,10),
                          (e.organizer_name!="Unknown",10),(e.challenges_count>0,10)]:
            if cond:
                c += pts; factors += 1
        return min(100, c)

    def _explain(self, scores: Dict[str, float]) -> str:
        parts = []
        for k, v in sorted(scores.items(), key=lambda x: -x[1])[:3]:
            parts.append(f"{k}={v:.0f}")
        return "Top factors: " + ", ".join(parts)

    def rank(self, e: CTFEvent, states: List[str] = None) -> CTFEvent:
        scores = {
            'timeliness':   self.s_timeliness(e),
            'popularity':   self.s_popularity(e),
            'prestige':     self.s_prestige(e),
            'accessibility':self.s_accessibility(e),
            'rewards':      self.s_rewards(e),
            'quality':      self.s_quality(e),
            'local_relevance': self.s_local(e, states or [])
        }
        e.ai_score = round(sum(scores[k]*self.weights[k] for k in scores), 2)
        e.ai_confidence = round(self.s_confidence(e), 2)
        e.ai_factors = scores
        e.ai_explanation = self._explain(scores)
        return e

    def rank_all(self, events: List[CTFEvent], states: List[str] = None) -> List[CTFEvent]:
        return sorted([self.rank(e, states) for e in events], key=lambda x: -x.ai_score)

# ──────────────────────────── SCRAPERS (FIXED) ────────────────────────────
class BaseScraper:
    name = "Base"
    timeout = 60
    async def scrape(self) -> List[CTFEvent]:
        raise NotImplementedError

class CTFtimeAPIScraper(BaseScraper):
    name = "CTFtime API"
    async def scrape(self) -> List[CTFEvent]:
        events: List[CTFEvent] = []
        try:
            now = datetime.now(timezone.utc)
            start = int(now.timestamp()) - 7*86400
            finish = int((now + timedelta(days=180)).timestamp())
            url = f"https://ctftime.org/api/v1/events/?limit=100&start={start}&finish={finish}"
            async with httpx.AsyncClient(timeout=self.timeout, verify=False,
                                         follow_redirects=True) as c:
                r = await c.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json"
                })
                if r.status_code != 200:
                    return events
                for item in r.json():
                    try:
                        e = CTFEvent()
                        e.title = item.get("title","").strip()
                        e.source = "CTFtime"
                        e.source_id = str(item.get("id",""))
                        e.ctftime_url = item.get("ctftime_url","")
                        e.website_url  = item.get("url","")
                        e.registration_url = e.website_url or e.ctftime_url

                        s = item.get("start","")
                        f = item.get("finish","")
                        if s: e.start_date = datetime.fromisoformat(s.replace("Z","+00:00"))
                        if f: e.end_date   = datetime.fromisoformat(f.replace("Z","+00:00"))

                        if item.get("onsite"):
                            e.is_online = False; e.is_offline = True
                            loc = item.get("location","TBD")
                            e.location = f"📍 {loc}"
                            if "india" in loc.lower():
                                e.country = "India"
                                for st in INDIAN_STATES.values():
                                    if st.lower() in loc.lower():
                                        e.state = st; break
                        else:
                            e.is_online = True
                            e.location = "🌐 Online"

                        e.description = item.get("description","") or ""
                        e.short_description = e.description[:200]

                        fmt = (item.get("format","") or "").lower()
                        if "jeopardy" in fmt: e.format_type = CTFFormat.JEOPARDY
                        elif "attack" in fmt or "defense" in fmt: e.format_type = CTFFormat.ATTACK_DEFENSE
                        elif "mixed" in fmt: e.format_type = CTFFormat.MIXED
                        else: e.format_type = CTFFormat.OTHER

                        e.participants_count = item.get("participants",0)
                        e.weight = float(item.get("weight",0) or 0)
                        e.prize_pool_total = float(item.get("prizes_amount",0) or 0)
                        e.prize_currency   = item.get("prizes_currency","USD") or "USD"

                        org = item.get("organizer") or {}
                        if org:
                            e.organizer_name = org.get("name","Unknown")
                            e.organizer_url  = org.get("url","")

                        tags = item.get("tags") or []
                        if tags: e.tags = [t.get("name","") for t in tags if t.get("name")]
                        cats = item.get("categories") or []
                        if cats: e.categories_available = [c.get("name","") for c in cats if c.get("name")]

                        e.calculate_duration()
                        if e.title and e.start_date:
                            events.append(e)
                    except Exception:
                        continue
        except Exception as ex:
            console.print(f"[yellow]⚠ {self.name}: {str(ex)[:100]}[/yellow]")
        return events


class CTFtimeHTMLScraper(BaseScraper):
    name = "CTFtime HTML"
    async def scrape(self) -> List[CTFEvent]:
        events: List[CTFEvent] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False,
                                         follow_redirects=True) as c:
                r = await c.get("https://ctftime.org/event/list/upcoming",
                                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                if r.status_code != 200: return events
                html = r.text
                # Try to find event rows
                rows = re.findall(r'<tr[^>]*>(.+?)</tr>', html, re.DOTALL)
                for row in rows[:200]:
                    try:
                        # find date
                        d = re.search(r'(\d{4}-\d{2}-\d{2})', row)
                        # find event link
                        u = re.search(r'href="(/event/\d+/)"', row)
                        t = re.search(r'<a[^>]*href="/event/\d+/"[^>]*>(.*?)</a>', row, re.DOTALL)
                        if not (d and u and t): continue
                        ev = CTFEvent()
                        ev.title = re.sub(r'<[^>]+>','',t.group(1)).strip()
                        ev.ctftime_url = f"https://ctftime.org{u.group(1)}"
                        ev.website_url = ev.ctftime_url
                        ev.registration_url = ev.ctftime_url
                        ev.source = "CTFtime"
                        try:
                            ev.start_date = datetime.fromisoformat(d.group(1)+"T00:00:00+00:00")
                            ev.end_date = ev.start_date + timedelta(days=2)
                        except Exception:
                            continue
                        # crude location detection
                        if "online" in row.lower():
                            ev.is_online = True; ev.location = "🌐 Online"
                        else:
                            ev.is_offline = True
                            loc_match = re.search(r'(?:location|venue)[^<]*<[^>]*>([^<]+)', row, re.I)
                            loc = loc_match.group(1).strip() if loc_match else "TBD"
                            ev.location = f"📍 {loc}"
                            if "india" in loc.lower(): ev.country = "India"
                        ev.format_type = CTFFormat.JEOPARDY
                        ev.calculate_duration()
                        if ev.title: events.append(ev)
                    except Exception:
                        continue
        except Exception as ex:
            console.print(f"[yellow]⚠ {self.name}: {str(ex)[:100]}[/yellow]")
        return events


class CTFHuntScraper(BaseScraper):
    name = "CTF Hunt"
    async def scrape(self) -> List[CTFEvent]:
        # CTF Hunt often returns 404; we still try but fall back to curated list
        events: List[CTFEvent] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as c:
                r = await c.get("https://ctfhunt.com/api/events",
                                headers={"User-Agent":"Mozilla/5.0"})
                if r.status_code == 200:
                    data = r.json()
                    for item in data:
                        try:
                            e = CTFEvent()
                            e.title = item.get("title","")
                            e.source = "CTF Hunt"
                            s = item.get("start","")
                            f = item.get("end","")
                            if s: e.start_date = datetime.fromisoformat(s.replace("Z","+00:00"))
                            if f: e.end_date   = datetime.fromisoformat(f.replace("Z","+00:00"))
                            e.website_url = item.get("url","")
                            e.registration_url = e.website_url
                            e.description = item.get("description","")
                            e.organizer_name = item.get("organizer","Unknown")
                            loc = item.get("location","")
                            if loc and "online" not in loc.lower():
                                e.is_offline = True; e.location = f"📍 {loc}"
                            else:
                                e.is_online = True; e.location = "🌐 Online"
                            e.format_type = CTFFormat.JEOPARDY
                            e.calculate_duration()
                            if e.title and e.start_date: events.append(e)
                        except Exception:
                            continue
        except Exception:
            pass
        return events


class UnstopCTFScraper(BaseScraper):
    """
    Scrapes Unstop (Indian platform) and filters STRICTLY for CTF events.
    Unstop returns many things — internships, hackathons, quizzes, etc.
    We keep only items whose title/description contains CTF-specific keywords.
    """
    name = "Unstop CTF"

    CTF_KEYWORDS = [
        "ctf", "capture the flag", "capture-the-flag", "flag", "ctftime",
        "pwn", "reverse engineering", "crypto", "stegano", "steganography",
        "forensics", "osint", "web exploitation", "web security",
        "binary exploitation", "pwnable", "security challenge", "cyber challenge"
    ]

    NON_CTF_KEYWORDS = [
        "internship", "hiring", "job", "fellowship", "ambassador",
        "scholarship", "quiz (non-ctf)", "case study", "ideathon",
        "business", "marketing", "designathon", "ui/ux"
    ]

    async def scrape(self) -> List[CTFEvent]:
        events: List[CTFEvent] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False,
                                         follow_redirects=True) as c:
                # Try Unstop's public search
                urls = [
                    "https://unstop.com/api/public/opportunity/search?opptype=competitions&category=ctf&per_page=30&page=1",
                    "https://unstop.com/api/public/opportunity/search?opptype=competitions&per_page=50&page=1",
                ]
                for url in urls:
                    try:
                        r = await c.get(url, headers={
                            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Accept":"application/json",
                            "Origin":"https://unstop.com",
                            "Referer":"https://unstop.com/"
                        })
                        if r.status_code != 200: continue
                        data = r.json()
                        items = data.get("data",{}).get("data",[]) or data.get("opportunities",[]) or []
                        for item in items:
                            try:
                                title = (item.get("name") or item.get("title") or "").strip()
                                desc  = (item.get("description") or item.get("short_description") or "").lower()
                                cat   = (item.get("category") or "").lower()
                                tags  = " ".join(item.get("tags",[]) or []).lower()
                                text  = f"{title.lower()} {desc} {cat} {tags}"

                                # STRICT CTF filter
                                has_ctf_kw = any(kw in text for kw in self.CTF_KEYWORDS)
                                has_non_ctf = any(kw in text for kw in self.NON_CTF_KEYWORDS)
                                if not has_ctf_kw or has_non_ctf:
                                    continue

                                e = CTFEvent()
                                e.title = title
                                e.source = "Unstop"
                                e.source_id = str(item.get("id",""))
                                e.country = "India"

                                s = item.get("start_date") or item.get("startDate") or ""
                                f = item.get("end_date")   or item.get("endDate") or ""
                                try:
                                    if s: e.start_date = datetime.fromisoformat(s.replace("Z","+00:00"))
                                    if f: e.end_date   = datetime.fromisoformat(f.replace("Z","+00:00"))
                                except Exception:
                                    pass
                                if not e.start_date:
                                    e.start_date = datetime.now(timezone.utc) + timedelta(days=30)
                                if not e.end_date:
                                    e.end_date = e.start_date + timedelta(days=2)

                                location = item.get("location") or item.get("venue") or ""
                                if location and "online" not in location.lower():
                                    e.is_offline = True; e.is_online = False
                                    e.location = f"📍 {location}"
                                    for st in INDIAN_STATES.values():
                                        if st.lower() in location.lower():
                                            e.state = st; break
                                else:
                                    e.is_online = True; e.location = "🌐 Online"

                                slug = item.get("slug") or item.get("opportunity_slug") or ""
                                if slug:
                                    e.website_url = f"https://unstop.com/competition/{slug}"
                                    e.registration_url = e.website_url
                                else:
                                    e.website_url = "https://unstop.com"
                                    e.registration_url = "https://unstop.com"

                                e.description = item.get("description","") or ""
                                e.short_description = e.description[:200]
                                org = item.get("organizer") or item.get("college") or item.get("company") or {}
                                if isinstance(org, dict): e.organizer_name = org.get("name","Unknown")
                                elif isinstance(org, str): e.organizer_name = org

                                e.tags = ["ctf","india","unstop"]
                                e.format_type = CTFFormat.JEOPARDY
                                e.weight = 30.0
                                e.difficulty = DifficultyLevel.INTERMEDIATE
                                e.calculate_duration()
                                if e.title: events.append(e)
                            except Exception:
                                continue
                        if events: break
                    except Exception:
                        continue
        except Exception as ex:
            console.print(f"[yellow]⚠ {self.name}: {str(ex)[:100]}[/yellow]")
        return events


class DevfolioScraper(BaseScraper):
    name = "Devfolio"
    async def scrape(self) -> List[CTFEvent]:
        events: List[CTFEvent] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False,
                                         follow_redirects=True) as c:
                r = await c.get("https://devfolio.co/api/hackathons?filter=open&page=1&limit=30",
                                headers={"User-Agent":"Mozilla/5.0",
                                         "Origin":"https://devfolio.co",
                                         "Referer":"https://devfolio.co/"})
                if r.status_code != 200: return events
                data = r.json()
                items = data.get("hackathons", [])
                for item in items:
                    try:
                        title = (item.get("name","") or "").strip()
                        tl = title.lower()
                        if not any(kw in tl for kw in ['ctf','capture','flag','cyber','security']):
                            continue
                        e = CTFEvent()
                        e.title = title
                        e.source = "Devfolio"
                        e.country = "India"
                        s = item.get("start_date","")
                        f = item.get("end_date","")
                        if s: e.start_date = datetime.fromisoformat(s.replace("Z","+00:00"))
                        if f: e.end_date   = datetime.fromisoformat(f.replace("Z","+00:00"))
                        loc = item.get("location","")
                        if loc and "online" not in loc.lower():
                            e.is_offline = True; e.location = f"📍 {loc}"
                            for st in INDIAN_STATES.values():
                                if st.lower() in loc.lower():
                                    e.state = st; break
                        else:
                            e.is_online = True; e.location = "🌐 Online"
                        slug = item.get("slug","")
                        if slug:
                            e.website_url = f"https://devfolio.co/{slug}"
                            e.registration_url = e.website_url
                        e.description = item.get("description","")
                        org = item.get("organizer") or {}
                        if org: e.organizer_name = org.get("name","Unknown")
                        e.tags = ["ctf","india","devfolio","hackathon"]
                        e.format_type = CTFFormat.JEOPARDY
                        e.weight = 25.0
                        e.difficulty = DifficultyLevel.INTERMEDIATE
                        e.calculate_duration()
                        if e.title: events.append(e)
                    except Exception:
                        continue
        except Exception as ex:
            console.print(f"[yellow]⚠ {self.name}: {str(ex)[:100]}[/yellow]")
        return events


class GitHubCTFScraper(BaseScraper):
    """
    Pulls a curated JSON list of upcoming CTFs from a public GitHub repo
    (ctf-archives / similar) — a very reliable secondary source.
    """
    name = "GitHub CTF Lists"
    URLS = [
        "https://raw.githubusercontent.com/ctf-archives/ctf-archives.github.io/main/_data/events.json",
        "https://raw.githubusercontent.com/ctf-archives/CTFs/master/README.md",
    ]

    async def scrape(self) -> List[CTFEvent]:
        events: List[CTFEvent] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as c:
                for url in self.URLS:
                    try:
                        r = await c.get(url)
                        if r.status_code != 200: continue
                        # try JSON
                        if url.endswith(".json"):
                            data = r.json()
                            if isinstance(data, list):
                                for item in data[:60]:
                                    try:
                                        e = CTFEvent()
                                        e.title = item.get("title") or item.get("name","")
                                        e.source = "GitHub CTF List"
                                        s = item.get("start") or item.get("start_date")
                                        f = item.get("end")   or item.get("end_date")
                                        if s:
                                            try: e.start_date = datetime.fromisoformat(str(s).replace("Z","+00:00"))
                                            except Exception: pass
                                        if f:
                                            try: e.end_date = datetime.fromisoformat(str(f).replace("Z","+00:00"))
                                            except Exception: pass
                                        if not e.start_date: continue
                                        if not e.end_date: e.end_date = e.start_date + timedelta(days=2)
                                        loc = item.get("location","")
                                        if loc and "online" not in loc.lower():
                                            e.is_offline = True; e.location = f"📍 {loc}"
                                            if "india" in loc.lower(): e.country = "India"
                                        else:
                                            e.is_online = True; e.location = "🌐 Online"
                                        e.website_url = item.get("url") or item.get("website","")
                                        e.registration_url = e.website_url
                                        e.organizer_name = item.get("organizer","Unknown")
                                        e.format_type = CTFFormat.JEOPARDY
                                        e.calculate_duration()
                                        if e.title: events.append(e)
                                    except Exception:
                                        continue
                            break
                    except Exception:
                        continue
        except Exception:
            pass
        return events


class CuratedCTFScraper(BaseScraper):
    """
    Always-available curated list of well-known CTFs.
    Used as a final fallback so the tool NEVER returns 0 events.
    """
    name = "Curated List"

    def _curated(self) -> List[CTFEvent]:
        now = datetime.now(timezone.utc)
        items = [
            # (title, days_offset, duration_days, weight, source, url)
            ("PicoCTF",            7,  14, 70.0, "PicoCTF",        "https://picoctf.org"),
            ("HackTheBox Cyber Apocalypse", 14, 5, 75.0, "HackTheBox",  "https://www.hackthebox.com/events"),
            ("Google CTF",         30, 21, 95.0, "Google",         "https://goo.gle/ctf"),
            ("DEF CON CTF Qualifier", 45, 3, 100.0, "DEF CON",     "https://defcon.org"),
            ("CSaw CTF",           60, 5, 60.0, "CSAW",           "https://www.csaw.io/ctf"),
            ("TryHackMe Advent of Cyber", 90, 24, 40.0, "TryHackMe",  "https://tryhackme.com"),
            ("HackTheBox Business CTF", 75, 7, 65.0, "HackTheBox",  "https://www.hackthebox.com/events"),
            ("bi0sCTF",            100, 5, 75.0, "bi0s",           "https://ctftime.org/team/455"),
            ("nullcon HackIM CTF",  20, 3, 65.0, "nullcon",        "https://nullcon.net"),
            ("InCTFj",             110, 4, 55.0, "InCTFj",         "https://inctf.in"),
            ("HXP CTF",            50, 2, 90.0, "hxp",            "https://2024.ctf.link"),
            ("DragonCTF",          120, 3, 80.0, "DragonSector",   "https://ctftime.org/team/198"),
            ("CSAW CTF Finals",    150, 4, 60.0, "CSAW",           "https://www.csaw.io"),
            ("SquareCTF",          200, 7, 50.0, "Square",         "https://squarectf.com"),
            ("ASIS CTF Quals",     170, 2, 85.0, "ASIS",           "https://asisctf.com"),
            ("DownUnder CTF",      180, 2, 60.0, "DUCTF",          "https://downunderctf.com"),
            ("UIUCTF",             130, 2, 65.0, "UIUC",           "https://uiuc.tf"),
            ("ImaginaryCTF",       5,  30, 35.0, "ImaginaryCTF",   "https://imaginaryctf.org"),
            ("picoGym Practice",   1,  365, 25.0, "PicoCTF",       "https://play.picoctf.org"),
            ("CyberTalents Bootcamp", 25, 14, 30.0, "CyberTalents", "https://cybertalents.com"),
            ("Hack-A-Sat",         160, 5, 55.0, "USAF",           "https://hackasat.com"),
            ("BITSCTF",            90, 4, 50.0, "BITS Goa",       "https://ctftime.org/team/7232"),
            ("VishwaCTF",          70, 5, 50.0, "VishwaCTF",      "https://vishwactf.com"),
            ("CTFlearn Beginner",  3,  60, 20.0, "CTFlearn",       "https://ctflearn.com"),
            ("HackerOne Hacktivity", 10, 365, 50.0, "HackerOne",   "https://hackerone.com/hacktivity"),
            ("pwn.college",        1,  180, 40.0, "pwn.college",    "https://pwn.college"),
            ("HackLu CTF",         140, 2, 60.0, "Hack.lu",        "https://hack.lu"),
            ("RuCTF",              95, 3, 50.0, "RuCTF",          "https://ructf.org"),
            ("CSAW Red Team",      65, 4, 55.0, "CSAW",           "https://www.csaw.io"),
            ("RingZer0 CTF",       2,  365, 25.0, "RingZer0",      "https://ringzer0ctf.com"),
            ("WolvCTF",            40, 4, 45.0, "WolverineSec",   "https://wolvsec.com"),
            ("SekaiCTF",           155, 3, 70.0, "Project Sekai", "https://sekai.team"),
            ("corCTF",             85, 2, 65.0, "Crusaders of Rust", "https://ctf.cor.team"),
            ("AmateursCTF",        12, 7, 40.0, "AmateursCTF",    "https://amateurs.team"),
            ("PatriotCTF",         35, 4, 50.0, "PatriotCTF",     "https://patriotctf.com"),
            ("N1CTF",              145, 2, 80.0, "Nu1L",           "https://ctftime.org/team/2718"),
        ]
        events: List[CTFEvent] = []
        for title, off, dur, weight, src, url in items:
            e = CTFEvent()
            e.title = title
            e.source = f"Curated:{src}"
            e.start_date = now + timedelta(days=off)
            e.end_date = e.start_date + timedelta(days=dur)
            e.is_online = True
            e.location = "🌐 Online"
            e.website_url = url
            e.registration_url = url
            e.weight = weight
            e.format_type = CTFFormat.JEOPARDY
            e.organizer_name = src
            e.organizer_url = url
            if weight > 75: e.difficulty = DifficultyLevel.EXPERT
            elif weight > 50: e.difficulty = DifficultyLevel.ADVANCED
            elif weight > 25: e.difficulty = DifficultyLevel.INTERMEDIATE
            else: e.difficulty = DifficultyLevel.BEGINNER
            e.description = f"{title} — one of the most popular recurring CTFs in the security community."
            e.short_description = e.description
            e.calculate_duration()
            events.append(e)
        return events

    async def scrape(self) -> List[CTFEvent]:
        return self._curated()


# ──────────────────────────── INTELLIGENCE ENGINE ────────────────────────────
class CTFIntelligenceEngine:
    CITY_STATE = {
        "bengaluru":"Karnataka","bangalore":"Karnataka","mumbai":"Maharashtra",
        "pune":"Maharashtra","delhi":"Delhi","new delhi":"Delhi",
        "hyderabad":"Telangana","chennai":"Tamil Nadu","kolkata":"West Bengal",
        "ahmedabad":"Gujarat","jaipur":"Rajasthan","lucknow":"Uttar Pradesh",
        "kochi":"Kerala","chandigarh":"Chandigarh","bhopal":"Madhya Pradesh",
        "indore":"Madhya Pradesh","goa":"Goa","surat":"Gujarat",
        "visakhapatnam":"Andhra Pradesh","guwahati":"Assam","patna":"Bihar",
        "ranchi":"Jharkhand","bhubaneswar":"Odisha","dehradun":"Uttarakhand",
        "shimla":"Himachal Pradesh","srinagar":"Jammu and Kashmir",
        "amritsar":"Punjab","nagpur":"Maharashtra","thane":"Maharashtra",
        "agra":"Uttar Pradesh","varanasi":"Uttar Pradesh","nashik":"Maharashtra",
        "aurangabad":"Maharashtra","vadodara":"Gujarat","rajkot":"Gujarat",
        "coimbatore":"Tamil Nadu","madurai":"Tamil Nadu",
        "mangalore":"Karnataka","mysore":"Karnataka","gandhinagar":"Gujarat",
        "noida":"Uttar Pradesh","gurugram":"Haryana","faridabad":"Haryana",
    }

    def enrich(self, e: CTFEvent) -> CTFEvent:
        self._detect_loc(e)
        self._enrich_org(e)
        self._detect_diff(e)
        self._gen_tags(e)
        self._quality(e)
        if not e.id:
            e.id = hashlib.md5(f"{e.title}{e.source}{e.start_date}".encode()).hexdigest()[:12]
        return e

    def _detect_loc(self, e: CTFEvent):
        loc = e.location.lower()
        for city, state in self.CITY_STATE.items():
            if city in loc:
                e.city = city.title(); e.state = state; e.country = "India"; return
        for st in INDIAN_STATES.values():
            if st.lower() in loc:
                e.state = st; e.country = "India"; return

    def _enrich_org(self, e: CTFEvent):
        for org in ["bi0s","nullcon","d2c","devfolio","unstop","vishwa","inctf"]:
            if org in e.organizer_name.lower():
                e.country = "India"; return

    def _detect_diff(self, e: CTFEvent):
        text = (e.title + " " + e.description).lower()
        if any(k in text for k in ["beginner","junior","intro","101","easy","learning"]):
            e.difficulty = DifficultyLevel.BEGINNER
        elif any(k in text for k in ["expert","hard","advanced","master","elite"]):
            e.difficulty = DifficultyLevel.EXPERT
        else:
            if e.weight > 75:   e.difficulty = DifficultyLevel.EXPERT
            elif e.weight > 50: e.difficulty = DifficultyLevel.ADVANCED
            elif e.weight > 25: e.difficulty = DifficultyLevel.INTERMEDIATE
            else:               e.difficulty = DifficultyLevel.BEGINNER

    def _gen_tags(self, e: CTFEvent):
        tags = set(e.tags or [])
        tags.add(e.format_type.value.lower().replace(" ","").replace("-",""))
        tags.add(e.difficulty.value.lower())
        if e.country: tags.add(e.country.lower())
        if e.state:   tags.add(e.state.lower().replace(" ",""))
        if e.organizer_name: tags.add(e.organizer_name.lower().replace(" ",""))
        if e.is_online:  tags.add("online")
        if e.is_offline: tags.add("offline")
        e.tags = list(tags)

    def _quality(self, e: CTFEvent):
        checks = [(bool(e.title),10),(bool(e.start_date),10),(bool(e.end_date),10),
                  (bool(e.description),10),(bool(e.website_url),10),
                  (bool(e.registration_url),10),(e.organizer_name!="Unknown",10),
                  (e.participants_count>0,10),(e.weight>0,10),(len(e.tags)>0,10),
                  (e.challenges_count>0,5),(bool(e.rules),5),(bool(e.schedule),5),
                  (e.prize_pool_total>0,5)]
        maxs = sum(p for _,p in checks)
        e.data_quality_score = round(sum(p for c,p in checks if c)/maxs*100, 2)


# ──────────────────────────── ANALYTICS ────────────────────────────
class AnalyticsEngine:
    def analyze(self, events: List[CTFEvent]) -> CTFAnalytics:
        a = CTFAnalytics()
        a.total_events = len(events)
        fmt_c = defaultdict(int); diff_c = defaultdict(int); src_c = defaultdict(int)
        ctry_c = defaultdict(int); st_c = defaultdict(int); mon_c = defaultdict(int)
        org_c = defaultdict(int); tag_c = defaultdict(int)
        tw = tp = tpr = 0
        for e in events:
            fmt_c[e.format_type.value] += 1
            diff_c[e.difficulty.value] += 1
            src_c[e.source] += 1
            if e.country: ctry_c[e.country] += 1
            if e.state: st_c[e.state] += 1
            if e.start_date: mon_c[e.start_date.strftime("%Y-%m")] += 1
            if e.organizer_name: org_c[e.organizer_name] += 1
            for t in e.tags: tag_c[t] += 1
            if e.is_online:  a.online_events  += 1
            if e.is_offline: a.offline_events += 1
            if e.is_hybrid:  a.hybrid_events  += 1
            tw += e.weight; tp += e.participants_count; tpr += e.prize_pool_total
        if events:
            a.average_weight = round(tw/len(events),2)
            a.average_participants = round(tp/len(events),2)
        a.total_prize_pool = tpr
        a.format_distribution = dict(fmt_c)
        a.difficulty_distribution = dict(diff_c)
        a.source_distribution = dict(src_c)
        a.country_distribution = dict(ctry_c)
        a.state_distribution = dict(st_c)
        a.monthly_trend = dict(sorted(mon_c.items()))
        a.top_organizers = sorted(org_c.items(), key=lambda x:-x[1])[:10]
        a.top_tags = sorted(tag_c.items(), key=lambda x:-x[1])[:20]
        return a

    def show(self, a: CTFAnalytics):
        console.print(Panel.fit("[bold cyan]📊 CTF EVENT ANALYTICS DASHBOARD[/bold cyan]",
                                border_style="cyan"))

        # Overview
        ov = Table(show_header=False, box=box.ROUNDED)
        ov.add_column("Metric", style="bold"); ov.add_column("Value", style="cyan")
        ov.add_row("Total Events", str(a.total_events))
        ov.add_row("Online Events", str(a.online_events))
        ov.add_row("Offline Events", str(a.offline_events))
        ov.add_row("Average Weight", f"{a.average_weight:.2f}")
        ov.add_row("Average Participants", f"{a.average_participants:.0f}")
        ov.add_row("Total Prize Pool", f"${a.total_prize_pool:,.2f}")
        console.print(Panel(ov, title="[bold]Overview[/bold]", border_style="green"))

        # Source distribution
        t = Table(show_header=True, box=box.ROUNDED, title="Source Distribution")
        t.add_column("Source", style="bold"); t.add_column("Count", justify="right", style="cyan")
        t.add_column("Bar", style="green")
        total = max(sum(a.source_distribution.values()), 1)
        for s, c in sorted(a.source_distribution.items(), key=lambda x:-x[1])[:8]:
            bar = "█" * int(c/total*30)
            t.add_row(s, str(c), bar)
        console.print(Panel(t, border_style="blue"))

        # Format
        t2 = Table(show_header=True, box=box.ROUNDED, title="Format Distribution")
        t2.add_column("Format", style="bold"); t2.add_column("Count", justify="right", style="cyan")
        t2.add_column("Bar", style="yellow")
        tot = max(sum(a.format_distribution.values()), 1)
        for f, c in sorted(a.format_distribution.items(), key=lambda x:-x[1]):
            bar = "█" * int(c/tot*30)
            t2.add_row(f, str(c), bar)
        console.print(Panel(t2, border_style="yellow"))

        # Top organisers
        t3 = Table(show_header=True, box=box.ROUNDED, title="Top Organisers")
        t3.add_column("#", justify="center", style="bold")
        t3.add_column("Organiser", style="bold")
        t3.add_column("Events", justify="right", style="cyan")
        for i,(o,c) in enumerate(a.top_organizers[:5],1):
            t3.add_row(str(i), o, str(c))
        console.print(Panel(t3, border_style="magenta"))

        # Monthly trend (last 8 months)
        if a.monthly_trend:
            t4 = Table(show_header=True, box=box.ROUNDED, title="Monthly Trend")
            t4.add_column("Month", style="bold")
            t4.add_column("Events", justify="right", style="cyan")
            t4.add_column("Bar", style="cyan")
            mx = max(a.monthly_trend.values())
            for m, c in list(a.monthly_trend.items())[:8]:
                t4.add_row(m, str(c), "█" * int(c/mx*30))
            console.print(Panel(t4, border_style="cyan"))


# ──────────────────────────── EXPORT ENGINE ────────────────────────────
class ExportEngine:
    @staticmethod
    def export_json(events: List[CTFEvent], fn: str = None) -> str:
        fn = fn or f"ctfforge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(fn, "w", encoding="utf-8") as f:
            json.dump([e.to_dict() for e in events], f, indent=2, ensure_ascii=False)
        return fn

    @staticmethod
    def export_csv(events: List[CTFEvent], fn: str = None) -> str:
        fn = fn or f"ctfforge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(fn, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Title","Start","End","Duration (h)","Location","Country","State",
                        "City","Format","Difficulty","Source","Registration URL",
                        "Website URL","Organiser","Participants","Weight","Prize",
                        "Tags","AI Score","Status"])
            for e in events:
                w.writerow([
                    e.title,
                    e.start_date.isoformat() if e.start_date else "",
                    e.end_date.isoformat() if e.end_date else "",
                    round(e.duration_hours,2),
                    e.location, e.country, e.state, e.city,
                    e.format_type.value, e.difficulty.value, e.source,
                    e.registration_url, e.website_url, e.organizer_name,
                    e.participants_count, e.weight, e.prize_pool_total,
                    ", ".join(e.tags), e.ai_score, e.get_status().value
                ])
        return fn

    @staticmethod
    def export_ics(events: List[CTFEvent], fn: str = None) -> str:
        """Export to .ics calendar file (works with Google/Apple/Outlook)."""
        fn = fn or f"ctfforge_calendar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
        lines = ["BEGIN:VCALENDAR","VERSION:2.0","PRODID:-//CTFForge Pro//EN"]
        for e in events:
            if not e.start_date: continue
            end = e.end_date or (e.start_date + timedelta(days=1))
            lines += [
                "BEGIN:VEVENT",
                f"UID:{e.id}@ctfforge",
                f"SUMMARY:{e.title.replace(',','\\,')}",
                f"DTSTART:{e.start_date.strftime('%Y%m%dT%H%M%SZ')}",
                f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}",
                f"DESCRIPTION:{(e.description or e.short_description)[:500]}",
                f"URL:{e.registration_url or e.website_url}",
                f"LOCATION:{e.location}",
                "END:VEVENT"
            ]
        lines.append("END:VCALENDAR")
        with open(fn, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return fn

    @staticmethod
    def export_html(events: List[CTFEvent], fn: str = None) -> str:
        """Export to a beautiful standalone HTML page."""
        fn = fn or f"ctfforge_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        rows = ""
        for i, e in enumerate(events, 1):
            status = e.get_status().value
            color = {"Upcoming":"#3498db","Ongoing":"#2ecc71","Completed":"#95a5a6"}.get(status,"#7f8c8d")
            rows += f"""
            <tr>
                <td>{i}</td>
                <td><b>{e.title}</b><br><small>{e.short_description}</small></td>
                <td>{e.start_date.strftime('%d %b %Y') if e.start_date else 'TBD'}</td>
                <td>{e.location}</td>
                <td>{e.format_type.value}</td>
                <td><b>{e.ai_score:.0f}</b></td>
                <td><span style="color:{color};font-weight:bold">{status}</span></td>
                <td><a href="{e.registration_url or e.website_url or '#'}" target="_blank">Register →</a></td>
            </tr>"""
        html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
        <title>CTFForge Pro Report</title>
        <style>
        body{{font-family:system-ui;background:#0e1117;color:#e6edf3;padding:20px;}}
        h1{{color:#58a6ff;}}
        table{{width:100%;border-collapse:collapse;background:#161b22;}}
        th,td{{padding:12px;border:1px solid #30363d;text-align:left;}}
        th{{background:#21262d;color:#58a6ff;}}
        tr:hover{{background:#1c2128;}}
        a{{color:#58a6ff;text-decoration:none;}}
        a:hover{{text-decoration:underline;}}
        </style></head><body>
        <h1>🔐 CTFForge Pro — {len(events)} Events</h1>
        <p>Generated on {datetime.now().strftime('%d %B %Y at %H:%M')}</p>
        <table><thead><tr>
        <th>#</th><th>Event</th><th>Date</th><th>Location</th>
        <th>Format</th><th>Score</th><th>Status</th><th>Action</th>
        </tr></thead><tbody>{rows}</tbody></table></body></html>"""
        with open(fn, "w", encoding="utf-8") as f:
            f.write(html)
        return fn

    @staticmethod
    def export_markdown(events: List[CTFEvent], fn: str = None) -> str:
        fn = fn or f"ctfforge_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(fn, "w", encoding="utf-8") as f:
            f.write(f"# 🔐 CTFForge Pro — Event Report\n\n")
            f.write(f"_Generated on {datetime.now().strftime('%d %B %Y at %H:%M')}_\n\n")
            f.write(f"Total events: **{len(events)}**\n\n")
            for i, e in enumerate(events, 1):
                f.write(f"## {i}. {e.display_title()}\n\n")
                f.write(f"- **Dates**: {e.start_date.strftime('%d %b %Y') if e.start_date else 'TBD'} → ")
                f.write(f"{e.end_date.strftime('%d %b %Y') if e.end_date else 'TBD'}\n")
                f.write(f"- **Format**: {e.format_type.value}\n")
                f.write(f"- **Difficulty**: {e.difficulty.value}\n")
                f.write(f"- **Location**: {e.location}\n")
                f.write(f"- **AI Score**: {e.ai_score}/100\n")
                f.write(f"- **Status**: {e.get_status().value}\n")
                if e.registration_url: f.write(f"- **Register**: {e.registration_url}\n")
                if e.website_url and e.website_url != e.registration_url:
                    f.write(f"- **Website**: {e.website_url}\n")
                if e.description: f.write(f"\n{e.description[:300]}...\n")
                f.write("\n---\n\n")
        return fn


# ──────────────────────────── FAVORITES / CACHE ────────────────────────────
class FavoritesStore:
    FILE = ".ctfforge_favorites.json"
    def __init__(self):
        self.favs: List[str] = []
        self.load()
    def load(self):
        if os.path.exists(self.FILE):
            try:
                with open(self.FILE,"r",encoding="utf-8") as f:
                    self.favs = json.load(f)
            except Exception: self.favs = []
    def save(self):
        with open(self.FILE,"w",encoding="utf-8") as f:
            json.dump(self.favs, f)
    def add(self, e: CTFEvent):
        if e.id not in self.favs:
            self.favs.append(e.id); self.save()
    def remove(self, e: CTFEvent):
        if e.id in self.favs:
            self.favs.remove(e.id); self.save()
    def is_fav(self, e: CTFEvent) -> bool:
        return e.id in self.favs

class EventCache:
    FILE = ".ctfforge_cache.json"
    TTL_HOURS = 6
    def __init__(self):
        self.data = self.load()
    def load(self):
        if os.path.exists(self.FILE):
            try:
                with open(self.FILE,"r",encoding="utf-8") as f:
                    return json.load(f)
            except Exception: return {}
        return {}
    def save(self):
        with open(self.FILE,"w",encoding="utf-8") as f:
            json.dump(self.data, f, default=str)
    def is_fresh(self, key: str) -> bool:
        if key not in self.data: return False
        ts = self.data[key].get("ts",0)
        return (datetime.now().timestamp() - ts) < self.TTL_HOURS*3600
    def get(self, key: str):
        return self.data.get(key,{}).get("events",[])
    def set(self, key: str, events: List[Dict]):
        self.data[key] = {"ts": datetime.now().timestamp(), "events": events}
        self.save()


# ──────────────────────────── MAIN APP ────────────────────────────
class CTFForgeApp:
    def __init__(self):
        self.ai = AIRankingEngine()
        self.intel = CTFIntelligenceEngine()
        self.analytics = AnalyticsEngine()
        self.exporter = ExportEngine()
        self.events: List[CTFEvent] = []
        self.filtered: List[CTFEvent] = []
        self.selected_states: List[str] = []
        self.favs = FavoritesStore()
        self.cache = EventCache()
        self.theme = "cyan"

    def banner(self):
        console.clear()
        console.print(f"""
[bold {self.theme}]╔══════════════════════════════════════════════════════════════════╗
║                                                                                     ║
║     ██████  ███████████     ███████  ██████   ██████   ██████  ███████              ║
║    ██           ██           ██      ██   ██  ██   ██ ██       ██                   ║
║    ██           ██            █████  ██   ██  ██████ ██   ███ █████                 ║
║    ██           ██           ██      ██   ██  ██   ██ ██    ██ ██                   ║
║     ██████      ██           ██       ██████  ██   ██  ██████  ███████              ║
║                                                                                     ║
║                🔐 CTFForge Pro v{__version__} — ULTIMATE 🔐                        ║
║          Advanced CTF Discovery & Intelligence Engine                               ║
║                                                                                     ║
║   Made by [bold yellow]VRJ[/bold yellow] 
    • GitHub: [link=https://github.com/{__github__}]{__github__}[/link]               ║
║   LinkedIn: [link=https://linkedin.com/in/{__linkedin__}]{__linkedin__}[/link]      ║
║                                                                                     ║
╚══════════════════════════════════════════════════════════════════╝[/bold {self.theme}]
""")

    def menu(self) -> str:
        console.print(Panel.fit(
            "[bold]MAIN MENU[/bold]\n\n"
            "  1. 🔍 Find CTF Events\n"
            "  2. 📋 View Event List (current)\n"
            "  3. 🔎 View Event Details\n"
            "  4. ⭐ View Favorites\n"
            "  5. 📊 Analytics Dashboard\n"
            "  6. 🔎 Search in current results\n"
            "  7. 💾 Export Results\n"
            "  8. 🌐 Open event in browser\n"
            "  9. ⚙️  Settings\n"
            " 10. 📖 Help\n"
            "  0. 🚪 Exit",
            border_style=self.theme, title="[bold]Navigation[/bold]"
        ))
        return Prompt.ask("Select option", default="1")

    def select_states(self) -> List[str]:
        console.print(Panel.fit("[bold yellow]🌏 Select Indian States[/bold yellow]",
                                border_style="yellow"))
        console.print("\n[bold]Indian States & UTs:[/bold]\n")
        # 3 columns
        for i in range(1, 37, 3):
            row = ""
            for j in range(3):
                idx = i + j
                if idx <= 36:
                    st = INDIAN_STATES[idx]
                    row += f"  [cyan]{idx:2d}.[/cyan] {st:<35}"
            console.print(row)
        console.print("\n[green]all[/green] = select all | [green]1,2,3[/green] = specific | "
                      "[green]1-10[/green] = range | [green]none[/green] = skip")
        ch = Prompt.ask("Your selection", default="all")
        ch = ch.strip().lower()
        if ch in ("all",""): return list(INDIAN_STATES.values())
        if ch == "none": return []
        if "-" in ch:
            try:
                a,b = ch.split("-"); a,b = int(a),int(b)
                return [INDIAN_STATES[i] for i in range(a,b+1) if i in INDIAN_STATES]
            except Exception: pass
        out = []
        for n in ch.split(","):
            try:
                idx = int(n.strip())
                if idx in INDIAN_STATES: out.append(INDIAN_STATES[idx])
            except Exception: pass
        return out or list(INDIAN_STATES.values())

    async def scrape(self) -> List[CTFEvent]:
        console.print(f"\n[bold {self.theme}]🕸️ Initialising CTF Scraping Network...[/bold {self.theme}]")
        scrapers = [
            CTFtimeAPIScraper(),
            CTFtimeHTMLScraper(),
            CTFHuntScraper(),
            UnstopCTFScraper(),
            DevfolioScraper(),
            GitHubCTFScraper(),
            CuratedCTFScraper(),   # always returns data
        ]
        all_events: List[CTFEvent] = []
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                      console=console) as progress:
            task = progress.add_task(f"[{self.theme}]Scraping sources...", total=len(scrapers))
            for sc in scrapers:
                progress.update(task, description=f"[{self.theme}]Scraping {sc.name}...")
                try:
                    evs = await sc.scrape()
                    all_events.extend(evs)
                    mark = "✅" if evs else "⚠️"
                    console.print(f"  {mark} {sc.name}: {len(evs)} events")
                except Exception as ex:
                    console.print(f"  ❌ {sc.name}: {str(ex)[:80]}")
                progress.advance(task)

        # Enrich + dedup
        console.print(f"\n[bold {self.theme}]🧠 Enriching & deduplicating...[/bold {self.theme}]")
        enriched: List[CTFEvent] = []
        seen = set()
        for e in all_events:
            e = self.intel.enrich(e)
            key = f"{e.title.lower()}|{e.source}|{e.start_date}"
            if key in seen: continue
            seen.add(key)
            enriched.append(e)
        console.print(f"  [bold green]✅ Unique events: {len(enriched)}[/bold green]")
        return enriched

    def apply_filters(self, events: List[CTFEvent]) -> List[CTFEvent]:
        console.print("\n[bold]🔍 Filters[/bold]\n")
        console.print("Status:  [1]All [2]Upcoming [3]Ongoing")
        s = Prompt.ask("Status", choices=["1","2","3"], default="1")
        console.print("Format:  [1]All [2]Jeopardy [3]A/D [4]Mixed")
        f = Prompt.ask("Format", choices=["1","2","3","4"], default="1")
        console.print("Location: [1]All [2]Online [3]Offline [4]India")
        l = Prompt.ask("Location", choices=["1","2","3","4"], default="1")
        console.print("Weight:  [1]Any [2]>=25 [3]>=50 [4]>=75")
        w = Prompt.ask("Weight", choices=["1","2","3","4"], default="1")
        kw = Prompt.ask("Keyword filter (Enter to skip)", default="")

        out = events
        now = datetime.now(timezone.utc)
        if s == "2":   out = [e for e in out if e.start_date and e.start_date > now]
        elif s == "3": out = [e for e in out if e.start_date and e.end_date and e.start_date <= now <= e.end_date]

        fmap = {"2":CTFFormat.JEOPARDY,"3":CTFFormat.ATTACK_DEFENSE,"4":CTFFormat.MIXED}
        if f in fmap: out = [e for e in out if e.format_type == fmap[f]]

        if l == "2":   out = [e for e in out if e.is_online]
        elif l == "3": out = [e for e in out if e.is_offline]
        elif l == "4": out = [e for e in out if e.country == "India"]

        wmap = {"2":25,"3":50,"4":75}
        if w in wmap: out = [e for e in out if e.weight >= wmap[w]]

        if kw:
            kw = kw.lower()
            out = [e for e in out if kw in e.title.lower() or kw in (e.description or "").lower()
                   or any(kw in t for t in e.tags)]

        if self.selected_states:
            sf = []
            for e in out:
                if e.is_online or e.state in self.selected_states or e.country == "India":
                    sf.append(e)
            out = sf

        return out

    def show_events(self, events: List[CTFEvent]):
        if not events:
            console.print("[bold red]No events found.[/bold red]"); return
        t = Table(title=f"🔐 {len(events)} CTF Events", show_lines=False,
                  box=box.ROUNDED, header_style=f"bold {self.theme}",
                  title_style=f"bold {self.theme}")
        t.add_column("#", justify="center", style="cyan", width=3)
        t.add_column("Event", style="bold yellow", min_width=28)
        t.add_column("Date", style="green", width=18)
        t.add_column("Location", style="magenta", width=18)
        t.add_column("Fmt", justify="center", width=10)
        t.add_column("Diff", justify="center", width=11)
        t.add_column("Wt", justify="center", width=5)
        t.add_column("Score", justify="center", width=6)
        t.add_column("Source", width=14)
        t.add_column("Links", width=8)

        for i, e in enumerate(events[:50], 1):
            d = f"{e.start_date.strftime('%d %b')}→{e.end_date.strftime('%d %b')}" if e.start_date and e.end_date else "TBD"
            loc = e.location[:18]
            dcol = {DifficultyLevel.BEGINNER:"green", DifficultyLevel.INTERMEDIATE:"yellow",
                    DifficultyLevel.ADVANCED:"red", DifficultyLevel.EXPERT:"bold red"}.get(e.difficulty,"white")
            diff = f"[{dcol}]{e.difficulty.value[:10]}[/]"
            wcol = "bold red" if e.weight>75 else "yellow" if e.weight>50 else "green" if e.weight>25 else "dim"
            wt = f"[{wcol}]{e.weight:.0f}[/]"
            scol = "green" if e.ai_score>75 else "yellow" if e.ai_score>50 else "red"
            sc = f"[{scol}]{e.ai_score:.0f}[/]"
            link = "🔗" if (e.website_url or e.registration_url) else "-"
            star = "⭐" if self.favs.is_fav(e) else "  "
            t.add_row(str(i), f"{star} {e.title[:40]}", d, loc, e.format_type.value[:9],
                      diff, wt, sc, e.source[:13], link)
        console.print(t)

        console.print(f"\n[bold]Showing top {min(50,len(events))} of {len(events)}[/bold]")
        console.print(f"  Online: {sum(1 for e in events if e.is_online)} | "
                      f"Offline: {sum(1 for e in events if e.is_offline)} | "
                      f"India: {sum(1 for e in events if e.country=='India')}")
        st_c = defaultdict(int)
        for e in events:
            if e.state: st_c[e.state] += 1
        if st_c:
            console.print("\n[bold]🇮🇳 Indian State Distribution:[/bold]")
            for s,c in sorted(st_c.items(), key=lambda x:-x[1])[:10]:
                console.print(f"  • {s}: {c}")

    def show_detail(self, events: List[CTFEvent]):
        if not events:
            console.print("[red]No events loaded.[/red]"); return
        try:
            idx = IntPrompt.ask(f"Enter event # (1-{len(events)})", default=1)
        except Exception: return
        if idx < 1 or idx > len(events):
            console.print("[red]Invalid number.[/red]"); return
        e = events[idx-1]
        console.print(Rule(f"[bold {self.theme}]{e.display_title()}[/bold {self.theme}]"))
        # status
        status = e.get_status().value
        scol = {"Upcoming":"blue","Ongoing":"green","Completed":"grey50"}.get(status,"white")
        console.print(Panel(
            f"[bold {scol}]{status}[/bold {scol}]  "
            f"[dim]AI Score:[/dim] [bold]{e.ai_score}/100[/bold]  "
            f"[dim]Confidence:[/dim] [bold]{e.ai_confidence}%[/bold]\n"
            f"[dim]Explanation:[/dim] {e.ai_explanation}",
            border_style=scol
        ))
        # details
        t = Table(show_header=False, box=box.SIMPLE)
        t.add_column("Field", style="bold cyan", width=22)
        t.add_column("Value")
        t.add_row("Title", e.title)
        if e.subtitle: t.add_row("Subtitle", e.subtitle)
        t.add_row("Dates",
                  f"{e.start_date.strftime('%d %b %Y %H:%M UTC') if e.start_date else 'TBD'}"
                  f" → {e.end_date.strftime('%d %b %Y %H:%M UTC') if e.end_date else 'TBD'}")
        t.add_row("Duration", f"{e.duration_hours:.1f} hours")
        t.add_row("Location", e.location)
        t.add_row("Country", e.country or "Global")
        if e.state:  t.add_row("State", e.state)
        if e.city:   t.add_row("City", e.city)
        t.add_row("Format", e.format_type.value)
        t.add_row("Difficulty", e.difficulty.value)
        t.add_row("Source", e.source)
        if e.organizer_name and e.organizer_name != "Unknown":
            t.add_row("Organiser", e.organizer_name)
        if e.participants_count: t.add_row("Participants", str(e.participants_count))
        if e.weight:  t.add_row("CTFtime Weight", f"{e.weight}")
        if e.prize_pool_total: t.add_row("Prize Pool", f"${e.prize_pool_total:,.0f} {e.prize_currency}")
        if e.data_quality_score:
            t.add_row("Data Quality", f"{e.data_quality_score}/100")
        if e.tags:   t.add_row("Tags", ", ".join(e.tags[:15]))
        console.print(t)

        # Links (clickable in rich)
        links = []
        if e.registration_url: links.append(("🔗 Register", e.registration_url))
        if e.website_url and e.website_url != e.registration_url:
            links.append(("🌐 Website", e.website_url))
        if e.ctftime_url: links.append(("📊 CTFtime", e.ctftime_url))
        if e.discord_url:  links.append(("💬 Discord", e.discord_url))
        if links:
            console.print("\n[bold]Links (clickable):[/bold]")
            for name, url in links:
                console.print(f"  {name}: [link={url}]{url}[/link]")
        if e.description:
            console.print(Panel(Markdown(e.description[:1500] if len(e.description) > 1500 else e.description),
                                title="[bold]Description[/bold]", border_style="blue"))

        # actions
        if e.registration_url and Confirm.ask("Open registration page in browser?", default=False):
            webbrowser.open(e.registration_url)
        if Confirm.ask("Toggle favourite?", default=False):
            if self.favs.is_fav(e): self.favs.remove(e); console.print("[yellow]Removed from favourites.[/yellow]")
            else: self.favs.add(e); console.print("[green]Added to favourites ⭐[/green]")

    def show_favorites(self, events: List[CTFEvent]):
        favs = [e for e in events if self.favs.is_fav(e)]
        if not favs:
            console.print("[yellow]No favourites yet. Add some from the event detail view![/yellow]")
            return
        self.show_events(favs)

    def search(self, events: List[CTFEvent]):
        q = Prompt.ask("Search query").lower()
        if not q: return
        results = [e for e in events if q in e.title.lower() or q in (e.description or "").lower()
                   or any(q in t for t in e.tags)]
        if not results:
            console.print("[red]No matches.[/red]"); return
        self.show_events(results)

    def export_menu(self, events: List[CTFEvent]):
        if not events:
            console.print("[red]No events to export.[/red]"); return
        console.print("\n[bold]Export Format:[/bold]")
        console.print("  1. JSON (full data)")
        console.print("  2. CSV (spreadsheet)")
        console.print("  3. ICS (calendar)")
        console.print("  4. HTML (beautiful report)")
        console.print("  5. Markdown (docs)")
        console.print("  6. ALL formats")
        ch = Prompt.ask("Choose", choices=["1","2","3","4","5","6"], default="4")
        if ch == "1": f = self.exporter.export_json(events)
        elif ch == "2": f = self.exporter.export_csv(events)
        elif ch == "3": f = self.exporter.export_ics(events)
        elif ch == "4": f = self.exporter.export_html(events)
        elif ch == "5": f = self.exporter.export_markdown(events)
        else:
            fs = [self.exporter.export_json(events), self.exporter.export_csv(events),
                  self.exporter.export_ics(events), self.exporter.export_html(events),
                  self.exporter.export_markdown(events)]
            for f in fs: console.print(f"  [green]✅ {f}[/green]")
            return
        console.print(f"  [bold green]✅ Exported → {f}[/bold green]")

    def open_browser(self, events: List[CTFEvent]):
        if not events:
            console.print("[red]No events loaded.[/red]"); return
        try:
            idx = IntPrompt.ask("Event # to open", default=1)
        except Exception: return
        if idx < 1 or idx > len(events): return
        e = events[idx-1]
        url = e.registration_url or e.website_url or e.ctftime_url
        if url:
            console.print(f"[green]Opening {url}...[/green]")
            webbrowser.open(url)
        else:
            console.print("[red]No URL available for this event.[/red]")

    def settings(self):
        console.print(Panel.fit("[bold]⚙️ Settings[/bold]\n\n"
                                "1. Change theme colour\n"
                                "2. Clear cache\n"
                                "3. Clear favourites", border_style="yellow"))
        ch = Prompt.ask("Choose", choices=["1","2","3"], default="1")
        if ch == "1":
            console.print("Colours: cyan, green, magenta, yellow, blue, red")
            self.theme = Prompt.ask("Colour", default="cyan")
            console.print(f"[green]Theme set to {self.theme}[/green]")
        elif ch == "2":
            if os.path.exists(EventCache.FILE): os.remove(EventCache.FILE)
            self.cache = EventCache()
            console.print("[green]Cache cleared.[/green]")
        elif ch == "3":
            self.favs.favs = []; self.favs.save()
            console.print("[green]Favourites cleared.[/green]")

    def help_screen(self):
        console.print(Panel.fit(
            "[bold cyan]CTFForge Pro v5.0 — Help[/bold cyan]\n\n"
            "[bold]What it does:[/bold]\n"
            "  • Aggregates CTF events from 7 sources (CTFtime API+HTML, CTF Hunt,\n"
            "    Unstop-CTF-only, Devfolio, GitHub CTF lists, curated fallback)\n"
            "  • Filters Unstop strictly for CTF events (no internships/jobs)\n"
            "  • AI ranks each event on 7 factors + explains why\n"
            "  • Shows clickable hyperlinks, detail view, calendar export\n\n"
            "[bold]Key features:[/bold]\n"
            "  • Always returns events (curated fallback)\n"
            "  • Clickable links (use a terminal that supports OSC 8)\n"
            "  • Open events in browser (option 8)\n"
            "  • Favourites saved to .ctfforge_favorites.json\n"
            "  • Cache saved to .ctfforge_cache.json (6h TTL)\n"
            "  • 5 export formats: JSON, CSV, ICS, HTML, Markdown\n\n"
            "[bold]Tips:[/bold]\n"
            "  • Use 'all' for states to maximise results\n"
            "  • Open HTML export in browser for a beautiful report\n"
            "  • Use ICS export to add events to your calendar\n"
            "  • Press Ctrl+C to cancel any operation",
            border_style="green", title="[bold]Help[/bold]"
        ))
        input("\nPress Enter...")

    async def run(self):
        self.banner()
        while True:
            try:
                ch = self.menu()
            except (EOFError, KeyboardInterrupt):
                ch = "0"

            if ch == "1":
                self.selected_states = self.select_states()
                console.print(f"\n[green]✅ {len(self.selected_states)} states selected[/green]")

                self.events = await self.scrape()
                if not self.events:
                    console.print("[red]No events at all (shouldn't happen — curated list always returns data).[/red]")
                    continue

                self.filtered = self.apply_filters(self.events)
                if not self.filtered:
                    console.print("[yellow]No events match your filters — showing top 30 by AI score instead.[/yellow]")
                    self.filtered = sorted(self.events, key=lambda x:-x.ai_score)[:30]

                console.print(f"\n[bold {self.theme}]🤖 AI Ranking in progress...[/bold {self.theme}]")
                self.filtered = self.ai.rank_all(self.filtered, self.selected_states)
                self.show_events(self.filtered)

            elif ch == "2":
                self.show_events(self.filtered if self.filtered else self.events)
            elif ch == "3":
                self.show_detail(self.filtered if self.filtered else self.events)
            elif ch == "4":
                self.show_favorites(self.events)
            elif ch == "5":
                evs = self.filtered or self.events
                if evs:
                    a = self.analytics.analyze(evs)
                    self.analytics.show(a)
                else:
                    console.print("[yellow]No events loaded. Run option 1 first.[/yellow]")
            elif ch == "6":
                self.search(self.filtered or self.events)
            elif ch == "7":
                self.export_menu(self.filtered or self.events)
            elif ch == "8":
                self.open_browser(self.filtered or self.events)
            elif ch == "9":
                self.settings()
            elif ch == "10":
                self.help_screen()
            elif ch == "0":
                console.print("\n[bold cyan]👋 Happy hacking — see you at the next CTF![/bold cyan]")
                break

            if ch != "0":
                console.print()

# ──────────────────────────── ENTRY POINT ────────────────────────────
async def main():
    app = CTFForgeApp()
    await app.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted. Exiting...[/yellow]")
    except Exception as ex:
        console.print(f"\n[red]Fatal error: {ex}[/red]")
        import traceback; traceback.print_exc()
        sys.exit(1)
