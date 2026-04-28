"""Real-call (T111): the Reference-Validator blocks a fabricated citation.

Skipped unless LLMXIVE_REAL_TESTS=1. Issues real HTTP requests to
arxiv.org to verify a real citation, and to a deliberately-fabricated
URL to confirm fabrication is flagged.

Per Constitution Principle II, this test exercises the live primary-
source fetch path that the Reference-Validator depends on.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from llmxive.agents.reference_validator import has_blocking_citations, validate_artifact
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


@pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="set LLMXIVE_REAL_TESTS=1 to exercise live citation fetches",
)
def test_real_arxiv_citation_verifies(tmp_path: Path) -> None:
    """A real arXiv reference (Attention Is All You Need) verifies."""
    repo = tmp_path
    (repo / "state" / "citations").mkdir(parents=True)

    art_text = """# Methods

We follow the [Attention Is All You Need](https://arxiv.org/abs/1706.03762)
formulation for attention.
"""
    records = validate_artifact(
        project_id="PROJ-001-arxivverify",
        artifact_path="projects/PROJ-001-arxivverify/idea/main.md",
        artifact_text=art_text,
        artifact_hash="0" * 64,
        repo_root=repo,
    )
    assert records, "expected at least one extracted citation"
    matched = [c for c in records if "1706.03762" in c.value or "attention" in (c.cited_title or "").lower()]
    assert matched, f"no record for the arXiv URL: {records}"
    # The arXiv landing page's <title> contains "Attention Is All You Need"
    # so token-overlap should comfortably exceed the threshold.
    assert any(c.verification_status.value == "verified" for c in matched), (
        f"real arXiv citation should verify; got: "
        f"{[(c.cite_id, c.verification_status.value) for c in matched]}"
    )


@pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="set LLMXIVE_REAL_TESTS=1 to exercise live citation fetches",
)
def test_fabricated_citation_blocks_advancement(tmp_path: Path) -> None:
    """A 404 + title-mismatch URL is recorded as mismatch and blocks accept."""
    repo = tmp_path
    for sub in ("projects", "run-log", "locks", "citations"):
        (repo / "state" / sub).mkdir(parents=True, exist_ok=True)

    art_text = """# Methods

We extend the [Foobar Attention Mechanism (Smith et al. 2019)](https://example.com/this-page-does-not-exist-9c47b1f8)
with novel improvements.
"""
    project_id = "PROJ-002-fabrication"
    records = validate_artifact(
        project_id=project_id,
        artifact_path=f"projects/{project_id}/idea/main.md",
        artifact_text=art_text,
        artifact_hash="0" * 64,
        repo_root=repo,
    )
    assert records, "expected at least one extracted citation"
    # The example.com URL exists (200) but the page title is "Example
    # Domain", which has zero overlap with "Foobar Attention Mechanism" —
    # so the verifier classifies it as `mismatch`, not `verified`.
    assert any(c.verification_status.value == "mismatch" for c in records), (
        f"fabricated citation should be mismatch (or unreachable); got: "
        f"{[(c.cite_id, c.verification_status.value, c.fetched_title) for c in records]}"
    )

    assert has_blocking_citations(project_id, repo_root=repo), (
        "fabricated citation should make has_blocking_citations() return True"
    )
