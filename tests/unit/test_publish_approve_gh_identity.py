"""Tests for the gh-identity binding on ``llmxive project publish-approve``.

The CLI now defaults ``--who`` to the active ``gh auth status``
username and persists the resolved gh identity alongside the
human-responsible field so audit reviewers see both values.

These tests cover ``resolve_gh_user()`` (the gh-auth wrapper) +
``write_signoff(..., recorded_by_gh_user=...)`` round-trip. The CLI
integration test for the end-to-end flow lives in
``tests/integration/test_audit_bugfixes.py``; this file is the
unit-level coverage.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.speckit._publication_signoff import (
    read_signoff,
    resolve_gh_user,
    write_signoff,
)

# --- write_signoff with recorded_by_gh_user --------------------------


def test_write_signoff_persists_recorded_by_gh_user(tmp_path: Path):
    p = write_signoff(
        tmp_path, who="Jeremy Manning", what="paper v1 ok",
        kind="initial", recorded_by_gh_user="jeremymanning",
    )
    data = yaml.safe_load(p.read_text())
    assert data["who"] == "Jeremy Manning"
    assert data["recorded_by_gh_user"] == "jeremymanning"


def test_write_signoff_omits_gh_user_when_not_supplied(tmp_path: Path):
    p = write_signoff(tmp_path, who="x", what="y")
    data = yaml.safe_load(p.read_text())
    assert "recorded_by_gh_user" not in data


def test_write_signoff_strips_whitespace_from_gh_user(tmp_path: Path):
    p = write_signoff(
        tmp_path, who="x", what="y",
        recorded_by_gh_user="  spaced-name  ",
    )
    data = yaml.safe_load(p.read_text())
    assert data["recorded_by_gh_user"] == "spaced-name"


def test_read_signoff_round_trips_gh_user_field(tmp_path: Path):
    write_signoff(
        tmp_path, who="alice", what="ok",
        recorded_by_gh_user="alicebot",
    )
    rec = read_signoff(tmp_path)
    assert rec is not None
    assert rec["who"] == "alice"
    assert rec["recorded_by_gh_user"] == "alicebot"


# --- resolve_gh_user -------------------------------------------------


def test_resolve_gh_user_returns_str_or_none():
    # We can't assert the value without making this test
    # environment-dependent; just confirm the contract holds.
    result = resolve_gh_user()
    assert result is None or isinstance(result, str)
    if isinstance(result, str):
        assert len(result) > 0
        # GitHub usernames are alnum + '-' only.
        assert all(c.isalnum() or c == "-" for c in result)


def test_resolve_gh_user_returns_none_when_gh_missing(monkeypatch):
    # Pretend gh isn't on PATH.
    monkeypatch.setattr(
        "shutil.which", lambda name: None if name == "gh" else "/usr/bin/" + name,
    )
    assert resolve_gh_user() is None


def test_resolve_gh_user_returns_none_when_gh_auth_fails(monkeypatch):
    import shutil
    import subprocess

    # Pretend gh exists but `gh auth status` fails.
    monkeypatch.setattr(shutil, "which", lambda name: "/fake/gh" if name == "gh" else None)

    class _FakeProc:
        returncode = 1
        stderr = "You are not logged into github.com"
        stdout = ""

    def _fake_run(*args, **kw):
        return _FakeProc()

    monkeypatch.setattr(subprocess, "run", _fake_run)
    assert resolve_gh_user() is None


def test_resolve_gh_user_parses_modern_gh_output(monkeypatch):
    """``gh auth status`` 2.x writes 'Logged in to github.com account <user>'."""
    import shutil
    import subprocess

    monkeypatch.setattr(shutil, "which", lambda name: "/fake/gh" if name == "gh" else None)

    class _FakeProc:
        returncode = 0
        stderr = (
            "github.com\n"
            "  ✓ Logged in to github.com account jeremymanning (keyring)\n"
            "  - Active account: true\n"
        )
        stdout = ""

    def _fake_run(*args, **kw):
        return _FakeProc()

    monkeypatch.setattr(subprocess, "run", _fake_run)
    assert resolve_gh_user() == "jeremymanning"


def test_resolve_gh_user_parses_legacy_gh_output(monkeypatch):
    """Pre-2.x ``gh auth status`` wrote 'Logged in to github.com as <user>'."""
    import shutil
    import subprocess

    monkeypatch.setattr(shutil, "which", lambda name: "/fake/gh" if name == "gh" else None)

    class _FakeProc:
        returncode = 0
        stderr = "✓ Logged in to github.com as alice (oauth_token)"
        stdout = ""

    def _fake_run(*args, **kw):
        return _FakeProc()

    monkeypatch.setattr(subprocess, "run", _fake_run)
    assert resolve_gh_user() == "alice"


def test_resolve_gh_user_returns_none_on_unparseable_output(monkeypatch):
    import shutil
    import subprocess

    monkeypatch.setattr(shutil, "which", lambda name: "/fake/gh" if name == "gh" else None)

    class _FakeProc:
        returncode = 0
        stderr = "garbage that doesn't match the expected format"
        stdout = ""

    def _fake_run(*args, **kw):
        return _FakeProc()

    monkeypatch.setattr(subprocess, "run", _fake_run)
    assert resolve_gh_user() is None


def test_resolve_gh_user_handles_subprocess_oserror(monkeypatch):
    import shutil
    import subprocess

    monkeypatch.setattr(shutil, "which", lambda name: "/fake/gh" if name == "gh" else None)

    def _boom(*args, **kw):
        raise OSError("permission denied")

    monkeypatch.setattr(subprocess, "run", _boom)
    assert resolve_gh_user() is None
