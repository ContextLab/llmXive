"""Stage-aware review-intake triage (spec 015 T038, FR-021/FR-022/FR-023).

A submitted human / simulated-personality review is routed through three filters:

  1. **Quality filter** — evidence-based, specific, relevant (length + indicators).
  2. **Safety + on-topic filter** — family-friendly + actually about the project.
  3. **Aspect-mapping** — which LLM reviewer lens(es) does the text address?

Preservation policy (FR-022):
  - Quality + safe + on-topic  → ``preserved=True``, mapped to lens(es); the matching
    LLM reviewer(s) receive the text as ADDITIONAL INPUT (never a gate).
  - Anything failing quality OR safety → ``preserved=False`` with a recorded reason
    (excluded from the publication's review log).
  - Quality+safe but NO lens match → preserved + ``mapped_lenses=[]`` (routes to the
    step's generic reviewer; recorded-but-not-actioned).

A rule-based path is the default (deterministic + offline-testable). A real-LLM
``judge_fn`` may be injected for nuanced judgments; same shape as the rule-based
output. Same pattern as ``tools/summarize.summarize_fn``.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from typing import Literal

from .types import TriageRecord

# --- rule-based heuristics ---------------------------------------------------

_MIN_QUALITY_CHARS = 80

# An evidence indicator means the review is *specific* (not generic praise/blame).
_EVIDENCE_INDICATORS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:FR|SC)-\d{2,4}\b"),
    re.compile(r"\bT\d{3,4}\b"),
    re.compile(r"§\d+"),
    re.compile(r"\bSection\s+\d", re.IGNORECASE),
    re.compile(r"\[[A-Za-z][A-Za-z .&-]+\d{4}[a-z]?\]"),  # [Smith2020]-style
    re.compile(r"https?://\S+"),
    re.compile(r"\b10\.\d{4,9}/\S+", re.IGNORECASE),       # DOI
    re.compile(r"\barXiv:\s*\d{4}\.\d{4,5}", re.IGNORECASE),
    re.compile(r'"[^"\n]{10,}"'),                          # quoted phrase ≥10 chars
    re.compile(r"```"),                                    # code fence
    re.compile(r"\b(?:methodology|claim|figure|table|equation|dataset|baseline|"
               r"hyperparameter|p-value|coefficient|theorem|lemma)\b", re.IGNORECASE),
)

# Bare-minimum family-unfriendly / unsafe content stop-list. Real production
# triage would call a safety LLM; this stop-list catches the obvious cases the
# tests need to assert and keeps the rule-based path offline.
_UNSAFE_PHRASES: tuple[str, ...] = (
    "kill yourself",
    "kys",
    "nsfw",
    "porn",
    "slur1",  # placeholder for an explicit slur the test asserts is blocked
)


def _has_evidence(text: str) -> bool:
    return any(pat.search(text) for pat in _EVIDENCE_INDICATORS)


def _is_unsafe(text: str) -> bool:
    lo = text.lower()
    return any(phrase in lo for phrase in _UNSAFE_PHRASES)


def _on_topic(text: str, stage: str, lenses: list[str]) -> bool:
    """Loose on-topic check: the review mentions the stage, OR any lens, OR a
    general scientific-project vocabulary word."""
    lo = text.lower()
    if stage and stage.lower() in lo:
        return True
    for lens in lenses:
        if not lens:
            continue
        if lens.lower() in lo:
            return True
        # Lens names use snake_case; also match the human form.
        if lens.replace("_", " ").lower() in lo:
            return True
    topic_words = (
        "paper", "spec", "plan", "task", "model", "data", "experiment",
        "result", "method", "abstract", "introduction", "discussion",
        "conclusion", "reference", "citation", "figure", "table",
    )
    return any(w in lo for w in topic_words)


def _map_lenses(text: str, lenses: list[str]) -> list[str]:
    """Return every lens whose name (snake_case OR human form) appears in the
    text. Order = ``lenses`` argument's order, deduped."""
    lo = text.lower()
    matched: list[str] = []
    for lens in lenses:
        if not lens or lens in matched:
            continue
        if lens.lower() in lo or lens.replace("_", " ").lower() in lo:
            matched.append(lens)
    return matched


# --- public API --------------------------------------------------------------

JudgeFn = Callable[[str, str, list[str]], dict]


def triage_submission(
    review_text: str,
    *,
    source: Literal["human", "personality"],
    author: str,
    stage: str,
    lenses: list[str],
    judge_fn: JudgeFn | None = None,
) -> TriageRecord:
    """Triage one submitted review.

    Returns a :class:`TriageRecord` (FR-022 fields). ``preserved=False`` records
    are excluded from the project's publication review log; ``preserved=True``
    records with non-empty ``mapped_lenses`` are forwarded to the matching LLM
    reviewer(s) as additional input.
    """
    if judge_fn is not None:
        verdict = judge_fn(review_text, stage, lenses)
        quality_pass = bool(verdict.get("quality_pass"))
        safe_on_topic = bool(verdict.get("safe_on_topic"))
        mapped_lenses = list(verdict.get("mapped_lenses") or [])
    else:
        quality_pass = len(review_text.strip()) >= _MIN_QUALITY_CHARS and _has_evidence(review_text)
        safe_on_topic = (not _is_unsafe(review_text)) and _on_topic(review_text, stage, lenses)
        mapped_lenses = _map_lenses(review_text, lenses) if (quality_pass and safe_on_topic) else []

    excluded_reason: str | None = None
    preserved = True
    if not quality_pass:
        preserved = False
        excluded_reason = (
            "quality filter: text is too short or lacks evidence indicators "
            "(no FR/SC/task id, citation, URL/DOI, quoted phrase, or specific term)"
        )
    elif not safe_on_topic:
        preserved = False
        excluded_reason = (
            "safety/on-topic filter: contains unsafe/family-unfriendly content or "
            "is off-topic for the project's stage"
        )

    return TriageRecord(
        source=source,
        author=author.strip(),
        stage_context=stage,
        quality_pass=quality_pass,
        safe_on_topic=safe_on_topic,
        mapped_lenses=mapped_lenses,
        preserved=preserved,
        excluded_reason=excluded_reason,
        review_text=review_text,
    )


__all__ = ["triage_submission"]
