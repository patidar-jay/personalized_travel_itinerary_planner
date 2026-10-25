"""Lightweight secrets loader.

Reads an optional API key/provider from (in priority order):
  1. Streamlit secrets (st.secrets) — for Community Cloud
  2. Environment variables
  3. A local .env file in the project root (gitignored)

No third-party dependency: a tiny .env parser is included so the app stays
deploy-friendly. Secrets are only ever held in memory; nothing is written back.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Tuple

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _parse_env_file(path: Path) -> dict:
    data: dict = {}
    if not path.exists():
        return data
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            data[key] = value
            # Export to the process environment (without clobbering values that
            # are already set), so modules reading os.environ (e.g. model
            # overrides) pick them up.
            os.environ.setdefault(key, value)
    except OSError:
        pass
    return data


def _from_streamlit_secrets(key: str) -> Optional[str]:
    try:
        import streamlit as st  # local import; may not have secrets configured

        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:  # noqa: BLE001 - no secrets file / not in streamlit context
        pass
    return None


def detect_provider_key() -> Tuple[Optional[str], Optional[str]]:
    """Return (provider, api_key) discovered from secrets/env/.env, or (None, None).

    Provider is normalized to 'groq' or 'gemini'. A Groq key is preferred if
    both are present unless LLM_PROVIDER says otherwise.
    """
    env_file = _parse_env_file(_ENV_PATH)

    def lookup(name: str) -> Optional[str]:
        return (
            _from_streamlit_secrets(name)
            or os.environ.get(name)
            or env_file.get(name)
        )

    provider = (lookup("LLM_PROVIDER") or "").lower().strip() or None
    groq_key = lookup("GROQ_API_KEY")
    gemini_key = lookup("GEMINI_API_KEY") or lookup("GOOGLE_API_KEY")

    if provider == "groq" and groq_key:
        return "groq", groq_key
    if provider == "gemini" and gemini_key:
        return "gemini", gemini_key

    # No explicit provider: prefer whichever key exists.
    if groq_key:
        return "groq", groq_key
    if gemini_key:
        return "gemini", gemini_key
    return None, None
