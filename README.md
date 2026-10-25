# ✈️ Personalized Travel Itinerary Planner

*Skill Wallet Capstone Project 4*

A production-ready **Streamlit** application that recommends destinations, builds
geographically optimized day-by-day itineraries, lets you customize any single
day on the fly, and exports a beautiful **offline PDF** travel guide — with
**zero external database** and a **1-click deploy** on Streamlit Community Cloud.

It works fully **offline in Demo Mode** (deterministic engine) and can also use a
live **Google Gemini** or **Groq** API key for AI-generated plans. If a live call
ever fails, it transparently falls back to the demo engine so the app never breaks.

---

## ✨ Features

### Sidebar — Configuration & Preferences (Epic 3)
- Secure API key entry (Gemini **or** Groq), password-masked, session-only (never written to disk).
- **Demo mode** toggle — no key required.
- Comprehensive preference form: destination *or* open-ended vibe (Beach / Mountains /
  Cultural / Urban), trip duration, travel dates, budget level, travel party, pace, and interests.

### Tab 1 — Smart Destination Recommender (Epic 3)
- Top 3 matching cities with **match score**, best season, estimated daily cost, and
  highlight tags — based on budget, weather season, and travel mood.
- One click to turn any recommendation into a full itinerary.

### Tab 2 — Day-by-Day Optimized Itinerary Generator (Epic 4)
- Four sequential slots per day: **Morning Sightseeing → Lunch Recommendation →
  Afternoon Leisure → Evening Dining & Entertainment**.
- **Geographic clustering**: each day is anchored to a single neighborhood so you
  don't crisscross the city — minimizing transit fatigue and backtracking.
- Itemized per-activity cost and a **running cumulative budget tracker** in
  **USD / INR / local currency**.

### Tab 3 — Vibe Customization & Dynamic Activity Swap (Epic 4)
- Modify a specific day (e.g. *"Swap museum for outdoor market"*, *"Find a vegetarian
  lunch spot"*) and **regenerate just that day** — the rest of the plan stays intact.

### Tab 4 — Trip Management & Offline PDF Export (Epic 5)
- **Simulated persistence** (session-based) with a trip history viewer.
- **1-click PDF export** — a clean, branded itinerary guide with a cover page,
  day-by-day plan, budget summary, and an **emergency contact checklist**.
- JSON backup / restore so you can keep trips across sessions without any database.

---

## 🧱 Architecture

```
app.py                      Streamlit entry point (wires sidebar + 4 tabs)
requirements.txt
.streamlit/config.toml      Wanderlust theme + headless server config
src/
  models.py                 Dataclasses (TripPreferences, Activity, DayPlan, Itinerary, ...)
  llm_provider.py           Gemini/Groq wrapper, robust JSON extraction, LLMError
  prompts.py                Prompt builders + the 4 time slots
  demo_engine.py            Deterministic offline engine (recommend / generate / swap)
  planner.py                Orchestrates LLM -> demo fallback (returns result + status)
  state.py                  Session state + simulated persistence (JSON export/import)
  pdf_export.py             Offline PDF generation via fpdf2 (returns bytes)
  styles.py                 Modern wanderlust-inspired CSS
  ui/
    sidebar.py              API config + preference form
    tab_recommend.py        Tab 1
    tab_itinerary.py        Tab 2
    tab_customize.py        Tab 3
    tab_manage.py           Tab 4
```

Design principles: modular packages, dependency-free data models (clean JSON
serialization), exception handling at every LLM boundary with graceful demo
fallback, and no on-disk state (session + optional JSON download).

---

## 🚀 Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the URL Streamlit prints (default http://localhost:8501).

### Demo mode vs live mode
- **Demo mode** (default): fully offline, no key needed.
- **Live mode**: in the sidebar, turn off demo mode, choose Gemini or Groq, paste a
  key, and click **Connect**.

---

## ☁️ Deploy on Streamlit Community Cloud

1. Push this repo to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io), create a new app pointing to
   `app.py`.
3. Deploy — no secrets or database required (demo mode works out of the box).
4. (Optional) Add a Gemini/Groq key at runtime via the sidebar, or configure it in
   the app's **Secrets** if you prefer.

---

## 🔐 Notes on keys & data
- API keys are entered at runtime, kept **in session memory only**, and never
  persisted to disk.
- There is **no external database**. Saved trips live in the Streamlit session;
  use the JSON backup/restore in Tab 4 to carry them between sessions.
- Currency figures are approximations for planning (static, offline) and do not
  make any network calls.

---

## 🛠️ Tech stack
- [Streamlit](https://streamlit.io/) — UI
- [fpdf2](https://py-pdf.github.io/fpdf2/) — PDF generation
- [google-generativeai](https://pypi.org/project/google-generativeai/) — Gemini (optional)
- [groq](https://pypi.org/project/groq/) — Groq (optional)
