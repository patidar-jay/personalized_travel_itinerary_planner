"""Session state & simulated persistence.

All persistence lives in st.session_state (plus an optional JSON download/upload
for the user), so there is ZERO external database dependency. This is what makes
the app a clean 1-click deploy on Streamlit Community Cloud.
"""
from __future__ import annotations

import json
from typing import List, Optional

import streamlit as st

from .models import Itinerary, SavedTrip, TripPreferences


def init_state() -> None:
    """Idempotently seed all session keys the app relies on."""
    defaults = {
        "preferences": TripPreferences(),
        "provider": None,            # LLMProvider | None
        "provider_label": "Demo Mode",
        "demo_mode": True,
        "recommendations": [],       # List[Destination]
        "rec_status": "",
        "itinerary": None,           # Itinerary | None
        "itin_status": "",
        "saved_trips": [],           # List[SavedTrip]
        "last_pdf": None,            # bytes | None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------
def get_prefs() -> TripPreferences:
    return st.session_state["preferences"]


def set_prefs(prefs: TripPreferences) -> None:
    st.session_state["preferences"] = prefs


# ---------------------------------------------------------------------------
# Itinerary
# ---------------------------------------------------------------------------
def set_itinerary(itin: Optional[Itinerary], status: str = "") -> None:
    st.session_state["itinerary"] = itin
    st.session_state["itin_status"] = status


def get_itinerary() -> Optional[Itinerary]:
    return st.session_state.get("itinerary")


# ---------------------------------------------------------------------------
# Saved trips (simulated DB)
# ---------------------------------------------------------------------------
def save_trip(name: str, itinerary: Itinerary) -> SavedTrip:
    trip = SavedTrip(name=name or itinerary.destination or "Untitled Trip",
                     itinerary=itinerary)
    st.session_state["saved_trips"].append(trip)
    return trip


def get_saved_trips() -> List[SavedTrip]:
    return st.session_state.get("saved_trips", [])


def delete_trip(trip_id: str) -> None:
    st.session_state["saved_trips"] = [
        t for t in st.session_state.get("saved_trips", []) if t.trip_id != trip_id
    ]


def export_trips_json() -> str:
    data = [t.to_dict() for t in get_saved_trips()]
    return json.dumps(data, indent=2, ensure_ascii=False)


def import_trips_json(raw: str) -> int:
    """Load trips from a previously exported JSON blob. Returns count imported."""
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(f"Invalid trips JSON: {exc}") from exc
    imported = [SavedTrip.from_dict(item) for item in data]
    existing_ids = {t.trip_id for t in get_saved_trips()}
    added = 0
    for trip in imported:
        if trip.trip_id not in existing_ids:
            st.session_state["saved_trips"].append(trip)
            added += 1
    return added
