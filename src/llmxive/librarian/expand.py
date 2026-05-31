"""Multi-step expanded search (spec 005 / FR-004 / Q3).

When the librarian's initial keyword search returns fewer than
``target_n`` verified citations, this module:

  1. Calls the brainstorming LLM (Dartmouth Chat by default,
     ``qwen.qwen3.5-122b``) with a prompt that includes the original
     term + project context (field + idea body excerpt) and asks for
     10-20 alternative phrasings ranked by relevance.
  2. Iterates through the ranked list, querying both Semantic Scholar
     and arXiv per term, accumulating verified citations.
  3. Terminates when ≥target_n verified accumulate OR the list is
     exhausted (hard cap of 20 expanded terms).

Per Q3 clarification: when expansion exhausts without reaching
``target_n``, the caller (typically ``flesh_out``) decides next action;
this module just returns the partial list with the right outcome flag.

Per Constitution Principle III: real LLM call, real backend searches.
Per Principle V: hard cap on expanded terms; bounded retry on each
search.
"""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Sequence

from llmxive.backends.base import ChatMessage
from llmxive.backends.router import chat_with_fallback
from llmxive.librarian.search import (
    ArxivClient,
    SemanticScholarClient,
    merge_candidates,
)
from llmxive.librarian.verify import VerifiedCitation, verify_citation

DEFAULT_EXPANSION_CAP = 20
DEFAULT_TARGET_N = 5


@dataclasses.dataclass(frozen=True)
class ExpansionResult:
    """Outcome of one multi-step expansion run."""

    expanded_terms_ranked: list[tuple[int, str]]  # [(rank, term), ...]
    per_term_hit_count: dict[str, int]  # verified-hit count per term
    total_queries_issued: int
    accumulated_verified: list[VerifiedCitation]
    outcome: str  # "success_after_expansion" | "exhausted"


def expand_terms(
    original_term: str,
    *,
    field: str | None,
    idea_body_excerpt: str | None,
    n: int = DEFAULT_EXPANSION_CAP,
    expansion_prompt: str | None = None,
    model: str = "qwen.qwen3.5-122b",
    default_backend: str = "dartmouth",
    fallback_backends: Sequence[str] = ("local",),
) -> list[tuple[int, str]]:
    """Ask the LLM for ``n`` ranked alternative phrasings of
    ``original_term``.

    Returns ``[(rank, term), ...]`` with ranks 1..n in relevance order.
    The original term itself is NOT included (the caller already tried
    it). Hard caps the list at ``DEFAULT_EXPANSION_CAP`` even if the
    LLM returns more.
    """
    sys_prompt = expansion_prompt or _DEFAULT_EXPANSION_PROMPT
    user_payload = (
        f"# Original term\n\n{original_term}\n\n"
        f"# Field\n\n{field or '(unspecified)'}\n\n"
        f"# Idea body excerpt\n\n{idea_body_excerpt or '(none)'}\n\n"
        f"# Task\n\nReturn 10-20 alternative phrasings or related concepts, "
        f"one per line, in relevance order."
    )

    response = chat_with_fallback(
        [
            ChatMessage(role="system", content=sys_prompt),
            ChatMessage(role="user", content=user_payload),
        ],
        default_backend=default_backend,
        fallback_backends=list(fallback_backends),
        model=model,
    )

    parsed = _parse_ranked_terms(response.text, original_term=original_term)
    return parsed[: min(n, DEFAULT_EXPANSION_CAP)]


def iterate_until_target(
    original_term: str,
    expanded: Sequence[tuple[int, str]],
    *,
    target_n: int = DEFAULT_TARGET_N,
    ss_client: SemanticScholarClient | None = None,
    arxiv_client: ArxivClient | None = None,
    summary_for_each: dict[str, str] | None = None,
    per_term_limit: int = 5,
) -> ExpansionResult:
    """Iterate over expanded terms, verifying candidates, until ≥target_n
    verified accumulate or the list is exhausted.

    ``summary_for_each``: optional mapping from candidate.primary_pointer
    to the librarian-generated summary string. If absent for a candidate,
    its claimed_abstract is used as the summary input to verify_citation.
    """
    summary_for_each = summary_for_each or {}
    ss = ss_client  # may be None if no SS key; in that case we only hit arXiv
    ax = arxiv_client or ArxivClient(min_interval_seconds=3.0)

    per_term_hit_count: dict[str, int] = {original_term: 0}
    accumulated: list[VerifiedCitation] = []
    seen_pointers: set[str] = set()
    total_queries = 0

    for _, term in expanded:
        per_term_hit_count.setdefault(term, 0)
        # Backend search.
        ss_results = ss.search_papers(term, limit=per_term_limit) if (ss and ss.has_key) else []
        ax_results = ax.search(term, max_results=per_term_limit)
        total_queries += (1 if (ss and ss.has_key) else 0) + 1
        candidates = merge_candidates(ss_results, ax_results)

        for c in candidates:
            if c.primary_pointer in seen_pointers:
                continue
            seen_pointers.add(c.primary_pointer)
            summary = summary_for_each.get(c.primary_pointer)
            # Each expanded term IS the effective query for the candidates
            # it surfaced — pass it through so the relevance gate filters
            # off-topic SS+arXiv hits per the spec 005 fix.
            result = verify_citation(
                c,
                summary=summary or c.claimed_abstract or "",
                query=term,
            )
            if isinstance(result, VerifiedCitation):
                accumulated.append(result)
                per_term_hit_count[term] += 1

        if len(accumulated) >= target_n:
            return ExpansionResult(
                expanded_terms_ranked=list(expanded),
                per_term_hit_count=per_term_hit_count,
                total_queries_issued=total_queries,
                accumulated_verified=accumulated,
                outcome="success_after_expansion",
            )

    return ExpansionResult(
        expanded_terms_ranked=list(expanded),
        per_term_hit_count=per_term_hit_count,
        total_queries_issued=total_queries,
        accumulated_verified=accumulated,
        outcome="exhausted",
    )


# --- Term parsing helpers ------------------------------------------------

_LIST_LINE_RE = re.compile(
    r"""
    ^\s*                       # optional leading whitespace
    (?:
        (?:\d+|\d+\.\d+)        # 1, 1.0
        \s*[\.\)\]]\s*          # delimiter: . ) ]
      | [-*•]\s+                 # bullet: - * •
    )?
    (.*?)                       # the term itself (lazy)
    \s*$
    """,
    re.VERBOSE,
)


def _parse_ranked_terms(
    text: str, *, original_term: str
) -> list[tuple[int, str]]:
    """Extract 10-20 ranked terms from the LLM's free-form response.

    Strategy: split into lines, strip list-marker prefixes (``1.``, ``-``,
    ``*``, etc.), drop empty lines, drop the original term (case-fold
    match), drop near-duplicates. Returns ``[(rank, term), ...]`` with
    rank starting at 1.
    """
    if not text:
        return []
    lines = text.splitlines()
    out: list[str] = []
    seen_lower: set[str] = set()
    orig_lower = original_term.strip().lower()

    for raw in lines:
        m = _LIST_LINE_RE.match(raw)
        if not m:
            continue
        term = m.group(1).strip().strip("\"'`*_")
        if not term:
            continue
        # Heuristic: ignore section headers and "Step N" banners.
        low = term.lower()
        if low.startswith(("step ", "## ", "### ", "alternative phras", "expanded term")):
            continue
        # Skip lines that are mostly punctuation / formatting.
        if not re.search(r"[A-Za-z]", term):
            continue
        if low == orig_lower:
            continue
        if low in seen_lower:
            continue
        seen_lower.add(low)
        out.append(term)

    return [(i + 1, t) for i, t in enumerate(out)]


_DEFAULT_EXPANSION_PROMPT = """You are the **librarian-expansion** sub-agent.

When the librarian's initial keyword search for a research-related
term returns fewer than 5 verified citations, you generate alternative
phrasings to broaden the search.

## Task

Given:
  - the original search term (the user-supplied query)
  - the project's field (e.g., "computer science", "biology")
  - an excerpt from the project's idea body (research question + motivation)

Produce **10-20 alternative search terms** that might surface relevant
papers the original term missed. These should be:

  - **Synonyms** (e.g., "code clones" → "duplicated source code")
  - **Sub-area terms** (e.g., "transformer attention" → "scaled dot-product
    attention", "self-attention", "multi-head attention")
  - **Domain-adjacent terms** (e.g., "code duplication LLM" → "AI-generated
    code redundancy", "language model code understanding")
  - **More-specific terms** narrowing the original scope to a single aspect
  - **More-general terms** broadening the original scope

Rank by approximate relevance to the original query. Most relevant
first.

## Output format

Numbered list, one term per line. Example:

```
1. self-attention mechanisms
2. multi-head attention
3. transformer encoder layers
4. ...
```

Do NOT repeat the original term. Do NOT include explanatory prose.
Do NOT include code blocks or markdown headers.
"""


__all__ = [
    "DEFAULT_EXPANSION_CAP",
    "DEFAULT_TARGET_N",
    "ExpansionResult",
    "expand_terms",
    "iterate_until_target",
]
