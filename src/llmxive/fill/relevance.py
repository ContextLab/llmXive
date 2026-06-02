"""PROSE-channel semantic substantiation gate (spec 019).

Literal presence of a value in fetched text substantiates a fill ONLY for
STRUCTURED channels (constants / OEIS / Wikidata), where the subject<->value link
is inherent. For PROSE channels (Wikipedia / theorem / paper full text) a small
value can appear coincidentally in an unrelated passage — the observed
"<=6 / Almoravid dynasty" failure, where the digit 6 of a knot crossing-number
bound matched "about 6 generations" in an unrelated article.

This module gates PROSE candidates in two layers, both fail-closed:

1. ``_subject_cooccurs`` — a deterministic, zero-network necessary condition: at
   least one of the claim's subject keywords must occur within a bounded window
   of an occurrence of the value. Rejects the coincidental match with NO LLM call.
2. ``prose_substantiated`` — for survivors, one semantic entailment call via the
   existing :func:`grounding.entailment.assess`; accept ONLY a ``grounded``
   verdict. ``contradicted`` / ``not_found`` / a missing backend / any error all
   reject (absence of evidence MUST NOT fill).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llmxive.agents.grounding_guard import _number_anchor_re
from llmxive.claims.canonical import subject_keywords
from llmxive.claims.models import Claim
from llmxive.fill.models import FetchedSource
from llmxive.grounding.entailment import _WINDOW, assess

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _SourceDoc:
    """Minimal adapter exposing exactly what :func:`assess` reads from a doc
    (``doc.full_text or doc.abstract``)."""

    full_text: str
    abstract: str = ""


def _value_spans(value: str, text: str) -> list[tuple[int, int]]:
    """Character spans of *value* in *text*.

    Numeric values use the same number-anchor regex :mod:`grounding.entailment`
    uses (so comma/space thousand-separator variants are honored); entity values
    (and any value the anchor cannot form) fall back to a case-insensitive
    substring scan.
    """
    spans: list[tuple[int, int]] = []
    anchor = _number_anchor_re(value)
    if anchor is not None:
        spans = [(m.start(), m.end()) for m in anchor.finditer(text)]
    if not spans:
        low_text = text.lower()
        low_val = value.strip().lower()
        if low_val:
            start = 0
            while True:
                i = low_text.find(low_val, start)
                if i < 0:
                    break
                spans.append((i, i + len(low_val)))
                start = i + len(low_val)
    return spans


def _keyword_near(keyword: str, window: str) -> bool:
    """True if *keyword* (singularized subject token) appears at a word start in
    *window*. Word-start anchoring (no trailing boundary) tolerates the plural /
    inflected forms the source text uses ("knot" matches "knots") while avoiding
    mid-word noise; leniency is intentional — this is a *necessary* pre-filter,
    not the decision (``assess`` is)."""
    if not keyword:
        return False
    return re.search(r"\b" + re.escape(keyword), window) is not None


def _subject_cooccurs(value: str, source_text: str, claim: Claim) -> bool:
    """Deterministic necessary condition for PROSE substantiation: a subject
    keyword co-occurs within +/- ``_WINDOW`` chars of an occurrence of *value*.

    Returns False (reject, fail-closed) when the value cannot be located, when the
    claim has no distinctive subject keywords, or when no keyword is near any
    occurrence. No network or LLM call.
    """
    text = source_text or ""
    spans = _value_spans(value, text)
    if not spans:
        return False
    keywords = [k for k in subject_keywords(claim) if k]
    if not keywords:
        return False
    low = text.lower()
    for start, end in spans:
        lo = max(0, start - _WINDOW)
        hi = min(len(text), end + _WINDOW)
        window = low[lo:hi]
        if any(_keyword_near(kw, window) for kw in keywords):
            return True
    return False


def prose_substantiated(
    value: str,
    source: FetchedSource,
    claim: Claim,
    *,
    backend: Any,
    model: str | None,
    repo_root: Path | None,
) -> bool:
    """Semantic substantiation gate for a PROSE-channel candidate.

    True ONLY when BOTH hold:
      1. ``_subject_cooccurs(value, source.text, claim)`` (deterministic; no LLM
         call when it fails), AND
      2. :func:`grounding.entailment.assess` returns a ``grounded`` verdict over
         the source text.

    Any failure — no co-occurrence, missing backend, ``contradicted`` /
    ``not_found`` verdict, or an exception — returns False (fail-closed: absence
    of evidence MUST NOT fill).
    """
    if not _subject_cooccurs(value, source.text, claim):
        return False
    if backend is None:
        # Cannot run entailment without a backend; PROSE substantiation requires
        # it, so refuse rather than accept on the literal/keyword layers alone.
        return False
    claim_text = claim.canonical or claim.raw_text or ""
    try:
        verdict = assess(
            claim_text,
            _SourceDoc(full_text=source.text),
            backend=backend,
            model=model,
            repo_root=repo_root,
        )
    except Exception as exc:  # defensive — assess already guards, but never leak
        logger.warning("prose_substantiated: assess raised (%s); -> reject", exc)
        return False
    return verdict.status == "grounded"


__all__ = ["prose_substantiated"]
