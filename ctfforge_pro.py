#!/usr/bin/env python3
"""
CTFForge Pro v4.1 - Advanced CTF Discovery & Intelligence Engine
Author: VRJ
GitHub: jadhavidhi06-sketch
LinkedIn: vidhi-jadhav

Fixed Version - Reliable scraping with proper fallbacks
"""

import asyncio
import json
import re
import csv
import os
import sys
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict

import httpx
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

console = Console()

__author__ = "VRJ"
__github__ = "jadhavidhi06-sketch"
__linkedin__ = "vidhi-jadhav"
__version__ = "4.1"
__tool_name__ = "CTFForge Pro"

# ==================== ENUMS ====================
class CTFFormat(Enum):
    JEOPARDY = "Jeopardy"
    ATTACK_DEFENSE = "Attack-Defense"
    MIXED = "Mixed"
    KING_OF_THE_HILL = "King of the Hill"
    BOOTCAMP = "Bootcamp"
    OTHER = "Other"

class DifficultyLevel(Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    EXPERT = "Expert"

class EventStatus(Enum):
    UPCOMING = "Upcoming"
    ONGOING = "Ongoing"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

# ==================== DATA MODELS ====================
@dataclass
class CTFEvent:
    """Comprehensive CTF Event Data Model"""
    id: str = ""
    title: str = ""
    subtitle: str = ""
    start_date: datetime = None
    end_date: datetime = None
    registration_deadline: Optional[datetime] = None
    duration_hours: float = 0.0
    location: str = "🌐 Online"
    country: str = "Global"
    state: str = ""
    city: str = ""
    is_online: bool = True
    is_offline: bool = False
    is_hybrid: bool = False
    format_type: CTFFormat = CTFFormat.JEOPARDY
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    source: str = ""
    source_url: str = ""
    source_id: str = ""
    registration_url: str = ""
    website_url: str = ""
    discord_url: Optional[str] = None
    twitter_url: Optional[str] = None
    writeup_url: Optional[str] = None
    organizer_name: str = "Unknown"
    organizer_url: Optional[str] = None
    organizer_email: Optional[str] = None
    organizer_logo: Optional[str] = None
    participants_count: int = 0
    max_participants: Optional[int] = None
    team_size_min: int = 1
    team_size_max: int = 10
    registered_teams: int = 0
    prize_pool_total: float = 0.0
    prize_currency: str = "USD"
    first_place_prize: float = 0.0
    second_place_prize: float = 0.0
    third_place_prize: float = 0.0
    has_swag: bool = False
    has_certificates: bool = False
    has_travel_aid: bool = False
    weight: float = 0.0
    rating: float = 0.0
    category: str = "General"
    tags: List[str] = field(default_factory=list)
    challenges_count: int = 0
    categories_available: List[str] = field(default_factory=list)
    description: str = ""
    short_description: str = ""
    requirements: str = ""
    rules: str = ""
    schedule: Dict[str, str] = field(default_factory=dict)
    twitter_hashtag: Optional[str] = None
    discord_invite: Optional[str] = None
    telegram_group: Optional[str] = None
    ctftime_url: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_scraped: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data_quality_score: float = 0.0
    ai_score: float = 0.0
    ai_confidence: float = 0.0
    ai_factors: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Enum):
                result[key] = value.value
            elif isinstance(value, list) and all(isinstance(v, Enum) for v in value):
                result[key] = [v.value for v in value]
            else:
                result[key] = value
        return result
    
    def calculate_duration(self) -> float:
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.duration_hours = delta.total_seconds() / 3600
        return self.duration_hours
    
    def get_status(self) -> EventStatus:
        now = datetime.now(timezone.utc)
        if not self.start_date:
            return EventStatus.UPCOMING
        if now < self.start_date:
            return EventStatus.UPCOMING
        if self.start_date <= now <= self.end_date:
            return EventStatus.ONGOING
        return EventStatus.COMPLETED

@dataclass
class CTFAnalytics:
    total_events: int = 0
    online_events: int = 0
    offline_events: int = 0
    hybrid_events: int = 0
    average_weight: float = 0.0
    average_participants: float = 0.0
    total_prize_pool: float = 0.0
    format_distribution: Dict[str, int] = field(default_factory=dict)
    difficulty_distribution: Dict[str, int] = field(default_factory=dict)
    source_distribution: Dict[str, int] = field(default_factory=dict)
    country_distribution: Dict[str, int] = field(default_factory=dict)
    state_distribution: Dict[str, int] = field(default_factory=dict)
    monthly_trend: Dict[str, int] = field(default_factory=dict)
    top_organizers: List[Tuple[str, int]] = field(default_factory=list)
    top_tags: List[Tuple[str, int]] = field(default_factory=list)

# ==================== INDIAN STATES DATABASE (COMPLETE) ====================
INDIAN_STATES = {
    1: "Andhra Pradesh",
    2: "Arunachal Pradesh",
    3: "Assam",
    4: "Bihar",
    5: "Chhattisgarh",
    6: "Goa",
    7: "Gujarat",
    8: "Haryana",
    9: "Himachal Pradesh",
    10: "Jharkhand",
    11: "Karnataka",
    12: "Kerala",
    13: "Madhya Pradesh",
    14: "Maharashtra",
    15: "Manipur",
    16: "Meghalaya",
    17: "Mizoram",
    18: "Nagaland",
    19: "Odisha",
    20: "Punjab",
    21: "Rajasthan",
    22: "Sikkim",
    23: "Tamil Nadu",
    24: "Telangana",
    25: "Tripura",
    26: "Uttar Pradesh",
    27: "Uttarakhand",
    28: "West Bengal",
    29: "Andaman and Nicobar Islands",
    30: "Chandigarh",
    31: "Dadra and Nagar Haveli and Daman and Diu",
    32: "Delhi",
    33: "Jammu and Kashmir",
    34: "Ladakh",
    35: "Lakshadweep",
    36: "Puducherry"
}

# ==================== CTF CATEGORIES ====================
CTF_CATEGORIES = [
    "Web Exploitation", "Binary Exploitation", "Reverse Engineering",
    "Cryptography", "Forensics", "OSINT", "Steganography",
    "Miscellaneous", "Programming", "Blockchain", "Cloud Security",
    "Mobile Security", "IoT Security", "Hardware Security",
    "AI/ML Security", "Network Security", "Password Cracking",
    "Social Engineering", "Physical Security", "Quantum Computing"
]

# ==================== AI RANKING ENGINE ====================
class AIRankingEngine:
    """Advanced AI-powered CTF ranking system"""
    
    def __init__(self):
        self.weights = {
            'timeliness': 0.20,
            'popularity': 0.15,
            'prestige': 0.20,
            'accessibility': 0.10,
            'rewards': 0.15,
            'quality': 0.10,
            'local_relevance': 0.10
        }
        
    def calculate_timeliness_score(self, event: CTFEvent) -> float:
        now = datetime.now(timezone.utc)
        if not event.start_date:
            return 0.0
        
        days_to_start = (event.start_date - now).days
        
        if days_to_start < 0:  # Ongoing
            return 100.0
        elif days_to_start <= 7:
            return 90.0 - (days_to_start * 5)
        elif days_to_start <= 30:
            return 60.0 - (days_to_start * 1.5)
        elif days_to_start <= 90:
            return 30.0 - (days_to_start * 0.3)
        else:
            return max(5.0, 20.0 - (days_to_start * 0.1))
    
    def calculate_popularity_score(self, event: CTFEvent) -> float:
        score = 0.0
        if event.participants_count > 0:
            participant_score = min(100, event.participants_count / 10)
            score += participant_score * 0.6
        if event.registered_teams > 0:
            team_score = min(100, event.registered_teams / 5)
            score += team_score * 0.4
        return min(100, score)
    
    def calculate_prestige_score(self, event: CTFEvent) -> float:
        score = 0.0
        if event.weight > 0:
            weight_score = min(100, event.weight * 1.2)
            score += weight_score * 0.5
        if event.rating > 0:
            rating_score = min(100, event.rating * 20)
            score += rating_score * 0.3
        
        prestige_keywords = ['def con', 'google ctf', 'hackthebox', 'tryhackme', 
                           'picoctf', 'csaw', 'asis', 'hxp', 'dragonctf', 'nullcon']
        title_lower = event.title.lower()
        for keyword in prestige_keywords:
            if keyword in title_lower:
                score += 15
        
        return min(100, score)
    
    def calculate_accessibility_score(self, event: CTFEvent) -> float:
        score = 50.0
        if event.is_online:
            score += 30
        if event.prize_pool_total == 0:
            score += 10
        if event.team_size_min <= 1:
            score += 5
        if event.difficulty == DifficultyLevel.BEGINNER:
            score += 10
        elif event.difficulty == DifficultyLevel.INTERMEDIATE:
            score += 5
        if len(event.categories_available) >= 5:
            score += 5
        return min(100, score)
    
    def calculate_rewards_score(self, event: CTFEvent) -> float:
        if event.prize_pool_total <= 0:
            return 0.0
        score = min(100, event.prize_pool_total / 100) * 0.6
        if event.has_swag:
            score += 15
        if event.has_certificates:
            score += 15
        if event.has_travel_aid:
            score += 10
        return min(100, score)
    
    def calculate_quality_score(self, event: CTFEvent) -> float:
        score = 0.0
        fields_checked = 0
        fields_filled = 0
        
        checks = [
            (event.description, 10),
            (event.organizer_name != "Unknown", 10),
            (event.challenges_count > 0, 10),
            (len(event.tags) > 0, 10),
            (event.duration_hours > 0, 10),
            (event.registration_url, 10),
            (event.website_url, 10),
            (len(event.categories_available) > 0, 10),
            (event.schedule, 10),
            (event.rules, 10)
        ]
        
        for condition, points in checks:
            fields_checked += 1
            if condition:
                fields_filled += 1
                score += points
        
        return score
    
    def calculate_local_relevance_score(self, event: CTFEvent, selected_states: List[str]) -> float:
        if not selected_states:
            return 50.0
        
        score = 0.0
        for state in selected_states:
            if state.lower() in event.location.lower() or state.lower() in event.state.lower():
                score += 40
        
        if event.country.lower() == "india":
            score += 20
        if event.is_online:
            score += 15
        
        return min(100, score)
    
    def calculate_confidence_score(self, event: CTFEvent) -> float:
        confidence = 0.0
        factors = 0
        
        if event.participants_count > 0:
            confidence += 15
            factors += 1
        if event.weight > 0:
            confidence += 20
            factors += 1
        if event.rating > 0:
            confidence += 15
            factors += 1
        if event.prize_pool_total > 0:
            confidence += 10
            factors += 1
        if event.description:
            confidence += 10
            factors += 1
        if len(event.tags) > 0:
            confidence += 10
            factors += 1
        if event.organizer_name != "Unknown":
            confidence += 10
            factors += 1
        if event.challenges_count > 0:
            confidence += 10
            factors += 1
        
        return min(100, confidence)
    
    def rank_event(self, event: CTFEvent, selected_states: List[str] = None) -> CTFEvent:
        scores = {
            'timeliness': self.calculate_timeliness_score(event),
            'popularity': self.calculate_popularity_score(event),
            'prestige': self.calculate_prestige_score(event),
            'accessibility': self.calculate_accessibility_score(event),
            'rewards': self.calculate_rewards_score(event),
            'quality': self.calculate_quality_score(event),
            'local_relevance': self.calculate_local_relevance_score(event, selected_states or [])
        }
        
        total_score = sum(scores[k] * self.weights[k] for k in scores)
        confidence = self.calculate_confidence_score(event)
        
        event.ai_score = round(total_score, 2)
        event.ai_confidence = round(confidence, 2)
        event.ai_factors = scores
        
        return event
    
    def rank_events(self, events: List[CTFEvent], selected_states: List[str] = None) -> List[CTFEvent]:
        ranked = [self.rank_event(event, selected_states) for event in events]
        return sorted(ranked, key=lambda x: x.ai_score, reverse=True)

# ==================== CTF SCRAPERS (FIXED) ====================
class BaseScraper:
    def __init__(self):
        self.name = "Base"
        self.timeout = 60
    
    async def scrape(self) -> List[CTFEvent]:
        raise NotImplementedError

class CTFtimeAPIScraper(BaseScraper):
    """Scraper for CTFtime API - Primary Source"""
    
    def __init__(self):
        super().__init__()
        self.name = "CTFtime API"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        try:
            # Get current timestamp and future events
            now = datetime.now(timezone.utc)
            start_ts = int(now.timestamp()) - 86400  # 1 day ago
            end_ts = int((now + timedelta(days=180)).timestamp())  # 6 months ahead
            
            url = f"https://ctftime.org/api/v1/events/?limit=100&start={start_ts}&finish={end_ts}"
            
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json"
                })
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data:
                        try:
                            event = CTFEvent()
                            event.title = item.get("title", "Unknown CTF")
                            event.source = "CTFtime"
                            event.source_id = str(item.get("id", ""))
                            event.ctftime_url = item.get("ctftime_url", "")
                            
                            # Dates
                            start_str = item.get("start", "")
                            end_str = item.get("finish", "")
                            if start_str:
                                event.start_date = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                            if end_str:
                                event.end_date = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                            
                            # Location
                            if item.get("onsite"):
                                event.is_online = False
                                event.is_offline = True
                                loc = item.get("location", "TBD")
                                event.location = f"📍 {loc}"
                                
                                # Check if in India
                                if "india" in loc.lower():
                                    event.country = "India"
                                    for state_name in INDIAN_STATES.values():
                                        if state_name.lower() in loc.lower():
                                            event.state = state_name
                                            break
                            else:
                                event.is_online = True
                                event.location = "🌐 Online"
                            
                            # Links
                            event.website_url = item.get("url", "")
                            event.registration_url = item.get("url", "") or event.ctftime_url
                            
                            # Description
                            event.description = item.get("description", "")
                            event.short_description = event.description[:200] if event.description else ""
                            
                            # Format
                            format_str = item.get("format", "").lower()
                            if "jeopardy" in format_str:
                                event.format_type = CTFFormat.JEOPARDY
                            elif "attack" in format_str or "defense" in format_str:
                                event.format_type = CTFFormat.ATTACK_DEFENSE
                            elif "mixed" in format_str:
                                event.format_type = CTFFormat.MIXED
                            else:
                                event.format_type = CTFFormat.OTHER
                            
                            # Statistics
                            event.participants_count = item.get("participants", 0)
                            event.weight = float(item.get("weight", 0))
                            
                            # Prizes
                            event.prize_pool_total = float(item.get("prizes_amount", 0))
                            event.prize_currency = item.get("prizes_currency", "USD")
                            
                            # Organizer
                            organizer = item.get("organizer", {})
                            if organizer:
                                event.organizer_name = organizer.get("name", "Unknown")
                                event.organizer_url = organizer.get("url", "")
                            
                            # Tags
                            tags = item.get("tags", [])
                            if tags:
                                event.tags = [tag.get("name", "") for tag in tags if tag.get("name")]
                            
                            # Categories
                            categories = item.get("categories", [])
                            if categories:
                                event.categories_available = [cat.get("name", "") for cat in categories if cat.get("name")]
                            
                            event.calculate_duration()
                            
                            if event.title and event.start_date:
                                events.append(event)
                                
                        except Exception as e:
                            continue
                            
        except Exception as e:
            console.print(f"[yellow]CTFtime API scrape warning: {str(e)[:100]}[/yellow]")
        
        return events

class CTFtimeHTMLScraper(BaseScraper):
    """Scraper for CTFtime website using httpx (no Playwright)"""
    
    def __init__(self):
        super().__init__()
        self.name = "CTFtime HTML"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False, follow_redirects=True) as client:
                response = await client.get(
                    "https://ctftime.org/event/list/upcoming",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "text/html,application/xhtml+xml"
                    }
                )
                
                if response.status_code == 200:
                    html = response.text
                    
                    # Parse events using regex
                    event_pattern = r'<tr[^>]*>.*?<td[^>]*>.*?(\d{4}-\d{2}-\d{2}).*?</td>.*?<td[^>]*>.*?<a[^>]*href="(/event/\d+/)"[^>]*>(.*?)</a>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?</tr>'
                    
                    matches = re.findall(event_pattern, html, re.DOTALL)
                    
                    for match in matches[:50]:
                        try:
                            event = CTFEvent()
                            event.title = match[2].strip()
                            event.ctftime_url = f"https://ctftime.org{match[1]}"
                            event.source = "CTFtime"
                            
                            # Parse date
                            date_str = match[0].strip()
                            event.start_date = datetime.fromisoformat(date_str + "T00:00:00+00:00")
                            event.end_date = event.start_date + timedelta(days=2)
                            
                            # Location
                            loc_text = match[3].strip()
                            if "online" in loc_text.lower():
                                event.is_online = True
                                event.location = "🌐 Online"
                            else:
                                event.is_offline = True
                                event.location = f"📍 {loc_text}"
                                if "india" in loc_text.lower():
                                    event.country = "India"
                            
                            # Format
                            format_text = match[4].strip().lower()
                            if "jeopardy" in format_text:
                                event.format_type = CTFFormat.JEOPARDY
                            elif "attack" in format_text:
                                event.format_type = CTFFormat.ATTACK_DEFENSE
                            
                            # Weight
                            weight_text = match[5].strip()
                            weight_match = re.search(r'[\d.]+', weight_text)
                            if weight_match:
                                event.weight = float(weight_match.group())
                            
                            # Participants
                            parts_text = match[6].strip()
                            parts_match = re.search(r'\d+', parts_text)
                            if parts_match:
                                event.participants_count = int(parts_match.group())
                            
                            event.website_url = event.ctftime_url
                            event.registration_url = event.ctftime_url
                            event.calculate_duration()
                            
                            if event.title:
                                events.append(event)
                                
                        except Exception:
                            continue
                            
        except Exception as e:
            console.print(f"[yellow]CTFtime HTML scrape warning: {str(e)[:100]}[/yellow]")
        
        return events

class CTFHuntScraper(BaseScraper):
    """Scraper for CTF Hunt"""
    
    def __init__(self):
        super().__init__()
        self.name = "CTF Hunt"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(
                    "https://ctfhunt.com/api/events",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data:
                        try:
                            event = CTFEvent()
                            event.title = item.get("title", "Unknown CTF")
                            event.source = "CTF Hunt"
                            event.source_id = str(item.get("id", ""))
                            
                            # Dates
                            start_str = item.get("start", "")
                            end_str = item.get("end", "")
                            if start_str:
                                event.start_date = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                            if end_str:
                                event.end_date = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                            
                            # Location
                            location = item.get("location", "")
                            if location and "online" not in location.lower():
                                event.is_online = False
                                event.is_offline = True
                                event.location = f"📍 {location}"
                            else:
                                event.is_online = True
                                event.location = "🌐 Online"
                            
                            # Links
                            event.website_url = item.get("url", "")
                            event.registration_url = item.get("registration_url", "") or event.website_url
                            
                            # Description
                            event.description = item.get("description", "")
                            event.short_description = event.description[:200] if event.description else ""
                            
                            # Format
                            format_str = item.get("format", "").lower()
                            if "jeopardy" in format_str:
                                event.format_type = CTFFormat.JEOPARDY
                            elif "attack" in format_str:
                                event.format_type = CTFFormat.ATTACK_DEFENSE
                            
                            # Statistics
                            event.participants_count = item.get("participants", 0)
                            
                            # Organizer
                            event.organizer_name = item.get("organizer", "Unknown")
                            
                            # Tags
                            tags = item.get("tags", [])
                            if tags:
                                event.tags = tags
                            
                            event.calculate_duration()
                            
                            if event.title and event.start_date:
                                events.append(event)
                                
                        except Exception:
                            continue
                            
        except Exception as e:
            pass  # CTF Hunt may not always be available
        
        return events

class UnstopCTFScraper(BaseScraper):
    """Scraper for Unstop CTF events (Indian platform)"""
    
    def __init__(self):
        super().__init__()
        self.name = "Unstop CTF"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False, follow_redirects=True) as client:
                response = await client.get(
                    "https://unstop.com/api/public/opportunity/search?opptype=competitions&category=ctf&per_page=20&page=1",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/json",
                        "Origin": "https://unstop.com",
                        "Referer": "https://unstop.com/"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse Unstop response
                    opportunities = data.get("data", {}).get("data", [])
                    if not opportunities:
                        opportunities = data.get("opportunities", [])
                    
                    for item in opportunities:
                        try:
                            event = CTFEvent()
                            event.title = item.get("name", item.get("title", "Unstop CTF"))
                            event.source = "Unstop"
                            event.source_id = str(item.get("id", ""))
                            event.country = "India"
                            
                            # Dates
                            start_str = item.get("start_date", item.get("startDate", ""))
                            end_str = item.get("end_date", item.get("endDate", ""))
                            if start_str:
                                try:
                                    event.start_date = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                                except:
                                    event.start_date = datetime.now(timezone.utc) + timedelta(days=30)
                            if end_str:
                                try:
                                    event.end_date = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                                except:
                                    event.end_date = event.start_date + timedelta(days=2) if event.start_date else None
                            
                            # Location
                            location = item.get("location", item.get("venue", ""))
                            if location:
                                event.is_offline = True
                                event.is_online = False
                                event.location = f"📍 {location}"
                                
                                # Detect state
                                for state_name in INDIAN_STATES.values():
                                    if state_name.lower() in location.lower():
                                        event.state = state_name
                                        break
                            else:
                                event.is_online = True
                                event.location = "🌐 Online"
                            
                            # Links
                            slug = item.get("slug", item.get("opportunity_slug", ""))
                            if slug:
                                event.website_url = f"https://unstop.com/competition/{slug}"
                                event.registration_url = event.website_url
                            
                            # Description
                            event.description = item.get("description", item.get("short_description", ""))
                            event.short_description = event.description[:200] if event.description else ""
                            
                            # Organizer
                            org = item.get("organizer", item.get("college", item.get("company", {})))
                            if isinstance(org, dict):
                                event.organizer_name = org.get("name", "Unknown")
                            elif isinstance(org, str):
                                event.organizer_name = org
                            
                            # Tags
                            event.tags = ["ctf", "india", "unstop"]
                            
                            # Set defaults for Indian CTFs
                            event.format_type = CTFFormat.JEOPARDY
                            event.weight = 30.0
                            event.difficulty = DifficultyLevel.INTERMEDIATE
                            event.calculate_duration()
                            
                            if event.title:
                                events.append(event)
                                
                        except Exception:
                            continue
                            
        except Exception as e:
            console.print(f"[yellow]Unstop scrape warning: {str(e)[:100]}[/yellow]")
        
        return events

class DevfolioCTFScraper(BaseScraper):
    """Scraper for Devfolio CTF/hackathon events"""
    
    def __init__(self):
        super().__init__()
        self.name = "Devfolio CTF"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False, follow_redirects=True) as client:
                response = await client.get(
                    "https://devfolio.co/api/hackathons?filter=open&page=1&limit=20",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/json",
                        "Origin": "https://devfolio.co",
                        "Referer": "https://devfolio.co/"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    hackathons = data.get("hackathons", [])
                    
                    for item in hackathons:
                        try:
                            # Only include CTF-related events
                            title = item.get("name", "")
                            if not any(kw in title.lower() for kw in ['ctf', 'capture', 'flag', 'hackathon', 'security', 'cyber']):
                                continue
                            
                            event = CTFEvent()
                            event.title = title
                            event.source = "Devfolio"
                            event.source_id = str(item.get("id", ""))
                            event.country = "India"
                            
                            # Dates
                            start_str = item.get("start_date", "")
                            end_str = item.get("end_date", "")
                            if start_str:
                                event.start_date = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                            if end_str:
                                event.end_date = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                            
                            # Location
                            location = item.get("location", "")
                            if location and "online" not in location.lower():
                                event.is_offline = True
                                event.is_online = False
                                event.location = f"📍 {location}"
                                
                                # Detect state
                                for state_name in INDIAN_STATES.values():
                                    if state_name.lower() in location.lower():
                                        event.state = state_name
                                        break
                            else:
                                event.is_online = True
                                event.location = "🌐 Online"
                            
                            # Links
                            slug = item.get("slug", "")
                            if slug:
                                event.website_url = f"https://devfolio.co/{slug}"
                                event.registration_url = event.website_url
                            
                            # Description
                            event.description = item.get("description", "")
                            event.short_description = event.description[:200] if event.description else ""
                            
                            # Organizer
                            org = item.get("organizer", {})
                            if org:
                                event.organizer_name = org.get("name", "Unknown")
                            
                            # Tags
                            event.tags = ["ctf", "india", "devfolio", "hackathon"]
                            
                            # Set defaults
                            event.format_type = CTFFormat.JEOPARDY
                            event.weight = 25.0
                            event.difficulty = DifficultyLevel.INTERMEDIATE
                            event.calculate_duration()
                            
                            if event.title:
                                events.append(event)
                                
                        except Exception:
                            continue
                            
        except Exception as e:
            console.print(f"[yellow]Devfolio scrape warning: {str(e)[:100]}[/yellow]")
        
        return events

class D2CCTFScraper(BaseScraper):
    """Scraper for D2C (Devil2Coding) CTF events"""
    
    def __init__(self):
        super().__init__()
        self.name = "D2C CTF"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False, follow_redirects=True) as client:
                response = await client.get(
                    "https://d2c.in/api/ctf/events",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ctfs = data.get("events", data.get("data", []))
                    
                    for item in ctfs:
                        try:
                            event = CTFEvent()
                            event.title = item.get("title", item.get("name", "D2C CTF"))
                            event.source = "D2C"
                            event.source_id = str(item.get("id", ""))
                            event.country = "India"
                            
                            # Dates
                            start_str = item.get("start_date", item.get("start", ""))
                            end_str = item.get("end_date", item.get("end", ""))
                            if start_str:
                                try:
                                    event.start_date = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                                except:
                                    event.start_date = datetime.now(timezone.utc) + timedelta(days=45)
                            if end_str:
                                try:
                                    event.end_date = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                                except:
                                    event.end_date = event.start_date + timedelta(days=3) if event.start_date else None
                            
                            # Location
                            location = item.get("location", "")
                            if location:
                                event.is_offline = True
                                event.is_online = False
                                event.location = f"📍 {location}"
                                for state_name in INDIAN_STATES.values():
                                    if state_name.lower() in location.lower():
                                        event.state = state_name
                                        break
                            else:
                                event.is_online = True
                                event.location = "🌐 Online"
                            
                            # Links
                            event.website_url = item.get("url", item.get("website", "https://d2c.in"))
                            event.registration_url = item.get("registration_url", event.website_url)
                            
                            # Description
                            event.description = item.get("description", "")
                            event.short_description = event.description[:200] if event.description else ""
                            
                            # Organizer
                            event.organizer_name = item.get("organizer", "D2C")
                            
                            # Tags
                            event.tags = ["ctf", "india", "d2c"]
                            
                            # Set defaults
                            event.format_type = CTFFormat.JEOPARDY
                            event.weight = 35.0
                            event.difficulty = DifficultyLevel.INTERMEDIATE
                            event.calculate_duration()
                            
                            if event.title:
                                events.append(event)
                                
                        except Exception:
                            continue
                            
        except Exception as e:
            pass  # D2C may not always be available
        
        return events

class HackerOneCTFScraper(BaseScraper):
    """Scraper for HackerOne CTF events"""
    
    def __init__(self):
        super().__init__()
        self.name = "HackerOne CTF"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.get(
                    "https://hackerone.com/ctf/events",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for item in data:
                        try:
                            event = CTFEvent()
                            event.title = item.get("title", "HackerOne CTF")
                            event.source = "HackerOne"
                            event.source_id = str(item.get("id", ""))
                            
                            # Dates
                            start_str = item.get("start_date", "")
                            end_str = item.get("end_date", "")
                            if start_str:
                                event.start_date = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                            if end_str:
                                event.end_date = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                            
                            # Online only
                            event.is_online = True
                            event.location = "🌐 Online"
                            
                            # Links
                            event.website_url = item.get("url", "https://hackerone.com/ctf")
                            event.registration_url = event.website_url
                            
                            # Description
                            event.description = item.get("description", "")
                            event.short_description = event.description[:200] if event.description else ""
                            
                            # Organizer
                            event.organizer_name = "HackerOne"
                            
                            # Tags
                            event.tags = ["ctf", "bugbounty", "hackerone"]
                            
                            # Set defaults
                            event.format_type = CTFFormat.JEOPARDY
                            event.weight = 60.0
                            event.difficulty = DifficultyLevel.ADVANCED
                            event.calculate_duration()
                            
                            if event.title:
                                events.append(event)
                                
                        except Exception:
                            continue
                            
        except Exception as e:
            pass  # HackerOne may not always be available
        
        return events

# ==================== CTF INTELLIGENCE ENGINE ====================
class CTFIntelligenceEngine:
    """Advanced CTF data enrichment and intelligence"""
    
    def __init__(self):
        self.indian_cities_states = {
            "bengaluru": "Karnataka", "bangalore": "Karnataka",
            "mumbai": "Maharashtra", "pune": "Maharashtra",
            "delhi": "Delhi", "new delhi": "Delhi",
            "hyderabad": "Telangana", "chennai": "Tamil Nadu",
            "kolkata": "West Bengal", "ahmedabad": "Gujarat",
            "jaipur": "Rajasthan", "lucknow": "Uttar Pradesh",
            "kochi": "Kerala", "thiruvananthapuram": "Kerala",
            "chandigarh": "Chandigarh", "bhopal": "Madhya Pradesh",
            "indore": "Madhya Pradesh", "goa": "Goa",
            "surat": "Gujarat", "visakhapatnam": "Andhra Pradesh",
            "guwahati": "Assam", "patna": "Bihar",
            "ranchi": "Jharkhand", "bhubaneswar": "Odisha",
            "dehradun": "Uttarakhand", "shimla": "Himachal Pradesh",
            "srinagar": "Jammu and Kashmir", "amritsar": "Punjab",
            "nagpur": "Maharashtra", "thane": "Maharashtra",
            "agra": "Uttar Pradesh", "varanasi": "Uttar Pradesh",
            "nashik": "Maharashtra", "aurangabad": "Maharashtra",
            "vadodara": "Gujarat", "rajkot": "Gujarat",
            "coimbatore": "Tamil Nadu", "madurai": "Tamil Nadu",
            "mangalore": "Karnataka", "mysore": "Karnataka",
        }
    
    def enrich_event(self, event: CTFEvent) -> CTFEvent:
        """Enrich event with additional intelligence"""
        self._detect_indian_location(event)
        self._enrich_organizer(event)
        self._detect_difficulty(event)
        self._generate_tags(event)
        self._calculate_data_quality(event)
        
        if not event.id:
            event.id = self._generate_id(event)
        
        return event
    
    def _detect_indian_location(self, event: CTFEvent):
        """Detect if event is in India and identify state"""
        location_lower = event.location.lower()
        
        # Check for Indian cities
        for city, state in self.indian_cities_states.items():
            if city in location_lower:
                event.city = city.title()
                event.state = state
                event.country = "India"
                break
        
        # Check for state names
        for state_name in INDIAN_STATES.values():
            if state_name.lower() in location_lower:
                event.state = state_name
                event.country = "India"
                break
    
    def _enrich_organizer(self, event: CTFEvent):
        """Enrich organizer information"""
        known_indian_orgs = ["bi0s", "infosec iit", "nullcon", "d2c", "devfolio", "unstop"]
        org_lower = event.organizer_name.lower()
        
        for org in known_indian_orgs:
            if org in org_lower:
                event.country = "India"
                break
    
    def _detect_difficulty(self, event: CTFEvent):
        """Detect CTF difficulty level"""
        title_lower = event.title.lower()
        desc_lower = event.description.lower()
        
        beginner_keywords = ["beginner", "junior", "intro", "101", "easy", "learning"]
        if any(kw in title_lower or kw in desc_lower for kw in beginner_keywords):
            event.difficulty = DifficultyLevel.BEGINNER
            return
        
        expert_keywords = ["expert", "hard", "advanced", "master", "elite"]
        if any(kw in title_lower or kw in desc_lower for kw in expert_keywords):
            event.difficulty = DifficultyLevel.EXPERT
            return
        
        if event.weight > 75:
            event.difficulty = DifficultyLevel.EXPERT
        elif event.weight > 50:
            event.difficulty = DifficultyLevel.ADVANCED
        elif event.weight > 25:
            event.difficulty = DifficultyLevel.INTERMEDIATE
        else:
            event.difficulty = DifficultyLevel.BEGINNER
    
    def _generate_tags(self, event: CTFEvent):
        """Generate relevant tags for the event"""
        tags = set(event.tags)
        tags.add(event.format_type.value.lower().replace("-", "").replace(" ", ""))
        tags.add(event.difficulty.value.lower())
        
        if event.country:
            tags.add(event.country.lower())
        if event.state:
            tags.add(event.state.lower().replace(" ", ""))
        if event.organizer_name:
            tags.add(event.organizer_name.lower().replace(" ", ""))
        
        if event.is_online:
            tags.add("online")
        if event.is_offline:
            tags.add("offline")
        
        event.tags = list(tags)
    
    def _calculate_data_quality(self, event: CTFEvent):
        """Calculate data quality score"""
        score = 0
        total_checks = 0
        
        checks = [
            (bool(event.title), 10),
            (bool(event.start_date), 10),
            (bool(event.end_date), 10),
            (bool(event.description), 10),
            (bool(event.website_url), 10),
            (bool(event.registration_url), 10),
            (event.organizer_name != "Unknown", 10),
            (event.participants_count > 0, 10),
            (event.weight > 0, 10),
            (len(event.tags) > 0, 10),
            (event.challenges_count > 0, 5),
            (bool(event.rules), 5),
            (bool(event.schedule), 5),
            (event.prize_pool_total > 0, 5),
        ]
        
        for condition, points in checks:
            total_checks += points
            if condition:
                score += points
        
        event.data_quality_score = round((score / total_checks) * 100, 2)
    
    def _generate_id(self, event: CTFEvent) -> str:
        """Generate unique ID for event"""
        unique_string = f"{event.title}{event.source}{event.start_date}{event.organizer_name}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]

# ==================== ANALYTICS ENGINE ====================
class AnalyticsEngine:
    """CTF Analytics and Statistics Engine"""
    
    def analyze_events(self, events: List[CTFEvent]) -> CTFAnalytics:
        """Analyze a list of CTF events and generate statistics"""
        analytics = CTFAnalytics()
        analytics.total_events = len(events)
        
        format_counts = defaultdict(int)
        difficulty_counts = defaultdict(int)
        source_counts = defaultdict(int)
        country_counts = defaultdict(int)
        state_counts = defaultdict(int)
        monthly_counts = defaultdict(int)
        organizer_counts = defaultdict(int)
        tag_counts = defaultdict(int)
        
        total_weight = 0
        total_participants = 0
        total_prize = 0
        
        for event in events:
            format_counts[event.format_type.value] += 1
            difficulty_counts[event.difficulty.value] += 1
            source_counts[event.source] += 1
            
            if event.country:
                country_counts[event.country] += 1
            if event.state:
                state_counts[event.state] += 1
            if event.start_date:
                month_key = event.start_date.strftime("%Y-%m")
                monthly_counts[month_key] += 1
            if event.organizer_name:
                organizer_counts[event.organizer_name] += 1
            for tag in event.tags:
                tag_counts[tag] += 1
            
            if event.is_online:
                analytics.online_events += 1
            if event.is_offline:
                analytics.offline_events += 1
            if event.is_hybrid:
                analytics.hybrid_events += 1
            
            total_weight += event.weight
            total_participants += event.participants_count
            total_prize += event.prize_pool_total
        
        if events:
            analytics.average_weight = round(total_weight / len(events), 2)
            analytics.average_participants = round(total_participants / len(events), 2)
            analytics.total_prize_pool = total_prize
        
        analytics.format_distribution = dict(format_counts)
        analytics.difficulty_distribution = dict(difficulty_counts)
        analytics.source_distribution = dict(source_counts)
        analytics.country_distribution = dict(country_counts)
        analytics.state_distribution = dict(state_counts)
        analytics.monthly_trend = dict(sorted(monthly_counts.items()))
        analytics.top_organizers = sorted(organizer_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        analytics.top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return analytics
    
    def display_analytics(self, analytics: CTFAnalytics):
        """Display analytics in a beautiful format"""
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]📊 CTF EVENT ANALYTICS DASHBOARD[/bold cyan]",
            border_style="cyan"
        ))
        
        # Overview
        overview = Table(show_header=False, box=box.ROUNDED)
        overview.add_column("Metric", style="bold")
        overview.add_column("Value", style="cyan")
        
        overview.add_row("Total Events", str(analytics.total_events))
        overview.add_row("Online Events", str(analytics.online_events))
        overview.add_row("Offline Events", str(analytics.offline_events))
        overview.add_row("Average Weight", f"{analytics.average_weight:.2f}")
        overview.add_row("Average Participants", f"{analytics.average_participants:.0f}")
        overview.add_row("Total Prize Pool", f"${analytics.total_prize_pool:,.2f}")
        
        console.print(Panel(overview, title="[bold]Overview[/bold]", border_style="green"))
        
        # Source Distribution
        source_table = Table(show_header=True, box=box.ROUNDED)
        source_table.add_column("Source", style="bold")
        source_table.add_column("Count", justify="right", style="cyan")
        source_table.add_column("Percentage", justify="right", style="green")
        
        total = sum(analytics.source_distribution.values())
        for src, count in sorted(analytics.source_distribution.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            source_table.add_row(src, str(count), f"{pct:.1f}%")
        
        console.print(Panel(source_table, title="[bold]Source Distribution[/bold]", border_style="blue"))
        
        # Format Distribution
        format_table = Table(show_header=True, box=box.ROUNDED)
        format_table.add_column("Format", style="bold")
        format_table.add_column("Count", justify="right", style="cyan")
        format_table.add_column("Percentage", justify="right", style="green")
        
        total = sum(analytics.format_distribution.values())
        for fmt, count in sorted(analytics.format_distribution.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            format_table.add_row(fmt, str(count), f"{pct:.1f}%")
        
        console.print(Panel(format_table, title="[bold]Format Distribution[/bold]", border_style="yellow"))
        
        # Top Organizers
        org_table = Table(show_header=True, box=box.ROUNDED)
        org_table.add_column("Rank", justify="center", style="bold")
        org_table.add_column("Organizer", style="bold")
        org_table.add_column("Events", justify="right", style="cyan")
        
        for i, (org, count) in enumerate(analytics.top_organizers[:5], 1):
            org_table.add_row(str(i), org, str(count))
        
        console.print(Panel(org_table, title="[bold]Top Organizers[/bold]", border_style="magenta"))

# ==================== EXPORT ENGINE ====================
class ExportEngine:
    """Export CTF events to various formats"""
    
    @staticmethod
    def export_json(events: List[CTFEvent], filename: str = None) -> str:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ctfforge_export_{timestamp}.json"
        
        data = [event.to_dict() for event in events]
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    @staticmethod
    def export_csv(events: List[CTFEvent], filename: str = None) -> str:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ctfforge_export_{timestamp}.csv"
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            writer.writerow([
                "Title", "Start Date", "End Date", "Duration (hours)",
                "Location", "Country", "State", "City",
                "Format", "Difficulty", "Source",
                "Registration URL", "Website URL",
                "Organizer", "Participants", "Weight",
                "Prize Pool", "Tags", "AI Score", "Status"
            ])
            
            for event in events:
                writer.writerow([
                    event.title,
                    event.start_date.isoformat() if event.start_date else "",
                    event.end_date.isoformat() if event.end_date else "",
                    event.duration_hours,
                    event.location,
                    event.country,
                    event.state,
                    event.city,
                    event.format_type.value,
                    event.difficulty.value,
                    event.source,
                    event.registration_url,
                    event.website_url,
                    event.organizer_name,
                    event.participants_count,
                    event.weight,
                    event.prize_pool_total,
                    ", ".join(event.tags),
                    event.ai_score,
                    event.get_status().value
                ])
        
        return filename

# ==================== MAIN APPLICATION ====================
class CTFForgeApp:
    """Main CTFForge Application"""
    
    def __init__(self):
        self.ai_engine = AIRankingEngine()
        self.intelligence_engine = CTFIntelligenceEngine()
        self.analytics_engine = AnalyticsEngine()
        self.export_engine = ExportEngine()
        self.events: List[CTFEvent] = []
        self.selected_states: List[str] = []
        
    def display_banner(self):
        """Display application banner"""
        console.clear()
        banner = f"""
[bold cyan]╔══════════════════════════════════════════════════════════════╗
║                                                                  ║
║     ██████  ████████ ███████  ██████  ██████   ██████  ███████  ║
║    ██       ██       ██      ██    ██ ██   ██ ██       ██       ║
║    ██   ███ █████    █████   ██    ██ ██████  ██   ███ █████    ║
║    ██    ██ ██       ██      ██    ██ ██   ██ ██    ██ ██       ║
║     ██████  ██       ██       ██████  ██   ██  ██████  ███████  ║
║                                                                  ║
║                    🔐 CTFForge Pro v{__version__} 🔐                      ║
║              Advanced CTF Discovery & Intelligence Engine         ║
║                                                                  ║
║    Made by [bold yellow]VRJ[/bold yellow] • GitHub: [link=https://github.com/{__github__}]{__github__}[/link]            ║
║    LinkedIn: [link=https://linkedin.com/in/{__linkedin__}]{__linkedin__}[/link]              ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝[/bold cyan]
"""
        console.print(banner)
    
    def display_menu(self) -> str:
        """Display main menu and get user choice"""
        menu = Panel.fit(
            "[bold]Main Menu[/bold]\n\n"
            "1. 🔍 Find CTF Events\n"
            "2. 📊 View Analytics Dashboard\n"
            "3. 📖 View Help & Documentation\n"
            "4. 🚪 Exit",
            border_style="cyan",
            title="[bold]Navigation[/bold]"
        )
        console.print(menu)
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4"], default="1")
        return choice
    
    def select_states(self) -> List[str]:
        """Interactive state selection - Complete list of all 36 states/UTs"""
        console.print(Panel.fit(
            "[bold yellow]🌏 Select Indian States for Local CTF Discovery[/bold yellow]",
            border_style="yellow"
        ))
        
        console.print("\n[bold]All Indian States & Union Territories:[/bold]\n")
        
        # Display all states in columns
        for i in range(1, 37, 3):
            row = ""
            for j in range(3):
                idx = i + j
                if idx <= 36:
                    state = INDIAN_STATES[idx]
                    row += f"  [cyan]{idx:2d}.[/cyan] {state:<35}"
            console.print(row)
        
        console.print("\n[bold]Options:[/bold]")
        console.print("  [green]all[/green] - Select all states")
        console.print("  [green]1,2,3[/green] - Select specific states by number")
        console.print("  [green]1-10[/green] - Select a range of states")
        
        choice = Prompt.ask("\nYour selection", default="all")
        
        if choice.lower() == "all":
            return list(INDIAN_STATES.values())
        
        selected = []
        
        # Handle ranges
        if "-" in choice:
            try:
                parts = choice.split("-")
                start = int(parts[0].strip())
                end = int(parts[1].strip())
                for i in range(start, end + 1):
                    if i in INDIAN_STATES:
                        selected.append(INDIAN_STATES[i])
            except:
                pass
        else:
            # Parse individual state numbers
            for num in choice.split(","):
                try:
                    idx = int(num.strip())
                    if idx in INDIAN_STATES:
                        selected.append(INDIAN_STATES[idx])
                except:
                    pass
        
        return selected if selected else list(INDIAN_STATES.values())
    
    async def scrape_events(self) -> List[CTFEvent]:
        """Scrape events from all sources"""
        console.print("\n[bold cyan]🕸️ Initializing CTF Scraping Network...[/bold cyan]")
        
        scrapers = [
            CTFtimeAPIScraper(),
            CTFtimeHTMLScraper(),
            CTFHuntScraper(),
            UnstopCTFScraper(),
            DevfolioCTFScraper(),
            D2CCTFScraper(),
            HackerOneCTFScraper()
        ]
        
        all_events = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]Scraping CTF sources...", total=len(scrapers))
            
            for scraper in scrapers:
                progress.update(task, description=f"[cyan]Scraping {scraper.name}...")
                try:
                    events = await scraper.scrape()
                    all_events.extend(events)
                    if events:
                        console.print(f"  [green]✅ {scraper.name}: {len(events)} events found[/green]")
                    else:
                        console.print(f"  [yellow]⚠️ {scraper.name}: 0 events found[/yellow]")
                except Exception as e:
                    console.print(f"  [red]❌ {scraper.name}: Failed - {str(e)[:80]}[/red]")
                progress.advance(task)
        
        # Enrich events with intelligence
        console.print("\n[bold cyan]🧠 Enriching events with intelligence...[/bold cyan]")
        enriched_events = []
        for event in all_events:
            enriched = self.intelligence_engine.enrich_event(event)
            enriched_events.append(enriched)
        
        # Deduplicate
        seen = set()
        unique_events = []
        for event in enriched_events:
            key = f"{event.title.lower()}|{event.source}|{event.start_date}"
            if key not in seen:
                seen.add(key)
                unique_events.append(event)
        
        console.print(f"  [bold green]✅ Total unique events: {len(unique_events)}[/bold green]")
        
        return unique_events
    
    def filter_events(self, events: List[CTFEvent]) -> List[CTFEvent]:
        """Apply user filters to events"""
        console.print("\n[bold]🔍 Apply Filters:[/bold]")
        
        # Status filter
        console.print("\n[bold]Status:[/bold]")
        console.print("1. All Events")
        console.print("2. Only Upcoming")
        console.print("3. Only Ongoing")
        status_choice = Prompt.ask("Select", choices=["1", "2", "3"], default="1")
        
        # Format filter
        console.print("\n[bold]Format:[/bold]")
        console.print("1. All Formats")
        console.print("2. Jeopardy")
        console.print("3. Attack-Defense")
        console.print("4. Mixed")
        format_choice = Prompt.ask("Select", choices=["1", "2", "3", "4"], default="1")
        
        # Location filter
        console.print("\n[bold]Location:[/bold]")
        console.print("1. All Locations")
        console.print("2. Online Only")
        console.print("3. Offline Only")
        console.print("4. India Only")
        loc_choice = Prompt.ask("Select", choices=["1", "2", "3", "4"], default="1")
        
        # Weight filter
        console.print("\n[bold]Minimum CTF Weight:[/bold]")
        console.print("1. Any Weight")
        console.print("2. > 25 (Intermediate+)")
        console.print("3. > 50 (Advanced+)")
        console.print("4. > 75 (Expert+)")
        weight_choice = Prompt.ask("Select", choices=["1", "2", "3", "4"], default="1")
        
        # Apply filters
        filtered = events.copy()
        
        now = datetime.now(timezone.utc)
        if status_choice == "2":
            filtered = [e for e in filtered if e.start_date and e.start_date > now]
        elif status_choice == "3":
            filtered = [e for e in filtered if e.start_date and e.end_date and e.start_date <= now <= e.end_date]
        
        format_map = {"2": CTFFormat.JEOPARDY, "3": CTFFormat.ATTACK_DEFENSE, "4": CTFFormat.MIXED}
        if format_choice in format_map:
            filtered = [e for e in filtered if e.format_type == format_map[format_choice]]
        
        if loc_choice == "2":
            filtered = [e for e in filtered if e.is_online]
        elif loc_choice == "3":
            filtered = [e for e in filtered if e.is_offline]
        elif loc_choice == "4":
            filtered = [e for e in filtered if e.country == "India"]
        
        weight_map = {"2": 25, "3": 50, "4": 75}
        if weight_choice in weight_map:
            filtered = [e for e in filtered if e.weight >= weight_map[weight_choice]]
        
        # State filter
        if self.selected_states:
            state_filtered = []
            for event in filtered:
                if event.is_online or event.state in self.selected_states or event.country == "India":
                    state_filtered.append(event)
            filtered = state_filtered
        
        console.print(f"  [green]✅ After filtering: {len(filtered)} events[/green]")
        
        return filtered
    
    def display_events(self, events: List[CTFEvent]):
        """Display events in a beautiful table"""
        if not events:
            console.print("[bold red]No events found matching your criteria.[/bold red]")
            return
        
        table = Table(
            title=f"🔐 {len(events)} CTF Events Found",
            show_lines=True,
            box=box.ROUNDED,
            header_style="bold cyan",
            title_style="bold cyan"
        )
        
        table.add_column("Rank", justify="center", style="cyan", width=4)
        table.add_column("CTF Name", style="bold yellow", width=30)
        table.add_column("Dates", style="green", width=18)
        table.add_column("Location", style="magenta", width=15)
        table.add_column("Format", justify="center", width=10)
        table.add_column("Difficulty", justify="center", width=10)
        table.add_column("Weight", justify="center", width=6)
        table.add_column("Score", justify="center", width=6)
        table.add_column("Source", justify="center", width=10)
        
        for i, event in enumerate(events[:30], 1):
            if event.start_date and event.end_date:
                date_str = f"{event.start_date.strftime('%d %b')}→{event.end_date.strftime('%d %b')}"
            else:
                date_str = "TBD"
            
            location = event.location[:18]
            
            diff_colors = {
                DifficultyLevel.BEGINNER: "green",
                DifficultyLevel.INTERMEDIATE: "yellow",
                DifficultyLevel.ADVANCED: "red",
                DifficultyLevel.EXPERT: "bold red"
            }
            diff_str = f"[{diff_colors.get(event.difficulty, 'white')}]{event.difficulty.value[:8]}[/]"
            
            if event.weight > 75:
                weight_str = f"[bold red]{event.weight:.0f}[/]"
            elif event.weight > 50:
                weight_str = f"[yellow]{event.weight:.0f}[/]"
            elif event.weight > 25:
                weight_str = f"[green]{event.weight:.0f}[/]"
            else:
                weight_str = f"[dim]{event.weight:.0f}[/]"
            
            score_color = "green" if event.ai_score > 75 else "yellow" if event.ai_score > 50 else "red"
            score_str = f"[{score_color}]{event.ai_score:.0f}[/]"
            
            table.add_row(
                str(i),
                event.title[:35] + ("..." if len(event.title) > 35 else ""),
                date_str,
                location,
                event.format_type.value[:8],
                diff_str,
                weight_str,
                score_str,
                event.source[:8]
            )
        
        console.print(table)
        
        # Show summary
        console.print(f"\n[bold cyan]📊 Summary:[/bold cyan]")
        console.print(f"  • Showing top {min(30, len(events))} of {len(events)} events")
        console.print(f"  • Online: {len([e for e in events if e.is_online])} | Offline: {len([e for e in events if e.is_offline])}")
        console.print(f"  • India: {len([e for e in events if e.country == 'India'])} | Global: {len([e for e in events if e.country != 'India'])}")
        
        # Show Indian state distribution
        indian_events = [e for e in events if e.state]
        if indian_events:
            state_counts = defaultdict(int)
            for e in indian_events:
                state_counts[e.state] += 1
            console.print(f"\n[bold]🇮🇳 Indian State Distribution:[/bold]")
            for state, count in sorted(state_counts.items(), key=lambda x: x[1], reverse=True):
                console.print(f"  • {state}: {count} events")
    
    async def run(self):
        """Main application loop"""
        self.display_banner()
        
        while True:
            choice = self.display_menu()
            
            if choice == "1":
                # Find CTF Events
                self.selected_states = self.select_states()
                console.print(f"\n[green]✅ Selected {len(self.selected_states)} states: {', '.join(self.selected_states[:5])}...[/green]")
                
                # Scrape events
                all_events = await self.scrape_events()
                self.events = all_events
                
                if not all_events:
                    console.print("[bold red]❌ No events found from any source. Check your internet connection.[/bold red]")
                    continue
                
                # Filter events
                filtered_events = self.filter_events(all_events)
                
                if not filtered_events:
                    console.print("[bold yellow]⚠️ No events match your filters. Try broader criteria.[/bold yellow]")
                    continue
                
                # Rank events
                console.print("\n[bold cyan]🤖 Applying AI Ranking...[/bold cyan]")
                ranked_events = self.ai_engine.rank_events(filtered_events, self.selected_states)
                
                # Display events
                self.display_events(ranked_events)
                
                # Export options
                if Confirm.ask("\n💾 Export results?", default=True):
                    console.print("\n[bold]Export Format:[/bold]")
                    console.print("1. JSON (Full Data)")
                    console.print("2. CSV (Spreadsheet)")
                    
                    export_choice = Prompt.ask("Select", choices=["1", "2"], default="1")
                    
                    if export_choice == "1":
                        filename = self.export_engine.export_json(ranked_events)
                    else:
                        filename = self.export_engine.export_csv(ranked_events)
                    
                    console.print(f"[bold green]✅ Exported to {filename}[/bold green]")
                
                # Show analytics
                if Confirm.ask("\n📊 Show analytics for these events?", default=False):
                    analytics = self.analytics_engine.analyze_events(ranked_events)
                    self.analytics_engine.display_analytics(analytics)
                
            elif choice == "2":
                # Analytics Dashboard
                if self.events:
                    analytics = self.analytics_engine.analyze_events(self.events)
                    self.analytics_engine.display_analytics(analytics)
                else:
                    console.print("[yellow]No events loaded. Please find CTF events first.[/yellow]")
            
            elif choice == "3":
                # Help
                console.print(Panel.fit(
                    "[bold]CTFForge Pro Help[/bold]\n\n"
                    "[bold]Quick Start:[/bold]\n"
                    "1. Select 'Find CTF Events'\n"
                    "2. Choose Indian states (enter numbers or 'all')\n"
                    "3. Wait for scraping (7 sources)\n"
                    "4. Apply filters\n"
                    "5. View AI-ranked results\n\n"
                    "[bold]Features:[/bold]\n"
                    "• 7 CTF sources: CTFtime, CTF Hunt, Unstop, Devfolio, D2C, HackerOne\n"
                    "• AI-powered ranking with 7 factors\n"
                    "• All 36 Indian states & UTs supported\n"
                    "• JSON & CSV export\n"
                    "• Analytics dashboard\n\n"
                    "[bold]Tips:[/bold]\n"
                    "• Use 'all' for maximum results\n"
                    "• Apply filters to narrow down\n"
                    "• Export to CSV for team sharing\n"
                    "• Check analytics for trends\n\n"
                    "[bold]Sources:[/bold]\n"
                    "• CTFtime API & HTML (Global)\n"
                    "• CTF Hunt (Global)\n"
                    "• Unstop (Indian CTFs)\n"
                    "• Devfolio (Indian Hackathons/CTFs)\n"
                    "• D2C (Indian CTFs)\n"
                    "• HackerOne (Bug Bounty CTFs)",
                    border_style="green",
                    title="[bold]Help & Documentation[/bold]"
                ))
                input("\nPress Enter to continue...")
            
            elif choice == "4":
                # Exit
                console.print("\n[bold cyan]👋 Thank you for using CTFForge Pro! Happy Hacking![/bold cyan]")
                break
        
        console.print("\n[dim]Made with ❤️ by VRJ • GitHub: jadhavidhi06-sketch[/dim]")

# ==================== ENTRY POINT ====================
async def main():
    """Main entry point"""
    app = CTFForgeApp()
    await app.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user. Exiting...[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
