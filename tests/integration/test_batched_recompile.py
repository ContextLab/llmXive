"""Integration tests for the FR-048 batched-recompile orchestrator +
its cron auto-trigger (spec 015, issue #239).

Real on-disk fixtures only — no mocks. The ONLY simulated boundary is
the Zenodo network mint, which is replaced by a real in-memory recording
stub (a plain callable that appends to a list); the FR-054 sign-off gate
logic itself is exercised for real via
:mod:`llmxive.speckit._publication_signoff`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from llmxive.agents import status_reporter
from llmxive.agents.living_document import (
    ingest_comment,
    pending_recompile_count,
    project_memory_dir,
    project_paper_source_dir,
    render_discussion_section,
    run_batched_recompile,
)
from llmxive.speckit._publication_signoff import write_signoff
from llmxive.state import project as project_store
from llmxive.types import Project, Stage

# A realistic on-topic comment that passes triage (matches the existing
# test_living_document.py fixture style).
_ON_TOPIC = (
    "Reading the paper, I notice the figure_critic lens applies: Figure 2's "
    "caption omits the sample size N=120. The statistical_analysis section "
    "in `paper/source/results.tex` could clarify whether the regression was "
    "OLS or ridge. Otherwise a solid contribution to the claim_accuracy story."
)
_ON_TOPIC_2 = (
    "A follow-up: the writing_quality lens flags an unclear sentence about "
    "the data_quality of the sample, and the figure_critic lens would also "
    "flag Figure 6's missing confidence interval in the results.tex source."
)


def _project(tmp_path: Path, project_id: str = "PROJ-001-test") -> Path:
    p = tmp_path / "projects" / project_id
    p.mkdir(parents=True)
    return p


def _seed_paper_source(project_dir: Path) -> Path:
    """Write a minimal compilable primary tex under paper/source/main.tex."""
    src = project_paper_source_dir(project_dir)
    src.mkdir(parents=True, exist_ok=True)
    main = src / "main.tex"
    main.write_text(
        "\\documentclass{article}\n"
        "\\begin{document}\n"
        "Body text.\n"
        "\\end{document}\n",
        encoding="utf-8",
    )
    return main


class _RecordingMint:
    """Real in-memory stub for the Zenodo version-DOI mint boundary.

    Records each invocation's kwargs so a test can assert the mint path
    was (or was not) exercised. This is NOT a mock — it is a concrete
    callable with observable state."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def __call__(self, **kwargs: object) -> None:
        self.calls.append(kwargs)


# --- orchestrator -------------------------------------------------------


def test_empty_queue_is_noop(tmp_path: Path):
    project = _project(tmp_path)
    result = run_batched_recompile(project, repo_root=tmp_path)
    assert result.ran is False
    assert result.reason == "no queued comments"
    assert result.version_doi_minted is False


def test_queue_nonempty_renders_discussion_and_detects_material(tmp_path: Path):
    project = _project(tmp_path)
    main = _seed_paper_source(project)
    ingest_comment(project_dir=project, comment_text=_ON_TOPIC, author="alice")
    assert pending_recompile_count(project) == 1

    mint = _RecordingMint()
    result = run_batched_recompile(
        project, repo_root=tmp_path, mint_version_doi=mint,
    )
    assert result.ran is True
    assert result.discussion_updated is True
    assert result.material_change is True
    # Discussion include was written + wired into the primary tex.
    include = project_paper_source_dir(project) / "_llmxive_discussion.tex"
    assert include.exists()
    assert "\\section{Discussion}" in include.read_text()
    assert "\\input{_llmxive_discussion.tex}" in main.read_text()


def test_material_change_without_signoff_does_not_mint(tmp_path: Path):
    project = _project(tmp_path)
    _seed_paper_source(project)
    ingest_comment(project_dir=project, comment_text=_ON_TOPIC, author="alice")

    mint = _RecordingMint()
    result = run_batched_recompile(
        project, repo_root=tmp_path, mint_version_doi=mint,
    )
    assert result.material_change is True
    assert result.awaiting_signoff is True
    assert result.version_doi_minted is False
    assert mint.calls == []  # mint never invoked
    # Queue preserved so a later signed run can mint.
    assert pending_recompile_count(project) == 1


def test_material_change_with_signoff_invokes_mint_path(tmp_path: Path):
    project = _project(tmp_path)
    _seed_paper_source(project)
    ingest_comment(project_dir=project, comment_text=_ON_TOPIC, author="alice")
    # Real FR-054 sign-off written via the production gate.
    write_signoff(
        project_memory_dir(project),
        who="maintainer",
        what="approve living-document version DOI",
        kind="version",
    )

    mint = _RecordingMint()
    result = run_batched_recompile(
        project, repo_root=tmp_path, mint_version_doi=mint,
    )
    assert result.material_change is True
    assert result.awaiting_signoff is False
    assert result.version_doi_minted is True
    assert len(mint.calls) == 1
    assert mint.calls[0]["project_dir"] == project
    assert mint.calls[0]["repo_root"] == tmp_path
    assert "digest" in mint.calls[0]
    # Queue cleared after a successful mint.
    assert pending_recompile_count(project) == 0


def test_awaiting_signoff_then_signed_run_mints(tmp_path: Path):
    """The staged (awaiting-signoff) run preserves the queue; once the
    maintainer signs off, a re-run mints."""
    project = _project(tmp_path)
    _seed_paper_source(project)
    ingest_comment(project_dir=project, comment_text=_ON_TOPIC, author="alice")
    mint = _RecordingMint()

    first = run_batched_recompile(
        project, repo_root=tmp_path, mint_version_doi=mint,
    )
    assert first.awaiting_signoff is True
    assert mint.calls == []

    write_signoff(
        project_memory_dir(project),
        who="maintainer", what="approve version", kind="version",
    )
    second = run_batched_recompile(
        project, repo_root=tmp_path, mint_version_doi=mint,
    )
    assert second.version_doi_minted is True
    assert len(mint.calls) == 1
    assert pending_recompile_count(project) == 0


def test_non_material_recompile_clears_queue_commits_digest(tmp_path: Path):
    """A recompile whose Discussion digest is unchanged vs the previous
    publish is cosmetic: no DOI, queue cleared, digest re-committed."""
    project = _project(tmp_path)
    _seed_paper_source(project)
    ingest_comment(project_dir=project, comment_text=_ON_TOPIC, author="alice")
    # Simulate a previous publish: commit the current digest so the next
    # recompile (no new comments) is non-material.
    from llmxive.agents.living_document import commit_digest, previous_digest

    render = render_discussion_section(project)
    commit_digest(project, render.digest)
    assert previous_digest(project) == render.digest

    mint = _RecordingMint()
    result = run_batched_recompile(
        project, repo_root=tmp_path, mint_version_doi=mint,
    )
    assert result.ran is True
    assert result.material_change is False
    assert result.version_doi_minted is False
    assert mint.calls == []
    assert pending_recompile_count(project) == 0  # queue cleared
    assert previous_digest(project) == render.digest  # digest re-committed


def test_off_topic_comment_never_enqueued_so_recompile_noop(tmp_path: Path):
    """Cross-check the ingest path: an off-topic comment is not preserved,
    the queue stays at 0, and the orchestrator is a no-op."""
    project = _project(tmp_path)
    res = ingest_comment(
        project_dir=project, comment_text="lol nice", author="rando",
    )
    assert res.persisted is False
    assert pending_recompile_count(project) == 0
    result = run_batched_recompile(project, repo_root=tmp_path)
    assert result.ran is False


def test_no_primary_tex_still_detects_material(tmp_path: Path):
    """If the paper source has no \\documentclass tex yet, the render
    write is a no-op but material-change detection + staging still work."""
    project = _project(tmp_path)  # no paper/source seeded
    ingest_comment(project_dir=project, comment_text=_ON_TOPIC, author="alice")
    result = run_batched_recompile(project, repo_root=tmp_path)
    assert result.ran is True
    assert result.material_change is True
    assert result.awaiting_signoff is True


# --- cron auto-trigger --------------------------------------------------


def _make_project(repo: Path, project_id: str, stage: Stage) -> Path:
    now = datetime.now(UTC)
    kwargs: dict[str, object] = {
        "id": project_id,
        "title": project_id,
        "field": "test",
        "current_stage": stage,
        "points_research": {},
        "points_paper": {},
        "created_at": now,
        "updated_at": now,
        "artifact_hashes": {},
    }
    project_store.save(Project(**kwargs), repo_root=repo)  # type: ignore[arg-type]
    return repo / "projects" / project_id


def test_cron_recompiles_posted_skips_non_posted(tmp_path: Path):
    posted_dir = _make_project(tmp_path, "PROJ-001-posted", Stage.POSTED)
    _seed_paper_source(posted_dir)
    ingest_comment(project_dir=posted_dir, comment_text=_ON_TOPIC, author="alice")

    # A non-posted project with a queued comment must be skipped.
    other_dir = _make_project(tmp_path, "PROJ-002-active", Stage.BRAINSTORMED)
    _seed_paper_source(other_dir)
    ingest_comment(
        project_dir=other_dir, comment_text=_ON_TOPIC, author="bob",
    )

    recompiled = status_reporter.run_living_document_recompiles(repo_root=tmp_path)
    assert recompiled == ["PROJ-001-posted"]
    # Auto-trigger never mints — material change staged, queue preserved.
    assert pending_recompile_count(posted_dir) == 1
    # The non-posted project's queue is untouched.
    assert pending_recompile_count(other_dir) == 1


def test_cron_one_failing_project_does_not_break_others(tmp_path: Path, monkeypatch):
    good_dir = _make_project(tmp_path, "PROJ-001-good", Stage.POSTED)
    _seed_paper_source(good_dir)
    ingest_comment(project_dir=good_dir, comment_text=_ON_TOPIC, author="alice")

    bad_dir = _make_project(tmp_path, "PROJ-002-bad", Stage.POSTED)
    _seed_paper_source(bad_dir)
    ingest_comment(project_dir=bad_dir, comment_text=_ON_TOPIC, author="bob")

    real_run = status_reporter.living_document.run_batched_recompile

    def flaky(project_dir, **kwargs):
        if project_dir == bad_dir:
            raise RuntimeError("simulated recompile fault")
        return real_run(project_dir, **kwargs)

    monkeypatch.setattr(
        status_reporter.living_document, "run_batched_recompile", flaky,
    )
    recompiled = status_reporter.run_living_document_recompiles(repo_root=tmp_path)
    # The good project still got recompiled despite the bad one raising.
    assert "PROJ-001-good" in recompiled
    assert "PROJ-002-bad" not in recompiled


def test_cron_skips_posted_project_with_empty_queue(tmp_path: Path):
    posted_dir = _make_project(tmp_path, "PROJ-001-quiet", Stage.POSTED)
    _seed_paper_source(posted_dir)
    recompiled = status_reporter.run_living_document_recompiles(repo_root=tmp_path)
    assert recompiled == []
