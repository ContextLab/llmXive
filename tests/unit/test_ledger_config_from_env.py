"""``ledger_config_from_env`` — the single production LedgerConfig source (spec 026
finding-3 / R5-1): remote + pinned bootstrap anchor from env, fail-closed on a
missing anchor so paid fallback stays disabled until an operator pins it."""

from __future__ import annotations

import pytest

from llmxive.model_selection.ledger_transport import (
    LEDGER_ANCHOR_ENV,
    LEDGER_REMOTE_ENV,
    LedgerConfig,
    LedgerError,
    ledger_config_from_env,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(LEDGER_REMOTE_ENV, raising=False)
    monkeypatch.delenv(LEDGER_ANCHOR_ENV, raising=False)


def test_full_config_from_env(monkeypatch):
    monkeypatch.setenv(LEDGER_REMOTE_ENV, "ledger-mirror")
    monkeypatch.setenv(LEDGER_ANCHOR_ENV, "abc123def456")
    cfg = ledger_config_from_env()
    assert cfg == LedgerConfig(remote="ledger-mirror", expected_anchor="abc123def456")


def test_remote_defaults_to_origin(monkeypatch):
    monkeypatch.setenv(LEDGER_ANCHOR_ENV, "anchor0")
    assert ledger_config_from_env().remote == "origin"


def test_remote_override_wins(monkeypatch):
    monkeypatch.setenv(LEDGER_REMOTE_ENV, "env-remote")
    monkeypatch.setenv(LEDGER_ANCHOR_ENV, "anchor0")
    assert ledger_config_from_env(remote="explicit").remote == "explicit"


def test_missing_anchor_fails_closed(monkeypatch):
    # No anchor pinned → refuse (paid fallback disabled until configured).
    with pytest.raises(LedgerError, match=LEDGER_ANCHOR_ENV):
        ledger_config_from_env()


def test_require_anchor_false_allows_missing_anchor(monkeypatch):
    cfg = ledger_config_from_env(require_anchor=False)
    assert cfg == LedgerConfig(remote="origin", expected_anchor=None)


def test_blank_anchor_is_treated_as_missing(monkeypatch):
    monkeypatch.setenv(LEDGER_ANCHOR_ENV, "   ")
    with pytest.raises(LedgerError):
        ledger_config_from_env()
