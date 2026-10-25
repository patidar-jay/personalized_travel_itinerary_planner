"""Tab 1 — Smart Destination Recommender."""
from __future__ import annotations

import streamlit as st

from .. import planner, state
from ..models import USD_TO_INR


def _dest_card(dest, col) -> None:
    with col:
        tags = "".join(f'<span class="wl-tag">{t}</span>' for t in dest.highlight_tags)
        st.markdown(
            f"""
            <div class="wl-card">
              <span class="wl-dest-score">{dest.match_score}% match</span>
              <h3>{dest.name}{f", {dest.country}" if dest.country else ""}</h3>
              <p style="color:#6e6e6e;margin:.2rem 0;">{dest.reason}</p>
              <p style="margin:.2rem 0;"><b>Best season:</b> {dest.best_season}</p>
              <p style="margin:.2rem 0;"><b>Est. daily cost:</b> ${dest.est_daily_cost_usd:,.0f}
                 (≈ ₹{dest.est_daily_cost_usd * USD_TO_INR:,.0f})</p>
              <div style="margin-top:.4rem;">{tags}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Plan {dest.name} →", key=f"plan_{dest.name}", use_container_width=True):
            prefs = state.get_prefs()
            prefs.destination = dest.name
            state.set_prefs(prefs)
            with st.spinner(f"Building your {dest.name} itinerary..."):
                itin, status = planner.generate_itinerary(
                    prefs, dest.name, st.session_state.get("provider")
                )
            state.set_itinerary(itin, status)
            st.success(f"Itinerary ready for {dest.name}! Open the Itinerary tab.")


def render() -> None:
    st.subheader("🌍 Smart Destination Recommender")
    st.write(
        "No fixed destination? Get the top 3 cities matched to your vibe, budget, "
        "season and interests."
    )
    prefs = state.get_prefs()

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("✨ Recommend destinations", use_container_width=True):
            with st.spinner("Matching destinations to your profile..."):
                recs, status = planner.recommend_destinations(
                    prefs, st.session_state.get("provider")
                )
            st.session_state["recommendations"] = recs
            st.session_state["rec_status"] = status
    with col2:
        if st.session_state.get("rec_status"):
            st.caption(f"ℹ️ {st.session_state['rec_status']}")

    recs = st.session_state.get("recommendations", [])
    if not recs:
        st.info("Set your preferences in the sidebar, then click **Recommend destinations**.")
        return

    cols = st.columns(len(recs))
    for dest, col in zip(recs, cols):
        _dest_card(dest, col)
