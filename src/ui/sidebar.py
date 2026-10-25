"""Sidebar: API configuration + trip preference form."""
from __future__ import annotations

from datetime import date

import streamlit as st

from .. import state
from ..config import detect_provider_key
from ..llm_provider import LLMProvider, LLMError, validate_key
from ..models import (
    TripPreferences,
    VIBES,
    BUDGET_LEVELS,
    TRAVEL_PARTIES,
    PACES,
    INTERESTS,
)


def _auto_connect_from_env() -> None:
    """Once per session, try to connect using a key from secrets/env/.env.

    Keeps the key in session memory only; never displays or logs the value.
    """
    if st.session_state.get("_auto_connect_tried"):
        return
    st.session_state["_auto_connect_tried"] = True

    provider_name, api_key = detect_provider_key()
    if not provider_name or not api_key:
        return
    try:
        st.session_state["provider"] = LLMProvider(provider_name, api_key)
        st.session_state["provider_label"] = f"Live: {provider_name.title()} (from .env)"
        st.session_state["demo_mode"] = False
    except LLMError:
        # Fall back silently to demo mode; the UI still lets the user paste a key.
        st.session_state["provider"] = None
        st.session_state["provider_label"] = "Demo Mode"



def _configure_provider() -> None:
    st.markdown("### 🔑 API Configuration")
    demo = st.toggle(
        "Demo mode (no API key needed)",
        value=st.session_state.get("demo_mode", True),
        help="Runs fully offline with a deterministic planning engine. "
             "Turn off to use a live Gemini or Groq key.",
    )
    st.session_state["demo_mode"] = demo

    if demo:
        st.session_state["provider"] = None
        st.session_state["provider_label"] = "Demo Mode"
        st.success("Demo mode active — no key required.")
        return

    provider_name = st.selectbox("Provider", ["Gemini", "Groq"], index=0)
    api_key = st.text_input(
        f"{provider_name} API key",
        type="password",
        placeholder="Paste your key here",
        help="Your key stays in this session only; it is never stored on disk.",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        connect = st.button("Connect", use_container_width=True)
    with col_b:
        disconnect = st.button("Disconnect", use_container_width=True)

    if disconnect:
        st.session_state["provider"] = None
        st.session_state["provider_label"] = "Demo Mode"
        st.session_state["demo_mode"] = True
        st.info("Disconnected. Back to demo mode.")
        return

    if connect:
        if not api_key.strip():
            st.error("Please enter an API key or enable demo mode.")
            return
        ok, msg = validate_key(provider_name.lower(), api_key)
        if ok:
            try:
                st.session_state["provider"] = LLMProvider(provider_name.lower(), api_key)
                st.session_state["provider_label"] = f"Live: {provider_name}"
                st.success(msg)
            except LLMError as exc:
                st.session_state["provider"] = None
                st.session_state["provider_label"] = "Demo Mode"
                st.error(f"Could not connect: {exc}")
        else:
            st.session_state["provider"] = None
            st.error(msg)

    # Status line
    label = st.session_state.get("provider_label", "Demo Mode")
    if st.session_state.get("provider") is not None:
        st.success(f"Connected — {label}")
    else:
        st.warning("Not connected — using demo engine as fallback.")


def _preference_form() -> None:
    st.markdown("### 🧭 Trip Preferences")
    prefs = state.get_prefs()

    with st.form("prefs_form"):
        destination = st.text_input(
            "Destination (optional)",
            value=prefs.destination,
            placeholder="Leave blank to get recommendations",
            help="If empty, use Tab 1 to discover destinations by vibe.",
        )
        vibe = st.selectbox(
            "Or pick a vibe", VIBES,
            index=VIBES.index(prefs.vibe) if prefs.vibe in VIBES else 0,
        )
        duration = st.slider("Trip duration (days)", 1, 14, prefs.duration_days)

        # Travel dates
        try:
            default_start = date.fromisoformat(prefs.start_date) if prefs.start_date else date.today()
        except ValueError:
            default_start = date.today()
        start = st.date_input("Travel start date", value=default_start)

        budget = st.select_slider(
            "Budget level", BUDGET_LEVELS,
            value=prefs.budget_level if prefs.budget_level in BUDGET_LEVELS else "Moderate",
        )
        party = st.selectbox(
            "Travel party", TRAVEL_PARTIES,
            index=TRAVEL_PARTIES.index(prefs.travel_party) if prefs.travel_party in TRAVEL_PARTIES else 1,
        )
        pace = st.radio(
            "Pace", PACES,
            index=PACES.index(prefs.pace) if prefs.pace in PACES else 1,
            horizontal=True,
        )
        interests = st.multiselect(
            "Interests", INTERESTS,
            default=[i for i in prefs.interests if i in INTERESTS] or ["Food", "History"],
        )

        submitted = st.form_submit_button("Save preferences", use_container_width=True)

    if submitted:
        new_prefs = TripPreferences(
            destination=destination.strip(),
            vibe=vibe,
            duration_days=int(duration),
            start_date=start.isoformat() if start else "",
            budget_level=budget,
            travel_party=party,
            pace=pace,
            interests=interests or ["Food"],
        )
        state.set_prefs(new_prefs)
        st.success("Preferences saved!")


def render_sidebar() -> None:
    _auto_connect_from_env()
    with st.sidebar:
        st.markdown("## ✈️ Planner Setup")
        _configure_provider()
        st.divider()
        _preference_form()
        st.divider()
        st.caption(state.get_prefs().summary())
