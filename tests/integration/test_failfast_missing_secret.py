"""Integration test (T127): preflight fails fast when DARTMOUTH_CHAT_API_KEY is missing.

Ensures Constitution Principle V: a misconfigured run terminates
within seconds rather than burning the full job timeout. We test the
preflight module directly rather than spawning a workflow.
"""

from __future__ import annotations

import os
import time

import pytest


def test_preflight_fails_fast_on_missing_dartmouth_key(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """preflight.main() must return 1 within seconds on missing key."""
    # Ensure the required key is unset.
    monkeypatch.delenv("DARTMOUTH_CHAT_API_KEY", raising=False)

    from llmxive import preflight

    start = time.time()
    rc = preflight.main()
    elapsed = time.time() - start

    assert rc == 1, "preflight must return 1 when required secret is missing"
    assert elapsed < 5.0, (
        f"preflight should fail in seconds (FR-024); took {elapsed:.2f}s"
    )

    err = capsys.readouterr().err
    assert "DARTMOUTH_CHAT_API_KEY" in err, (
        "failure message must name the missing secret"
    )
