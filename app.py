"""Personalized Travel Itinerary Planner — Streamlit entry point.

Skill Wallet Capstone Project 4.

Run locally:
    streamlit run app.py

Modular design: all logic lives in the `src` package.
  - src/models.py        data models
  - src/llm_provider.py  Gemini/Groq wrapper
  - src/prompts.py       prompt builders
  - src/demo_engine.py   offline deterministic engine
  - src/planner.py       LLM<->demo orchestration
  - src/state.py         session state + simulated persistence
  - src/pdf_export.py    offline PDF generation
  - src/styles.py        wanderlust CSS
  - src/ui/*             sidebar + 4 tabs
"""
from __future__ import annotations

import streamlit as st

from src import state
from src.styles import inject_css, hero
from src.ui import sidebar, tab_recommend, tab_itinerary, tab_customize, tab_manage


def main() -> None:
    st.set_page_config(
        page_title="Personalized Travel Itinerary Planner",
        page_icon="✈️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_css()
    state.init_state()

    hero(
        "✈️ Personalized Travel Itinerary Planner",
        "Discover destinations, build geographically optimized day-by-day plans, "
        "customize on the fly, and export a beautiful offline PDF guide.",
    )

    sidebar.render_sidebar()

    tabs = st.tabs([
        "🌍 Destination Recommender",
        "🗓️ Itinerary Generator",
        "🎨 Customize & Swap",
        "🧳 Manage & Export",
    ])

    with tabs[0]:
        tab_recommend.render()
    with tabs[1]:
        tab_itinerary.render()
    with tabs[2]:
        tab_customize.render()
    with tabs[3]:
        tab_manage.render()


if __name__ == "__main__":
    main()
