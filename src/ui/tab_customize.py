"""Tab 3 — Vibe Customization & Dynamic Activity Swap."""
from __future__ import annotations

import streamlit as st

from .. import planner, state

_QUICK = [
    "Swap museum for outdoor market",
    "Find a vegetarian lunch spot",
    "Make the evening more nightlife-focused",
    "Keep it budget-friendly / cheaper",
    "Add more adventure activities",
]


def render() -> None:
    st.subheader("🎨 Vibe Customization & Activity Swap")
    itin = state.get_itinerary()
    prefs = state.get_prefs()

    if itin is None or not itin.days:
        st.info("Generate an itinerary in the Itinerary tab first, then fine-tune it here.")
        return

    st.write(
        "Tweak a single day without wiping the rest of your plan. Describe what you "
        "want changed and regenerate just that day."
    )

    day_numbers = [d.day_number for d in itin.days]
    col1, col2 = st.columns([1, 2])
    with col1:
        day_number = st.selectbox("Day to customize", day_numbers, format_func=lambda n: f"Day {n}")
    with col2:
        quick = st.selectbox("Quick instruction (optional)", ["(custom)"] + _QUICK)

    default_instr = "" if quick == "(custom)" else quick
    instruction = st.text_input(
        "Customization instruction",
        value=default_instr,
        placeholder='e.g. "Swap the museum for an outdoor market and find a vegetarian lunch"',
    )

    # Preview current day
    day = next((d for d in itin.days if d.day_number == day_number), None)
    if day:
        with st.expander(f"Current Day {day_number} — {day.cluster}", expanded=True):
            for a in day.activities:
                st.markdown(f"- **{a.slot}:** {a.title}  · ${a.cost_usd:,.0f}")

    if st.button("🔄 Regenerate this day", use_container_width=True):
        if not instruction.strip():
            st.error("Describe the change you want (or pick a quick instruction).")
            return
        with st.spinner(f"Revising Day {day_number}..."):
            new_day, status = planner.swap_day(
                prefs, itin, day_number, instruction, st.session_state.get("provider")
            )
        # Replace only the targeted day; keep the rest intact.
        itin.days = [new_day if d.day_number == day_number else d for d in itin.days]
        state.set_itinerary(itin, status)
        st.success(f"Day {day_number} updated! {status}")

        st.markdown(f"#### ✨ Revised Day {day_number} — {new_day.cluster}")
        for a in new_day.activities:
            st.markdown(
                f"<div class='wl-slot'><div class='slot-name'>{a.slot}</div>"
                f"<div class='slot-title'>{a.title}</div>"
                f"<div class='slot-meta'>💵 ${a.cost_usd:,.0f} USD · {a.description}</div></div>",
                unsafe_allow_html=True,
            )
