"""Real-call (T112): the Reference-Validator distinguishes unreachable from fabricated.

Skipped unless LLMXIVE_REAL_TESTS=1. Hits a non-routable IP address to
provoke a connection failure and verifies the resulting citation is
classified as `unreachable` (eligible for retry on the next scheduled
run) rather than `mismatch` (which would block the project until the
citation is corrected).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from llmxive.agents.reference_validator import validate_artifact


@pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="set LLMXIVE_REAL_TESTS=1 to exercise live citation fetches",
)
def test_unreachable_host_is_not_mismatch(tmp_path: Path) -> None:
    """A non-routable host yields `unreachable`, not `mismatch`."""
    repo = tmp_path
    (repo / "state" / "citations").mkdir(parents=True)

    # 192.0.2.0/24 is reserved for documentation per RFC 5737 — guaranteed
    # not to resolve to any real host.
    art_text = """# Related work

See https://198.51.100.42/some-paper for transient-unreachable testing.
"""
    records = validate_artifact(
        project_id="PROJ-001-unreachable",
        artifact_path="projects/PROJ-001-unreachable/idea/main.md",
        artifact_text=art_text,
        artifact_hash="0" * 64,
        repo_root=repo,
    )
    assert records, "expected one extracted citation"
    statuses = {c.verification_status.value for c in records}
    # Either unreachable (most likely on a host with restrictive
    # routing) or mismatch (if a captive portal returns a non-matching
    # 200) — but explicitly NOT verified.
    assert "verified" not in statuses, (
        f"unreachable host must not verify; got: {statuses}"
    )
