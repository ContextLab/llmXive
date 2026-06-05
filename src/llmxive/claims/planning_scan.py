"""Spec 020 — deterministic empirical-value strip for planning documents.

The LLM extractor (``extract_claims``) raises planning recall but cannot GUARANTEE
that every low-level empirical value is detected — it is non-deterministic, so a
given run may miss some. This module is the deterministic GUARANTEE: it removes the
high-confidence empirical patterns spec 020 defers out of planning docs, regardless
of the LLM's recall, while being conservative enough never to touch STRUCTURAL
numbers.

STRIPPED (high-confidence empirical specifics):
  - comma-grouped counts/magnitudes:  27,635   1,701,936   2,000
  - percentages:                      95%   ≥10%   0.5%
  - timed/measured quantities:        15 minutes   60s   1s   2 hours   30 ms

PRESERVED (structural / qualifier — never matched):
  - scope bounds & indices:           ≤13 crossings   Phase 1   crossing number 13
  - ranges:                           1-10
  - versions / dotted:                1.0.0
  - dates:                            2026-05-29
  - hashes / identifiers:             SHA-256   ds002800
  - bare decimals (thresholds):       0.7   (ambiguous — left to the LLM pass)

It runs as the FINAL pass of the planning claim layer, AFTER the LLM strip/smooth,
so the LLM handles prose quality on what it detected and this guarantees nothing
empirical survives. Idempotent: once the tokens are gone, re-running is a no-op.
PURE / deterministic — no IO, no LLM.
"""

from __future__ import annotations

import re

# A comma-grouped number requires at least one ``,ddd`` group, so a bare index/year
# (13, 1976) and a sentence comma after a number ("number 13, the …") never match.
_COMMA_NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?"
_PERCENT = r"\d+(?:\.\d+)?\s*%"
# Explicit time/size units allow a space; the bare "s" form must be attached
# (``60s``) so "13 strands" / "5 servers" are never matched.
_TIMED = (
    r"\d+(?:\.\d+)?\s*"
    r"(?:milliseconds?|ms|seconds?|secs?|minutes?|mins?|hours?|hrs?|days?)\b"
    r"|\d+s\b"
)

# The empirical token, NOT preceded by a word char / slash / dot / hyphen — so a
# number inside an identifier or hyphenated/dotted token (SHA-256, 1.0.0, ds-002)
# is never picked up.
_EMPIRICAL_TOKEN = re.compile(
    rf"(?<![\w/.\-])(?:{_COMMA_NUM}|{_PERCENT}|{_TIMED})",
    re.IGNORECASE,
)

# A leading comparison operator (≥ ~ < …) or approximator word to absorb together
# with the value, so "≥95%" / "within 15 minutes" / "~27,635" leave clean prose.
_LEAD = re.compile(
    r"(?:[~≈≥≤<>±]\s*|"
    r"\b(?:approximately|about|roughly|around|nearly|exactly|over|under|"
    r"up\s+to|at\s+least|at\s+most|within|a\s+total\s+of|some)\s+)$",
    re.IGNORECASE,
)


def has_empirical_value(text: str) -> bool:
    """True iff ``text`` contains a high-confidence empirical value (count/%/time)."""
    return _EMPIRICAL_TOKEN.search(text) is not None


def _tidy(line: str) -> str:
    line = re.sub(r"[ \t]{2,}", " ", line)
    line = re.sub(r"\(\s*\)", "", line)        # empty parens left by removal
    line = re.sub(r"\(\s+", "(", line)
    line = re.sub(r"\s+([.,;:)])", r"\1", line)
    line = re.sub(r"([(])\s*[,;]\s*", r"\1", line)
    return line.rstrip()


def strip_empirical_values(text: str) -> str:
    """Remove every high-confidence empirical value from ``text`` (deterministic).

    Operates line by line (markdown headers and fenced code are left untouched).
    For each empirical token it also absorbs an immediately-preceding comparison
    operator / approximator (``≥95%`` → removed whole). Guaranteed claim-free of
    these patterns and idempotent. Surrounding prose, references, and all
    structural numbers are preserved.
    """
    out: list[str] = []
    in_fence = False
    for line in text.split("\n"):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence or stripped.startswith("#"):
            out.append(line)
            continue
        new = line
        # Remove tokens right-to-left so earlier offsets stay valid.
        while True:
            m = _EMPIRICAL_TOKEN.search(new)
            if m is None:
                break
            start = m.start()
            lead = _LEAD.search(new[:start])
            if lead is not None:
                start = lead.start()
            new = new[:start] + new[m.end():]
        out.append(_tidy(new) if new != line else line)
    return "\n".join(out)


__all__ = ["has_empirical_value", "strip_empirical_values"]
