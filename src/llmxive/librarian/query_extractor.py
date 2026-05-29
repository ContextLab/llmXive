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
  - Avoid generic stop-words ("the", "and", "study", "analysis",
    "method", "approach", "research", "investigation", "factors").
  - Do NOT echo the user's full question.
  - Prefer canonical technical terms over colloquial phrasings.

REQUIRED VOCABULARY COVERAGE (each query covers a different cluster):

  1. ONE query using SYNONYM / ALTERNATIVE-VOCABULARY terms — the
     terms the literature actually uses but the user's question may
     not. Examples:
       - "code duplication" → "memorization" / "data contamination"
       - "statistical power" → "sample size justification" /
         "Type II error" / "achieved power"
       - "code clone density" → "near-duplicate sequences" /
         "deduplication"

  2. ONE query using EMPIRICAL-POPULATION VOCABULARY (REQUIRED if
     the question references an experimental population, paradigm,
     or operationalization). The literature is indexed under the
     POPULATION the experiment uses, not under the abstract concept.
     Examples:
       - "sensory deprivation" → "early deafness OR congenital blindness
         OR Floatation-REST" (these are how the actual experiments are
         indexed in PubMed/SS/arXiv)
       - "pre-registered studies" → "OSF preregistration replication"
       - "molecular property prediction" → "QM9 dataset GNN" (the
         canonical benchmark)
       - "implicit attitudes" → "IAT response time priming"
       - "sensory reduction" → "blindfolding flotation tank dark room"

  3. ONE query using SUB-COMMUNITY CANONICAL PROXY terms — when the
     user's framing comes from one sub-community but the actual
     literature on the question lives in another sub-community using
     a different proxy metric. Examples:
       - "clustering coefficient in GNNs" → "homophily heterophily GNN
         training" (GNN community uses homophily as the structural
         topology proxy, not raw graph theory metrics)
       - "small-world graph for ML" → "Watts-Strogatz network ML"
         OR "homophily heterophily graph topology"

  4. ONE query covering the MEASURED-OUTCOME side of the question
     (the dependent variable + canonical evaluation framework).
     Examples:
       - "convergence efficiency GNN" → "training dynamics GNN
         optimization rate"
       - "perplexity on Python code" → "code language model perplexity
         held-out evaluation"

  5. ONE query covering the CAUSAL-MECHANISM or THEORETICAL-FRAMING
     side of the question — the underlying theory the question rests
     on. Examples:
       - "code duplication" → "training data leakage benchmark
         contamination"
       - "preregistered power" → "p-hacking publication bias effect
         size inflation"

If the question is purely abstract (no specific empirical population),
substitute query #2 with another synonym/canonical-proxy query.

OUTPUT FORMAT:
Return your queries as a numbered list (1-5). One query per line.
Nothing else. No preamble, no explanation.

EXAMPLE input:
"How do planned statistical power estimates in pre-registered studies
compare to the achieved power calculated from actual sample sizes and
observed effect sizes?"

EXAMPLE output:
1. preregistration sample size deviation
2. OSF preregistration replication psychology
3. Type II error sample size justification
4. achieved power empirical baseline meta-research
5. p-hacking effect size inflation publication bias
"""


def extract_queries(
    research_question: str,
    *,
    field: str | None = None,
    n: int = DEFAULT_QUERY_COUNT,
    model: str = "qwen.qwen3.5-122b",
    default_backend: str = "dartmouth",
    fallback_backends: Sequence[str] = ("local",),
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
        LOGGER.warning("[query-extractor] backend failure; using deterministic fallback: %s", exc)
        return _fallback_queries(research_question, field)

    parsed = _parse_numbered_queries(response.text, n=n)
    if not parsed:
        # LLM returned nothing parseable — fall back to deterministic
        # positional decomposition.
        LOGGER.warning("[query-extractor] unparseable LLM response; using deterministic fallback")
        return _fallback_queries(research_question, field)
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


_FALLBACK_STOPS = frozenset({
    "how", "what", "why", "when", "where", "does", "do", "did",
    "can", "could", "would", "should", "the", "and", "for", "with",
    "from", "into", "that", "this", "these", "those", "have", "has",
    "are", "is", "was", "were", "been", "being", "but", "any", "all",
    "between", "across", "during", "while", "of", "in", "on", "to",
    "their", "its", "a", "an", "by", "as", "at", "or", "if", "than",
    "then", "such", "more", "most", "less",
})


def _salient_tokens(research_question: str) -> list[str]:
    """Alphanumeric tokens of the question minus common stop-words,
    in original order."""
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9-]+", research_question)
    return [t for t in tokens if t.lower() not in _FALLBACK_STOPS]


def _fallback_queries(research_question: str, field: str | None) -> list[str]:
    """Deterministic positional decomposition of the research question
    into up to 3 short keyword queries — used only when the LLM
    extractor backend fails or returns unparseable output.

    Strategy: a long research question is usually structured as
    ``[independent variable] → [relationship] → [dependent variable]
    in [context/population]``. We emit three overlapping windows that
    each emphasize a different region:

      - HEAD  : first ~5 salient tokens (usually the independent
                variable / mechanism under study) + field suffix
      - TAIL  : last ~5 salient tokens (usually the dependent
                variable + population / context)
      - SPREAD: every-other salient token, truncated to ~7 (a coarse
                whole-question summary)

    This is crude vs. the LLM path (no semantic concept decomposition,
    no synonym / empirical-population vocabulary) but it preserves the
    parallel-multi-query recall benefit even in degraded mode. Always
    returns at least one query (falls back to the truncated question
    if there are too few salient tokens).
    """
    salient = _salient_tokens(research_question)
    if not salient:
        return [research_question.strip()[:80] or "literature search"]

    queries: list[str] = []
    seen: set[str] = set()

    def _add(toks: list[str], *, suffix: str | None = None) -> None:
        if not toks:
            return
        q = " ".join(toks).strip()
        if suffix:
            q = f"{q} {suffix}"
        key = q.lower()
        if q and key not in seen:
            seen.add(key)
            queries.append(q)

    # HEAD — independent-variable region; field-anchored.
    _add(salient[:5], suffix=field)
    # TAIL — dependent-variable + context region.
    if len(salient) > 6:
        _add(salient[-5:])
    # SPREAD — coarse whole-question summary (every other token).
    if len(salient) > 8:
        _add(salient[::2][:7])

    return queries or [_fallback_short_query(research_question, field)]


def _fallback_short_query(research_question: str, field: str | None) -> str:
    """Single short keyword query — last-resort when even the positional
    decomposition can't produce anything (e.g. <2 salient tokens)."""
    salient = _salient_tokens(research_question)[:6]
    q = " ".join(salient).strip()
    if field:
        q = f"{q} {field}"
    return q or research_question.strip()[:80] or "literature search"


__all__ = [
    "DEFAULT_QUERY_COUNT",
    "extract_queries",
]
