"""Real guarded Git pushes survive a later interrupted step; no model calls."""
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from llmxive import cli
from llmxive.pipeline import graph, scheduler
from llmxive.pipeline.checkpoint import TickCheckpoint
from llmxive.state import project as project_store
from llmxive.types import Project, Stage

ROOT = Path(__file__).resolve().parents[2]
PID = "PROJ-901-checkpoint"


def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo, stderr=subprocess.STDOUT).decode().strip()


@pytest.fixture
def repository(tmp_path, monkeypatch):
    saved = dict(os.environ)
    repo, remote = tmp_path / "repo", tmp_path / "remote.git"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.invalid")
    for name in ["scripts/ci/commit-and-push.sh", "src/llmxive/checks/pipeline_writes.py",
                 "src/llmxive/checks/repository_layout.py"]:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
    (repo / "projects" / PID).mkdir(parents=True)
    now = datetime.now(UTC)
    project_store.save(Project(id=PID, title="test", field="test", current_stage=Stage.VALIDATED,
                               speckit_research_dir=f"projects/{PID}/specs/001-test",
                               created_at=now, updated_at=now), repo_root=repo)
    git(repo, "add", ".")
    git(repo, "commit", "-m", "initial")
    git(repo, "init", "--bare", str(remote))
    git(repo, "remote", "add", "origin", str(remote))
    git(repo, "push", "-u", "origin", "main")
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(repo))
    monkeypatch.setenv("PATH", str(Path(sys.executable).parent) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("PRE_COMMIT_ALLOW_NO_CONFIG", "1")
    monkeypatch.setenv("COMMIT_PUSH_ATTEMPTS", "1")
    monkeypatch.setenv("RUNNER_TEMP", str(tmp_path))
    monkeypatch.setenv("LLMXIVE_RUN_WALL_BUDGET_S", "2400")
    yield repo, remote
    os.environ.clear()
    os.environ.update(saved)


def args(**kw):
    return SimpleNamespace(**(dict(agent=None, stage=None, project=PID, max_tasks=10,
                                   worker=None, workers=6, checkpoint=True) | kw))


def advance(project):
    stage = Stage.PROJECT_INITIALIZED if project.current_stage == Stage.VALIDATED else Stage.SPECIFIED
    updated = project.model_copy(update={"current_stage": stage})
    project_store.save(updated)
    return updated


def test_first_tick_is_remote_before_second_tick_is_interrupted(repository, monkeypatch):
    repo, remote = repository
    calls = []

    def step(project):
        calls.append(project.id)
        if len(calls) == 2:
            persisted = git(remote, "show", f"main:state/projects/{PID}.yaml")
            assert "project_initialized" in persisted
            (repo / "projects" / PID / "partial.txt").write_text("interrupted")
            raise KeyboardInterrupt("simulated runner interruption")
        return advance(project)

    monkeypatch.setattr(graph, "run_one_step", step)
    with pytest.raises(KeyboardInterrupt):
        cli._cmd_run(args())
    assert len(calls) == 2
    assert git(remote, "rev-list", "--count", "main") == "2"
    assert "partial.txt" not in git(remote, "ls-tree", "-r", "--name-only", "main")


@pytest.mark.parametrize("no_progress", [False, True])
def test_failure_diagnostics_are_remote_before_exit(repository, monkeypatch, no_progress):
    _, remote = repository
    if no_progress:
        project = project_store.load(PID)
        project.current_stage = Stage.IN_PROGRESS
        project_store.save(project)
        monkeypatch.setattr(graph, "_incomplete_task_count", lambda *a, **kw: 3)
        monkeypatch.setattr(graph, "run_one_step", lambda p: p)
    else:
        def fail(project):
            raise RuntimeError("dead reference HTTP 404")
        monkeypatch.setattr(graph, "run_one_step", fail)
    assert cli._cmd_run(args()) == 0
    record = json.loads(git(remote, "show", f"main:state/advance_errors/{PID}.json"))
    assert record["consecutive_count"] == 1
    assert "no implementation progress" in record["last_error"] if no_progress else "404" in record["last_error"]


def test_checkpoint_failure_stops_before_next_step(repository, monkeypatch):
    repo, remote = repository
    # A real pre-receive rejection against a local remote.
    hook = remote / "hooks/pre-receive"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    calls = []
    def step(project):
        calls.append(project.id)
        return advance(project)
    monkeypatch.setattr(graph, "run_one_step", step)
    assert cli._cmd_run(args()) == 1
    assert calls == [PID]
    assert git(remote, "rev-list", "--count", "main") == "1"
    assert "project_initialized" in git(repo, "show", f"HEAD:state/projects/{PID}.yaml")


def test_opt_in_is_required_for_any_push(repository, monkeypatch):
    _, remote = repository
    monkeypatch.setattr(graph, "run_one_step", advance)
    assert cli._cmd_run(args(checkpoint=False, max_tasks=1)) == 0
    assert git(remote, "rev-list", "--count", "main") == "1"


def test_checkpoint_time_consumes_single_pass_budget(repository, monkeypatch):
    monkeypatch.setenv("LLMXIVE_RUN_WALL_BUDGET_S", "2400")
    clock = [0.0]
    monkeypatch.setattr(time, "monotonic", lambda: clock[0])
    calls = []
    def step(project):
        calls.append(project.id)
        return advance(project)
    original = TickCheckpoint.persist
    def checkpoint(self, project_id, tick):
        result = original(self, project_id, tick)
        clock[0] += 2401
        return result
    monkeypatch.setattr(graph, "run_one_step", step)
    monkeypatch.setattr(TickCheckpoint, "persist", checkpoint)
    assert cli._cmd_run(args()) == 0
    assert calls == [PID]


def test_worker_is_selected_once_and_tick_limit_is_not_reset(repository, monkeypatch):
    selections, calls = [], []
    def select(worker, workers):
        selections.append((worker, workers))
        return project_store.load(PID)
    def step(project):
        calls.append(project.id)
        # Alternate stages only to drive the existing scheduler loop ten times.
        updated = project.model_copy(update={"current_stage": (
            Stage.PROJECT_INITIALIZED if project.current_stage == Stage.VALIDATED else Stage.VALIDATED)})
        project_store.save(updated)
        return updated
    monkeypatch.setattr(scheduler, "pick_for_worker", select)
    monkeypatch.setattr(graph, "run_one_step", step)
    assert cli._cmd_run(args(worker=0, project=None)) == 0
    assert selections == [(0, 6)]
    assert calls == [PID] * 10


def test_modified_guard_is_refused_before_execution(repository):
    repo, remote = repository
    (repo / "scripts/ci/commit-and-push.sh").write_text("touch SHOULD_NOT_EXIST\n")
    assert TickCheckpoint(repo).persist(PID, 1) == 1
    assert not (repo / "SHOULD_NOT_EXIST").exists()
    assert git(remote, "rev-list", "--count", "main") == "1"


def test_platform_rebase_is_published_then_stops_before_next_step(repository, monkeypatch, tmp_path):
    _, remote = repository
    peer = tmp_path / "peer"
    git(tmp_path, "clone", "-b", "main", str(remote), str(peer))
    git(peer, "config", "user.name", "Peer")
    git(peer, "config", "user.email", "peer@example.invalid")
    (peer / "README.md").write_text("new platform revision")
    git(peer, "add", "README.md")
    git(peer, "commit", "-m", "concurrent platform change")
    git(peer, "push", "origin", "main")
    calls = []
    def step(project):
        calls.append(project.id)
        return advance(project)
    monkeypatch.setattr(graph, "run_one_step", step)
    assert cli._cmd_run(args()) == 0
    assert calls == [PID]
    assert git(remote, "show", "main:README.md") == "new platform revision"
    assert "project_initialized" in git(remote, "show", f"main:state/projects/{PID}.yaml")


def test_advance_workflow_explicitly_enables_checkpoint_with_original_budget():
    text = (ROOT / ".github/workflows/advance.yml").read_text()
    assert 'python -u -m llmxive run --checkpoint' in text
    assert 'LLMXIVE_RUN_WALL_BUDGET_S: "2400"' in text
    assert '--max-tasks "${MAX_TASKS:-10}"' in text
    assert 'group: advance-${{ matrix.worker }}' in text
    assert 'cancel-in-progress: false' in text
    assert 'if: always()' in text
    assert cli.build_parser().parse_args(["run"]).checkpoint is False


def test_conflicting_checkpoint_keeps_remote_state_and_recovery_patch(repository, monkeypatch, tmp_path):
    repo, remote = repository
    peer = tmp_path / "peer"
    git(tmp_path, "clone", "-b", "main", str(remote), str(peer))
    git(peer, "config", "user.name", "Peer")
    git(peer, "config", "user.email", "peer@example.invalid")
    newer = project_store.load(PID, repo_root=peer)
    newer.current_stage = Stage.TASKED
    project_store.save(newer, repo_root=peer)
    git(peer, "add", "state")
    git(peer, "commit", "-m", "concurrent project progress")
    git(peer, "push", "origin", "main")
    calls = []
    def step(project):
        calls.append(project.id)
        return advance(project)
    monkeypatch.setattr(graph, "run_one_step", step)
    assert cli._cmd_run(args()) == 1
    assert calls == [PID]
    assert "current_stage: tasked" in git(remote, "show", f"main:state/projects/{PID}.yaml")
    patch = tmp_path / "llmxive-unpushed.patch"
    assert patch.exists() and "project_initialized" in patch.read_text()
    assert git(repo, "diff", "--name-only", "--diff-filter=U") == ""
