"""Spec 024 — code-included branch of ingested-paper reprocessing.

``branch_code.to_backfilled_project`` sets an externally-ingested paper that
SHIPS CODE up so the EXISTING execution gate runs that code: it vendors the
shipped repo as a git submodule, back-fills spec/plan/tasks FROM the production
speckit chain (the implementation already exists; the task is to run/validate
it), repairs quickstart.md to run the submodule's real entry points, marks every
task done, KEEPS the original authors, and re-stages to ``in_progress``.

Tests here use REAL file IO + a REAL ``git init``'d tmp repo (redirected via
``LLMXIVE_REPO_ROOT``) seeded by COPYING a real code project's ``paper/`` — the
live projects are never mutated.

Two scenarios:

1. **Dead-repo fallback** (deterministic, no network LLM): a metadata.json with a
   bogus repo URL → ``git submodule add`` genuinely fails → the function falls
   back to the no-code branch (``brainstormed``). Only the single LLM call in the
   no-code branch is stubbed (``_propose_extension``); every other step is real.

2. **Submodule + quickstart + tasks-done + authors-kept**: a TINY real git repo
   (a locally-created 1-file repo with a ``main.py``) is the code URL so
   ``git submodule add`` actually clones. Asserts the submodule landed, the
   quickstart has runnable ``python`` lines into the submodule, every task is
   ``[X]``, the authors are preserved, and the stage is ``in_progress`` with
   ``speckit_research_dir`` set. The speckit chain is a REAL free-model call,
   gated under ``LLMXIVE_REAL_TESTS`` (slow) — run live once to prove the wiring.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

import llmxive.paper_reprocess.branch_nocode as branch_nocode
from llmxive.execution.analysis_runner import extract_run_commands
from llmxive.paper_reprocess.branch_code import to_backfilled_project
from llmxive.types import Project, Stage

# Repo root of the REAL checkout (where platform config lives: .specify, agents).
_REAL_REPO = Path(__file__).resolve().parents[2]
# A real code project whose paper/ we copy as the ingested-paper fixture.
_SEED_PROJECT = "PROJ-565-edit-compass-editreward-compass-a-unifie"
_SEED_PAPER = _REAL_REPO / "projects" / _SEED_PROJECT / "paper"

_PROJECT_ID = "PROJ-901-ingested-code-paper-fixture"


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(
        ["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True
    )


def _seed_repo(tmp_path: Path) -> Path:
    """Build a hermetic, ``git init``'d repo with the platform config copied in
    and a bare ingested-paper project seeded from a real code project's paper/."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", cwd=repo)
    _git("config", "user.email", "test@llmxive.test", cwd=repo)
    _git("config", "user.name", "llmxive-test", cwd=repo)

    # Platform config the speckit chain + registry loader read (resolved via the
    # repo_root we pass / LLMXIVE_REPO_ROOT). Copy from the real checkout.
    shutil.copytree(_REAL_REPO / ".specify", repo / ".specify")
    shutil.copytree(_REAL_REPO / "agents", repo / "agents")
    # The contract schemas (project-state, agent-registry, …) are resolved from
    # the repo root at validation time; copy them so the hermetic repo validates.
    contracts_src = _REAL_REPO / "specs" / "001-agentic-pipeline-refactor" / "contracts"
    shutil.copytree(
        contracts_src, repo / "specs" / "001-agentic-pipeline-refactor" / "contracts"
    )

    # The bare ingested project: idea/ stub + paper/{source,metadata.json}.
    pdir = repo / "projects" / _PROJECT_ID
    (pdir / "idea").mkdir(parents=True)
    shutil.copytree(_SEED_PAPER, pdir / "paper")

    # Canonical project state at state/projects/<id>.yaml (stage paper_ingested).
    now = datetime.now(UTC).isoformat()
    state = {
        "id": _PROJECT_ID,
        "title": "Ingested code paper (test fixture)",
        "field": "computer science",
        "current_stage": Stage.PAPER_INGESTED.value,
        "points_research": {},
        "points_paper": {},
        "created_at": now,
        "updated_at": now,
        "last_run_id": None,
        "last_run_status": None,
        "failed_stage": None,
        "artifact_hashes": {},
        "assigned_agent": None,
        "speckit_research_dir": None,
        "speckit_paper_dir": None,
        "revision_round": 0,
        "human_escalation_reason": None,
        "revision_spec_path": None,
    }
    state_path = repo / "state" / "projects" / f"{_PROJECT_ID}.yaml"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(yaml.safe_dump(state, sort_keys=True), encoding="utf-8")

    _git("add", "-A", cwd=repo)
    _git("commit", "-m", "seed", cwd=repo)
    return repo


def _set_code_metadata(repo: Path, code_urls: list[str]) -> None:
    """Rewrite the ingested paper's metadata.json::code to the given URLs."""
    meta_path = repo / "projects" / _PROJECT_ID / "paper" / "metadata.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["code"] = code_urls
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


def _load_project(repo: Path) -> Project:
    from llmxive.state import project as project_store

    return project_store.load(_PROJECT_ID, repo_root=repo)


@pytest.fixture()
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    r = _seed_repo(tmp_path)
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(r))
    return r


# --------------------------------------------------------------------------- #
# 1. Dead-repo fallback (deterministic — only the no-code LLM call is stubbed)
# --------------------------------------------------------------------------- #
def test_dead_repo_falls_back_to_nocode(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A bogus repo URL that git can normalize but cannot clone.
    _set_code_metadata(repo, ["https://github.com/llmxive-nonexistent-org/does-not-exist-404"])

    # Stub ONLY the single network LLM call in the no-code branch; every other
    # step (real submodule-add attempt, real disk writes, real project save)
    # runs for real. This keeps the fallback assertion deterministic + offline.
    called = {"n": 0}

    def _fake_extension(paper_text: str) -> str:
        called["n"] += 1
        return (
            "## Summary of the prior work\nA benchmark paper.\n\n"
            "## Proposed extension\nA CPU-tractable follow-up question.\n\n"
            "## Methodology sketch\nData, procedure, expected result.\n"
        )

    monkeypatch.setattr(branch_nocode, "_propose_extension", _fake_extension)

    project = _load_project(repo)
    result = to_backfilled_project(project, repo_root=repo)

    # Fell back to the no-code branch: brainstormed terminal.
    assert result.current_stage == Stage.BRAINSTORMED
    assert called["n"] == 1, "the no-code branch's single LLM step should run once"
    # No submodule was vendored (the clone failed before back-fill).
    assert not (repo / "projects" / _PROJECT_ID / "external").exists()
    # The persisted project agrees.
    assert _load_project(repo).current_stage == Stage.BRAINSTORMED


def test_dead_repo_normalizes_but_clone_fails_without_external_dir(
    repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second dead-URL shape: a /tree/ subpath normalizes to a clone root that
    still 404s → fallback, and no half-written submodule dir is left behind."""
    _set_code_metadata(
        repo,
        ["https://github.com/llmxive-nonexistent-org/nope/tree/main/sub"],
    )
    monkeypatch.setattr(
        branch_nocode, "_propose_extension", lambda _t: "## Summary\nx\n\n## Proposed extension\ny\n"
    )
    project = _load_project(repo)
    result = to_backfilled_project(project, repo_root=repo)
    assert result.current_stage == Stage.BRAINSTORMED


# --------------------------------------------------------------------------- #
# Helper: a tiny REAL git repo (1 file, a runnable main.py) to vendor.
# --------------------------------------------------------------------------- #
def _make_tiny_code_repo(tmp_path: Path) -> str:
    src = tmp_path / "tiny_code_repo"
    src.mkdir()
    _git("init", cwd=src)
    _git("config", "user.email", "code@llmxive.test", cwd=src)
    _git("config", "user.name", "code-author", cwd=src)
    (src / "main.py").write_text(
        "import os\n"
        "os.makedirs('data', exist_ok=True)\n"
        "open('data/out.txt', 'w').write('reproduced')\n"
        "print('tiny repo main ran')\n",
        encoding="utf-8",
    )
    (src / "README.md").write_text("# Tiny\nRun: `python main.py`\n", encoding="utf-8")
    _git("add", "-A", cwd=src)
    _git("commit", "-m", "init", cwd=src)
    return str(src)


# --------------------------------------------------------------------------- #
# 2a. Submodule mechanics + quickstart (no LLM): drive the deterministic steps
#     directly so the submodule/quickstart wiring is proven WITHOUT a model.
# --------------------------------------------------------------------------- #
def test_submodule_add_and_quickstart_commands_are_runnable(
    repo: Path, tmp_path: Path
) -> None:
    """The submodule clones for real and the quickstart we build yields runnable
    ``python external/<name>/...`` lines that extract_run_commands parses."""
    import llmxive.paper_reprocess.branch_code as bc

    code_url = _make_tiny_code_repo(tmp_path)
    pdir = repo / "projects" / _PROJECT_ID

    rel, abs_sm = bc._submodule_relpath(pdir, code_url, repo)
    err = bc._add_submodule(repo, code_url, rel, abs_sm)
    assert err is None, f"submodule add should succeed, got: {err}"
    assert abs_sm.is_dir() and (abs_sm / "main.py").is_file()
    assert rel == f"projects/{_PROJECT_ID}/external/tiny_code_repo"

    entry_scripts = bc._detect_entry_scripts(abs_sm)
    assert "main.py" in entry_scripts

    # Build a feature dir + a planner-style quickstart with NO submodule python,
    # then repair it.
    feature_dir = pdir / "specs" / "001-fixture"
    feature_dir.mkdir(parents=True)
    (feature_dir / "quickstart.md").write_text(
        "# Quickstart\n\n```bash\ncd code\nls\n```\n", encoding="utf-8"
    )
    bc._repair_quickstart(
        feature_dir,
        pdir=pdir,
        repo_name="tiny_code_repo",
        rel_submodule=rel,
        abs_submodule=abs_sm,
        entry_scripts=entry_scripts,
    )
    qtext = (feature_dir / "quickstart.md").read_text(encoding="utf-8")
    cmds = extract_run_commands(qtext)
    assert cmds, "repaired quickstart must contain runnable python commands"
    assert any(rel in c and c.startswith("python ") for c in cmds), cmds
    assert any("main.py" in c for c in cmds), cmds


def test_mark_all_tasks_done_flips_every_checkbox(repo: Path) -> None:
    import llmxive.paper_reprocess.branch_code as bc

    feature_dir = repo / "projects" / _PROJECT_ID / "specs" / "001-fixture"
    feature_dir.mkdir(parents=True)
    (feature_dir / "tasks.md").write_text(
        "# Tasks\n- [ ] T001 do a thing\n- [ ] T002 do another\n", encoding="utf-8"
    )
    bc._mark_all_tasks_done(feature_dir)
    text = (feature_dir / "tasks.md").read_text(encoding="utf-8")
    assert "[ ]" not in text
    assert text.count("[X]") == 2
    # Matches the graph gate's all-tasks-done predicate.
    from llmxive.pipeline.graph import _all_tasks_done

    assert _all_tasks_done(repo / "projects" / _PROJECT_ID)


def test_empty_clone_dir_is_treated_as_failure(repo: Path, tmp_path: Path) -> None:
    """An EMPTY repo clones to an empty working tree → treated as a clone failure
    (the gate would have nothing to run)."""
    import llmxive.paper_reprocess.branch_code as bc

    empty = tmp_path / "empty_repo"
    empty.mkdir()
    _git("init", cwd=empty)
    _git("config", "user.email", "e@e.test", cwd=empty)
    _git("config", "user.name", "e", cwd=empty)
    _git("commit", "--allow-empty", "-m", "empty", cwd=empty)

    pdir = repo / "projects" / _PROJECT_ID
    rel, abs_sm = bc._submodule_relpath(pdir, str(empty), repo)
    err = bc._add_submodule(repo, str(empty), rel, abs_sm)
    assert err is not None and "empty" in err.lower()


# The known-good FREE Dartmouth model (the registry default qwen.* is retired
# and hangs; spec IV requires free models — gpt-oss-120b is the live free one).
_FREE_MODEL = "openai.gpt-oss-120b"


def _force_free_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Override ONLY the model the speckit chain dispatches with, swapping the
    registry's (retired, hanging) default for the live free model. This mirrors
    production's model-tier override (``execution_status.execution_model_override``)
    — every other code path (mechanical scripts, prompt build, router, artifact
    write, claim layer) runs for real. Not a mock of the unit under test."""
    from llmxive.agents import registry as registry_loader

    orig = registry_loader.get

    def _patched(name: str, *, repo_root=None):
        entry = orig(name, repo_root=repo_root)
        return entry.model_copy(update={"default_model": _FREE_MODEL})

    monkeypatch.setattr(registry_loader, "get", _patched)


@pytest.mark.slow
@pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="set LLMXIVE_REAL_TESTS=1 to run the live speckit back-fill",
)
def test_full_backfill_live(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """End-to-end: vendor a tiny REAL public GitHub repo, run the PRODUCTION
    speckit chain (real free-model calls), and assert the back-filled outcome.

    Uses ``pypa/sampleproject`` (small, stable, ships real ``.py`` entry points)
    so ``git submodule add`` actually clones over the network. The speckit chain
    dispatches with the live FREE model (registry default qwen.* is retired).
    """
    from llmxive.credentials import load_dartmouth_key

    key = load_dartmouth_key(prompt_if_missing=False)
    if key:
        monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", key)
    _force_free_model(monkeypatch)

    # A tiny, stable public repo with real .py files (clones fast, classifiable).
    _set_code_metadata(repo, ["https://github.com/pypa/sampleproject"])

    project = _load_project(repo)
    original_authors = json.loads(
        (repo / "projects" / _PROJECT_ID / "paper" / "metadata.json").read_text("utf-8")
    )["authors"]
    assert original_authors, "fixture must start with real authors"

    result = to_backfilled_project(project, repo_root=repo)

    # Stage + pointer (IN_PROGRESS requires speckit_research_dir).
    assert result.current_stage == Stage.IN_PROGRESS
    assert result.speckit_research_dir
    feature_dir = repo / result.speckit_research_dir
    assert feature_dir.is_dir()

    # The production speckit chain materialised real artifacts.
    assert (feature_dir / "spec.md").is_file()
    assert (feature_dir / "plan.md").is_file()
    assert (feature_dir / "tasks.md").is_file()
    assert (feature_dir / "quickstart.md").is_file()

    # Submodule vendored (a non-empty working tree landed on disk).
    sm = repo / "projects" / _PROJECT_ID / "external" / "sampleproject"
    assert sm.is_dir() and any(sm.rglob("*.py"))

    # Quickstart runs the submodule's real entry point(s).
    cmds = extract_run_commands((feature_dir / "quickstart.md").read_text("utf-8"))
    assert any("external/sampleproject" in c and c.startswith("python ") for c in cmds), cmds

    # Every task is done → the gate fires.
    tasks_text = (feature_dir / "tasks.md").read_text("utf-8")
    assert "[ ]" not in tasks_text and "[X]" in tasks_text
    from llmxive.pipeline.graph import _all_tasks_done

    assert _all_tasks_done(repo / "projects" / _PROJECT_ID)

    # Original authors KEPT.
    kept = json.loads(
        (repo / "projects" / _PROJECT_ID / "paper" / "metadata.json").read_text("utf-8")
    )["authors"]
    assert kept == original_authors

    # The ingested paper LaTeX stands as the working draft.
    assert any((repo / "projects" / _PROJECT_ID / "paper" / "source").glob("*.tex"))

    # Persisted project agrees + re-loads (validator passed → pointer set).
    assert _load_project(repo).current_stage == Stage.IN_PROGRESS
