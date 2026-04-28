"""Single source of truth for tunable constants (T019).

Per FR-038 the canonical thresholds live in web/about.html. This module
parses them at import time. If the about page does not yet publish a
threshold, a documented default is used and preflight surfaces a warning
(but does not fail) — letting the system bootstrap before T130 lands the
authoritative thresholds on the about page.
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

# Defaults documented in spec.md / plan.md / research.md.
DEFAULTS: dict[str, float | int] = {
    "RESEARCH_ACCEPT_THRESHOLD": 5.0,
    "PAPER_ACCEPT_THRESHOLD": 5.0,
    "TASKER_MAX_REVISION_ROUNDS": 5,
    "LEAF_TASK_BUDGET_SECONDS": 300,
    "SANDBOX_BUDGET_SECONDS": 240,
    "CITATION_TITLE_OVERLAP_THRESHOLD": 0.7,
    "STAGE_ADVANCEMENT_RATE_WINDOW_DAYS": 7,
}

# Patterns for parsing the about page. Format expected:
#   <span data-threshold="research_accept_threshold">5.0</span>
# or a markdown table cell with the threshold name. The parser is
# deliberately tolerant: it accepts either form.
_THRESHOLD_RE: re.Pattern[str] = re.compile(
    r"data-threshold=\"(?P<key>[a-z_]+)\"[^>]*>\s*(?P<value>[\d.]+)\s*<",
    re.IGNORECASE,
)


def _about_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "web" / "about.html"


@lru_cache(maxsize=1)
def _parsed() -> dict[str, float]:
    path = _about_path()
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    found: dict[str, float] = {}
    for match in _THRESHOLD_RE.finditer(text):
        try:
            found[match.group("key").upper()] = float(match.group("value"))
        except ValueError:
            continue
    return found


def get(key: str) -> float | int:
    """Return the about-page value, or DEFAULTS[key] if not yet published."""
    parsed = _parsed()
    if key in parsed:
        return parsed[key]
    if key not in DEFAULTS:
        raise KeyError(f"unknown config key: {key}")
    return DEFAULTS[key]


def about_page_published(key: str) -> bool:
    return key.upper() in _parsed()


def all_keys() -> list[str]:
    return list(DEFAULTS.keys())


# Module-level convenience constants (resolved at import time).
RESEARCH_ACCEPT_THRESHOLD: float = float(get("RESEARCH_ACCEPT_THRESHOLD"))
PAPER_ACCEPT_THRESHOLD: float = float(get("PAPER_ACCEPT_THRESHOLD"))
TASKER_MAX_REVISION_ROUNDS: int = int(get("TASKER_MAX_REVISION_ROUNDS"))
LEAF_TASK_BUDGET_SECONDS: int = int(get("LEAF_TASK_BUDGET_SECONDS"))
SANDBOX_BUDGET_SECONDS: int = int(get("SANDBOX_BUDGET_SECONDS"))
CITATION_TITLE_OVERLAP_THRESHOLD: float = float(get("CITATION_TITLE_OVERLAP_THRESHOLD"))
STAGE_ADVANCEMENT_RATE_WINDOW_DAYS: int = int(get("STAGE_ADVANCEMENT_RATE_WINDOW_DAYS"))


__all__ = [
    "RESEARCH_ACCEPT_THRESHOLD",
    "PAPER_ACCEPT_THRESHOLD",
    "TASKER_MAX_REVISION_ROUNDS",
    "LEAF_TASK_BUDGET_SECONDS",
    "SANDBOX_BUDGET_SECONDS",
    "CITATION_TITLE_OVERLAP_THRESHOLD",
    "STAGE_ADVANCEMENT_RATE_WINDOW_DAYS",
    "DEFAULTS",
    "get",
    "about_page_published",
    "all_keys",
]
