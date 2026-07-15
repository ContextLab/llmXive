"""Atomic + compare-and-swap state I/O (issue #1139 / defect D19).

Before this work only ``publication.py`` and ``revision_history.py`` wrote
state atomically (each with a duplicated private ``_atomic_write``); every
other core state store did a bare ``path.write_text(...)`` and NONE did
compare-and-swap. This suite exercises the ONE shared helper
(:mod:`llmxive.state._io`) plus every owned store's public write API with
REAL tmp files — a crash mid-write must leave the ORIGINAL intact and no
leftover temp file, a normal write must round-trip, and each store's
save/write must produce a file its own ``load`` reads back.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.state import _io
from llmxive.state._io import (
    StaleWriteError,
    atomic_write_text,
    atomic_write_text_cas,
    read_mtime_ns,
)

# ---------------------------------------------------------------------------
# (a) mid-write failure leaves the ORIGINAL intact + no leftover temp file
# ---------------------------------------------------------------------------


def test_failed_replace_preserves_original_and_leaves_no_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = tmp_path / "state.yaml"
    p.write_text("ORIGINAL", encoding="utf-8")

    def boom(src: object, dst: object) -> None:
        raise OSError("simulated crash during os.replace")

    # Patch the ``os`` reference the module actually calls through.
    monkeypatch.setattr(_io.os, "replace", boom)

    with pytest.raises(OSError, match="simulated crash"):
        atomic_write_text(p, "NEW-CONTENT-THAT-MUST-NOT-LAND")

    # Original untouched — a reader never sees a truncated file.
    assert p.read_text(encoding="utf-8") == "ORIGINAL"
    # The temp file was cleaned up (no ``.state.yaml.XXXX`` debris).
    leftovers = [
        c.name for c in tmp_path.iterdir() if c.name.startswith(".state.yaml.")
    ]
    assert leftovers == [], f"leftover temp files: {leftovers}"


def test_failed_write_on_new_path_creates_no_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    p = tmp_path / "sub" / "brand-new.json"

    def boom(src: object, dst: object) -> None:
        raise OSError("boom")

    monkeypatch.setattr(_io.os, "replace", boom)
    with pytest.raises(OSError):
        atomic_write_text(p, "payload")

    assert not p.exists()
    # No orphan temp file in the freshly-created parent dir either.
    assert [c for c in (tmp_path / "sub").iterdir()] == []


# ---------------------------------------------------------------------------
# (b) a normal write round-trips (incl. parent-dir creation + overwrite)
# ---------------------------------------------------------------------------


def test_atomic_write_roundtrips_and_creates_parents(tmp_path: Path) -> None:
    p = tmp_path / "a" / "b" / "c.txt"
    atomic_write_text(p, "hello world")
    assert p.read_text(encoding="utf-8") == "hello world"
    # Overwrite in place.
    atomic_write_text(p, "second version")
    assert p.read_text(encoding="utf-8") == "second version"


def test_cas_writes_when_token_is_current(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    atomic_write_text(p, "v1")
    atomic_write_text_cas(p, "v2", expected_mtime_ns=read_mtime_ns(p))
    assert p.read_text(encoding="utf-8") == "v2"


def test_cas_accepts_none_token_for_new_file(tmp_path: Path) -> None:
    p = tmp_path / "new.txt"  # does not exist -> read_mtime_ns would be None
    atomic_write_text_cas(p, "created", expected_mtime_ns=None)
    assert p.read_text(encoding="utf-8") == "created"


def test_cas_rejects_stale_token_and_keeps_content(tmp_path: Path) -> None:
    p = tmp_path / "x.txt"
    atomic_write_text(p, "v1")
    stale = read_mtime_ns(p)
    assert stale is not None
    # Simulate a concurrent writer bumping the mtime after our read.
    os.utime(p, ns=(stale + 1000, stale + 1000))
    with pytest.raises(StaleWriteError):
        atomic_write_text_cas(p, "v2", expected_mtime_ns=stale)
    assert p.read_text(encoding="utf-8") == "v1"  # newer state preserved


# ---------------------------------------------------------------------------
# project.py — canonical state + compare-and-swap in update()
# ---------------------------------------------------------------------------


def _make_project(project_id: str = "PROJ-001-atomic"):
    from llmxive.types import Project, Stage

    now = datetime(2026, 7, 15, 12, 0, 0, tzinfo=UTC)
    return Project(
        id=project_id,
        title="Atomic I/O test project",
        field="computer science",
        current_stage=Stage.BRAINSTORMED,
        created_at=now,
        updated_at=now,
    )


def test_project_save_load_roundtrip(tmp_path: Path) -> None:
    from llmxive.state import project as project_store

    proj = _make_project()
    project_store.save(proj, repo_root=tmp_path)
    loaded = project_store.load(proj.id, repo_root=tmp_path)
    assert loaded.id == proj.id
    assert loaded.title == proj.title


def test_project_save_cas_rejects_stale_mtime(tmp_path: Path) -> None:
    from llmxive.state import project as project_store

    proj = _make_project()
    project_store.save(proj, repo_root=tmp_path)
    path = tmp_path / "state" / "projects" / f"{proj.id}.yaml"
    stale = read_mtime_ns(path)
    assert stale is not None
    # A concurrent tick lands (bump mtime) after we captured ``stale``.
    os.utime(path, ns=(stale + 1000, stale + 1000))
    with pytest.raises(StaleWriteError):
        project_store.save(proj, repo_root=tmp_path, expected_mtime_ns=stale)


def test_project_update_merges_and_persists(tmp_path: Path) -> None:
    from llmxive.state import project as project_store

    proj = _make_project()
    project_store.save(proj, repo_root=tmp_path)
    updated = project_store.update(
        proj.id, {"title": "renamed via update"}, repo_root=tmp_path
    )
    assert updated.title == "renamed via update"
    assert project_store.load(proj.id, repo_root=tmp_path).title == "renamed via update"


def test_project_update_retries_once_on_stale_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """update() re-reads + re-applies its partial fields ONCE when the CAS
    write is rejected, so an overlapping tick cannot make it silently fail."""
    from llmxive.state import project as project_store

    proj = _make_project()
    project_store.save(proj, repo_root=tmp_path)

    calls = {"n": 0}

    def flaky_cas(path, content, *, expected_mtime_ns, encoding="utf-8"):
        calls["n"] += 1
        if calls["n"] == 1:
            raise StaleWriteError("simulated concurrent write")
        _io.atomic_write_text(path, content, encoding=encoding)

    monkeypatch.setattr(project_store, "atomic_write_text_cas", flaky_cas)
    updated = project_store.update(
        proj.id, {"title": "won-the-retry"}, repo_root=tmp_path
    )
    assert calls["n"] == 2  # first attempt stale, second succeeds
    assert updated.title == "won-the-retry"
    assert project_store.load(proj.id, repo_root=tmp_path).title == "won-the-retry"


# ---------------------------------------------------------------------------
# citations.py
# ---------------------------------------------------------------------------


def test_citations_save_load_roundtrip(tmp_path: Path) -> None:
    from llmxive.state import citations as citations_store
    from llmxive.types import Citation

    cite = Citation(
        cite_id="cite-1",
        artifact_path="projects/PROJ-001-atomic/paper/main.tex",
        artifact_hash="a" * 64,
        kind="doi",
        value="10.5281/zenodo.1",
        verification_status="pending",
    )
    citations_store.save("PROJ-001-atomic", [cite], repo_root=tmp_path)
    loaded = citations_store.load("PROJ-001-atomic", repo_root=tmp_path)
    assert len(loaded) == 1
    assert loaded[0].cite_id == "cite-1"


# ---------------------------------------------------------------------------
# claims.py
# ---------------------------------------------------------------------------


def test_claims_save_load_roundtrip(tmp_path: Path) -> None:
    from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
    from llmxive.state import claims as claims_store

    claim = Claim(
        claim_id="claim-1",
        kind=ClaimKind.NUMERIC,
        raw_text="the accuracy was 0.9",
        canonical="accuracy = 0.9",
        context="results section",
        artifact_path="projects/PROJ-001-atomic/paper/main.tex",
        source_type="computed",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-07-15T00:00:00Z",
    )
    claims_store.save("PROJ-001-atomic", [claim], repo_root=tmp_path)
    loaded = claims_store.load("PROJ-001-atomic", repo_root=tmp_path)
    assert len(loaded) == 1
    assert loaded[0].claim_id == "claim-1"


# ---------------------------------------------------------------------------
# results.py
# ---------------------------------------------------------------------------


def test_results_save_load_roundtrip(tmp_path: Path) -> None:
    import hashlib

    from llmxive.results.receipt import Receipt
    from llmxive.state import results as results_store

    receipt = Receipt(
        result_id="r_atomic01",
        value="42.0",
        kind="scalar",
        producer={"script_path": "code/run.py", "code_sha": "abc",
                  "entrypoint": "main", "seed": 0},
        inputs={"dataset_id": "ds", "data_sha256": "deadbeef", "params": {}},
        env_sha="env_sha",
        captured={"stdout_path": "out.txt", "return_repr": "42.0"},
        output_sha256=hashlib.sha256(b"42.0").hexdigest(),
        created_at="2026-07-15T00:00:00Z",
        hmac="placeholder",
    )
    results_store.save("PROJ-001-atomic", receipt, repo_root=tmp_path)
    loaded = results_store.load("PROJ-001-atomic", "r_atomic01", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.result_id == "r_atomic01"
    assert loaded.value == "42.0"


# ---------------------------------------------------------------------------
# reviews.py
# ---------------------------------------------------------------------------


def test_reviews_write_read_roundtrip(tmp_path: Path) -> None:
    from llmxive.state import reviews as reviews_store
    from llmxive.types import BackendName, ReviewerKind, ReviewRecord

    record = ReviewRecord(
        reviewer_name="paper_reviewer_jargon_police",
        reviewer_kind=ReviewerKind.LLM,
        artifact_path="projects/PROJ-001-atomic/paper/metadata.json",
        artifact_hash="a" * 64,
        score=0.5,
        verdict="accept",
        feedback="looks good",
        reviewed_at=datetime(2026, 7, 15, tzinfo=UTC),
        prompt_version="1.1.0",
        model_name="qwen.qwen3.5-122b",
        backend=BackendName.DARTMOUTH,
        action_items=[],
    )
    path = reviews_store.write(
        record,
        body="Detailed review body.",
        stage="paper",
        review_type="paper_review",
        produced_by_agent=None,
        repo_root=tmp_path,
    )
    back = reviews_store.read(path)
    assert back.reviewer_name == "paper_reviewer_jargon_police"
    assert back.verdict == "accept"


# ---------------------------------------------------------------------------
# paper_status.py
# ---------------------------------------------------------------------------


def test_paper_status_save_load_roundtrip(tmp_path: Path) -> None:
    from llmxive.state import paper_status

    rec = paper_status.record_compile_result(
        "PROJ-001-atomic",
        {"ok": True, "strategy": "llmxive-compile",
         "pdf": "main-llmxive.pdf", "errors": []},
        repo_root=tmp_path,
    )
    assert rec["status"] == paper_status.STATUS_RESTYLED_UNAUDITED
    loaded = paper_status.load("PROJ-001-atomic", repo_root=tmp_path)
    assert loaded is not None
    assert loaded["pdf"] == "main-llmxive.pdf"


# ---------------------------------------------------------------------------
# escalations.py
# ---------------------------------------------------------------------------


def test_escalations_write_list_roundtrip(tmp_path: Path) -> None:
    from llmxive.state import escalations

    escalations.write_record(
        escalations.EscalationRecord(
            project_id="PROJ-001-atomic", stage="plan",
            loop="convergence-kickback", bound=3, rounds_used=3,
        ),
        repo_root=tmp_path,
    )
    records = escalations.list_records(repo_root=tmp_path)
    assert len(records) == 1
    assert records[0].project_id == "PROJ-001-atomic"


# ---------------------------------------------------------------------------
# runlog.py — the invalid-entry dump is the atomic full-file write; the
# happy-path append round-trips through the public reader.
# ---------------------------------------------------------------------------


def test_runlog_append_read_roundtrip(tmp_path: Path) -> None:
    from llmxive.state import runlog
    from llmxive.types import BackendName, Outcome, RunLogEntry

    entry = RunLogEntry(
        run_id="run-atomic-1",
        entry_id="entry-1",
        agent_name="tasker",
        project_id="PROJ-001-atomic",
        task_id="task-1",
        inputs=[],
        outputs=["projects/PROJ-001-atomic/specs/001-f/tasks.md"],
        backend=BackendName.DARTMOUTH,
        model_name="qwen.qwen3.5-122b",
        prompt_version="1.0.0",
        started_at=datetime(2026, 7, 15, tzinfo=UTC),
        ended_at=datetime(2026, 7, 15, tzinfo=UTC),
        outcome=Outcome.SUCCESS,
        cost_estimate_usd=0.0,
    )
    runlog.append_entry(entry, repo_root=tmp_path)
    back = runlog.read_entries("run-atomic-1", repo_root=tmp_path)
    assert len(back) == 1
    assert back[0].agent_name == "tasker"


# ---------------------------------------------------------------------------
# publication.py — private _atomic_write deleted; now routes through shared.
# ---------------------------------------------------------------------------


def test_publication_save_load_roundtrip(tmp_path: Path) -> None:
    from llmxive.state import publication as pub_state
    from llmxive.types import AuthorEntry, DOIVersion, Publication

    now = datetime(2026, 7, 15, 10, 30, 0, tzinfo=UTC)
    pub = Publication(
        project_id="PROJ-001-atomic",
        title="A Paper",
        volume="26",
        issue="07",
        display_volume_issue="26.07",
        doi="10.5281/zenodo.13456789",
        doi_url="https://doi.org/10.5281/zenodo.13456789",
        concept_doi=None,
        doi_versions=[
            DOIVersion(doi="10.5281/zenodo.13456789", version_index=1,
                       published_at=now, pdf_sha256="a" * 64),
        ],
        zenodo_id=13456789,
        zenodo_environment="production",
        citation_string="Alice. 2026. *A Paper*. llmXive **26.07**.",
        authors_at_publication=[AuthorEntry(name="Alice", kind="human")],
        accepted_at=now,
        published_at=now,
        review_summary={"num_reviewers": 13, "num_revision_rounds": 1,
                        "num_action_items_addressed": 5, "num_action_items_failed": 0},
    )
    pub_state.save("PROJ-001-atomic", pub, repo_root=tmp_path)
    loaded = pub_state.load("PROJ-001-atomic", repo_root=tmp_path)
    assert loaded is not None
    assert loaded.doi == pub.doi
    # The metadata.json mirror was written atomically too.
    meta = tmp_path / "projects" / "PROJ-001-atomic" / "paper" / "metadata.json"
    assert meta.is_file()


# ---------------------------------------------------------------------------
# revision_history.py — private _atomic_write deleted; now routes through shared.
# ---------------------------------------------------------------------------


def test_revision_history_append_load_roundtrip(tmp_path: Path) -> None:
    from llmxive.state import revision_history as rh
    from llmxive.types import RevisionRound

    now = datetime(2026, 7, 15, 10, 14, 0, tzinfo=UTC)
    rnd = RevisionRound(
        round_number=1,
        ran_at=now,
        implementer_agent="llmXive-implementer-v1.0",
        canonical_identity=f"llmXive-implementer-v1.0 (m on b, {now:%Y-%m-%d})",
        tasks_done=5,
        tasks_failed=0,
        tasks_skipped=0,
        resulting_pdf_sha256="a" * 64,
        implementer_log_path=(
            "specs/auto-revisions/PROJ-001-atomic/round-1/implementer-log.yaml"
        ),
        task_outcomes=[],
    )
    rh.append_round("PROJ-001-atomic", rnd, repo_root=tmp_path)
    hist = rh.load("PROJ-001-atomic", repo_root=tmp_path)
    assert len(hist.rounds) == 1
    assert hist.rounds[0].round_number == 1
