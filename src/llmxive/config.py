"""Single source of truth for tunable constants (T019).

Per FR-038 the canonical thresholds live in web/about.html. This module
parses them at import time. If the about page does not yet publish a
threshold, a documented default is used and preflight surfaces a warning
(but does not fail) — letting the system bootstrap before T130 lands the
authoritative thresholds on the about page.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path


def repo_root() -> Path:
    """Resolve the llmXive repository root.

    Honors the ``LLMXIVE_REPO_ROOT`` environment variable when set and
    non-empty (returning ``Path(env).resolve()``); otherwise falls back to
    the installed repo root computed from this module's own fixed location
    (``src/llmxive/config.py`` → ``parent.parent.parent``).

    The env override lets hermetic tests / alternate checkouts redirect all
    DATA lookups (schemas, prompts, registry, projects, state, constitution,
    inspections, run-log) to a synthetic root, while the CODE still runs from
    the installed package. Because this is computed from a fixed location it
    is depth-independent — callers never need to count ``.parent`` climbs.
    """
    env = os.environ.get("LLMXIVE_REPO_ROOT")
    if env:
        return Path(env).resolve()
    return Path(__file__).resolve().parent.parent.parent

# Defaults documented in spec.md / plan.md / research.md.
DEFAULTS: dict[str, float | int] = {
    "TASKER_MAX_REVISION_ROUNDS": 5,
    "LEAF_TASK_BUDGET_SECONDS": 300,
    "SANDBOX_BUDGET_SECONDS": 240,
    "CITATION_TITLE_OVERLAP_THRESHOLD": 0.7,
    "STAGE_ADVANCEMENT_RATE_WINDOW_DAYS": 7,
    # Spec 015: convergence engine per-step round cap + per-round wall-clock budget.
    "CONVERGENCE_MAX_ROUNDS": 3,
    "CONVERGENCE_PER_ROUND_BUDGET_SECONDS": 600,
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
    return repo_root() / "web" / "about.html"


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
TASKER_MAX_REVISION_ROUNDS: int = int(get("TASKER_MAX_REVISION_ROUNDS"))
LEAF_TASK_BUDGET_SECONDS: int = int(get("LEAF_TASK_BUDGET_SECONDS"))
SANDBOX_BUDGET_SECONDS: int = int(get("SANDBOX_BUDGET_SECONDS"))
CITATION_TITLE_OVERLAP_THRESHOLD: float = float(get("CITATION_TITLE_OVERLAP_THRESHOLD"))
STAGE_ADVANCEMENT_RATE_WINDOW_DAYS: int = int(get("STAGE_ADVANCEMENT_RATE_WINDOW_DAYS"))
CONVERGENCE_MAX_ROUNDS: int = int(get("CONVERGENCE_MAX_ROUNDS"))
CONVERGENCE_PER_ROUND_BUDGET_SECONDS: int = int(get("CONVERGENCE_PER_ROUND_BUDGET_SECONDS"))


def unpaywall_email() -> str | None:
    """Contact email for the Unpaywall API (tier-2 OA discovery).

    Defaults to the project mailbox. Returns None when explicitly set blank,
    which disables the Unpaywall retrieval tier (Semantic Scholar OA still runs).
    """
    if "UNPAYWALL_EMAIL" in os.environ:
        return os.environ["UNPAYWALL_EMAIL"] or None
    return "llmxive@gmail.com"


def grounding_cache_dir(root: Path | None = None) -> Path:
    """Directory for the full-text + verdict caches (transient, uncommitted)."""
    r = root if root is not None else repo_root()
    return r / "state" / "grounding-cache"


__all__ = [
    "CITATION_TITLE_OVERLAP_THRESHOLD",
    "CONVERGENCE_MAX_ROUNDS",
    "CONVERGENCE_PER_ROUND_BUDGET_SECONDS",
    "DEFAULTS",
    "LEAF_TASK_BUDGET_SECONDS",
    "SANDBOX_BUDGET_SECONDS",
    "STAGE_ADVANCEMENT_RATE_WINDOW_DAYS",
    "TASKER_MAX_REVISION_ROUNDS",
    "about_page_published",
    "all_keys",
    "get",
    "grounding_cache_dir",
    "repo_root",
    "unpaywall_email",
]
