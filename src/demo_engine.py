"""Deterministic demo engine.

Produces plausible destinations and itineraries WITHOUT any API key or network
access. This guarantees the app is fully functional for 1-click Streamlit
Community Cloud deployment and offline grading. It also implements real
geographic clustering so Tab 2's "minimize backtracking" promise holds even in
demo mode.
"""
from __future__ import annotations

import random
from typing import Dict, List

from .models import (
    Activity,
    DayPlan,
    Destination,
    Itinerary,
    TripPreferences,
    BUDGET_DAILY_USD,
)
from .prompts import SLOTS

# ---------------------------------------------------------------------------
# Static knowledge base (offline-friendly, no network)
# ---------------------------------------------------------------------------
_CURRENCY = {
    "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 150.0, "INR": 83.0,
    "THB": 36.0, "IDR": 15700.0, "VND": 24500.0, "AED": 3.67, "TRY": 34.0,
}

# vibe -> candidate destinations with metadata and named neighborhoods (clusters)
_DEST_DB: Dict[str, List[dict]] = {
    "Beach": [
        {"name": "Bali", "country": "Indonesia", "ccy": "IDR", "season": "Apr-Oct (dry)",
         "tags": ["Surf", "Temples", "Rice Terraces"],
         "clusters": ["Seminyak Coast", "Ubud Highlands", "Uluwatu Cliffs"]},
        {"name": "Phuket", "country": "Thailand", "ccy": "THB", "season": "Nov-Apr",
         "tags": ["Islands", "Street Food", "Night Markets"],
         "clusters": ["Patong Beach", "Old Town", "Phi Phi Day Trip"]},
        {"name": "Goa", "country": "India", "ccy": "INR", "season": "Nov-Feb",
         "tags": ["Shacks", "Portuguese Heritage", "Flea Markets"],
         "clusters": ["North Goa Beaches", "Panaji Old Quarter", "South Goa Calm"]},
    ],
    "Mountains": [
        {"name": "Interlaken", "country": "Switzerland", "ccy": "EUR", "season": "Jun-Sep",
         "tags": ["Alps", "Paragliding", "Lakes"],
         "clusters": ["Lake Thun Shore", "Jungfrau Region", "Harder Kulm Ridge"]},
        {"name": "Pokhara", "country": "Nepal", "ccy": "INR", "season": "Oct-Nov",
         "tags": ["Himalaya Views", "Lakeside", "Trekking"],
         "clusters": ["Phewa Lakeside", "Sarangkot Viewpoint", "World Peace Hill"]},
        {"name": "Banff", "country": "Canada", "ccy": "USD", "season": "Jun-Aug",
         "tags": ["Glacial Lakes", "Hiking", "Wildlife"],
         "clusters": ["Banff Townsite", "Lake Louise", "Icefields Parkway"]},
    ],
    "Cultural": [
        {"name": "Kyoto", "country": "Japan", "ccy": "JPY", "season": "Mar-May / Oct-Nov",
         "tags": ["Temples", "Tea Ceremony", "Gardens"],
         "clusters": ["Higashiyama District", "Arashiyama", "Gion & Downtown"]},
        {"name": "Istanbul", "country": "Turkey", "ccy": "TRY", "season": "Apr-May / Sep-Oct",
         "tags": ["Bazaars", "Mosques", "Bosphorus"],
         "clusters": ["Sultanahmet", "Beyoglu & Galata", "Bosphorus Shore"]},
        {"name": "Jaipur", "country": "India", "ccy": "INR", "season": "Oct-Mar",
         "tags": ["Forts", "Palaces", "Bazaars"],
         "clusters": ["Old Pink City", "Amer Fort Area", "Civil Lines"]},
    ],
    "Urban": [
        {"name": "Tokyo", "country": "Japan", "ccy": "JPY", "season": "Mar-May / Oct-Nov",
         "tags": ["Neon Nights", "Food Halls", "Tech"],
         "clusters": ["Shibuya & Shinjuku", "Asakusa & Ueno", "Odaiba Bayfront"]},
        {"name": "Dubai", "country": "UAE", "ccy": "AED", "season": "Nov-Mar",
         "tags": ["Skyline", "Luxury", "Desert"],
         "clusters": ["Downtown Dubai", "Marina & JBR", "Old Dubai Creek"]},
        {"name": "London", "country": "United Kingdom", "ccy": "GBP", "season": "May-Sep",
         "tags": ["Museums", "Theatre", "Markets"],
         "clusters": ["Westminster", "South Bank", "Camden & North"]},
    ],
}

# slot -> activity templates keyed loosely by interest for flavor
_SLOT_TEMPLATES = {
    "Morning Sightseeing": [
        ("Guided tour of {cluster}", ["History", "Art"]),
        ("Sunrise walk around {cluster}", ["Nature", "Adventure"]),
        ("Landmark visit in {cluster}", ["History"]),
    ],
    "Lunch Recommendation": [
        ("Local tasting lunch in {cluster}", ["Food"]),
        ("Street-food crawl in {cluster}", ["Food"]),
        ("Cafe lunch with a view in {cluster}", ["Food"]),
    ],
    "Afternoon Leisure": [
        ("Market browsing in {cluster}", ["Shopping"]),
        ("Museum or gallery in {cluster}", ["Art", "History"]),
        ("Outdoor activity near {cluster}", ["Adventure", "Nature"]),
    ],
    "Evening Dining & Entertainment": [
        ("Signature dinner in {cluster}", ["Food"]),
        ("Rooftop bar & nightlife in {cluster}", ["Nightlife"]),
        ("Cultural show in {cluster}", ["Art", "History"]),
    ],
}

# Fraction of the per-day budget allocated to each slot.
_SLOT_COST_WEIGHT = {
    "Morning Sightseeing": 0.25,
    "Lunch Recommendation": 0.15,
    "Afternoon Leisure": 0.25,
    "Evening Dining & Entertainment": 0.35,
}

_PACE_DURATION = {"Relaxed": 2.0, "Moderate": 2.5, "Fast-Paced": 3.0}


def _season_month(start_date: str) -> int:
    try:
        return int(start_date.split("-")[1]) if start_date else 0
    except (IndexError, ValueError):
        return 0


def recommend_destinations(prefs: TripPreferences) -> List[Destination]:
    """Return top 3 destinations for the user's vibe with match scoring."""
    pool = _DEST_DB.get(prefs.vibe, _DEST_DB["Cultural"])
    daily = BUDGET_DAILY_USD.get(prefs.budget_level, 200)
    results: List[Destination] = []

    for entry in pool:
        # Deterministic-ish match score blending budget fit + interest overlap.
        score = 70
        # Budget fit nudges the score.
        est = daily * random.uniform(0.85, 1.15)
        if prefs.budget_level == "Budget" and entry["ccy"] in ("INR", "THB", "IDR", "VND"):
            score += 12
        if prefs.budget_level == "Luxury" and entry["ccy"] in ("EUR", "GBP", "AED", "USD"):
            score += 10
        # Interest/tag overlap.
        overlap = len(set(prefs.interests) & set(
            t for tag in entry["tags"] for t in [tag]
        ))
        score += overlap * 3
        score = max(60, min(99, score))

        results.append(Destination(
            name=entry["name"],
            country=entry["country"],
            match_score=score,
            reason=(
                f"Great {prefs.vibe.lower()} match for a {prefs.budget_level.lower()} "
                f"{prefs.travel_party.lower()} trip; best around {entry['season']}."
            ),
            best_season=entry["season"],
            est_daily_cost_usd=round(est, 2),
            highlight_tags=entry["tags"],
        ))

    results.sort(key=lambda d: d.match_score, reverse=True)
    return results[:3]


def _find_entry(destination: str, vibe: str) -> dict:
    for entries in _DEST_DB.values():
        for e in entries:
            if e["name"].lower() == destination.lower():
                return e
    # Unknown destination: synthesize generic clusters so clustering still works.
    return {
        "name": destination,
        "country": "",
        "ccy": "USD",
        "season": "Year-round",
        "tags": ["City Highlights", "Local Cuisine", "Hidden Gems"],
        "clusters": [
            f"{destination} Historic Center",
            f"{destination} Waterfront",
            f"{destination} Uptown",
        ],
    }


def generate_itinerary(prefs: TripPreferences, destination: str) -> Itinerary:
    """Deterministic day-by-day plan with geographic clustering.

    Clustering strategy: each day is anchored to a single neighborhood cluster
    (rotating through the destination's cluster list). All of that day's
    activities share the cluster, so the traveler stays in one area per day and
    avoids crisscrossing the city.
    """
    entry = _find_entry(destination, prefs.vibe)
    clusters = entry["clusters"]
    ccy = entry["ccy"]
    per_usd = _CURRENCY.get(ccy, 1.0)
    daily_budget = BUDGET_DAILY_USD.get(prefs.budget_level, 200)
    dur = _PACE_DURATION.get(prefs.pace, 2.5)

    days: List[DayPlan] = []
    for i in range(1, prefs.duration_days + 1):
        cluster = clusters[(i - 1) % len(clusters)]
        activities: List[Activity] = []
        for slot in SLOTS:
            templates = _SLOT_TEMPLATES[slot]
            # Prefer a template whose tags intersect the user's interests.
            chosen = None
            for title_tmpl, tags in templates:
                if set(tags) & set(prefs.interests):
                    chosen = (title_tmpl, tags)
                    break
            if chosen is None:
                chosen = templates[(i - 1) % len(templates)]
            title_tmpl, tags = chosen
            cost = round(daily_budget * _SLOT_COST_WEIGHT[slot], 2)
            activities.append(Activity(
                slot=slot,
                title=title_tmpl.format(cluster=cluster),
                description=(
                    f"A {prefs.pace.lower()}-paced {slot.lower()} experience tailored "
                    f"to {prefs.travel_party.lower()} travelers in {cluster}."
                ),
                location=cluster,
                cluster=cluster,
                cost_usd=cost,
                duration_hrs=dur,
                tags=tags,
            ))
        days.append(DayPlan(
            day_number=i,
            title=f"Day {i}: Exploring {cluster}",
            cluster=cluster,
            activities=activities,
        ))

    return Itinerary(
        destination=destination,
        preferences=prefs,
        days=days,
        local_currency=ccy,
        local_per_usd=per_usd,
        notes=(
            "Demo itinerary generated offline. Each day stays within one "
            "neighborhood cluster to minimize transit and backtracking."
        ),
    )


def swap_day(prefs: TripPreferences, itinerary: Itinerary, day_number: int, instruction: str) -> DayPlan:
    """Regenerate a single day in demo mode, honoring a free-text instruction."""
    entry = _find_entry(itinerary.destination, prefs.vibe)
    clusters = entry["clusters"]
    cluster = clusters[(day_number - 1) % len(clusters)]
    daily_budget = BUDGET_DAILY_USD.get(prefs.budget_level, 200)
    dur = _PACE_DURATION.get(prefs.pace, 2.5)
    instr = instruction.lower()

    def apply_instruction(slot: str, base_title: str) -> str:
        if "veg" in instr and slot == "Lunch Recommendation":
            return f"Vegetarian-friendly lunch in {cluster}"
        if ("market" in instr or "outdoor" in instr) and slot in (
            "Afternoon Leisure", "Morning Sightseeing"
        ):
            return f"Open-air market & stroll in {cluster}"
        if "museum" in instr and "swap" in instr and slot == "Afternoon Leisure":
            return f"Scenic outdoor walk in {cluster}"
        if "night" in instr and slot == "Evening Dining & Entertainment":
            return f"Live music & nightlife in {cluster}"
        if "budget" in instr or "cheap" in instr:
            return f"Budget-friendly {slot.lower()} in {cluster}"
        return base_title

    activities: List[Activity] = []
    for slot in SLOTS:
        base = f"Revised {slot.lower()} in {cluster}"
        title = apply_instruction(slot, base)
        cost = round(daily_budget * _SLOT_COST_WEIGHT[slot], 2)
        if "budget" in instr or "cheap" in instr:
            cost = round(cost * 0.7, 2)
        activities.append(Activity(
            slot=slot,
            title=title,
            description=f"Updated per request: \"{instruction}\".",
            location=cluster,
            cluster=cluster,
            cost_usd=cost,
            duration_hrs=dur,
            tags=["Custom"],
        ))

    return DayPlan(
        day_number=day_number,
        title=f"Day {day_number}: {cluster} (revised)",
        cluster=cluster,
        activities=activities,
    )
