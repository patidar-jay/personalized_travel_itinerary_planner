"""Modern wanderlust-inspired CSS injected into the Streamlit app."""
from __future__ import annotations

import streamlit as st

_CSS = """
<style>
/* ---------- Palette ---------- */
:root {
  --wl-orange: #FF6B35;
  --wl-orange-2: #FF9154;
  --wl-teal: #1B998B;
  --wl-dark: #2B2118;
  --wl-sand: #FFF3E6;
}

/* ---------- App background ---------- */
.stApp {
  background:
    radial-gradient(1200px 500px at 10% -10%, #FFE8D6 0%, rgba(255,255,255,0) 60%),
    radial-gradient(900px 400px at 100% 0%, #DFF6F2 0%, rgba(255,255,255,0) 55%),
    #FFFDF9;
}

/* ---------- Hero banner ---------- */
.wl-hero {
  background: linear-gradient(120deg, var(--wl-orange) 0%, var(--wl-orange-2) 55%, #FFB37A 100%);
  color: #fff;
  padding: 1.6rem 1.8rem;
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(255,107,53,0.28);
  margin-bottom: 1.2rem;
}
.wl-hero h1 { margin: 0; font-size: 2.0rem; font-weight: 800; letter-spacing: -0.5px; }
.wl-hero p  { margin: 0.35rem 0 0; opacity: 0.95; font-size: 1.02rem; }

/* ---------- Cards ---------- */
.wl-card {
  background: #fff;
  border: 1px solid #F0E3D4;
  border-radius: 16px;
  padding: 1.1rem 1.25rem;
  box-shadow: 0 6px 18px rgba(43,33,24,0.06);
  margin-bottom: 1rem;
}
.wl-card h3 { margin-top: 0; color: var(--wl-dark); }

.wl-dest-score {
  display:inline-block; background: var(--wl-teal); color:#fff;
  padding: 2px 12px; border-radius: 999px; font-weight:700; font-size:0.85rem;
}

/* ---------- Tags ---------- */
.wl-tag {
  display:inline-block; background: var(--wl-sand); color: var(--wl-orange);
  border:1px solid #FFD9BF; padding: 3px 10px; border-radius:999px;
  font-size:0.78rem; font-weight:600; margin: 2px 4px 2px 0;
}

/* ---------- Slot rows ---------- */
.wl-slot {
  border-left: 4px solid var(--wl-orange);
  background: #fff; border-radius: 10px;
  padding: 0.6rem 0.9rem; margin: 0.4rem 0;
  box-shadow: 0 3px 10px rgba(43,33,24,0.05);
}
.wl-slot .slot-name { color: var(--wl-teal); font-weight:700; font-size:0.82rem; text-transform:uppercase; letter-spacing:0.5px;}
.wl-slot .slot-title { font-weight:700; color: var(--wl-dark); font-size:1.02rem; }
.wl-slot .slot-meta  { color:#8a7a6a; font-size:0.85rem; }

.wl-cluster-chip {
  display:inline-block; background:#E8F6F4; color:var(--wl-teal);
  border:1px solid #BFE6E0; padding:2px 10px; border-radius:999px;
  font-size:0.78rem; font-weight:700;
}

/* ---------- Buttons ---------- */
.stButton>button, .stDownloadButton>button {
  background: linear-gradient(120deg, var(--wl-orange), var(--wl-orange-2));
  color:#fff; border:none; border-radius:12px; font-weight:700;
  padding: 0.55rem 1.1rem; transition: transform .08s ease, box-shadow .15s ease;
  box-shadow: 0 6px 16px rgba(255,107,53,0.25);
}
.stButton>button:hover, .stDownloadButton>button:hover {
  transform: translateY(-1px); box-shadow: 0 10px 22px rgba(255,107,53,0.35); color:#fff;
}

/* ---------- Tabs ---------- */
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] {
  background:#fff; border:1px solid #F0E3D4; border-radius:12px 12px 0 0;
  padding: 8px 16px; font-weight:600;
}
.stTabs [aria-selected="true"] {
  background: var(--wl-orange); color:#fff !important; border-color: var(--wl-orange);
}

/* ---------- Metric cards ---------- */
div[data-testid="stMetric"] {
  background:#fff; border:1px solid #F0E3D4; border-radius:14px; padding:0.6rem 0.9rem;
  box-shadow: 0 4px 12px rgba(43,33,24,0.05);
}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="wl-hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )
