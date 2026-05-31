"""Edge-case tests for the summarize/desummarize primitive (spec 015 T008, FR-004/005).

Covers the 7 enumerated edge cases plus the core no-loss invariant, using real
on-disk file I/O (no LLM: the deterministic no-loss guarantee is what matters here).
"""

from __future__ import annotations

import re

import pytest

from llmxive.tools.summarize import (
    desummarize,
    estimate_tokens,
    extract_critical,
    summarize,
)

BUDGET = 500  # tokens — small enough to force overflow on the doc below


def _doc() -> str:
    parts = ["PREMISE: every widget in the study is blue.\n\n"]
    for i in range(40):
        parts.append(
            f"## Section {i}\n"
            f"See https://example.com/path/{i}/resource and DOI 10.1234/abcd.{i:04d} "
            f"and arXiv:2401.{i:05d}.\n"
            f"Requirement FR-{i:03d} maps to task T{i:03d}; metric = {i * 3.14:.2f}% "
            f"with N={i * 100} and ratio 0.{i:03d}.\n"
            f"Citation [Smith{2000 + i}] supports this.\n\n"
        )
    parts.append("CONCLUSION: therefore this particular widget is blue.\n")
    return "".join(parts)


@pytest.fixture()
def doc() -> str:
    return _doc()


def test_overflow_produces_bounded_pointer_block(doc, tmp_path):
    """Edge 6 (output cut-off): the PROSE chunk-summaries are bounded by the
    budget, but the critical-element section is MANDATORY and complete (§3a):
    every critical element is inlined verbatim in the rendered block — not just
    on disk — even if that pushes the block past the soft budget, because
    silently dropping a URL/DOI/id is worse than overflowing the target. So the
    block is bounded by ``budget + size(critical-element list)`` (the list is
    small in practice), and every critical element is present in the block."""
    block = summarize(doc, goal="preserve every URL/DOI verbatim", token_budget=BUDGET,
                      cache_dir=tmp_path)
    assert block.startswith("[[LLMXIVE-SUMMARY v1]]")
    assert estimate_tokens(doc) > BUDGET  # sanity: the doc really did overflow
    # Every critical element appears verbatim in the rendered block itself.
    crit = list(dict.fromkeys(extract_critical(doc)))
    for c in crit:
        assert c in block, f"critical element missing from rendered block: {c!r}"
    # Prose is bounded: the only allowed overage is the mandatory critical list.
    crit_tokens = estimate_tokens("\n".join(f"- {c}" for c in crit))
    assert estimate_tokens(block) <= BUDGET + crit_tokens + 100


def test_no_critical_element_lost_roundtrip(doc, tmp_path):
    """Core no-loss invariant + edges 1/2/4/7: every critical element recovers verbatim."""
    block = summarize(doc, goal="preserve every URL/DOI/id/number verbatim",
                      token_budget=BUDGET, cache_dir=tmp_path)
    restored = desummarize(block)
    for crit in extract_critical(doc):
        assert crit in restored, f"lost critical element: {crit!r}"


def test_atomic_units_not_split(doc, tmp_path):
    """Edge 1: URLs/DOIs/arXiv ids survive as whole substrings (never cut mid-token)."""
    block = summarize(doc, goal="preserve every URL/DOI verbatim", token_budget=BUDGET,
                      cache_dir=tmp_path)
    restored = desummarize(block)
    for url in re.findall(r"https?://\S+", doc):
        assert url.rstrip(".") in restored


def test_ordering_preserved(doc, tmp_path):
    """Edge 5: ordering-sensitive content (FR ids) keeps source order after desummarize."""
    block = summarize(doc, goal="preserve every FR/SC/task id", token_budget=BUDGET,
                      cache_dir=tmp_path)
    restored = desummarize(block)
    src_order = re.findall(r"FR-\d{3}", doc)
    got_order = re.findall(r"FR-\d{3}", restored)
    assert got_order == src_order


def test_cross_chunk_logic_chain_preserved(doc, tmp_path):
    """Edge 3: premise (start) and conclusion (end) both survive across chunks."""
    block = summarize(doc, goal="preserve the full argument chain", token_budget=BUDGET,
                      cache_dir=tmp_path)
    restored = desummarize(block)
    assert "PREMISE: every widget in the study is blue." in restored
    assert "CONCLUSION: therefore this particular widget is blue." in restored


def test_quantitative_claims_verbatim(tmp_path):
    """Edge 4: numbers survive verbatim (no rounding/dropping)."""
    body = "filler line\n" * 4000
    doc = f"The measured value was 3.14159 and the cohort had N=12345 subjects.\n{body}"
    block = summarize(doc, goal="preserve all numeric results verbatim", token_budget=BUDGET,
                      cache_dir=tmp_path)
    restored = desummarize(block)
    assert "3.14159" in restored
    assert "12345" in restored


def test_recursion_loss_long_single_line(tmp_path):
    """Edge 7: a single line far larger than the budget still preserves its criticals."""
    long_line = ("data " * 8000) + " https://example.com/deep/link DOI 10.9999/zzz.0001\n"
    doc = "## Head\nintro\n\n" + long_line + "\n## Tail\nFR-042 T042\n"
    block = summarize(doc, goal="preserve every URL/DOI/id verbatim", token_budget=BUDGET,
                      cache_dir=tmp_path)
    restored = desummarize(block)
    assert "https://example.com/deep/link" in restored
    assert "10.9999/zzz.0001" in restored
    assert "FR-042" in restored


def test_under_budget_returns_verbatim(tmp_path):
    """Content that fits is returned unchanged; desummarize is a no-op on plain text."""
    small = "Just a short note with FR-001 and https://x.test/a.\n"
    out = summarize(small, goal="preserve every URL", token_budget=BUDGET, cache_dir=tmp_path)
    assert out == small
    assert desummarize(out) == small


def test_want_filter_pages_in_subset(doc, tmp_path):
    """desummarize(..., want=[...]) returns content matching the requested element."""
    block = summarize(doc, goal="preserve every FR/SC/task id", token_budget=BUDGET,
                      cache_dir=tmp_path)
    subset = desummarize(block, want=["FR-007"])
    assert "FR-007" in subset
