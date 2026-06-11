"""Spec 020 — deterministic empirical-value strip for planning documents.

The LLM extractor (``extract_claims``) raises planning recall but cannot GUARANTEE
that every low-level empirical value is detected — it is non-deterministic, so a
given run may miss some. This module is the deterministic GUARANTEE: it removes the
high-confidence empirical patterns spec 020 defers out of planning docs, regardless
of the LLM's recall, while being conservative enough never to touch STRUCTURAL
numbers.

DEFERRED (bare/approximated empirical assertions → ``[deferred]``):
  - comma-grouped counts/magnitudes:  27,635   ~1,701,936   a total of 2,000
  - bare/approximated percentages:    95% of records   approximately 10%
  - bare timed quantities:            takes 15 minutes   60s

PRESERVED (never deferred):
  - DESIGN TARGETS (spec 023 #16) — bound-led values are requirements the
    project CHOOSES, not claims about the world:
    ≥95% completeness   at least 80% power   within 15 minutes   ≤30 ms
  - verified-facts values (the ``exempt`` parameter)
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

# Two distinct lead classes (spec 023 defect #16):
#
# A BOUND lead marks a CHOSEN DESIGN TARGET — a requirement the project
# sets ("≥95% match", "at least 80% power", "within 60 minutes",
# "up to 13 crossings"). Targets are requirements, not empirical claims:
# they are KEPT (stripping them made every success criterion untestable —
# the reviewer-vs-strip war observed live on PROJ-552).
_BOUND_LEAD = re.compile(
    r"(?:[≥≤<>±=]\s*|"
    r"\b(?:up\s+to|at\s+least|at\s+most|within|minimum(?:\s+of)?|"
    r"maximum(?:\s+of)?|no\s+more\s+than|no\s+fewer\s+than|"
    r"no\s+less\s+than)\s+)$",
    re.IGNORECASE,
)

# An APPROXIMATOR lead hedges an EMPIRICAL assertion ("approximately
# 27,635 papers", "~1,701,936 records", "a total of 2,000 knots") — the
# value is a claim about the world and is absorbed + deferred whole.
_LEAD = re.compile(
    r"(?:[~≈]\s*|"
    r"\b(?:approximately|about|roughly|around|nearly|exactly|over|under|"
    r"a\s+total\s+of|some)\s+)$",
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


#: Grammatical stand-in for a deferred empirical value (spec 023 defect
#: #15): bare DELETION left broken prose — "≥95% of records have X" became
#: "of records have X" — which review panels then (correctly) flagged as an
#: incomplete placeholder, and the reviser's re-added number was stripped
#: again on the next render: an unwinnable loop observed live on PROJ-552.
#: The marker is sanctioned in the shared panel-review block; panels must
#: not flag it.
DEFERRED_MARKER = "[deferred]"


def _normalize_value(token: str) -> str:
    """Canonical form for exempt-value comparison: digits/percent only."""
    return re.sub(r"[^\d.%]", "", token).rstrip(".")


def strip_empirical_values(
    text: str, *, exempt: tuple[str, ...] = ()
) -> str:
    """Defer every high-confidence empirical value in ``text`` (deterministic).

    Operates line by line (markdown headers and fenced code are left
    untouched). Each empirical token — together with an immediately-
    preceding comparison operator / approximator (``≥95%`` is handled
    whole) — is replaced by :data:`DEFERRED_MARKER`, keeping the sentence
    grammatical. Idempotent; structural numbers are preserved.

    ``exempt`` (spec 023 defect #15): values verified against a primary
    source (the project's ``verified_facts.yaml``) are EXACTLY what the
    planning rule wants cited — they are kept, not deferred.
    """
    exempt_norm = {_normalize_value(v) for v in exempt if v}
    exempt_norm.discard("")
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
        pos = 0
        while True:
            m = _EMPIRICAL_TOKEN.search(new, pos)
            if m is None:
                break
            if _normalize_value(m.group(0)) in exempt_norm:
                pos = m.end()
                continue
            start = m.start()
            if _BOUND_LEAD.search(new[:start]) is not None:
                # Spec 023 defect #16: a bound-led value (>=95%, "at least
                # 80%", "within 60 minutes") is a CHOSEN DESIGN TARGET — a
                # requirement the project sets, not an empirical claim
                # about the world. Stripping targets made every success
                # criterion untestable, and the testability reviewers
                # (correctly) re-flagged the [deferred] holes each round
                # while the strip deleted every threshold the reviser
                # restored — an unwinnable reviewer-vs-strip war observed
                # live on PROJ-552's spec panel. Bounded targets are KEPT;
                # bare/approximated empirical assertions are deferred.
                pos = m.end()
                continue
            lead = _LEAD.search(new[:start])
            if lead is not None:
                start = lead.start()
            new = new[:start] + DEFERRED_MARKER + new[m.end():]
            pos = start + len(DEFERRED_MARKER)
        out.append(_tidy(new) if new != line else line)
    return "\n".join(out)


__all__ = ["DEFERRED_MARKER", "has_empirical_value", "strip_empirical_values"]
