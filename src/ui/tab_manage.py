"""Tab 4 — Trip Management & Offline PDF Export."""
from __future__ import annotations

import streamlit as st

from .. import state
from ..pdf_export import build_itinerary_pdf


def _save_section() -> None:
    st.markdown("### 💾 Save current trip")
    itin = state.get_itinerary()
    if itin is None:
        st.info("Generate an itinerary first to save it.")
        return

    col1, col2 = st.columns([2, 1])
    with col1:
        name = st.text_input(
            "Trip name",
            value=f"{itin.destination} ({itin.preferences.duration_days}d)",
        )
    with col2:
        st.write("")
        st.write("")
        if st.button("Save trip", use_container_width=True):
            trip = state.save_trip(name, itin)
            st.success(f"Saved '{trip.name}' (ID {trip.trip_id}).")


def _history_section() -> None:
    st.markdown("### 🧳 Trip history")
    trips = state.get_saved_trips()
    if not trips:
        st.info("No saved trips yet. Save a trip above to build your history.")
        return

    for trip in reversed(trips):
        itin = trip.itinerary
        with st.expander(f"📌 {trip.name}  ·  {itin.destination}  ·  saved {trip.saved_at}"):
            c1, c2, c3 = st.columns(3)
            c1.metric("Days", len(itin.days))
            c2.metric("Total USD", f"${itin.total_cost_usd:,.0f}")
            c3.metric("Total INR", f"₹{itin.total_cost_inr:,.0f}")

            st.caption("Clusters: " + ", ".join(d.cluster for d in itin.days))

            btns = st.columns(3)
            with btns[0]:
                try:
                    pdf_bytes = build_itinerary_pdf(itin, trip.name)
                    st.download_button(
                        "⬇️ Export PDF",
                        data=pdf_bytes,
                        file_name=f"{trip.name.replace(' ', '_')}_itinerary.pdf",
                        mime="application/pdf",
                        key=f"pdf_{trip.trip_id}",
                        use_container_width=True,
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"PDF generation failed: {exc}")
            with btns[1]:
                if st.button("📂 Load into planner", key=f"load_{trip.trip_id}",
                             use_container_width=True):
                    state.set_prefs(itin.preferences)
                    state.set_itinerary(itin, "Loaded from trip history.")
                    st.success(f"Loaded '{trip.name}' into the planner.")
            with btns[2]:
                if st.button("🗑️ Delete", key=f"del_{trip.trip_id}",
                             use_container_width=True):
                    state.delete_trip(trip.trip_id)
                    st.rerun()


def _current_pdf_section() -> None:
    st.markdown("### 🖨️ Quick export (current itinerary)")
    itin = state.get_itinerary()
    if itin is None:
        st.info("No active itinerary to export.")
        return
    try:
        pdf_bytes = build_itinerary_pdf(itin)
        st.download_button(
            "⬇️ Download current itinerary PDF",
            data=pdf_bytes,
            file_name=f"{itin.destination.replace(' ', '_') or 'trip'}_itinerary.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"PDF generation failed: {exc}")


def _backup_section() -> None:
    st.markdown("### 🔐 Backup & restore (JSON)")
    st.caption(
        "No external database — trips live in your session. Download a JSON backup "
        "to keep them, or upload to restore."
    )
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Download trips JSON",
            data=state.export_trips_json(),
            file_name="saved_trips.json",
            mime="application/json",
            use_container_width=True,
        )
    with col2:
        uploaded = st.file_uploader("Restore from JSON", type=["json"], label_visibility="collapsed")
        if uploaded is not None:
            try:
                count = state.import_trips_json(uploaded.read().decode("utf-8"))
                st.success(f"Imported {count} trip(s).")
            except ValueError as exc:
                st.error(str(exc))


def render() -> None:
    st.subheader("🧳 Trip Management & PDF Export")
    _save_section()
    st.divider()
    _current_pdf_section()
    st.divider()
    _history_section()
    st.divider()
    _backup_section()
