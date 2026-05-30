"""Derive the search subject from a claim (spec 017, fill-layer contract).

strip_asserted_value — PURE: removes the asserted value/number from raw text
                        while keeping subject, qualifiers, and context.
subject_query        — returns the search query string for a claim; falls back
                        to strip_asserted_value when no backend is supplied.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from llmxive.claims.models import Claim


def strip_asserted_value(raw_text: str, value: str | None) -> str:
    """Remove the asserted *value* from *raw_text*, keeping subject+qualifiers.

    Handles comma-separated, space-separated, and plain digit-only variants of
    the number.  Strips surrounding whitespace artifacts left by the removal so
    the result reads cleanly.  Returns *raw_text* unchanged when *value* is
    None or empty.

    Examples
    --------
    >>> strip_asserted_value("27,635 prime knots at crossing number 13", "27635")
    'prime knots at crossing number 13'
    >>> strip_asserted_value("There are 9988 prime knots", "9988")
    'There are prime knots'
    """
    if not value:
        return raw_text

    # Normalise the value to its bare digits (strip commas/spaces the caller
    # may have included in the value string itself).
    bare = re.sub(r"[\s,]", "", value)

    if not bare.replace(".", "").isdigit() and "." not in bare:
        # Non-numeric value: do a plain substring removal (case-insensitive).
        pattern = re.compile(re.escape(value), re.IGNORECASE)
        cleaned = pattern.sub("", raw_text)
        return _tidy(cleaned)

    # Build a pattern that matches all human-formatted variants of the number:
    # * plain: 27635
    # * comma-thousands: 27,635
    # * space-thousands: 27 635
    #
    # Strategy: insert an optional separator (,| ) between every group of
    # digits as they appear in the bare number.  We split the bare digits into
    # chunks of at most 3 from the right (as in standard thousand-grouping) and
    # allow any mix of comma or space between them.
    variants = _build_number_variants(bare)
    pattern = re.compile(
        r"(?<!\d)(?:" + "|".join(re.escape(v) for v in variants) + r")(?!\d)"
    )
    cleaned = pattern.sub("", raw_text)
    return _tidy(cleaned)


def _build_number_variants(bare: str) -> list[str]:
    """Return the set of human-formatted variants for bare digits *bare*."""
    variants = {bare}
    # Only apply thousand-grouping to the integer part (before any decimal point)
    if "." in bare:
        int_part, dec_part = bare.split(".", 1)
    else:
        int_part, dec_part = bare, None

    # Group digits from the right in blocks of 3 (standard thousand separator)
    if len(int_part) > 3:
        groups: list[str] = []
        remaining = int_part
        while remaining:
            groups.insert(0, remaining[-3:])
            remaining = remaining[:-3]
        # Comma separator
        comma_fmt = ",".join(groups)
        # Space separator
        space_fmt = " ".join(groups)
        if dec_part is not None:
            comma_fmt += "." + dec_part
            space_fmt += "." + dec_part
        variants.add(comma_fmt)
        variants.add(space_fmt)

    # Also add the original value string in case it was already formatted
    return sorted(variants, key=len, reverse=True)  # longest first → greedy match


def _tidy(text: str) -> str:
    """Collapse multiple spaces / leading-trailing whitespace after removal."""
    # Replace runs of spaces (but not newlines) left by removals
    text = re.sub(r" {2,}", " ", text)
    # Remove orphan commas or punctuation left directly adjacent to spaces
    text = re.sub(r"\s+,\s+", " ", text)
    text = re.sub(r"^[,\s]+", "", text)
    text = re.sub(r"[,\s]+$", "", text)
    return text.strip()


def subject_query(
    claim: Claim,
    *,
    backend: Any = None,
    model: str | None = None,
    repo_root: Path | None = None,
) -> str:
    """Return a search query string for *claim*.

    When *backend* is ``None`` (pure / offline), falls back to
    :func:`strip_asserted_value` applied to the claim's ``raw_text`` using
    ``resolved_value`` as the value to remove.  The resulting string contains
    the subject + qualifiers without the asserted number, which is exactly what
    a search engine needs.

    When *backend* is provided, an LLM call is made (Phase 3+); the pure
    fallback is still used if the LLM call fails or returns an empty string.
    """
    # Pure fallback path (always taken in this Phase-2 implementation)
    raw = claim.raw_text or claim.canonical or ""
    value = claim.resolved_value
    stripped = strip_asserted_value(raw, value)
    if stripped.strip():
        return stripped.strip()
    # If stripping left nothing meaningful, return the raw text as-is
    return raw


__all__ = ["strip_asserted_value", "subject_query"]
