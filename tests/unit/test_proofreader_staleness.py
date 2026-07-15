"""Proofreader verdicts are bound to the source they were computed against.

Issue #1139 D13: the recon probe (PROBE2) showed a stored "clean" verdict stayed
"clean" after the paper source was rewritten to introduce typos — presence of a
cached PASS was mistaken for a fresh verified verdict. ``proofreader_clean`` now
re-derives the CURRENT source hash and only reports clean when the stored verdict
still matches the source, the verifier version, and a freshness TTL.

These are REAL tests: they run the production store path
(``ProofreaderAgent.handle_response``) against real files on disk and read the
verdict back through the production ``proofreader_clean`` gate.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import yaml

from llmxive.agents.base import AgentContext
from llmxive.agents.proofreader import (
    PROOFREADER_VERDICT_TTL,
    PROOFREADER_VERIFIER_VERSION,
    ProofreaderAgent,
    _source_hash,
    proofreader_clean,
)
from llmxive.backends.base import ChatResponse

_CLEAN_TEX = "\\section{Introduction}\nThis is a well written paragraph.\n"


def _write_source(repo: Path, project_id: str, body: str = _CLEAN_TEX) -> Path:
    src = repo / "projects" / project_id / "paper" / "source"
    src.mkdir(parents=True, exist_ok=True)
    (src / "main.tex").write_text(body, encoding="utf-8")
    return src


def _store_clean_verdict(project_id: str) -> list[str]:
    """Run the real proofreader store path for a ``clean`` verdict.

    ``handle_response`` resolves the repo via ``LLMXIVE_REPO_ROOT`` (set by the
    caller) and does not touch ``self``, so a bare instance exercises the exact
    production store code.
    """
    ctx = AgentContext(project_id=project_id, run_id="r1", task_id="t1", inputs=[])
    resp = ChatResponse(
        text="verdict: clean\nflags: []\n", model="local", backend="local"
    )
    agent = object.__new__(ProofreaderAgent)
    return agent.handle_response(ctx, resp)


def _flags_path(repo: Path, project_id: str) -> Path:
    return (
        repo / "projects" / project_id / "paper" / ".specify" / "memory"
        / "proofreader_flags.yaml"
    )


def test_proofreader_clean_invalidated_by_source_edit(tmp_path, monkeypatch):
    """PROBE2: clean verdict -> edit source -> NOT clean (the D13 regression)."""
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    project_id = "PROJ-777-staleness"
    src = _write_source(tmp_path, project_id)

    _store_clean_verdict(project_id)
    assert proofreader_clean(project_id, repo_root=tmp_path) is True

    # Rewrite the source AFTER the clean verdict was recorded (introduce a typo).
    (src / "main.tex").write_text(
        "\\section{Introduction}\nThis is a wel written paragrpah.\n", encoding="utf-8"
    )
    assert proofreader_clean(project_id, repo_root=tmp_path) is False, (
        "a stored clean verdict must not survive a later source edit"
    )


def test_proofreader_clean_true_when_source_unchanged(tmp_path, monkeypatch):
    """The gate is not over-strict: an untouched source stays clean."""
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    project_id = "PROJ-781-fresh"
    _write_source(tmp_path, project_id)
    _store_clean_verdict(project_id)
    assert proofreader_clean(project_id, repo_root=tmp_path) is True


def test_proofreader_clean_expires_after_ttl(tmp_path, monkeypatch):
    """A clean verdict older than the TTL is stale even if the source is intact."""
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    project_id = "PROJ-778-ttl"
    _write_source(tmp_path, project_id)
    _store_clean_verdict(project_id)

    assert proofreader_clean(project_id, repo_root=tmp_path) is True
    expired = datetime.now(UTC) + PROOFREADER_VERDICT_TTL + timedelta(days=1)
    assert proofreader_clean(project_id, repo_root=tmp_path, now=expired) is False


def test_proofreader_clean_invalidated_by_verifier_bump(tmp_path):
    """A verdict produced by a different verifier version is stale."""
    project_id = "PROJ-779-verbump"
    src = _write_source(tmp_path, project_id)
    doc = {
        "verdict": "clean",
        "flags": [],
        "source_hash": _source_hash(src),
        "verifier_version": PROOFREADER_VERIFIER_VERSION + "-OLD",
        "verified_at": datetime.now(UTC).isoformat(),
    }
    path = _flags_path(tmp_path, project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=True), encoding="utf-8")
    assert proofreader_clean(project_id, repo_root=tmp_path) is False


def test_proofreader_clean_rejects_legacy_record_without_provenance(tmp_path):
    """A legacy verdict (no source hash / version / timestamp) is treated as stale,
    forcing a bounded re-proofread rather than a silent pass on existence."""
    project_id = "PROJ-780-legacy"
    _write_source(tmp_path, project_id)
    path = _flags_path(tmp_path, project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"verdict": "clean", "flags": []}, sort_keys=True),
        encoding="utf-8",
    )
    assert proofreader_clean(project_id, repo_root=tmp_path) is False


def test_proofreader_not_clean_when_flags_present(tmp_path, monkeypatch):
    """A non-empty flag list is never clean (preserved base behavior), even with a
    matching source hash."""
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))
    project_id = "PROJ-782-flagged"
    src = _write_source(tmp_path, project_id)
    doc = {
        "verdict": "clean",
        "flags": [{"location": "main.tex:1", "issue": "typo"}],
        "source_hash": _source_hash(src),
        "verifier_version": PROOFREADER_VERIFIER_VERSION,
        "verified_at": datetime.now(UTC).isoformat(),
    }
    path = _flags_path(tmp_path, project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=True), encoding="utf-8")
    assert proofreader_clean(project_id, repo_root=tmp_path) is False
