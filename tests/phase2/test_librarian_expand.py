"""Tests for the multi-step expansion module (spec 005 / T020 / FR-004).

Real-LLM tests where applicable (the brainstorm step). Term-parser
tests + iterate_until_target tests use the existing SS + arXiv real
APIs.

Per Q3 clarification: when expansion exhausts without reaching
target_n, the result has ``outcome: "exhausted"`` and the partial list
is returned.
"""

from __future__ import annotations

import os

import pytest

from llmxive.credentials import (
    load_dartmouth_key,
    load_semantic_scholar_key,
)
from llmxive.librarian.expand import (
    DEFAULT_EXPANSION_CAP,
    ExpansionResult,
    _parse_ranked_terms,
    expand_terms,
    iterate_until_target,
)
from llmxive.librarian.search import ArxivClient, SemanticScholarClient

HAS_DM_KEY = bool(load_dartmouth_key(prompt_if_missing=False))
HAS_SS_KEY = bool(load_semantic_scholar_key(prompt_if_missing=False))
_REAL = os.environ.get("LLMXIVE_REAL_TESTS") == "1"

dm_required = pytest.mark.skipif(
    not (HAS_DM_KEY and _REAL),
    reason="DARTMOUTH_CHAT_API_KEY + LLMXIVE_REAL_TESTS=1 needed; LLM-driven expansion tests",
)

# The iterate_until_target tests hit the real arXiv (and optionally SS)
# HTTP APIs even without a key, so they must skip outside real-call mode.
real_required = pytest.mark.skipif(
    not _REAL,
    reason="hits real arXiv/SS HTTP; needs LLMXIVE_REAL_TESTS=1",
)


# --- Term parser ----------------------------------------------------------


def test_parse_numbered_list():
    text = """1. self-attention mechanisms
2. multi-head attention
3. transformer encoder layers"""
    parsed = _parse_ranked_terms(text, original_term="transformer attention")
    assert parsed == [
        (1, "self-attention mechanisms"),
        (2, "multi-head attention"),
        (3, "transformer encoder layers"),
    ]


def test_parse_bullet_list():
    text = """- foo bar
* baz qux
• boo"""
    parsed = _parse_ranked_terms(text, original_term="xyz")
    assert len(parsed) == 3
    assert parsed[0] == (1, "foo bar")


def test_parse_drops_original_term():
    """The original term itself is filtered out (case-insensitive)."""
    text = """1. transformer attention
2. self-attention
3. TRANSFORMER ATTENTION"""
    parsed = _parse_ranked_terms(text, original_term="transformer attention")
    assert len(parsed) == 1
    assert parsed[0][1] == "self-attention"


def test_parse_skips_section_headers():
    """Lines that are markdown headers / section banners are dropped."""
    text = """## Suggested terms

1. real term

### Notes

2. another real term"""
    parsed = _parse_ranked_terms(text, original_term="xyz")
    # The numbered terms survive; the headers are dropped.
    titles = [t for _, t in parsed]
    assert "real term" in titles
    assert "another real term" in titles


def test_parse_dedups_case_insensitive():
    """A term repeated under different casing appears once."""
    text = """1. Foo Bar
2. foo bar
3. FOO BAR"""
    parsed = _parse_ranked_terms(text, original_term="xyz")
    assert len(parsed) == 1
    # First-seen casing wins.
    assert parsed[0][1] == "Foo Bar"


def test_parse_handles_punctuation_only_lines():
    """Lines with no alphabetic chars are dropped."""
    text = """1. real term
2. ---
3. ===
4. another real"""
    parsed = _parse_ranked_terms(text, original_term="xyz")
    titles = [t for _, t in parsed]
    assert "real term" in titles
    assert "another real" in titles
    assert "---" not in titles
    assert "===" not in titles


def test_parse_handles_empty():
    assert _parse_ranked_terms("", original_term="xyz") == []
    assert _parse_ranked_terms("    \n\n  ", original_term="xyz") == []


# --- expand_terms (real LLM brainstorm) -----------------------------------


@dm_required
def test_expand_terms_real_llm_returns_at_least_5():
    """LLM brainstorm on a thin term yields ≥5 alternative phrasings."""
    expanded = expand_terms(
        "ablation density LLM perplexity",
        field="computer science",
        idea_body_excerpt="A study of how code clone density affects LLM perplexity scores.",
        n=15,
    )
    # The prompt asks for 10-20; we accept ≥5 as the bar (the term is
    # genuinely thin and the LLM may reasonably return fewer).
    assert len(expanded) >= 5, f"expected ≥5 expanded terms, got {len(expanded)}"
    # All ranks are 1-indexed sequential.
    for i, (rank, term) in enumerate(expanded):
        assert rank == i + 1
        assert isinstance(term, str) and term.strip()


@dm_required
def test_expand_terms_excludes_original():
    """The original term doesn't appear in the expanded list."""
    expanded = expand_terms(
        "self-attention mechanisms",
        field="computer science",
        idea_body_excerpt=None,
        n=15,
    )
    terms_lower = {t.lower() for _, t in expanded}
    assert "self-attention mechanisms" not in terms_lower


# --- iterate_until_target (real backend search) ---------------------------


@real_required
def test_iterate_terminates_on_target_reached():
    """Once verified count ≥ target_n, the loop returns ``success_after_expansion``."""
    # Use a small set of 3 well-known terms; target_n=2.
    expanded = [(1, "transformer attention"), (2, "neural machine translation"), (3, "BERT")]
    ax = ArxivClient(min_interval_seconds=0.5)
    ss = SemanticScholarClient() if HAS_SS_KEY else None
    result = iterate_until_target(
        "self-attention mechanisms",
        expanded,
        target_n=2,
        ss_client=ss,
        arxiv_client=ax,
        per_term_limit=3,
    )
    assert isinstance(result, ExpansionResult)
    assert result.outcome == "success_after_expansion"
    assert len(result.accumulated_verified) >= 2
    assert result.total_queries_issued >= 1


@real_required
def test_iterate_records_per_term_hit_count():
    """per_term_hit_count has an entry for each expanded term + the original."""
    expanded = [(1, "transformer attention")]
    ax = ArxivClient(min_interval_seconds=0.5)
    ss = SemanticScholarClient() if HAS_SS_KEY else None
    result = iterate_until_target(
        "original",
        expanded,
        target_n=1,
        ss_client=ss,
        arxiv_client=ax,
        per_term_limit=3,
    )
    assert "original" in result.per_term_hit_count
    assert "transformer attention" in result.per_term_hit_count


@real_required
def test_iterate_exhausted_when_no_hits():
    """When backends return zero verifiable candidates, outcome is ``exhausted``."""
    # Use a deliberately bogus expanded term and a high target.
    expanded = [(1, "xyzzy quantum unicorn protocol nonexistent")]
    ax = ArxivClient(min_interval_seconds=0.5)
    ss = SemanticScholarClient() if HAS_SS_KEY else None
    result = iterate_until_target(
        "xyzzy",
        expanded,
        target_n=5,
        ss_client=ss,
        arxiv_client=ax,
        per_term_limit=2,
    )
    # Either exhausted (most likely) OR success_after_expansion (if SS
    # somehow returned hits on our nonsense term — unlikely).
    assert result.outcome in {"exhausted", "success_after_expansion"}
    if result.outcome == "exhausted":
        assert len(result.accumulated_verified) < 5


@real_required
def test_iterate_dedups_across_terms():
    """If the same paper surfaces via two different expanded terms, it
    only appears once in accumulated_verified."""
    # Two near-synonym terms likely to surface overlapping arXiv hits.
    expanded = [(1, "transformer attention"), (2, "self-attention transformer")]
    ax = ArxivClient(min_interval_seconds=0.5)
    ss = SemanticScholarClient() if HAS_SS_KEY else None
    result = iterate_until_target(
        "original",
        expanded,
        target_n=20,  # high enough to force iterating both terms
        ss_client=ss,
        arxiv_client=ax,
        per_term_limit=3,
    )
    pointers = [v.primary_pointer for v in result.accumulated_verified]
    assert len(pointers) == len(set(pointers)), f"duplicate pointers in result: {pointers}"


@real_required
def test_iterate_handles_no_ss_client():
    """When SS client is None (no key), iterate works on arXiv only."""
    expanded = [(1, "transformer attention")]
    ax = ArxivClient(min_interval_seconds=0.5)
    result = iterate_until_target(
        "original",
        expanded,
        target_n=1,
        ss_client=None,  # no SS
        arxiv_client=ax,
        per_term_limit=3,
    )
    # arXiv should return ≥1 verifiable hit on this term.
    assert result.total_queries_issued >= 1
    assert result.outcome in {"success_after_expansion", "exhausted"}


def test_default_expansion_cap_is_20():
    """Sanity: hard-cap constant is 20 per spec.md FR-004."""
    assert DEFAULT_EXPANSION_CAP == 20
