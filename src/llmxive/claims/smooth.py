"""Spec 020 — strip/smooth a low-level claim out of a planning document (FR-002a/b/c).

In a *planning* stage (specify/clarify/plan/tasks) the claim layer does not verify
low-level empirical claims; instead it replaces each detected low-level claim with a
higher-level statement so no unverified/false specific value remains (and nothing
blocks). The transform:

1. **LLM rewrite** — ask the model to restate the passage at a higher level,
   removing the specific value while preserving citations, the research question,
   and the method (the value comes from the centralized ``reasoning_chat`` policy).
2. **Re-detect guard** — deterministically confirm the asserted value is gone
   (reusing :func:`canonical._asserted_value` / the pointer token logic). This is
   the deterministic detector: a value-free passage carries no low-level claim, so
   the guard is what makes the transform *idempotent* (FR-002b / SC-001a).
3. **Deterministic fallback** — if the rewrite still asserts the value, excise the
   asserted token and its leading quantifier words deterministically (no LLM), so
   the result is *always* claim-free.

Reuses (Principle I / FR-015): ``canonical._asserted_value`` to identify the
asserted token, ``pointer._digits_only`` to compare value identity, and
``backends.router.reasoning_chat`` for the rewrite.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from llmxive.claims.canonical import _asserted_value as asserted_value
from llmxive.claims.models import Claim
from llmxive.claims.pointer import _digits_only, _numeric_tokens

logger = logging.getLogger(__name__)

# Quantifier words that introduce an asserted count/quantity; removed alongside
# the value token in the deterministic fallback so "exactly 9,988 prime knots"
# collapses to "prime knots" rather than leaving a dangling "exactly".
_QUANTIFIERS = (
    "exactly", "precisely", "approximately", "about", "roughly", "around",
    "nearly", "almost", "some", "a total of", "totaling", "totalling",
    "up to", "at least", "at most", "over", "more than", "fewer than",
    "less than",
)


def _asserts(text: str, asserted: str) -> bool:
    """True iff ``text`` still contains a number token equal (digits-only) to ``asserted``."""
    target = _digits_only(asserted)
    if not target:
        return asserted.strip() in text
    return any(_digits_only(m.group(0)) == target for m in _numeric_tokens(text))


def _deterministic_strip(passage: str, asserted: str) -> str:
    """Remove the asserted value token (+ adjacent quantifier words) from ``passage``.

    Guaranteed to leave the passage claim-free of ``asserted`` while preserving the
    rest of the prose (citations, research question, method). Conservative: it only
    touches the matched value span and immediately-preceding quantifier words.
    """
    target = _digits_only(asserted)
    out = passage
    for m in _numeric_tokens(passage):
        if _digits_only(m.group(0)) != target or not target:
            continue
        start, end = m.start(), m.end()
        # Absorb a single leading quantifier phrase, if present.
        prefix = out[:start].rstrip()
        for q in sorted(_QUANTIFIERS, key=len, reverse=True):
            if prefix.lower().endswith(q):
                start = len(prefix) - len(q)
                break
        out = out[:start] + out[end:]
        break
    # Tidy: collapse the gap left by the removal without disturbing other prose.
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r"\s+([.,;:)])", r"\1", out)
    out = re.sub(r"\(\s+", "(", out)
    return out.strip()


def _llm_generalize(
    passage: str, claim: Claim, *, backend: Any, model: str | None
) -> str | None:
    """Ask the model to restate ``passage`` at a higher level, value removed.

    Returns the rewritten passage, or ``None`` if the backend is unavailable or
    the reply is empty (the caller then uses the deterministic fallback).
    """
    if backend is None:
        return None
    from llmxive.backends.base import ChatMessage
    from llmxive.backends.router import reasoning_chat

    messages = [
        ChatMessage(
            role="system",
            content=(
                "You revise a sentence from a research PLANNING document. The "
                "planning document must state the research question, the method, "
                "and the references — but MUST NOT assert specific low-level "
                "empirical values (exact counts, measured quantities, specific "
                "magnitudes); those belong to the later implementation/research "
                "phase. Rewrite the given passage so it no longer asserts the "
                "specific value, replacing it with a higher-level qualitative "
                "statement that preserves the intent. PRESERVE any citation "
                "(DOI/arXiv/author-year), the research question, and the method "
                "verbatim. Return ONLY the rewritten passage, no preamble."
            ),
        ),
        ChatMessage(
            role="user",
            content=(
                f"Passage:\n{passage}\n\n"
                f"The specific value to remove/generalize: "
                f"{asserted_value(claim.raw_text or claim.canonical or '') or claim.canonical!r}\n\n"
                "Rewritten passage:"
            ),
        ),
    ]
    try:
        response = reasoning_chat(backend, messages, model=model)
        reply = (getattr(response, "text", "") or "").strip()
        return reply or None
    except Exception as exc:  # never raise — fall back deterministically
        logger.warning("claims.smooth: LLM rewrite failed (%s); using fallback", exc)
        return None


def strip_and_smooth(
    passage: str, claim: Claim, *, backend: Any, model: str | None
) -> str:
    """Replace the low-level assertion in ``passage`` with a claim-free higher-level statement.

    Idempotent (FR-002b / SC-001a): if ``passage`` no longer asserts the claim's
    specific value, it is returned unchanged. Otherwise an LLM rewrite is attempted
    and accepted only if it removed the value (re-detect guard); if not, a
    deterministic clause-removal fallback guarantees a claim-free result. Citations
    and surrounding content are preserved (FR-002c).
    """
    asserted = asserted_value(claim.raw_text or claim.canonical or "")
    if not asserted or not _asserts(passage, asserted):
        # Nothing specific to strip (already smoothed / no identifiable value).
        return passage

    rewritten = _llm_generalize(passage, claim, backend=backend, model=model)
    if rewritten and not _asserts(rewritten, asserted):
        return rewritten

    # Rewrite unavailable or still asserts the value → deterministic fallback.
    return _deterministic_strip(passage, asserted)


__all__ = ["strip_and_smooth"]
