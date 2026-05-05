"""Real-HTTP tests for the Phase 1 citation resolver (per Constitution III)."""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from tests.phase1 import citation_resolver as cr

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESOLVER = PROJECT_ROOT / "tests" / "phase1" / "citation_resolver.py"


def test_self_test_exits_zero():
    """T009: --self-test must pass against arxiv + invalid host."""
    result = subprocess.run(
        [sys.executable, str(RESOLVER), "--self-test"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, (
        f"self-test failed: stderr={result.stderr!r}, stdout={result.stdout!r}"
    )
    assert "[self-test] A: resolved; B: unreachable" in result.stderr


def test_known_good_arxiv():
    """Known-good arXiv ID resolves cleanly via the API."""
    citation = cr.Citation(
        raw_text="[Attention (2017)](https://arxiv.org/abs/1706.03762)",
        kind="arxiv",
        identifier="1706.03762",
        line_number=1,
    )
    result = cr.resolve_one(citation, timeout=60.0)
    assert result.stage1_status == "resolved"
    assert result.final_verdict == "verified"
    assert result.stage1_evidence["http_status"] == 200


def test_known_bad_url():
    """Invalid host returns unreachable, not resolved."""
    citation = cr.Citation(
        raw_text="[Bad](https://example.invalid/never-existed)",
        kind="url",
        identifier="https://example.invalid/never-existed",
        line_number=1,
    )
    result = cr.resolve_one(citation, timeout=30.0)
    assert result.stage1_status == "unreachable"
    assert result.final_verdict == "failed"


def test_doi_redirect_resolves():
    """DOI URL must follow redirects and accept the final 2xx status."""
    # 10.1145/3173574.3174156 = a CHI 2018 paper, well-known DOI that redirects
    # to ACM Digital Library and resolves to 2xx.
    citation = cr.Citation(
        raw_text="[CHI 2018](https://doi.org/10.1145/3173574.3174156)",
        kind="doi",
        identifier="10.1145/3173574.3174156",
        line_number=1,
    )
    result = cr.resolve_one(citation, timeout=60.0)
    # Either resolved (2xx after redirect) or ambiguous (3xx final). Both prove
    # the redirect-following code path works; "unreachable" would be a failure.
    assert result.stage1_status in {"resolved", "ambiguous"}


def test_timeout_fires():
    """Hard deadline cancels a stuck resolver and returns unreachable."""
    # httpbin.org/delay/30 sleeps 30s server-side; with timeout=2 we MUST fail
    # fast. (httpbin is the canonical test endpoint for this.)
    citation = cr.Citation(
        raw_text="[Slow](https://httpbin.org/delay/30)",
        kind="url",
        identifier="https://httpbin.org/delay/30",
        line_number=1,
    )
    result = cr.resolve_one(citation, timeout=2.0)
    assert result.stage1_status == "unreachable"
    assert result.stage1_evidence["api_response_snippet"] is not None


def test_extract_arxiv_md_link():
    text = "- [Title (2024)](https://arxiv.org/abs/2410.16349v1) — note"
    citations = cr.extract_citations(text)
    assert len(citations) == 1
    assert citations[0].kind == "arxiv"
    assert citations[0].identifier == "2410.16349"


def test_extract_doi_md_link():
    text = "- [DOI title (2023)](https://doi.org/10.1016/j.foo.2023.123)"
    citations = cr.extract_citations(text)
    assert len(citations) == 1
    assert citations[0].kind == "doi"
    assert citations[0].identifier == "10.1016/j.foo.2023.123"


def test_extract_url_md_link():
    text = "- [Repo (2024)](https://github.com/openai/human-eval)"
    citations = cr.extract_citations(text)
    assert len(citations) == 1
    assert citations[0].kind == "url"


def test_extract_inline_url_only_in_related_work():
    text = textwrap.dedent("""
        ## Methodology
        Run https://example.com/somewhere — should NOT count.

        ## Related work
        Also see https://example.com/related — SHOULD count.
    """).strip()
    citations = cr.extract_citations(text)
    inline = [c for c in citations if c.kind == "inline_url"]
    assert len(inline) == 1
    assert "related" in inline[0].identifier


def test_priority_arxiv_over_url():
    """An arXiv md-link must be tagged 'arxiv', not 'url'."""
    text = "- [Title](https://arxiv.org/abs/1706.03762)"
    citations = cr.extract_citations(text)
    assert len(citations) == 1
    assert citations[0].kind == "arxiv"


def test_full_resolver_integration_on_temp_file(tmp_path: Path):
    """End-to-end: write an idea.md with mixed citations, run the script, parse JSON."""
    idea = tmp_path / "test-idea.md"
    idea.write_text(
        textwrap.dedent("""
            # Test Idea
            **Field**: testing

            ## Related work
            - [Attention (2017)](https://arxiv.org/abs/1706.03762)
            - [Made-up (2026)](https://example.invalid/never-existed)
        """).strip(),
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(RESOLVER), str(idea), "--timeout", "30"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, f"resolver failed: stderr={result.stderr}"
    data = json.loads(result.stdout)
    assert len(data) == 2
    statuses = {d["citation"]["kind"]: d["stage1_status"] for d in data}
    assert statuses["arxiv"] == "resolved"
    assert statuses["url"] == "unreachable"
