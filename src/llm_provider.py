"""LLM provider abstraction.

Supports Google Gemini and Groq, with graceful degradation. All network/SDK
imports are lazy so the app boots even when optional packages are missing or
no API key is supplied (demo mode). Every public method returns parsed JSON
(dict/list) or raises LLMError, which callers handle by falling back to the
deterministic demo engine.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

GEMINI_MODEL = "gemini-1.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"


class LLMError(Exception):
    """Raised when the LLM call or response parsing fails."""


def _extract_json(text: str) -> Any:
    """Best-effort extraction of a JSON object/array from raw model text.

    Handles ```json fences, leading prose, and trailing commentary that
    chat models sometimes emit around structured output.
    """
    if not text or not text.strip():
        raise LLMError("Empty response from model.")

    cleaned = text.strip()

    # Strip markdown code fences if present.
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()

    # Direct parse first.
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fall back to locating the outermost JSON structure.
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = cleaned.find(open_ch)
        end = cleaned.rfind(close_ch)
        if start != -1 and end != -1 and end > start:
            candidate = cleaned[start : end + 1]
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    raise LLMError("Could not parse JSON from model response.")


class LLMProvider:
    """Thin wrapper over Gemini/Groq SDKs returning structured JSON."""

    def __init__(self, provider: str, api_key: str):
        self.provider = (provider or "").lower().strip()
        self.api_key = (api_key or "").strip()
        self._client = None

        if self.provider not in ("gemini", "groq"):
            raise LLMError(f"Unsupported provider: {provider!r}")
        if not self.api_key:
            raise LLMError("API key is required for live mode.")

        self._init_client()

    def _init_client(self) -> None:
        try:
            if self.provider == "gemini":
                import google.generativeai as genai  # lazy import

                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(GEMINI_MODEL)
            else:  # groq
                from groq import Groq  # lazy import

                self._client = Groq(api_key=self.api_key)
        except ImportError as exc:
            raise LLMError(
                f"The SDK for {self.provider} is not installed: {exc}"
            ) from exc
        except Exception as exc:  # noqa: BLE001 - surface any init failure uniformly
            raise LLMError(f"Failed to initialize {self.provider} client: {exc}") from exc

    # ------------------------------------------------------------------
    # Low-level completion
    # ------------------------------------------------------------------
    def _complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            if self.provider == "gemini":
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                resp = self._client.generate_content(full_prompt)
                return getattr(resp, "text", "") or ""
            else:  # groq
                resp = self._client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    response_format={"type": "json_object"},
                )
                return resp.choices[0].message.content or ""
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"{self.provider} request failed: {exc}") from exc

    # ------------------------------------------------------------------
    # High-level JSON helpers
    # ------------------------------------------------------------------
    def generate_json(self, system_prompt: str, user_prompt: str) -> Any:
        raw = self._complete(system_prompt, user_prompt)
        return _extract_json(raw)


def validate_key(provider: str, api_key: str) -> tuple[bool, str]:
    """Lightweight validation that attempts to instantiate the client.

    Returns (ok, message). Does not make a billed completion request.
    """
    try:
        LLMProvider(provider, api_key)
        return True, f"{provider.title()} client initialized successfully."
    except LLMError as exc:
        return False, str(exc)
