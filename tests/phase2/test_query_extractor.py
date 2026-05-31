"""Tests for the concept-decomposed query extractor (spec 005 fix-up #3).

Pure-function parser tests + a real LLM smoke test gated on
DARTMOUTH_CHAT_API_KEY so CI without the key still passes.
"""

from __future__ import annotations

import os

import pytest

from llmxive.credentials import load_dartmouth_key
from llmxive.librarian.query_extractor import (
    _fallback_queries,
    _fallback_short_query,
    _parse_numbered_queries,
    extract_queries,
)

HAS_DM_KEY = bool(load_dartmouth_key(prompt_if_missing=False))
_REAL = os.environ.get("LLMXIVE_REAL_TESTS") == "1"


# --- Parser tests (no LLM) ----------------------------------------------------


def test_parse_numbered_dot_form() -> None:
    text = """1. preregistration sample size deviation
2. achieved power observed effect size
3. Type II error preregistration psychology
4. preregistered study sample size justification
5. statistical power post-hoc estimation"""
    qs = _parse_numbered_queries(text, n=5)
    assert len(qs) == 5
    assert qs[0] == "preregistration sample size deviation"
    assert qs[2] == "Type II error preregistration psychology"


def test_parse_numbered_paren_form() -> None:
    text = """1) gut microbiome cognitive aging
2) gut-brain axis dementia
3) microbiota cognition aging humans"""
    qs = _parse_numbered_queries(text, n=5)
    assert len(qs) == 3


def test_parse_dash_bullets() -> None:
    text = """- code memorization language model
- training data contamination LLM
- deduplication code corpus perplexity"""
    qs = _parse_numbered_queries(text, n=5)
    assert len(qs) == 3
    assert qs[0] == "code memorization language model"


def test_parse_rejects_full_sentences() -> None:
    """Lines with too many tokens should be filtered out — we want
    keyword queries, not full sentences."""
    text = """1. This is a very long natural-language sentence that exceeds the eight-token limit"""
    qs = _parse_numbered_queries(text, n=5)
    assert qs == []


def test_parse_rejects_too_short() -> None:
    text = """1. foo
2. cat"""
    qs = _parse_numbered_queries(text, n=5)
    # Both are 1-token; neither survives the >=2 token filter.
    assert qs == []


def test_parse_dedupe() -> None:
    text = """1. preregistration sample size
2. preregistration sample size
3. achieved power discrepancy"""
    qs = _parse_numbered_queries(text, n=5)
    assert len(qs) == 2


def test_parse_caps_at_n() -> None:
    text = "\n".join(f"{i}. token{i} word{i}" for i in range(1, 11))
    qs = _parse_numbered_queries(text, n=5)
    assert len(qs) == 5


def test_parse_empty() -> None:
    assert _parse_numbered_queries("", n=5) == []
    assert _parse_numbered_queries("   \n  \n", n=5) == []


def test_fallback_short_query_drops_stop_words() -> None:
    q = _fallback_short_query(
        "How do planned statistical power estimates compare to achieved power?",
        field="statistics",
    )
    # First 6 non-stop tokens + field appended
    assert "planned" in q
    assert "statistical" in q
    assert "power" in q
    # Stop words excluded
    assert " how " not in f" {q.lower()} "
    assert " do " not in f" {q.lower()} "
    assert q.endswith("statistics")


def test_fallback_short_query_caps_length() -> None:
    q = _fallback_short_query(
        "term " * 100, field=None,
    )
    assert len(q.split()) <= 7  # 6 tokens + maybe field


# --- _fallback_queries (multi-query degraded mode) ---------------------------


def test_fallback_queries_produces_multiple_distinct_for_long_question() -> None:
    """A long structured question yields 3 overlapping positional windows
    (head / tail / spread), each emphasizing a different region."""
    qs = _fallback_queries(
        "How does the spatial clustering of impurity atoms in the bulk "
        "lattice influence the thermodynamic driving force for their "
        "segregation to grain boundaries in polycrystalline alloys?",
        field="materials science",
    )
    assert len(qs) >= 2, f"expected ≥2 fallback queries, got {qs!r}"
    # Distinct.
    assert len(set(qs)) == len(qs)
    # HEAD query is field-anchored.
    assert qs[0].endswith("materials science")
    # HEAD emphasizes the front of the question (independent variable).
    assert "spatial" in qs[0].lower() and "clustering" in qs[0].lower()
    # Some later query reaches the dependent-variable region.
    joined = " ".join(qs).lower()
    assert "segregation" in joined
    assert "grain" in joined or "boundaries" in joined
    # Each query is short (keyword-shaped, not a sentence).
    for q in qs:
        assert len(q.split()) <= 8, f"query too long: {q!r}"


def test_fallback_queries_head_and_tail_differ() -> None:
    qs = _fallback_queries(
        "Does increased neighborhood greenspace exposure reduce cortisol "
        "levels and improve self-reported wellbeing in urban adolescents?",
        field="psychology",
    )
    assert len(qs) >= 2
    # The head query should NOT be identical to the tail query.
    assert qs[0] != qs[1]
    # Head touches the front (greenspace exposure); tail touches the
    # back (wellbeing / adolescents).
    assert "greenspace" in qs[0].lower() or "neighborhood" in qs[0].lower()


def test_fallback_queries_short_question_single_query() -> None:
    """A short question with few salient tokens degrades to a single
    query rather than padding with garbage."""
    qs = _fallback_queries("transformer attention mechanism", field=None)
    # Only ~3 salient tokens → at most one window.
    assert len(qs) == 1
    assert "transformer" in qs[0].lower()


def test_fallback_queries_empty_question() -> None:
    qs = _fallback_queries("", field=None)
    assert len(qs) == 1
    assert qs[0]  # non-empty placeholder


def test_fallback_queries_all_stop_words() -> None:
    """A question that's nothing but stop-words still returns one
    non-empty query (the truncated raw text)."""
    qs = _fallback_queries("how do the and of in to", field=None)
    assert len(qs) == 1
    assert qs[0]


# --- Real LLM smoke test ------------------------------------------------------


@pytest.mark.skipif(not (HAS_DM_KEY and _REAL), reason="extractor LLM requires DARTMOUTH_CHAT_API_KEY + LLMXIVE_REAL_TESTS=1")
def test_extract_queries_returns_short_decomposed_set() -> None:
    """End-to-end: a sentence-shaped research question gets decomposed
    into 3-5 short keyword queries, each different from the others."""
    qs = extract_queries(
        "How does the local density of syntactic code clones correlate with "
        "the perplexity and bug-detection accuracy of pre-trained language "
        "models on open-source Python code?",
        field="computer science",
    )
    assert qs, "extractor returned empty list"
    # Should produce multiple queries, each short.
    assert len(qs) >= 3
    for q in qs:
        token_count = len(q.split())
        assert 2 <= token_count <= 8, f"query out of length range: {q!r}"
    # Queries should not be identical.
    assert len(set(qs)) >= 3


@pytest.mark.skipif(not (HAS_DM_KEY and _REAL), reason="extractor LLM requires DARTMOUTH_CHAT_API_KEY + LLMXIVE_REAL_TESTS=1")
def test_extract_queries_includes_synonym_vocabulary() -> None:
    """For a question that uses 'code duplication', at least one
    query should use the canonical alternative vocabulary
    (memorization / contamination / deduplication / leakage)."""
    qs = extract_queries(
        "How does the local density of syntactic code clones correlate with "
        "the perplexity and bug-detection accuracy of pre-trained language "
        "models on open-source Python code?",
        field="computer science",
    )
    joined = " ".join(qs).lower()
    # The extractor system prompt explicitly instructs synonym variants;
    # check that AT LEAST ONE of the canonical alternative-vocabulary
    # terms appears across the query set.
    synonyms = {
        "memorization", "memorisation", "contamination", "leakage",
        "deduplication", "duplicate", "near-duplicate", "duplication",
        "data leak", "train-test", "overlap",
    }
    assert any(s in joined for s in synonyms), (
        f"extracted queries don't include any canonical alt-vocab term; got: {qs!r}"
    )
