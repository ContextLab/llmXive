"""Concept-decomposed query extraction (spec 005 fix-up #3).

The librarian's earlier behavior was to pass the user's full natural-
language research question directly to Semantic Scholar + arXiv.
Manual lit-search audits revealed three systematic retrieval failures:

  Mode 1 — Vocabulary mismatch: the user says "code duplication" but
    the canonical literature says "memorization", "data contamination",
    "deduplication". SS+arXiv keyword indices don't surface
    vocabulary-divergent papers, and the LLM relevance judge then
    correctly notes "not narrowly on-topic" because the question's
    vocabulary truly doesn't match the candidate's vocabulary.

  Mode 2 — Sentence-shaped queries: long natural-language questions
    ("How does the intrinsic organization of human brain functional
    networks change...") get bag-of-words-ified; generic tokens like
    "how", "change", "experimentally" dilute signal. Short keyword
    queries ("sensory deprivation rs-fMRI modularity") would surface
    known relevant papers immediately.

  Mode 3 — Single broad query: a question with multiple concept axes
    (e.g. {sensory modality} x {neuroimaging measure} x {population})
    can't be covered by one query. Manual searches succeed because
    they decompose into concept-pair queries.

This module addresses all three with one LLM-driven pre-search step:
ask the LLM to generate 5 short, concept-decomposed keyword queries
for the research question — including synonym variants for
vocabulary clusters that diverge between question and literature.
The librarian then runs all 5 in parallel and unions the candidate
sets before verification.

Cost: one extra LLM call per librarian invocation (negligible vs
per-candidate judge calls).
"""

from __future__ import annotations

import logging
import re
from collections.abc import Sequence

from llmxive.backends.base import ChatMessage
from llmxive.backends.router import chat_with_fallback

LOGGER = logging.getLogger(__name__)

DEFAULT_QUERY_COUNT = 5

_QUERY_EXTRACTOR_SYSTEM_PROMPT = """\
You are a research-librarian query-construction expert. The user has a
specific research question. Your task: produce 5 short keyword search
queries that, run in parallel against Semantic Scholar + arXiv, will
maximize recall of genuinely on-topic prior literature.

CRITICAL CONSTRAINTS:
  - Each query MUST be 2-6 keywords. NOT a sentence. NOT a question.
  - Each query MUST target a DIFFERENT concept axis or vocabulary cluster.
  - At least 1 query MUST use synonym/alternative-vocabulary terms that
    the literature uses but the user's question may not (e.g. if the
    user says "code duplication", include a query with "memorization"
    or "data contamination"; if the user says "statistical power",
    include a query with "sample size justification" or "Type II error").
  - Avoid generic stop-words ("the", "and", "study", "analysis",
    "method", "approach", "research", "investigation", "factors").
  - Do NOT echo the user's full question.
  - Prefer canonical technical terms over colloquial phrasings.

OUTPUT FORMAT:
Return your queries as a numbered list (1-5). One query per line.
Nothing else. No preamble, no explanation.

EXAMPLE input:
"How do planned statistical power estimates in pre-registered studies
compare to the achieved power calculated from actual sample sizes and
observed effect sizes?"

EXAMPLE output:
1. preregistration sample size deviation
2. achieved power observed effect size meta-research
3. Type II error preregistration psychology
4. preregistered study sample size justification
5. statistical power post-hoc estimation discrepancy
"""


def extract_queries(
    research_question: str,
    *,
    field: str | None = None,
    n: int = DEFAULT_QUERY_COUNT,
    model: str = "qwen.qwen3.5-122b",
    default_backend: str = "dartmouth",
    fallback_backends: Sequence[str] = ("huggingface", "local"),
) -> list[str]:
    """Decompose the research question into N short keyword queries.

    Returns a list of 1-N strings. Falls back to a single
    deterministic short-form derivation of the input on backend
    failure (so the librarian never goes silent).
    """
    if not research_question or not research_question.strip():
        return []

    user_payload = (
        f"# Research question\n\n{research_question.strip()}\n\n"
        f"# Field\n\n{field or '(unspecified)'}\n\n"
        f"# Task\n\nReturn {n} short keyword queries per the system "
        f"prompt's rules. Numbered list, one per line, no preamble."
    )
    try:
        response = chat_with_fallback(
            [
                ChatMessage(role="system", content=_QUERY_EXTRACTOR_SYSTEM_PROMPT),
                ChatMessage(role="user", content=user_payload),
            ],
            default_backend=default_backend,
            fallback_backends=list(fallback_backends),
            model=model,
        )
    except Exception as exc:
        LOGGER.warning("[query-extractor] backend failure: %s", exc)
        return [_fallback_short_query(research_question, field)]

    parsed = _parse_numbered_queries(response.text, n=n)
    if not parsed:
        # LLM returned nothing parseable — fall back to short form.
        return [_fallback_short_query(research_question, field)]
    return parsed


def _parse_numbered_queries(text: str, *, n: int) -> list[str]:
    """Extract numbered-list queries from the LLM response.

    Tolerates: "1. foo", "1) foo", "- foo", "1: foo", and bare lines.
    Filters: empty lines, lines that look like full sentences (>=8 tokens),
    duplicates, the original question itself.
    """
    if not text:
        return []
    queries: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        # Strip leading list marker (1., 1), 1:, -, *).
        stripped = re.sub(r"^[-*]\s+|^\d+[\.\)\:]\s*", "", line).strip()
        if not stripped:
            continue
        # Reject anything that's still sentence-like (too many tokens).
        token_count = len(stripped.split())
        if token_count < 2 or token_count > 8:
            continue
        # Reject anything that contains stop-word-only signal.
        lower = stripped.lower()
        if lower in seen:
            continue
        seen.add(lower)
        queries.append(stripped)
        if len(queries) >= n:
            break
    return queries


def _fallback_short_query(research_question: str, field: str | None) -> str:
    """Derive a short keyword query from the research question without
    an LLM. Used only when the extractor backend fails."""
    # Take the first 6 alphanumeric tokens, dropping common stop-words.
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9-]+", research_question)
    stops = {
        "how", "what", "why", "when", "where", "does", "do", "did",
        "can", "could", "would", "should", "the", "and", "for", "with",
        "from", "into", "that", "this", "these", "those", "have", "has",
        "are", "is", "was", "were", "been", "being", "but", "any", "all",
        "between", "across", "during", "while",
    }
    salient = [t for t in tokens if t.lower() not in stops][:6]
    q = " ".join(salient).strip()
    if field:
        q = f"{q} {field}"
    return q or research_question.strip()[:80]


__all__ = [
    "DEFAULT_QUERY_COUNT",
    "extract_queries",
]
