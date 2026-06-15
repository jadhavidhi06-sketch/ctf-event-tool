#!/usr/bin/env python3
"""
CTFForge Pro v4.0 - Advanced CTF Discovery & Intelligence Engine
Author: VRJ
GitHub: jadhavidhi06-sketch
LinkedIn: vidhi-jadhav

Professional CTF Event Aggregator with Multi-Source Intelligence,
Advanced AI Ranking, Real-time Monitoring, and Comprehensive Analytics
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
from playwright.async_api import async_playwright
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

# ==================== CONFIGURATION ====================
console = Console()

__author__ = "VRJ"
__github__ = "jadhavidhi06-sketch"
__linkedin__ = "vidhi-jadhav"
__version__ = "4.0"
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
    # Core Identification
    id: str = ""
    title: str = ""
    subtitle: str = ""
    
    # Timing
    start_date: datetime = None
    end_date: datetime = None
    registration_deadline: Optional[datetime] = None
    duration_hours: float = 0.0
    
    # Location & Format
    location: str = "🌐 Online"
    country: str = "Global"
    state: str = ""
    city: str = ""
    is_online: bool = True
    is_offline: bool = False
    is_hybrid: bool = False
    format_type: CTFFormat = CTFFormat.JEOPARDY
    difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE
    
    # Source Information
    source: str = ""
    source_url: str = ""
    source_id: str = ""
    
    # Links
    registration_url: str = ""
    website_url: str = ""
    discord_url: Optional[str] = None
    twitter_url: Optional[str] = None
    writeup_url: Optional[str] = None
    
    # Organizer Details
    organizer_name: str = "Unknown"
    organizer_url: Optional[str] = None
    organizer_email: Optional[str] = None
    organizer_logo: Optional[str] = None
    
    # Statistics
    participants_count: int = 0
    max_participants: Optional[int] = None
    team_size_min: int = 1
    team_size_max: int = 10
    registered_teams: int = 0
    
    # Prizes & Rewards
    prize_pool_total: float = 0.0
    prize_currency: str = "USD"
    first_place_prize: float = 0.0
    second_place_prize: float = 0.0
    third_place_prize: float = 0.0
    has_swag: bool = False
    has_certificates: bool = False
    has_travel_aid: bool = False
    
    # CTF Specifications
    weight: float = 0.0
    rating: float = 0.0
    category: str = "General"
    tags: List[str] = field(default_factory=list)
    challenges_count: int = 0
    categories_available: List[str] = field(default_factory=list)
    
    # Description & Content
    description: str = ""
    short_description: str = ""
    requirements: str = ""
    rules: str = ""
    schedule: Dict[str, str] = field(default_factory=dict)
    
    # Social & Community
    twitter_hashtag: Optional[str] = None
    discord_invite: Optional[str] = None
    telegram_group: Optional[str] = None
    ctftime_url: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_scraped: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data_quality_score: float = 0.0
    
    # AI Scoring
    ai_score: float = 0.0
    ai_confidence: float = 0.0
    ai_factors: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for export"""
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
        """Calculate event duration in hours"""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.duration_hours = delta.total_seconds() / 3600
        return self.duration_hours
    
    def get_status(self) -> EventStatus:
        """Determine current event status"""
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
    """Analytics and statistics for CTF events"""
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

# ==================== INDIAN STATES DATABASE ====================
INDIAN_STATES = {
    "Andhra Pradesh": {"capital": "Amaravati", "region": "South", "timezone": "IST"},
    "Arunachal Pradesh": {"capital": "Itanagar", "region": "Northeast", "timezone": "IST"},
    "Assam": {"capital": "Dispur", "region": "Northeast", "timezone": "IST"},
    "Bihar": {"capital": "Patna", "region": "East", "timezone": "IST"},
    "Chhattisgarh": {"capital": "Raipur", "region": "Central", "timezone": "IST"},
    "Goa": {"capital": "Panaji", "region": "West", "timezone": "IST"},
    "Gujarat": {"capital": "Gandhinagar", "region": "West", "timezone": "IST"},
    "Haryana": {"capital": "Chandigarh", "region": "North", "timezone": "IST"},
    "Himachal Pradesh": {"capital": "Shimla", "region": "North", "timezone": "IST"},
    "Jharkhand": {"capital": "Ranchi", "region": "East", "timezone": "IST"},
    "Karnataka": {"capital": "Bengaluru", "region": "South", "timezone": "IST"},
    "Kerala": {"capital": "Thiruvananthapuram", "region": "South", "timezone": "IST"},
    "Madhya Pradesh": {"capital": "Bhopal", "region": "Central", "timezone": "IST"},
    "Maharashtra": {"capital": "Mumbai", "region": "West", "timezone": "IST"},
    "Manipur": {"capital": "Imphal", "region": "Northeast", "timezone": "IST"},
    "Meghalaya": {"capital": "Shillong", "region": "Northeast", "timezone": "IST"},
    "Mizoram": {"capital": "Aizawl", "region": "Northeast", "timezone": "IST"},
    "Nagaland": {"capital": "Kohima", "region": "Northeast", "timezone": "IST"},
    "Odisha": {"capital": "Bhubaneswar", "region": "East", "timezone": "IST"},
    "Punjab": {"capital": "Chandigarh", "region": "North", "timezone": "IST"},
    "Rajasthan": {"capital": "Jaipur", "region": "North", "timezone": "IST"},
    "Sikkim": {"capital": "Gangtok", "region": "Northeast", "timezone": "IST"},
    "Tamil Nadu": {"capital": "Chennai", "region": "South", "timezone": "IST"},
    "Telangana": {"capital": "Hyderabad", "region": "South", "timezone": "IST"},
    "Tripura": {"capital": "Agartala", "region": "Northeast", "timezone": "IST"},
    "Uttar Pradesh": {"capital": "Lucknow", "region": "North", "timezone": "IST"},
    "Uttarakhand": {"capital": "Dehradun", "region": "North", "timezone": "IST"},
    "West Bengal": {"capital": "Kolkata", "region": "East", "timezone": "IST"},
    "Delhi": {"capital": "New Delhi", "region": "North", "timezone": "IST"},
    "Jammu and Kashmir": {"capital": "Srinagar", "region": "North", "timezone": "IST"},
    "Ladakh": {"capital": "Leh", "region": "North", "timezone": "IST"},
    "Puducherry": {"capital": "Puducherry", "region": "South", "timezone": "IST"},
    "Chandigarh": {"capital": "Chandigarh", "region": "North", "timezone": "IST"},
    "Andaman and Nicobar Islands": {"capital": "Port Blair", "region": "Islands", "timezone": "IST"},
    "Dadra and Nagar Haveli and Daman and Diu": {"capital": "Daman", "region": "West", "timezone": "IST"},
    "Lakshadweep": {"capital": "Kavaratti", "region": "Islands", "timezone": "IST"}
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
        """Score based on how soon the event starts"""
        now = datetime.now(timezone.utc)
        if not event.start_date:
            return 0.0
        
        days_to_start = (event.start_date - now).days
        
        if days_to_start < 0:  # Ongoing
            return 100.0
        elif days_to_start <= 7:  # Within a week
            return 90.0 - (days_to_start * 5)
        elif days_to_start <= 30:  # Within a month
            return 60.0 - (days_to_start * 1.5)
        elif days_to_start <= 90:  # Within 3 months
            return 30.0 - (days_to_start * 0.3)
        else:
            return max(5.0, 20.0 - (days_to_start * 0.1))
    
    def calculate_popularity_score(self, event: CTFEvent) -> float:
        """Score based on participant count and engagement"""
        score = 0.0
        
        # Participant count
        if event.participants_count > 0:
            participant_score = min(100, event.participants_count / 10)
            score += participant_score * 0.6
        
        # Team registration
        if event.registered_teams > 0:
            team_score = min(100, event.registered_teams / 5)
            score += team_score * 0.4
        
        return min(100, score)
    
    def calculate_prestige_score(self, event: CTFEvent) -> float:
        """Score based on CTF weight and reputation"""
        score = 0.0
        
        # CTFtime weight
        if event.weight > 0:
            weight_score = min(100, event.weight * 1.2)
            score += weight_score * 0.5
        
        # Rating
        if event.rating > 0:
            rating_score = min(100, event.rating * 20)
            score += rating_score * 0.3
        
        # Historical prestige keywords
        prestige_keywords = ['def con', 'google ctf', 'hackthebox', 'tryhackme', 
                           'picoctf', 'csaw', 'asis', 'hxp', 'dragonctf']
        title_lower = event.title.lower()
        for keyword in prestige_keywords:
            if keyword in title_lower:
                score += 15
        
        return min(100, score)
    
    def calculate_accessibility_score(self, event: CTFEvent) -> float:
        """Score based on how accessible the event is"""
        score = 50.0  # Base score
        
        # Online events are more accessible
        if event.is_online:
            score += 30
        
        # Free events
        if event.prize_pool_total == 0:
            score += 10
        
        # Team size flexibility
        if event.team_size_min <= 1:
            score += 5
        
        # Beginner friendly
        if event.difficulty == DifficultyLevel.BEGINNER:
            score += 10
        elif event.difficulty == DifficultyLevel.INTERMEDIATE:
            score += 5
        
        # Multiple categories
        if len(event.categories_available) >= 5:
            score += 5
        
        return min(100, score)
    
    def calculate_rewards_score(self, event: CTFEvent) -> float:
        """Score based on prizes and rewards"""
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
        """Score based on data completeness and event quality"""
        score = 0.0
        fields_checked = 0
        fields_filled = 0
        
        # Check various fields
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
        """Score based on relevance to selected Indian states"""
        if not selected_states:
            return 50.0  # Neutral if no states selected
        
        score = 0.0
        
        # Check if event is in any selected state
        for state in selected_states:
            if state.lower() in event.location.lower() or state.lower() in event.state.lower():
                score += 40
        
        # Check if event is in India
        if event.country.lower() == "india":
            score += 20
        
        # Online events are always relevant
        if event.is_online:
            score += 15
        
        return min(100, score)
    
    def calculate_confidence_score(self, event: CTFEvent) -> float:
        """Calculate confidence in the AI score"""
        confidence = 0.0
        factors = 0
        
        # More data = higher confidence
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
        
        # Normalize
        return min(100, confidence)
    
    def rank_event(self, event: CTFEvent, selected_states: List[str] = None) -> CTFEvent:
        """Apply AI ranking to a single event"""
        scores = {
            'timeliness': self.calculate_timeliness_score(event),
            'popularity': self.calculate_popularity_score(event),
            'prestige': self.calculate_prestige_score(event),
            'accessibility': self.calculate_accessibility_score(event),
            'rewards': self.calculate_rewards_score(event),
            'quality': self.calculate_quality_score(event),
            'local_relevance': self.calculate_local_relevance_score(event, selected_states or [])
        }
        
        # Calculate weighted score
        total_score = sum(scores[k] * self.weights[k] for k in scores)
        
        # Calculate confidence
        confidence = self.calculate_confidence_score(event)
        
        # Update event
        event.ai_score = round(total_score, 2)
        event.ai_confidence = round(confidence, 2)
        event.ai_factors = scores
        
        return event
    
    def rank_events(self, events: List[CTFEvent], selected_states: List[str] = None) -> List[CTFEvent]:
        """Rank multiple events"""
        ranked = [self.rank_event(event, selected_states) for event in events]
        return sorted(ranked, key=lambda x: x.ai_score, reverse=True)

# ==================== CTF SCRAPERS ====================
class BaseScraper:
    """Base class for all CTF scrapers"""
    
    def __init__(self):
        self.name = "Base"
        self.timeout = 30
        self.retry_count = 3
    
    async def scrape(self) -> List[CTFEvent]:
        """Main scrape method - override in subclasses"""
        raise NotImplementedError
    
    async def retry_scrape(self, coro, max_retries: int = 3) -> Any:
        """Retry a scrape operation with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return await coro
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

class CTFtimeAPIScraper(BaseScraper):
    """Scraper for CTFtime API"""
    
    def __init__(self):
        super().__init__()
        self.name = "CTFtime API"
        self.base_url = "https://ctftime.org/api/v1"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        try:
            now_ts = int(datetime.now(timezone.utc).timestamp())
            url = f"{self.base_url}/events/?limit=200&start={now_ts-86400}&finish={now_ts+180*86400}"
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers={
                    "User-Agent": f"{__tool_name__}/{__version__}",
                    "Accept": "application/json"
                })
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
                        event.location = f"📍 {item.get('location', 'TBD')}"
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
                    
                    # Duration
                    event.calculate_duration()
                    
                    events.append(event)
                except Exception as e:
                    continue
                    
        except Exception as e:
            console.print(f"[red]CTFtime API scrape failed: {e}[/red]")
        
        return events

class CTFtimeHTMLScraper(BaseScraper):
    """Scraper for CTFtime website (detailed info)"""
    
    def __init__(self):
        super().__init__()
        self.name = "CTFtime HTML"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto("https://ctftime.org/event/list/upcoming", 
                              timeout=self.timeout * 1000)
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(3000)
                
                # Get all event rows
                rows = await page.query_selector_all('table tbody tr')
                
                for row in rows[:100]:  # Limit to 100 events
                    try:
                        event = CTFEvent()
                        
                        # Title and link
                        title_el = await row.query_selector('td:nth-child(2) a')
                        if title_el:
                            event.title = (await title_el.inner_text()).strip()
                            href = await title_el.get_attribute('href')
                            if href:
                                event.ctftime_url = f"https://ctftime.org{href}"
                        
                        # Date
                        date_el = await row.query_selector('td:nth-child(1)')
                        if date_el:
                            date_text = await date_el.inner_text()
                            # Parse date
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                            if date_match:
                                event.start_date = datetime.fromisoformat(date_match.group(1) + "T00:00:00+00:00")
                        
                        # Location
                        loc_el = await row.query_selector('td:nth-child(4)')
                        if loc_el:
                            loc_text = await loc_el.inner_text()
                            event.location = loc_text.strip()
                            if "online" in loc_text.lower():
                                event.is_online = True
                            else:
                                event.is_offline = True
                        
                        # Format
                        format_el = await row.query_selector('td:nth-child(5)')
                        if format_el:
                            format_text = (await format_el.inner_text()).strip()
                            if "jeopardy" in format_text.lower():
                                event.format_type = CTFFormat.JEOPARDY
                            elif "attack" in format_text.lower():
                                event.format_type = CTFFormat.ATTACK_DEFENSE
                        
                        # Weight
                        weight_el = await row.query_selector('td:nth-child(6)')
                        if weight_el:
                            weight_text = (await weight_el.inner_text()).strip()
                            weight_match = re.search(r'[\d.]+', weight_text)
                            if weight_match:
                                event.weight = float(weight_match.group())
                        
                        # Set end date (default 2 days after start)
                        if event.start_date:
                            event.end_date = event.start_date + timedelta(days=2)
                        
                        event.source = "CTFtime"
                        event.calculate_duration()
                        
                        if event.title:
                            events.append(event)
                            
                    except Exception:
                        continue
                        
            except Exception as e:
                console.print(f"[yellow]CTFtime HTML scrape warning: {e}[/yellow]")
            finally:
                await browser.close()
        
        return events

class CTFHuntScraper(BaseScraper):
    """Scraper for CTF Hunt"""
    
    def __init__(self):
        super().__init__()
        self.name = "CTF Hunt"
        self.base_url = "https://ctfhunt.com/api"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/events", 
                                          headers={"User-Agent": f"{__tool_name__}/{__version__}"})
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
                    
                    # Duration
                    event.calculate_duration()
                    
                    events.append(event)
                except Exception:
                    continue
                    
        except Exception:
            pass  # CTF Hunt may not always be available
        
        return events

class HackTheBoxCTFScraper(BaseScraper):
    """Scraper for HackTheBox CTF events"""
    
    def __init__(self):
        super().__init__()
        self.name = "HackTheBox CTF"
        self.base_url = "https://ctf.hackthebox.com/api"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Get upcoming CTFs
                response = await client.get(f"{self.base_url}/events/upcoming",
                                          headers={"User-Agent": f"{__tool_name__}/{__version__}"})
                data = response.json()
            
            for item in data.get("data", []):
                try:
                    event = CTFEvent()
                    event.title = item.get("name", "HTB CTF")
                    event.source = "HackTheBox"
                    event.source_id = str(item.get("id", ""))
                    
                    # Dates
                    start_str = item.get("start_date", "")
                    end_str = item.get("end_date", "")
                    if start_str:
                        event.start_date = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    if end_str:
                        event.end_date = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    
                    # Location
                    event.is_online = True
                    event.location = "🌐 Online"
                    
                    # Links
                    event.website_url = f"https://ctf.hackthebox.com/event/{item.get('id', '')}"
                    event.registration_url = event.website_url
                    
                    # Description
                    event.description = item.get("description", "")
                    event.short_description = event.description[:200] if event.description else ""
                    
                    # Format
                    event.format_type = CTFFormat.JEOPARDY
                    
                    # Statistics
                    event.participants_count = item.get("participants_count", 0)
                    
                    # Organizer
                    event.organizer_name = "HackTheBox"
                    
                    # Tags
                    event.tags = ["hackthebox", "htb", "cybersecurity"]
                    
                    # Duration
                    event.calculate_duration()
                    
                    # Weight (HTB CTFs are prestigious)
                    event.weight = 50.0
                    
                    events.append(event)
                except Exception:
                    continue
                    
        except Exception:
            pass  # HTB API may not always be available
        
        return events

class TryHackMeCTFScraper(BaseScraper):
    """Scraper for TryHackMe CTF events"""
    
    def __init__(self):
        super().__init__()
        self.name = "TryHackMe CTF"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto("https://tryhackme.com/ctfs", 
                              timeout=self.timeout * 1000)
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(3000)
                
                # Get CTF cards
                cards = await page.query_selector_all('.ctf-card, [class*="ctf"]')
                
                for card in cards[:50]:
                    try:
                        event = CTFEvent()
                        
                        # Title
                        title_el = await card.query_selector('h3, .title, .name')
                        if title_el:
                            event.title = (await title_el.inner_text()).strip()
                        
                        # Link
                        link_el = await card.query_selector('a')
                        if link_el:
                            href = await link_el.get_attribute('href')
                            if href:
                                event.website_url = f"https://tryhackme.com{href}"
                                event.registration_url = event.website_url
                        
                        # Description
                        desc_el = await card.query_selector('p, .description')
                        if desc_el:
                            event.description = (await desc_el.inner_text()).strip()
                            event.short_description = event.description[:200]
                        
                        # Date
                        date_el = await card.query_selector('.date, time, [class*="date"]')
                        if date_el:
                            date_text = (await date_el.inner_text()).strip()
                            # Parse date
                            date_match = re.search(r'(\d{1,2}\s+\w+\s+\d{4})', date_text)
                            if date_match:
                                try:
                                    event.start_date = datetime.strptime(date_match.group(1), "%d %B %Y").replace(tzinfo=timezone.utc)
                                    event.end_date = event.start_date + timedelta(days=3)
                                except:
                                    pass
                        
                        # Set defaults
                        event.source = "TryHackMe"
                        event.is_online = True
                        event.location = "🌐 Online"
                        event.format_type = CTFFormat.JEOPARDY
                        event.organizer_name = "TryHackMe"
                        event.tags = ["tryhackme", "thm", "beginner-friendly"]
                        event.weight = 25.0
                        event.difficulty = DifficultyLevel.BEGINNER
                        event.calculate_duration()
                        
                        if event.title:
                            events.append(event)
                            
                    except Exception:
                        continue
                        
            except Exception as e:
                console.print(f"[yellow]TryHackMe scrape warning: {e}[/yellow]")
            finally:
                await browser.close()
        
        return events

class PicoCTFScraper(BaseScraper):
    """Scraper for PicoCTF events"""
    
    def __init__(self):
        super().__init__()
        self.name = "PicoCTF"
    
    async def scrape(self) -> List[CTFEvent]:
        events = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get("https://picoctf.org/api/events",
                                          headers={"User-Agent": f"{__tool_name__}/{__version__}"})
                data = response.json()
            
            for item in data.get("events", []):
                try:
                    event = CTFEvent()
                    event.title = item.get("title", "PicoCTF")
                    event.source = "PicoCTF"
                    event.source_id = str(item.get("id", ""))
                    
                    # Dates
                    start_str = item.get("start_date", "")
                    end_str = item.get("end_date", "")
                    if start_str:
                        event.start_date = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                    if end_str:
                        event.end_date = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                    
                    # Location
                    event.is_online = True
                    event.location = "🌐 Online"
                    
                    # Links
                    event.website_url = item.get("url", "https://picoctf.org")
                    event.registration_url = item.get("registration_url", "https://picoctf.org")
                    
                    # Description
                    event.description = item.get("description", "")
                    event.short_description = event.description[:200] if event.description else ""
                    
                    # Format
                    event.format_type = CTFFormat.JEOPARDY
                    
                    # Statistics
                    event.participants_count = item.get("participants", 0)
                    
                    # Organizer
                    event.organizer_name = "Carnegie Mellon University"
                    
                    # Tags
                    event.tags = ["picoctf", "education", "beginner-friendly", "k-12"]
                    
                    # Difficulty
                    event.difficulty = DifficultyLevel.BEGINNER
                    
                    # Duration
                    event.calculate_duration()
                    
                    # Weight
                    event.weight = 30.0
                    
                    events.append(event)
                except Exception:
                    continue
                    
        except Exception:
            pass  # PicoCTF API may not always be available
        
        return events

# ==================== CTF INTELLIGENCE ENGINE ====================
class CTFIntelligenceEngine:
    """Advanced CTF data enrichment and intelligence"""
    
    def __init__(self):
        self.known_organizers = {
            "carnegie mellon university": {"country": "USA", "reputation": 90},
            "hackthebox": {"country": "Global", "reputation": 85},
            "tryhackme": {"country": "Global", "reputation": 75},
            "google": {"country": "USA", "reputation": 95},
            "def con": {"country": "USA", "reputation": 100},
            "nullcon": {"country": "India", "reputation": 80},
            "bi0s": {"country": "India", "reputation": 85},
            "infosec iit": {"country": "India", "reputation": 75},
        }
        
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
        }
    
    def enrich_event(self, event: CTFEvent) -> CTFEvent:
        """Enrich event with additional intelligence"""
        
        # Detect Indian states from location
        self._detect_indian_location(event)
        
        # Enrich organizer info
        self._enrich_organizer(event)
        
        # Detect difficulty
        self._detect_difficulty(event)
        
        # Generate tags
        self._generate_tags(event)
        
        # Calculate data quality
        self._calculate_data_quality(event)
        
        # Generate unique ID
        if not event.id:
            event.id = self._generate_id(event)
        
        return event
    
    def _detect_indian_location(self, event: CTFEvent):
        """Detect if event is in India and identify state"""
        location_lower = event.location.lower()
        
        # Check if in India
        if "india" in location_lower or "in" in location_lower:
            event.country = "India"
        
        # Check for Indian cities
        for city, state in self.indian_cities_states.items():
            if city in location_lower:
                event.city = city.title()
                event.state = state
                event.country = "India"
                break
        
        # Check for state names
        for state in INDIAN_STATES:
            if state.lower() in location_lower:
                event.state = state
                event.country = "India"
                break
    
    def _enrich_organizer(self, event: CTFEvent):
        """Enrich organizer information"""
        organizer_lower = event.organizer_name.lower()
        
        for known_org, info in self.known_organizers.items():
            if known_org in organizer_lower:
                if info["country"] != "Global" and event.country == "Global":
                    event.country = info["country"]
                break
    
    def _detect_difficulty(self, event: CTFEvent):
        """Detect CTF difficulty level"""
        title_lower = event.title.lower()
        desc_lower = event.description.lower()
        
        # Beginner indicators
        beginner_keywords = ["beginner", "junior", "intro", "101", "easy", "learning"]
        if any(kw in title_lower or kw in desc_lower for kw in beginner_keywords):
            event.difficulty = DifficultyLevel.BEGINNER
            return
        
        # Expert indicators
        expert_keywords = ["expert", "hard", "advanced", "master", "elite"]
        if any(kw in title_lower or kw in desc_lower for kw in expert_keywords):
            event.difficulty = DifficultyLevel.EXPERT
            return
        
        # Weight-based difficulty
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
        
        # Add format-based tags
        tags.add(event.format_type.value.lower().replace("-", "").replace(" ", ""))
        
        # Add difficulty tag
        tags.add(event.difficulty.value.lower())
        
        # Add location tags
        if event.country:
            tags.add(event.country.lower())
        if event.state:
            tags.add(event.state.lower().replace(" ", ""))
        
        # Add organizer tag
        if event.organizer_name:
            tags.add(event.organizer_name.lower().replace(" ", ""))
        
        # Add online/offline tag
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
    
    def __init__(self):
        self.analytics = CTFAnalytics()
    
    def analyze_events(self, events: List[CTFEvent]) -> CTFAnalytics:
        """Analyze a list of CTF events and generate statistics"""
        analytics = CTFAnalytics()
        analytics.total_events = len(events)
        
        # Count by category
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
            # Format distribution
            format_counts[event.format_type.value] += 1
            
            # Difficulty distribution
            difficulty_counts[event.difficulty.value] += 1
            
            # Source distribution
            source_counts[event.source] += 1
            
            # Country distribution
            if event.country:
                country_counts[event.country] += 1
            
            # State distribution
            if event.state:
                state_counts[event.state] += 1
            
            # Monthly trend
            if event.start_date:
                month_key = event.start_date.strftime("%Y-%m")
                monthly_counts[month_key] += 1
            
            # Organizer counts
            if event.organizer_name:
                organizer_counts[event.organizer_name] += 1
            
            # Tag counts
            for tag in event.tags:
                tag_counts[tag] += 1
            
            # Location type
            if event.is_online:
                analytics.online_events += 1
            if event.is_offline:
                analytics.offline_events += 1
            if event.is_hybrid:
                analytics.hybrid_events += 1
            
            # Averages
            total_weight += event.weight
            total_participants += event.participants_count
            total_prize += event.prize_pool_total
        
        # Calculate averages
        if events:
            analytics.average_weight = round(total_weight / len(events), 2)
            analytics.average_participants = round(total_participants / len(events), 2)
            analytics.total_prize_pool = total_prize
        
        # Distribution dicts
        analytics.format_distribution = dict(format_counts)
        analytics.difficulty_distribution = dict(difficulty_counts)
        analytics.source_distribution = dict(source_counts)
        analytics.country_distribution = dict(country_counts)
        analytics.state_distribution = dict(state_counts)
        analytics.monthly_trend = dict(sorted(monthly_counts.items()))
        
        # Top organizers
        analytics.top_organizers = sorted(organizer_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Top tags
        analytics.top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        self.analytics = analytics
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
        
        # Format Distribution
        format_table = Table(show_header=True, box=box.ROUNDED)
        format_table.add_column("Format", style="bold")
        format_table.add_column("Count", justify="right", style="cyan")
        format_table.add_column("Percentage", justify="right", style="green")
        
        total = sum(analytics.format_distribution.values())
        for fmt, count in sorted(analytics.format_distribution.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            format_table.add_row(fmt, str(count), f"{pct:.1f}%")
        
        console.print(Panel(format_table, title="[bold]Format Distribution[/bold]", border_style="blue"))
        
        # Difficulty Distribution
        diff_table = Table(show_header=True, box=box.ROUNDED)
        diff_table.add_column("Difficulty", style="bold")
        diff_table.add_column("Count", justify="right", style="cyan")
        diff_table.add_column("Percentage", justify="right", style="green")
        
        total = sum(analytics.difficulty_distribution.values())
        for diff, count in sorted(analytics.difficulty_distribution.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            diff_table.add_row(diff, str(count), f"{pct:.1f}%")
        
        console.print(Panel(diff_table, title="[bold]Difficulty Distribution[/bold]", border_style="yellow"))
        
        # Top Organizers
        org_table = Table(show_header=True, box=box.ROUNDED)
        org_table.add_column("Rank", justify="center", style="bold")
        org_table.add_column("Organizer", style="bold")
        org_table.add_column("Events", justify="right", style="cyan")
        
        for i, (org, count) in enumerate(analytics.top_organizers[:5], 1):
            org_table.add_row(str(i), org, str(count))
        
        console.print(Panel(org_table, title="[bold]Top Organizers[/bold]", border_style="magenta"))
        
        # Top Tags
        tag_table = Table(show_header=True, box=box.ROUNDED)
        tag_table.add_column("Rank", justify="center", style="bold")
        tag_table.add_column("Tag", style="bold")
        tag_table.add_column("Count", justify="right", style="cyan")
        
        for i, (tag, count) in enumerate(analytics.top_tags[:10], 1):
            tag_table.add_row(str(i), tag, str(count))
        
        console.print(Panel(tag_table, title="[bold]Top Tags[/bold]", border_style="cyan"))
        
        # Monthly Trend
        if analytics.monthly_trend:
            trend_table = Table(show_header=True, box=box.ROUNDED)
            trend_table.add_column("Month", style="bold")
            trend_table.add_column("Events", justify="right", style="cyan")
            
            for month, count in list(analytics.monthly_trend.items())[-6:]:  # Last 6 months
                trend_table.add_row(month, str(count))
            
            console.print(Panel(trend_table, title="[bold]Monthly Trend (Last 6 Months)[/bold]", border_style="green"))

# ==================== EXPORT ENGINE ====================
class ExportEngine:
    """Export CTF events to various formats"""
    
    @staticmethod
    def export_json(events: List[CTFEvent], filename: str = None) -> str:
        """Export events to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ctfforge_export_{timestamp}.json"
        
        data = [event.to_dict() for event in events]
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename
    
    @staticmethod
    def export_csv(events: List[CTFEvent], filename: str = None) -> str:
        """Export events to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ctfforge_export_{timestamp}.csv"
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                "Title", "Start Date", "End Date", "Duration (hours)",
                "Location", "Country", "State", "City",
                "Format", "Difficulty", "Source",
                "Registration URL", "Website URL",
                "Organizer", "Participants", "Weight",
                "Prize Pool", "Tags", "AI Score", "Status"
            ])
            
            # Data
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
    
    @staticmethod
    def export_markdown(events: List[CTFEvent], filename: str = None) -> str:
        """Export events to Markdown file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ctfforge_export_{timestamp}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# CTF Events Export\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Total Events: {len(events)}\n\n")
            
            for i, event in enumerate(events, 1):
                f.write(f"## {i}. {event.title}\n\n")
                f.write(f"- **Start:** {event.start_date.strftime('%Y-%m-%d %H:%M UTC') if event.start_date else 'N/A'}\n")
                f.write(f"- **End:** {event.end_date.strftime('%Y-%m-%d %H:%M UTC') if event.end_date else 'N/A'}\n")
                f.write(f"- **Duration:** {event.duration_hours:.1f} hours\n")
                f.write(f"- **Location:** {event.location}\n")
                f.write(f"- **Format:** {event.format_type.value}\n")
                f.write(f"- **Difficulty:** {event.difficulty.value}\n")
                f.write(f"- **Organizer:** {event.organizer_name}\n")
                f.write(f"- **Participants:** {event.participants_count}\n")
                f.write(f"- **Weight:** {event.weight}\n")
                f.write(f"- **AI Score:** {event.ai_score}\n")
                f.write(f"- **Status:** {event.get_status().value}\n")
                f.write(f"- **Registration:** {event.registration_url}\n")
                f.write(f"- **Website:** {event.website_url}\n\n")
                
                if event.description:
                    f.write(f"### Description\n\n{event.description[:500]}...\n\n")
                
                if event.tags:
                    f.write(f"**Tags:** {', '.join(event.tags)}\n\n")
                
                f.write("---\n\n")
        
        return filename
    
    @staticmethod
    def export_ics(events: List[CTFEvent], filename: str = None) -> str:
        """Export events to iCalendar file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ctfforge_export_{timestamp}.ics"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("BEGIN:VCALENDAR\n")
            f.write("VERSION:2.0\n")
            f.write("PRODID:-//CTFForge//EN\n")
            
            for event in events:
                if event.start_date and event.end_date:
                    f.write("BEGIN:VEVENT\n")
                    f.write(f"UID:{event.id}@ctfforge\n")
                    f.write(f"DTSTART:{event.start_date.strftime('%Y%m%dT%H%M%SZ')}\n")
                    f.write(f"DTEND:{event.end_date.strftime('%Y%m%dT%H%M%SZ')}\n")
                    f.write(f"SUMMARY:{event.title}\n")
                    f.write(f"DESCRIPTION:{event.short_description}\n")
                    f.write(f"LOCATION:{event.location}\n")
                    f.write(f"URL:{event.registration_url}\n")
                    f.write(f"ORGANIZER;CN={event.organizer_name}:{event.organizer_url or ''}\n")
                    f.write("END:VEVENT\n")
            
            f.write("END:VCALENDAR\n")
        
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
            "3. ⚙️ Configure Settings\n"
            "4. 📖 View Help & Documentation\n"
            "5. 🚪 Exit",
            border_style="cyan",
            title="[bold]Navigation[/bold]"
        )
        console.print(menu)
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3", "4", "5"], default="1")
        return choice
    
    def select_states(self) -> List[str]:
        """Interactive state selection"""
        console.print(Panel.fit(
            "[bold yellow]🌏 Select Indian States for Local CTF Discovery[/bold yellow]",
            border_style="yellow"
        ))
        
        # Group states by region
        regions = defaultdict(list)
        for state, info in INDIAN_STATES.items():
            regions[info["region"]].append(state)
        
        console.print("\n[bold]Available Regions:[/bold]")
        region_list = list(regions.keys())
        for i, region in enumerate(region_list, 1):
            console.print(f"  [cyan]{i}.[/cyan] {region} ({len(regions[region])} states)")
        
        console.print("\n[bold]Options:[/bold]")
        console.print("  [green]all[/green] - Select all states")
        console.print("  [green]region N[/green] - Select all states in a region")
        console.print("  [green]1,2,3[/green] - Select specific states by number")
        
        choice = Prompt.ask("Your selection", default="all")
        
        if choice.lower() == "all":
            return list(INDIAN_STATES.keys())
        
        if choice.lower().startswith("region"):
            try:
                region_idx = int(choice.split()[1]) - 1
                if 0 <= region_idx < len(region_list):
                    return regions[region_list[region_idx]]
            except:
                pass
        
        # Parse individual state numbers
        selected = []
        for num in choice.split(","):
            try:
                idx = int(num.strip()) - 1
                if 0 <= idx < len(INDIAN_STATES):
                    selected.append(list(INDIAN_STATES.keys())[idx])
            except:
                pass
        
        return selected if selected else list(INDIAN_STATES.keys())[:5]
    
    async def scrape_events(self) -> List[CTFEvent]:
        """Scrape events from all sources"""
        console.print("\n[bold cyan]🕸️ Initializing CTF Scraping Network...[/bold cyan]")
        
        scrapers = [
            CTFtimeAPIScraper(),
            CTFtimeHTMLScraper(),
            CTFHuntScraper(),
            HackTheBoxCTFScraper(),
            TryHackMeCTFScraper(),
            PicoCTFScraper()
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
                    console.print(f"  [green]✅ {scraper.name}: {len(events)} events found[/green]")
                except Exception as e:
                    console.print(f"  [red]❌ {scraper.name}: Failed - {str(e)[:50]}[/red]")
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
        
        console.print(f"  [green]✅ Total unique events: {len(unique_events)}[/green]")
        
        return unique_events
    
    def filter_events(self, events: List[CTFEvent]) -> List[CTFEvent]:
        """Apply user filters to events"""
        console.print("\n[bold]🔍 Apply Filters:[/bold]")
        
        # Status filter
        console.print("\n[bold]Status:[/bold]")
        console.print("1. All Events")
        console.print("2. Only Upcoming")
        console.print("3. Only Ongoing")
        console.print("4. Only Completed")
        status_choice = Prompt.ask("Select", choices=["1", "2", "3", "4"], default="1")
        
        # Format filter
        console.print("\n[bold]Format:[/bold]")
        console.print("1. All Formats")
        console.print("2. Jeopardy")
        console.print("3. Attack-Defense")
        console.print("4. Mixed")
        format_choice = Prompt.ask("Select", choices=["1", "2", "3", "4"], default="1")
        
        # Difficulty filter
        console.print("\n[bold]Difficulty:[/bold]")
        console.print("1. All Levels")
        console.print("2. Beginner")
        console.print("3. Intermediate")
        console.print("4. Advanced")
        console.print("5. Expert")
        diff_choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5"], default="1")
        
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
        
        # Status filter
        now = datetime.now(timezone.utc)
        if status_choice == "2":
            filtered = [e for e in filtered if e.start_date and e.start_date > now]
        elif status_choice == "3":
            filtered = [e for e in filtered if e.start_date and e.end_date and e.start_date <= now <= e.end_date]
        elif status_choice == "4":
            filtered = [e for e in filtered if e.end_date and e.end_date < now]
        
        # Format filter
        format_map = {"2": CTFFormat.JEOPARDY, "3": CTFFormat.ATTACK_DEFENSE, "4": CTFFormat.MIXED}
        if format_choice in format_map:
            filtered = [e for e in filtered if e.format_type == format_map[format_choice]]
        
        # Difficulty filter
        diff_map = {"2": DifficultyLevel.BEGINNER, "3": DifficultyLevel.INTERMEDIATE, 
                   "4": DifficultyLevel.ADVANCED, "5": DifficultyLevel.EXPERT}
        if diff_choice in diff_map:
            filtered = [e for e in filtered if e.difficulty == diff_map[diff_choice]]
        
        # Location filter
        if loc_choice == "2":
            filtered = [e for e in filtered if e.is_online]
        elif loc_choice == "3":
            filtered = [e for e in filtered if e.is_offline]
        elif loc_choice == "4":
            filtered = [e for e in filtered if e.country == "India"]
        
        # Weight filter
        weight_map = {"2": 25, "3": 50, "4": 75}
        if weight_choice in weight_map:
            filtered = [e for e in filtered if e.weight >= weight_map[weight_choice]]
        
        # State filter (if states selected)
        if self.selected_states:
            state_filtered = []
            for event in filtered:
                # Include if event is in selected state or is online
                if event.is_online or event.state in self.selected_states:
                    state_filtered.append(event)
            filtered = state_filtered
        
        console.print(f"  [green]✅ After filtering: {len(filtered)} events[/green]")
        
        return filtered
    
    def display_events(self, events: List[CTFEvent]):
        """Display events in a beautiful table"""
        if not events:
            console.print("[bold red]No events found matching your criteria.[/bold red]")
            return
        
        # Create main table
        table = Table(
            title=f"🔐 {len(events)} CTF Events Found",
            show_lines=True,
            box=box.ROUNDED,
            header_style="bold cyan",
            title_style="bold cyan"
        )
        
        table.add_column("Rank", justify="center", style="cyan", width=4)
        table.add_column("CTF Name", style="bold yellow", width=30)
        table.add_column("Dates", style="green", width=20)
        table.add_column("Location", style="magenta", width=15)
        table.add_column("Format", justify="center", width=10)
        table.add_column("Difficulty", justify="center", width=10)
        table.add_column("Weight", justify="center", width=6)
        table.add_column("Score", justify="center", width=6)
        table.add_column("Link", style="blue underline", width=40)
        
        for i, event in enumerate(events[:30], 1):
            # Format dates
            if event.start_date and event.end_date:
                date_str = f"{event.start_date.strftime('%d %b')}→{event.end_date.strftime('%d %b')}"
            else:
                date_str = "TBD"
            
            # Format location with emoji
            location = event.location[:20]
            
            # Format difficulty with color
            diff_colors = {
                DifficultyLevel.BEGINNER: "green",
                DifficultyLevel.INTERMEDIATE: "yellow",
                DifficultyLevel.ADVANCED: "red",
                DifficultyLevel.EXPERT: "bold red"
            }
            diff_str = f"[{diff_colors.get(event.difficulty, 'white')}]{event.difficulty.value[:6]}[/]"
            
            # Format weight with color
            if event.weight > 75:
                weight_str = f"[bold red]{event.weight:.0f}[/]"
            elif event.weight > 50:
                weight_str = f"[yellow]{event.weight:.0f}[/]"
            elif event.weight > 25:
                weight_str = f"[green]{event.weight:.0f}[/]"
            else:
                weight_str = f"[dim]{event.weight:.0f}[/]"
            
            # Format AI score
            score_color = "green" if event.ai_score > 75 else "yellow" if event.ai_score > 50 else "red"
            score_str = f"[{score_color}]{event.ai_score:.0f}[/]"
            
            # Create clickable link
            link_text = Text(event.registration_url[:37] + "..." if len(event.registration_url) > 37 else event.registration_url)
            link_text.stylize(f"link {event.registration_url}")
            
            table.add_row(
                str(i),
                event.title[:35] + ("..." if len(event.title) > 35 else ""),
                date_str,
                location,
                event.format_type.value[:8],
                diff_str,
                weight_str,
                score_str,
                link_text
            )
        
        console.print(table)
        
        # Show summary
        console.print(f"\n[bold cyan]📊 Summary:[/bold cyan]")
        console.print(f"  • Showing top {min(30, len(events))} of {len(events)} events")
        console.print(f"  • Online: {len([e for e in events if e.is_online])} | Offline: {len([e for e in events if e.is_offline])}")
        console.print(f"  • India: {len([e for e in events if e.country == 'India'])} | Global: {len([e for e in events if e.country != 'India'])}")
    
    def display_event_details(self, event: CTFEvent):
        """Display detailed information about a specific event"""
        console.print("\n")
        
        # Main details panel
        details = f"""
[bold yellow]{event.title}[/bold yellow]
[dim]{event.subtitle if event.subtitle else ''}[/dim]

[bold]📅 Schedule:[/bold]
  • Start: {event.start_date.strftime('%A, %B %d, %Y at %H:%M UTC') if event.start_date else 'TBD'}
  • End: {event.end_date.strftime('%A, %B %d, %Y at %H:%M UTC') if event.end_date else 'TBD'}
  • Duration: {event.duration_hours:.1f} hours ({event.duration_hours/24:.1f} days)
  • Status: {event.get_status().value}

[bold]📍 Location:[/bold]
  • Venue: {event.location}
  • Country: {event.country}
  • State: {event.state if event.state else 'N/A'}
  • City: {event.city if event.city else 'N/A'}
  • Type: {"Online" if event.is_online else ""}{" + " if event.is_hybrid else ""}{"Offline" if event.is_offline else ""}

[bold]🎯 CTF Details:[/bold]
  • Format: {event.format_type.value}
  • Difficulty: {event.difficulty.value}
  • Weight: {event.weight}
  • Rating: {event.rating}/5.0
  • Categories: {', '.join(event.categories_available) if event.categories_available else 'N/A'}
  • Challenges: {event.challenges_count if event.challenges_count > 0 else 'N/A'}

[bold]👥 Participants:[/bold]
  • Registered: {event.participants_count}
  • Max Capacity: {event.max_participants if event.max_participants else 'Unlimited'}
  • Team Size: {event.team_size_min}-{event.team_size_max} members

[bold]🏆 Prizes:[/bold]
  • Total Pool: ${event.prize_pool_total:,.2f} {event.prize_currency}
  • 1st Place: ${event.first_place_prize:,.2f}
  • 2nd Place: ${event.second_place_prize:,.2f}
  • 3rd Place: ${event.third_place_prize:,.2f}
  • Swag: {'✅' if event.has_swag else '❌'}
  • Certificates: {'✅' if event.has_certificates else '❌'}
  • Travel Aid: {'✅' if event.has_travel_aid else '❌'}

[bold]🏢 Organizer:[/bold]
  • Name: {event.organizer_name}
  • Website: {event.organizer_url if event.organizer_url else 'N/A'}
  • Email: {event.organizer_email if event.organizer_email else 'N/A'}

[bold]🔗 Links:[/bold]
  • Register: [link={event.registration_url}]{event.registration_url}[/link]
  • Website: [link={event.website_url}]{event.website_url}[/link]
  • CTFtime: [link={event.ctftime_url}]{event.ctftime_url}[/link] if event.ctftime_url else 'N/A'}
  • Discord: {event.discord_url if event.discord_url else 'N/A'}
  • Twitter: {event.twitter_url if event.twitter_url else 'N/A'}

[bold]🏷️ Tags:[/bold]
  {', '.join(f'[cyan]{tag}[/cyan]' for tag in event.tags[:10])}

[bold]📝 Description:[/bold]
{event.description[:500] if event.description else 'No description available'}...

[bold]🤖 AI Analysis:[/bold]
  • Score: {event.ai_score}/100
  • Confidence: {event.ai_confidence}%
  • Data Quality: {event.data_quality_score}%
"""
        
        console.print(Panel.fit(details, border_style="cyan", title="[bold]Event Details[/bold]"))
        
        # Show AI factors
        if event.ai_factors:
            factors_table = Table(show_header=True, box=box.ROUNDED)
            factors_table.add_column("Factor", style="bold")
            factors_table.add_column("Score", justify="right", style="cyan")
            factors_table.add_column("Weight", justify="right", style="green")
            factors_table.add_column("Contribution", justify="right", style="yellow")
            
            for factor, score in event.ai_factors.items():
                weight = self.ai_engine.weights.get(factor, 0)
                contribution = score * weight
                factors_table.add_row(
                    factor.replace("_", " ").title(),
                    f"{score:.1f}",
                    f"{weight:.0%}",
                    f"{contribution:.1f}"
                )
            
            factors_table.add_row(
                "[bold]Total[/bold]",
                "",
                "",
                f"[bold]{event.ai_score:.1f}[/bold]"
            )
            
            console.print(Panel(factors_table, title="[bold]AI Ranking Factors[/bold]", border_style="green"))
    
    async def run(self):
        """Main application loop"""
        self.display_banner()
        
        while True:
            choice = self.display_menu()
            
            if choice == "1":
                # Find CTF Events
                self.selected_states = self.select_states()
                console.print(f"\n[green]Selected {len(self.selected_states)} states[/green]")
                
                # Scrape events
                all_events = await self.scrape_events()
                self.events = all_events
                
                # Filter events
                filtered_events = self.filter_events(all_events)
                
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
                    console.print("3. Markdown (Documentation)")
                    console.print("4. ICS (Calendar)")
                    
                    export_choice = Prompt.ask("Select", choices=["1", "2", "3", "4"], default="1")
                    
                    export_map = {
                        "1": self.export_engine.export_json,
                        "2": self.export_engine.export_csv,
                        "3": self.export_engine.export_markdown,
                        "4": self.export_engine.export_ics
                    }
                    
                    filename = export_map[export_choice](ranked_events)
                    console.print(f"[bold green]✅ Exported to {filename}[/bold green]")
                
                # View details
                if Confirm.ask("\n🔍 View detailed info for a specific event?", default=False):
                    try:
                        idx = IntPrompt.ask("Enter rank number") - 1
                        if 0 <= idx < len(ranked_events):
                            self.display_event_details(ranked_events[idx])
                    except:
                        pass
                
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
                # Settings
                console.print(Panel.fit(
                    "[bold]Settings[/bold]\n\n"
                    "1. AI Ranking Weights\n"
                    "2. Scraper Configuration\n"
                    "3. Export Preferences\n"
                    "4. Back to Main Menu",
                    border_style="cyan",
                    title="[bold]Settings[/bold]"
                ))
                Prompt.ask("Select", choices=["1", "2", "3", "4"], default="4")
            
            elif choice == "4":
                # Help
                console.print(Panel.fit(
                    "[bold]CTFForge Pro Help[/bold]\n\n"
                    "[bold]Quick Start:[/bold]\n"
                    "1. Select 'Find CTF Events'\n"
                    "2. Choose Indian states\n"
                    "3. Wait for scraping\n"
                    "4. Apply filters\n"
                    "5. View AI-ranked results\n\n"
                    "[bold]Features:[/bold]\n"
                    "• Multi-source scraping (6 sources)\n"
                    "• AI-powered ranking\n"
                    "• State-wise filtering\n"
                    "• Multiple export formats\n"
                    "• Analytics dashboard\n"
                    "• Clickable links\n\n"
                    "[bold]Tips:[/bold]\n"
                    "• Use 'all' states for maximum results\n"
                    "• Apply filters to narrow down\n"
                    "• Export to CSV for team sharing\n"
                    "• Check analytics for trends\n\n"
                    "[bold]Sources:[/bold]\n"
                    "• CTFtime API & HTML\n"
                    "• CTF Hunt\n"
                    "• HackTheBox CTF\n"
                    "• TryHackMe CTF\n"
                    "• PicoCTF",
                    border_style="green",
                    title="[bold]Help & Documentation[/bold]"
                ))
                input("\nPress Enter to continue...")
            
            elif choice == "5":
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
        sys.exit(1)
