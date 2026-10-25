"""Core data models for the travel itinerary planner.

These dataclasses are intentionally dependency-free (standard library only)
so they serialize cleanly to/from JSON for the simulated persistence layer
and remain easy to render in Streamlit and the PDF exporter.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid


# ---------------------------------------------------------------------------
# Enumerated option sets (single source of truth for UI + prompts)
# ---------------------------------------------------------------------------
VIBES = ["Beach", "Mountains", "Cultural", "Urban"]
BUDGET_LEVELS = ["Budget", "Moderate", "Luxury"]
TRAVEL_PARTIES = ["Solo", "Couple", "Family", "Friends"]
PACES = ["Relaxed", "Moderate", "Fast-Paced"]
INTERESTS = ["Food", "Adventure", "History", "Nightlife", "Nature", "Shopping", "Art", "Wellness"]

# Approximate per-person daily budget bands in USD, used for demo estimates
# and for grounding the LLM cost expectations.
BUDGET_DAILY_USD = {
    "Budget": 80,
    "Moderate": 200,
    "Luxury": 500,
}

# Rough USD -> INR conversion used for the dual-currency tracker. This is a
# static approximation; no network calls are made (offline-friendly).
USD_TO_INR = 83.0


@dataclass
class TripPreferences:
    """Everything the user tells us about the trip they want."""

    destination: str = ""              # empty => use destination recommender
    vibe: str = "Cultural"
    duration_days: int = 5
    start_date: str = ""               # ISO date string (yyyy-mm-dd)
    budget_level: str = "Moderate"
    travel_party: str = "Couple"
    pace: str = "Moderate"
    interests: List[str] = field(default_factory=lambda: ["Food", "History"])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TripPreferences":
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)

    def summary(self) -> str:
        where = self.destination.strip() or f"{self.vibe} getaway"
        return (
            f"{self.duration_days}-day {self.pace.lower()} {where} for a "
            f"{self.travel_party.lower()} party on a {self.budget_level.lower()} budget"
        )


@dataclass
class Activity:
    """A single time-slot activity inside a day plan."""

    slot: str                          # e.g. "Morning Sightseeing"
    title: str
    description: str = ""
    location: str = ""                 # named area/cluster for grouping
    cluster: str = ""                  # geographic cluster label
    cost_usd: float = 0.0
    duration_hrs: float = 2.0
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Activity":
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)


@dataclass
class DayPlan:
    """A full day's worth of sequential activities within a cluster."""

    day_number: int
    title: str = ""
    cluster: str = ""                  # dominant geographic cluster for the day
    activities: List[Activity] = field(default_factory=list)

    @property
    def day_cost_usd(self) -> float:
        return round(sum(a.cost_usd for a in self.activities), 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "day_number": self.day_number,
            "title": self.title,
            "cluster": self.cluster,
            "activities": [a.to_dict() for a in self.activities],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DayPlan":
        return cls(
            day_number=data.get("day_number", 1),
            title=data.get("title", ""),
            cluster=data.get("cluster", ""),
            activities=[Activity.from_dict(a) for a in data.get("activities", [])],
        )


@dataclass
class Itinerary:
    """The complete multi-day plan for a destination."""

    destination: str
    preferences: TripPreferences
    days: List[DayPlan] = field(default_factory=list)
    local_currency: str = "USD"
    local_per_usd: float = 1.0         # 1 USD = local_per_usd local units
    notes: str = ""

    @property
    def total_cost_usd(self) -> float:
        return round(sum(d.day_cost_usd for d in self.days), 2)

    @property
    def total_cost_inr(self) -> float:
        return round(self.total_cost_usd * USD_TO_INR, 2)

    @property
    def total_cost_local(self) -> float:
        return round(self.total_cost_usd * self.local_per_usd, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "destination": self.destination,
            "preferences": self.preferences.to_dict(),
            "days": [d.to_dict() for d in self.days],
            "local_currency": self.local_currency,
            "local_per_usd": self.local_per_usd,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Itinerary":
        return cls(
            destination=data.get("destination", ""),
            preferences=TripPreferences.from_dict(data.get("preferences", {})),
            days=[DayPlan.from_dict(d) for d in data.get("days", [])],
            local_currency=data.get("local_currency", "USD"),
            local_per_usd=data.get("local_per_usd", 1.0),
            notes=data.get("notes", ""),
        )


@dataclass
class Destination:
    """A recommended destination card from Tab 1."""

    name: str
    country: str = ""
    match_score: int = 0               # 0-100
    reason: str = ""
    best_season: str = ""
    est_daily_cost_usd: float = 0.0
    highlight_tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Destination":
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)


@dataclass
class SavedTrip:
    """A persisted trip record for the Trip Management tab."""

    name: str
    itinerary: Itinerary
    trip_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    saved_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trip_id": self.trip_id,
            "name": self.name,
            "saved_at": self.saved_at,
            "itinerary": self.itinerary.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SavedTrip":
        return cls(
            trip_id=data.get("trip_id", uuid.uuid4().hex[:8]),
            name=data.get("name", "Untitled Trip"),
            saved_at=data.get("saved_at", datetime.now().isoformat(timespec="seconds")),
            itinerary=Itinerary.from_dict(data.get("itinerary", {})),
        )
