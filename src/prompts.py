"""Prompt builders for LLM calls.

Each builder returns (system_prompt, user_prompt) and specifies a strict JSON
schema so responses parse reliably in llm_provider._extract_json.
"""
from __future__ import annotations

from typing import Tuple

from .models import TripPreferences, Itinerary

SLOTS = [
    "Morning Sightseeing",
    "Lunch Recommendation",
    "Afternoon Leisure",
    "Evening Dining & Entertainment",
]


def destination_prompt(prefs: TripPreferences) -> Tuple[str, str]:
    system = (
        "You are an expert travel advisor. Recommend destinations that match a "
        "traveler's vibe, budget, season and interests. Respond with STRICT JSON only."
    )
    schema = (
        '{"destinations":[{"name":str,"country":str,"match_score":int(0-100),'
        '"reason":str,"best_season":str,"est_daily_cost_usd":number,'
        '"highlight_tags":[str,str,str]}]}'
    )
    user = (
        f"Traveler profile:\n"
        f"- Vibe: {prefs.vibe}\n"
        f"- Trip duration: {prefs.duration_days} days\n"
        f"- Start date: {prefs.start_date or 'flexible'}\n"
        f"- Budget level: {prefs.budget_level}\n"
        f"- Travel party: {prefs.travel_party}\n"
        f"- Pace: {prefs.pace}\n"
        f"- Interests: {', '.join(prefs.interests) or 'general'}\n\n"
        f"Recommend EXACTLY the top 3 best-matching cities. Consider budget fit, "
        f"the weather/season for the start date, and how well the mood matches. "
        f"Give 3 short highlight tags per city.\n"
        f"Return JSON matching this schema: {schema}"
    )
    return system, user


def itinerary_prompt(prefs: TripPreferences, destination: str) -> Tuple[str, str]:
    system = (
        "You are a meticulous trip planner specializing in geographic optimization. "
        "You cluster nearby attractions on the same day to minimize transit fatigue "
        "and avoid backtracking. Respond with STRICT JSON only."
    )
    schema = (
        '{"destination":str,"local_currency":str,"local_per_usd":number,"notes":str,'
        '"days":[{"day_number":int,"title":str,"cluster":str,'
        '"activities":[{"slot":str,"title":str,"description":str,"location":str,'
        '"cluster":str,"cost_usd":number,"duration_hrs":number,"tags":[str]}]}]}'
    )
    user = (
        f"Plan a {prefs.duration_days}-day itinerary for {destination}.\n"
        f"Traveler profile:\n"
        f"- Budget level: {prefs.budget_level}\n"
        f"- Travel party: {prefs.travel_party}\n"
        f"- Pace: {prefs.pace}\n"
        f"- Interests: {', '.join(prefs.interests) or 'general'}\n"
        f"- Start date: {prefs.start_date or 'flexible'}\n\n"
        f"Rules:\n"
        f"1. Each day MUST have these 4 sequential slots in order: "
        f"{', '.join(SLOTS)}.\n"
        f"2. GEOGRAPHIC CLUSTERING: group attractions that are physically near each "
        f"other into the same day; give each day a 'cluster' (neighborhood/area) so "
        f"the traveler does not crisscross the city. Set each activity's 'cluster' to "
        f"match its day.\n"
        f"3. Provide realistic per-activity cost_usd appropriate to the budget level.\n"
        f"4. Use the destination's real local currency code and its approx units per 1 USD.\n"
        f"Return JSON matching this schema: {schema}"
    )
    return system, user


def swap_prompt(prefs: TripPreferences, itinerary: Itinerary, day_number: int, instruction: str) -> Tuple[str, str]:
    system = (
        "You are a trip editor. You revise a SINGLE day of an itinerary based on a "
        "user instruction while keeping the same 4 sequential slots and preserving "
        "geographic clustering. Respond with STRICT JSON only."
    )
    day = next((d for d in itinerary.days if d.day_number == day_number), None)
    current = ""
    if day:
        for a in day.activities:
            current += f"  - {a.slot}: {a.title} ({a.location}) ${a.cost_usd}\n"
    schema = (
        '{"day_number":int,"title":str,"cluster":str,'
        '"activities":[{"slot":str,"title":str,"description":str,"location":str,'
        '"cluster":str,"cost_usd":number,"duration_hrs":number,"tags":[str]}]}'
    )
    user = (
        f"Destination: {itinerary.destination}\n"
        f"Budget level: {prefs.budget_level}, Party: {prefs.travel_party}, "
        f"Pace: {prefs.pace}, Interests: {', '.join(prefs.interests)}\n\n"
        f"Current Day {day_number} plan:\n{current}\n"
        f"User instruction: \"{instruction}\"\n\n"
        f"Revise ONLY this day. Keep the same 4 slots in order "
        f"({', '.join(SLOTS)}), keep the cluster coherent, honor the instruction, "
        f"and provide realistic costs.\n"
        f"Return JSON matching this schema: {schema}"
    )
    return system, user
