"""Tab 2 — Day-by-Day Optimized Itinerary Generator."""
from __future__ import annotations

import streamlit as st

from .. import planner, state
from ..models import USD_TO_INR


def _render_day(day, local_ccy: str, local_per_usd: float, running_usd: float) -> float:
    st.markdown(
        f"#### {day.title or f'Day {day.day_number}'}  "
        f"<span class='wl-cluster-chip'>📍 {day.cluster}</span>",
        unsafe_allow_html=True,
    )
    for a in day.activities:
        local_cost = a.cost_usd * local_per_usd
        st.markdown(
            f"""
            <div class="wl-slot">
              <div class="slot-name">{a.slot}</div>
              <div class="slot-title">{a.title}</div>
              <div class="slot-meta">📍 {a.location} &nbsp;·&nbsp; ⏱ {a.duration_hrs:g}h
                 &nbsp;·&nbsp; 💵 ${a.cost_usd:,.0f} USD
                 &nbsp;·&nbsp; ₹{a.cost_usd * USD_TO_INR:,.0f}
                 &nbsp;·&nbsp; {local_cost:,.0f} {local_ccy}</div>
              <div class="slot-meta" style="margin-top:.2rem;">{a.description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    running_usd += day.day_cost_usd
    c1, c2, c3 = st.columns(3)
    c1.metric("Day total (USD)", f"${day.day_cost_usd:,.0f}")
    c2.metric("Running total (USD)", f"${running_usd:,.0f}")
    c3.metric("Running total (INR)", f"₹{running_usd * USD_TO_INR:,.0f}")
    st.divider()
    return running_usd


def render() -> None:
    st.subheader("🗓️ Day-by-Day Optimized Itinerary")
    prefs = state.get_prefs()

    top = st.columns([2, 1])
    with top[0]:
        dest_input = st.text_input(
            "Destination to plan",
            value=prefs.destination,
            placeholder="e.g. Kyoto (or pick one from the Recommender tab)",
        )
    with top[1]:
        st.write("")
        st.write("")
        generate = st.button("🧭 Generate itinerary", use_container_width=True)

    if generate:
        dest = dest_input.strip()
        if not dest:
            st.error("Enter a destination, or use the Recommender tab first.")
        else:
            prefs.destination = dest
            state.set_prefs(prefs)
            with st.spinner(f"Optimizing your {dest} itinerary with geographic clustering..."):
                itin, status = planner.generate_itinerary(
                    prefs, dest, st.session_state.get("provider")
                )
            state.set_itinerary(itin, status)

    itin = state.get_itinerary()
    if itin is None:
        st.info("Generate an itinerary to see the optimized day-by-day plan.")
        return

    if st.session_state.get("itin_status"):
        st.caption(f"ℹ️ {st.session_state['itin_status']}")

    # Budget headline
    st.markdown("### 💰 Budget Tracker")
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Total (USD)", f"${itin.total_cost_usd:,.0f}")
    b2.metric("Total (INR)", f"₹{itin.total_cost_inr:,.0f}")
    b3.metric(f"Total ({itin.local_currency})", f"{itin.total_cost_local:,.0f}")
    b4.metric("Per day avg", f"${itin.total_cost_usd / max(1, len(itin.days)):,.0f}")

    st.caption(
        "🧠 Clustering: each day is anchored to one neighborhood to minimize "
        "transit fatigue and avoid backtracking across the city."
    )
    st.divider()

    running = 0.0
    for day in itin.days:
        running = _render_day(day, itin.local_currency, itin.local_per_usd, running)
