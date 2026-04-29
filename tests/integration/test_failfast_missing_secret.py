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
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], tmp_path
) -> None:
    """preflight.main() must return 1 within seconds on missing key.

    Per FR-019 the credentials file is a valid alternative source; we
    point XDG_CONFIG_HOME at a fresh tmp_path so neither the env nor
    the credentials file provides a key.
    """
    monkeypatch.delenv("DARTMOUTH_CHAT_API_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    # Windows fallback: APPDATA path resolution
    monkeypatch.setenv("APPDATA", str(tmp_path))

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
