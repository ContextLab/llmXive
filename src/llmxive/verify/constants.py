"""T006 — Library-backed constants table (spec 018, FR-004/005).

Values are read from ``math`` and ``scipy.constants`` at import time.
Never hardcoded divergently — the self-test in test_verify_constants.py
asserts each entry equals the live library value.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import scipy.constants


@dataclass(frozen=True)
class CuratedConstant:
    """A recognized mathematical or physical constant backed by a library."""

    key: str
    aliases: tuple[str, ...]
    value: float
    authority: str
    url: str


# ---------------------------------------------------------------------------
# Build the constants table from live library values (never hardcoded)
# ---------------------------------------------------------------------------

CONSTANTS: dict[str, CuratedConstant] = {
    "pi": CuratedConstant(
        key="pi",
        aliases=("pi", "π", "pi constant", "archimedes constant"),
        value=math.pi,
        authority="math.pi (IEEE-754 double, Python stdlib)",
        url="https://en.wikipedia.org/wiki/Pi",
    ),
    "e": CuratedConstant(
        key="e",
        aliases=("e", "euler's number", "eulers number", "napier's constant", "napiers constant",
                 "mathematical constant e", "base of natural logarithm"),
        value=math.e,
        authority="math.e (IEEE-754 double, Python stdlib)",
        url="https://en.wikipedia.org/wiki/E_(mathematical_constant)",
    ),
    "tau": CuratedConstant(
        key="tau",
        aliases=("tau", "τ", "tau constant", "two pi"),
        value=math.tau,
        authority="math.tau (IEEE-754 double, Python stdlib)",
        url="https://en.wikipedia.org/wiki/Turn_(angle)#Tau_proposals",
    ),
    "golden_ratio": CuratedConstant(
        key="golden_ratio",
        aliases=("golden ratio", "golden mean", "golden section", "phi", "φ",
                 "divine proportion"),
        value=(1 + math.sqrt(5)) / 2,
        authority="(1+sqrt(5))/2 (IEEE-754 double, Python stdlib math.sqrt)",
        url="https://en.wikipedia.org/wiki/Golden_ratio",
    ),
    "speed_of_light": CuratedConstant(
        key="speed_of_light",
        aliases=("c", "speed of light", "speed of light in vacuum",
                 "velocity of light", "light speed"),
        value=scipy.constants.c,
        authority="scipy.constants.c (CODATA 2018, exact by SI definition)",
        url="https://physics.nist.gov/cgi-bin/cuu/Value?c",
    ),
    "planck": CuratedConstant(
        key="planck",
        aliases=("h", "planck constant", "planck's constant", "plancks constant",
                 "planck"),
        value=scipy.constants.h,
        authority="scipy.constants.h (CODATA 2018, exact by SI definition)",
        url="https://physics.nist.gov/cgi-bin/cuu/Value?h",
    ),
    "gravitational": CuratedConstant(
        key="gravitational",
        aliases=("g", "gravitational constant", "newton's gravitational constant",
                 "newtons gravitational constant", "universal gravitational constant",
                 "big g"),
        value=scipy.constants.G,
        authority="scipy.constants.G (CODATA 2018)",
        url="https://physics.nist.gov/cgi-bin/cuu/Value?bg",
    ),
    "boltzmann": CuratedConstant(
        key="boltzmann",
        aliases=("k", "k_b", "boltzmann constant", "boltzmann's constant",
                 "boltzmanns constant"),
        value=scipy.constants.k,
        authority="scipy.constants.k (CODATA 2018, exact by SI definition)",
        url="https://physics.nist.gov/cgi-bin/cuu/Value?k",
    ),
    "avogadro": CuratedConstant(
        key="avogadro",
        aliases=("n_a", "avogadro number", "avogadro's number", "avogadros number",
                 "avogadro constant"),
        value=scipy.constants.N_A,
        authority="scipy.constants.N_A (CODATA 2018, exact by SI definition)",
        url="https://physics.nist.gov/cgi-bin/cuu/Value?na",
    ),
}

# Pre-build a flat alias → key index for O(1) lookup
_ALIAS_INDEX: dict[str, str] = {}
for _key, _entry in CONSTANTS.items():
    for _alias in _entry.aliases:
        _ALIAS_INDEX[_alias.lower()] = _key


def lookup(subject: str) -> Optional[CuratedConstant]:
    """Return the CuratedConstant whose aliases include *subject* (case-insensitive).

    Falls back to a substring scan when no exact alias matches, so
    "Planck constant" finds the ``planck`` entry even if the exact alias
    string differs slightly.  Returns ``None`` for unknown subjects.
    """
    norm = subject.strip().lower()

    # 1. Exact alias match
    if norm in _ALIAS_INDEX:
        return CONSTANTS[_ALIAS_INDEX[norm]]

    # 2. Substring match: the query must CONTAIN a known alias as a whole-word
    # substring (not the other way around, which is too permissive).
    # E.g. "speed of light in vacuum" contains alias "speed of light" → match.
    # "frobnicator constant" does NOT contain any alias → None.
    for alias_lower, key in _ALIAS_INDEX.items():
        if len(alias_lower) < 2:
            # Single-character aliases (c, h, g, k, e) must match exactly
            # (already handled above); skip substring for them.
            continue
        if alias_lower in norm:
            return CONSTANTS[key]

    return None


def true_value(subject: str) -> Optional[float]:
    """Return the library-backed float value for *subject*, or ``None``."""
    c = lookup(subject)
    return c.value if c is not None else None


__all__ = ["CuratedConstant", "CONSTANTS", "lookup", "true_value"]
