"""Real repository regression coverage for revision persistence and compatibility."""
import importlib
import subprocess

import pytest

from llmxive.checks.pipeline_writes import unexpected_writes
from llmxive.convergence.revision_adapter import kickback_to_revision_spec, next_round_number
from llmxive.convergence.types import Concern, KickbackRecord, Severity
from llmxive.state.revision_paths import (
    archive_revision_cycle,
    project_control_dir,
    resolve_revision_path,
    revision_round,
)

PID = "PROJ-777-local-revisions"


def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, text=True)


def test_revision_and_reset_outputs_fit_real_research_guard(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "-c", "user.name=Test", "-c", "user.email=test@example.org", "commit", "--allow-empty", "-qm", "base")
    concern = Concern(id="aabbccddeeff", reviewer="paper_reviewer", severity=Severity.WRITING,
                      artifact=f"projects/{PID}/paper/source/main.tex", location="", text="Fix typo", round=1)
    kickback = KickbackRecord(from_stage="paper_review", to_stage="paper_tasked",
                            worst_severity=Severity.WRITING, unresolved_concerns=[concern],
                            artifact_links=[], reason="test")
    first = kickback_to_revision_spec(kickback, project_id=PID, repo_root=tmp_path)
    original = {p.name: p.read_bytes() for p in first.iterdir()}
    assert first == revision_round(tmp_path, PID, 1)
    assert unexpected_writes(tmp_path) == []
    archive = archive_revision_cycle(tmp_path, PID)
    assert {p.name: p.read_bytes() for p in (archive / "auto-revisions" / "round-1").iterdir()} == original
    assert next_round_number(tmp_path, PID) == 1
    assert unexpected_writes(tmp_path) == []
    assert kickback_to_revision_spec(kickback, project_id=PID, repo_root=tmp_path).name == "round-1"
    assert next_round_number(tmp_path, PID) == 2


def test_historical_pointers_prefer_migrated_files_without_rewriting_bytes(tmp_path):
    old = f"specs/auto-revisions/{PID}/round-4/tasks.md"
    legacy = tmp_path / old
    legacy.parent.mkdir(parents=True)
    legacy.write_bytes(b"historical task\n")
    assert resolve_revision_path(tmp_path, PID, old) == legacy
    canonical = revision_round(tmp_path, PID, 4) / "tasks.md"
    canonical.parent.mkdir(parents=True)
    legacy.rename(canonical)
    assert resolve_revision_path(tmp_path, PID, old) == canonical
    assert canonical.read_bytes() == b"historical task\n"
    assert next_round_number(tmp_path, PID) == 5


def test_reset_does_not_resurrect_legacy_round_budget_or_modify_legacy(tmp_path):
    old = tmp_path / "specs" / "auto-revisions" / PID / "round-7" / "tasks.md"
    old.parent.mkdir(parents=True)
    old.write_bytes(b"legacy provenance\n")
    assert next_round_number(tmp_path, PID) == 8
    archive = archive_revision_cycle(tmp_path, PID)
    assert old.read_bytes() == b"legacy provenance\n"
    assert (archive / "legacy-auto-revisions" / "round-7" / "tasks.md").read_bytes() == old.read_bytes()
    assert next_round_number(tmp_path, PID) == 1
    assert not resolve_revision_path(tmp_path, PID, str(old.relative_to(tmp_path))).exists()


@pytest.mark.parametrize("relative", ["../outside", "/tmp/outside", "specs/auto-revisions/PROJ-other/round-1", f"specs/auto-revisions/{PID}/../../outside"])
def test_pointer_cannot_read_another_project_or_platform(tmp_path, relative):
    with pytest.raises(ValueError):
        resolve_revision_path(tmp_path, PID, relative)


def test_project_and_round_symlinks_cannot_escape(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "projects" / PID
    root.mkdir(parents=True)
    (root / ".specify").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        project_control_dir(tmp_path, PID)
    (root / ".specify").unlink()
    base = revision_round(tmp_path, PID, 1).parent
    base.mkdir(parents=True)
    (base / "round-1").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        revision_round(tmp_path, PID, 1)


@pytest.mark.parametrize("module, cls", [
    ("flesh_out_reviser", "FleshOutReviser"), ("spec_reviser", "SpecReviser"),
    ("plan_reviser", "PlanReviser"), ("tasks_reviser", "TasksReviser"),
    ("implementer_reviser", "ImplementerReviser"),
    ("paper_spec_reviser", "PaperSpecReviser"), ("paper_implement_reviser", "PaperImplementReviser"),
])
def test_all_reviser_default_cache_writes_are_project_owned(tmp_path, module, cls):
    reviser_class = getattr(importlib.import_module(f"llmxive.convergence.revisers.{module}"), cls)
    reviser = reviser_class(backend=object(), repo_root=tmp_path, project_id=PID)
    assert reviser._summarize_cache_dir == tmp_path / "projects" / PID / ".specify" / "summarize_cache"


def test_real_overflow_cache_preserves_full_source_inside_project(tmp_path):
    from llmxive.convergence.engine import _maybe_reduce
    from llmxive.tools.summarize import desummarize

    git(tmp_path, "init", "-q")
    git(tmp_path, "-c", "user.name=Test", "-c", "user.email=test@example.org", "commit", "--allow-empty", "-qm", "base")
    cache = project_control_dir(tmp_path, PID) / "summarize_cache"
    source = "Scientifically important source evidence.\n" * 2000
    reduced = _maybe_reduce({"document": source}, goal="retain evidence", model="test", budget=1000, cache_dir=cache)
    assert reduced["document"] != source
    assert list(cache.glob("*/manifest.json"))
    # Expansion adds a separator between lossless chunks. Every source token
    # remains present, in order and with its original multiplicity.
    assert desummarize(reduced["document"]).split() == source.split()
    assert unexpected_writes(tmp_path) == []


def test_repository_symlink_alias_preserves_relative_pointer_contract(tmp_path):
    repo = tmp_path / "real"
    repo.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(repo, target_is_directory=True)
    first = revision_round(alias, PID, 1)
    first.mkdir(parents=True)
    (first / "tasks.md").write_text("preserved")
    assert first.relative_to(alias).as_posix() == f"projects/{PID}/.specify/auto-revisions/round-1"
    archive = archive_revision_cycle(alias, PID)
    assert (archive / "auto-revisions" / "round-1" / "tasks.md").read_text() == "preserved"


@pytest.mark.parametrize("escape", ["archive", "legacy", "nested_legacy", "nested_canonical", "paper", "counter"])
def test_archive_preflight_refuses_symlinks_without_moving_any_source(tmp_path, escape):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "evidence").write_text("do not import or move")
    canonical = revision_round(repo, PID, 2)
    canonical.mkdir(parents=True)
    tasks = canonical / "tasks.md"
    tasks.write_text("preserve current cycle")
    control = project_control_dir(repo, PID)
    legacy = repo / "specs" / "auto-revisions" / PID
    legacy.parent.mkdir(parents=True)
    if escape == "archive":
        (control / "revision-archives").symlink_to(outside, target_is_directory=True)
    elif escape == "legacy":
        legacy.symlink_to(outside, target_is_directory=True)
    elif escape == "nested_legacy":
        legacy.mkdir()
        (legacy / "round-1").symlink_to(outside, target_is_directory=True)
    elif escape == "nested_canonical":
        (canonical / "external.txt").symlink_to(outside / "evidence")
    elif escape == "paper":
        (repo / "projects" / PID / "paper").symlink_to(outside, target_is_directory=True)
    else:
        (repo / "state").mkdir()
        (repo / "state" / f"{PID}.implementer.yaml").symlink_to(outside / "evidence")
    with pytest.raises(ValueError):
        archive_revision_cycle(repo, PID)
    assert tasks.read_text() == "preserve current cycle"
    assert sorted(p.name for p in outside.iterdir()) == ["evidence"]
    assert not (control / "auto-revisions" / ".legacy-retired").exists()


def test_legacy_symlink_cannot_authorize_an_external_pointer(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    legacy = tmp_path / "specs" / "auto-revisions" / PID
    legacy.parent.mkdir(parents=True)
    legacy.symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError):
        resolve_revision_path(tmp_path, PID, f"specs/auto-revisions/{PID}/tasks.md")


def test_project_runner_passes_owned_cache_to_real_overflow_engine(tmp_path, monkeypatch):
    import llmxive.tools.summarize as summary_module
    from llmxive.convergence.project_runner import run_engine_for_project
    from llmxive.convergence.types import ReviewSpec

    monkeypatch.setattr(summary_module, "_usable_budget", lambda model, budget: 1000)
    source = "Project-specific evidence line.\n" * 2000
    document = tmp_path / "projects" / PID / "docs" / "research.md"
    document.parent.mkdir(parents=True)
    document.write_text(source)
    key = document.relative_to(tmp_path).as_posix()

    class Reviewer:
        name = "test"

        def identify(self, artifacts, **kwargs):
            assert summary_module.desummarize(artifacts[key]).split() == source.split()
            return []

    spec = ReviewSpec(stage="test", artifacts=[key], reviewers=[Reviewer()], reviser=None,
                      kickback_routing={}, overflow_goal="preserve evidence")
    run_engine_for_project(spec=spec, artifact_paths={key: document}, repo_root=tmp_path)
    assert list((project_control_dir(tmp_path, PID) / "summarize_cache").glob("*/manifest.json"))
    assert document.read_text() == source
    assert not (tmp_path / ".summaries").exists()
    assert not (tmp_path / "state").exists()


def test_dashboard_legacy_history_link_resolves_to_migrated_log(tmp_path):
    import yaml

    from llmxive.web_data import _project_revision_history

    old = f"specs/auto-revisions/{PID}/round-1/implementer-log.yaml"
    log = revision_round(tmp_path, PID, 1) / "implementer-log.yaml"
    log.parent.mkdir(parents=True)
    log.write_text("historical log bytes")
    history = tmp_path / "projects" / PID / "paper" / "revision_history.yaml"
    history.parent.mkdir()
    original = yaml.safe_dump({"rounds": [{"round_number": 1, "implementer_log_path": old}]})
    history.write_text(original)
    rows = _project_revision_history(tmp_path, PID)
    assert rows[0]["changelog_url"].endswith(log.relative_to(tmp_path).as_posix())
    assert history.read_text() == original
