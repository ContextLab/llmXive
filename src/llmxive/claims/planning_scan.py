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

# A value sitting in a statistical / numeric DESIGN-PARAMETER context is the
# operator's CHOSEN setting, not an empirical claim about the world, and must
# stay concrete — exactly like a bound-led target or ``α = 0.05``:
#   * confidence / significance — ``95% confidence``, ``Wilson 95% CI``,
#     ``significance level of 0.05``, ``α = 0.05``;
#   * tolerance / threshold / margin — ``relative tolerance of 0.05``,
#     ``discrepancy threshold of 0.1``, ``margin of 0.02`` — the cutoff a rule
#     compares against, which the operator picks, not measures.
#   * relative-of-reference — ``0.1 of the reported p-value``, ``[N] of the
#     larger count`` — a RELATIVE tolerance written as a fraction of a reference
#     quantity (reported / reconstructed / expected / larger / …). The
#     design-context word ("tolerance") is often NOT adjacent to the fraction
#     (``max(0.01, 0.1 of the reported p)``), so the ``of the <reference>``
#     construction itself is the design signal.
#   * synthetic-data / statistical-procedure COUNTS — ``10,000 replicates``,
#     ``10,000 simulated summaries``, ``synthetic dataset of 10,000``,
#     ``5,000 bootstrap resamples`` — an operator-CHOSEN N for a generated /
#     simulated procedure, NOT a measured world quantity. The planning convention
#     defers REAL/observed dataset sizes, but a SYNTHETIC size or a Monte-Carlo /
#     bootstrap / permutation replicate count IS the design (and is usually pinned
#     by an FR, so deferring it in the plan/tasks creates a spec↔task mismatch
#     the consistency panel re-flags forever — the live PROJ-492 plan loop on
#     FR-026's 10,000-replicate Monte-Carlo validation + synthetic dataset size).
# Deferring any of these produces e.g. ``[deferred] of the reported p-value`` /
# ``[deferred] replicates``, which the testability/soundness/consistency panels
# (correctly) re-flag as unverifiable forever: the reviser sets the value, the
# strip re-defers it next render. KEEP these concrete.
_STAT_DESIGN_CONTEXT = re.compile(
    r"confidence|\bCIs?\b|credible\s+interval|significance\s+level|\balpha\b|α"
    r"|toleranc|threshold|\bmargin\b"
    r"|of\s+the\s+(?:reported|reconstructed|expected|observed|nominal|larger"
    r"|smaller|total|reference|baseline|true|actual|predicted)"
    r"|replicat|\bsimulat|\bsynthetic\b|bootstrap|permutation|monte[\s-]*carlo"
    r"|resampl",
    re.IGNORECASE,
)


def has_empirical_value(text: str) -> bool:
    """True iff ``text`` contains a high-confidence empirical value (count/%/time)."""
    return _EMPIRICAL_TOKEN.search(text) is not None


# A bound operator immediately preceding a number — the *unanchored* twin of
# :data:`_BOUND_LEAD`, for testing whether an arbitrary span CONTAINS a
# design target (≥95%, "at least 80%", "within 60 minutes", "up to 13").
_DESIGN_TARGET = re.compile(
    r"(?:[≥≤<>±=]|"
    r"\b(?:up\s+to|at\s+least|at\s+most|within|minimum(?:\s+of)?|"
    r"maximum(?:\s+of)?|no\s+more\s+than|no\s+fewer\s+than|no\s+less\s+than))"
    r"\s*\d",
    re.IGNORECASE,
)


def is_design_target(text: str) -> bool:
    """True iff ``text`` contains a bound-led DESIGN TARGET (a threshold the
    system must MEET), not an empirical claim about the world.

    Spec 023 defect #16 made the deterministic strip KEEP these. This is
    the same protection for the LLM claim-detection/smooth path (defect
    #23): a span like ``"≥ 95% of knots ... populated"`` is a success
    criterion, not a world-claim — smoothing it into "the vast majority
    of knots ..." re-introduces the exact unquantified wording testability
    reviewers reject, and the reviser re-vagues it differently every round
    (the PROJ-552 spec non-convergence loop)."""
    return _DESIGN_TARGET.search(text) is not None


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

# A reviser sometimes fills in a concrete value but leaves the STALE [deferred]
# marker beside it — e.g. "the baseline of 0.05 ([deferred])" (PROJ-492 SC-014).
# The value IS present, so the marker is pure noise that the testability lens
# (correctly) re-flags every round, blocking convergence. Collapse a [deferred]
# marker that sits immediately next to a concrete numeric value. This is SAFE:
# the strip itself REPLACES a value WITH the marker, so it never leaves a
# concrete number adjacent to a genuine deferral — only a reviser's stray marker
# matches here.
_NUM_FRAG = r"\d[\d.,]*(?:\s?%)?"
_REDUNDANT_DEFERRED_RE = re.compile(
    rf"(?P<a>{_NUM_FRAG})\s*\(\[deferred\]\)"               # 0.05 ([deferred])
    rf"|(?P<b>{_NUM_FRAG})\s+\[deferred\](?=[\s,.;:)\]]|$)"  # 0.05 [deferred]
    rf"|\(\[deferred\]\)\s*(?P<c>{_NUM_FRAG})",            # ([deferred]) 0.05
    re.IGNORECASE,
)


def _collapse_redundant_deferred(text: str) -> str:
    """Drop a ``[deferred]`` marker left adjacent to an already-concrete value."""
    return _REDUNDANT_DEFERRED_RE.sub(
        lambda m: m.group("a") or m.group("b") or m.group("c") or "", text
    )


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
            # Spec 023 defect #16b (observed on 552's FR-010 retry schedule
            # "1s → 2s → 4s → 8s → 60s (max)", deferred into nonsense): a
            # bare TIMED quantity in a planning doc is essentially always a
            # DESIGN PARAMETER (timeout, backoff, budget), not a claim
            # about the world. Defer timed values only when approximator-
            # led ("takes approximately 15 minutes" — a runtime claim).
            if re.fullmatch(_TIMED, m.group(0), re.IGNORECASE) and not _LEAD.search(
                new[:start]
            ):
                pos = m.end()
                continue
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
            if _STAT_DESIGN_CONTEXT.search(new[max(0, start - 30):m.end() + 30]):
                # A confidence level / CI width is a statistical DESIGN
                # parameter (the PROJ-492 "[deferred] confidence level" loop) —
                # keep it concrete, do not defer.
                pos = m.end()
                continue
            lead = _LEAD.search(new[:start])
            if lead is not None:
                start = lead.start()
            new = new[:start] + DEFERRED_MARKER + new[m.end():]
            pos = start + len(DEFERRED_MARKER)
        out.append(_tidy(new) if new != line else line)
    return _collapse_redundant_deferred("\n".join(out))


__all__ = [
    "DEFERRED_MARKER",
    "has_empirical_value",
    "is_design_target",
    "strip_empirical_values",
]
