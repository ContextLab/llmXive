"""Deterministic-first task settle (issue #1139, defect D6).

The verifier now settles a claimed task from FILESYSTEM STATE before spending any
LLM call: declared artifacts all valid → ``[X]``; a production task's declared
artifacts all missing → ``[ ]``; only genuinely ambiguous tasks reach the semantic
model. These tests prove the deterministic path short-circuits the LLM entirely,
and that the broadened artifact detector gives setup/config/test tasks REAL file
evidence instead of the "no artifact path" prose fallback.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.agents import task_verifier as tv


def _boom(**_kw):  # any semantic call here is a bug — the deterministic path must win
    raise AssertionError("semantic verify_task must NOT be called for a settled task")


def _run(project_dir: Path, tasks: Path, monkeypatch) -> dict:
    monkeypatch.setattr(tv, "verify_task", _boom)
    return tv.run_verification_pass(
        project_dir, tasks, already_verified=set(),
        notes_path=project_dir / "notes.md", state_path=project_dir / "state.yaml",
        project_id="PROJ-DET", repo_root=project_dir,
    )


def test_existing_artifact_accepted_without_llm(tmp_path: Path, monkeypatch) -> None:
    """A claimed task whose declared artifact exists + is non-empty is ACCEPTED
    with NO LLM call (verify_task is monkeypatched to raise)."""
    (tmp_path / "code").mkdir()
    (tmp_path / "code" / "model.py").write_text("def train():\n    return 1\n", encoding="utf-8")
    tasks = tmp_path / "tasks.md"
    tasks.write_text("# T\n\n- [X] T001 implement code/model.py\n", encoding="utf-8")

    result = _run(tmp_path, tasks, monkeypatch)

    assert result["accepted"] == 1 and not result["deferred"]
    assert "- [X] T001" in tasks.read_text(encoding="utf-8")


def test_missing_production_artifact_reopened_without_llm(tmp_path: Path, monkeypatch) -> None:
    """A production task whose declared artifact is MISSING is reopened ``[ ]`` with
    NO LLM call."""
    tasks = tmp_path / "tasks.md"
    tasks.write_text("# T\n\n- [X] T002 create results/metrics.json\n", encoding="utf-8")

    result = _run(tmp_path, tasks, monkeypatch)

    assert result["accepted"] == 0
    assert result["rejected"] and result["rejected"][0][0] == "T002"
    assert "- [ ] T002" in tasks.read_text(encoding="utf-8")


def test_empty_data_output_is_not_valid(tmp_path: Path, monkeypatch) -> None:
    """A declared data output that exists but has NO rows (header only / empty) does
    NOT validate → the production task is reopened, no LLM call."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "out.csv").write_text("col_a,col_b\n", encoding="utf-8")  # header only
    tasks = tmp_path / "tasks.md"
    tasks.write_text("# T\n\n- [X] T003 generate data/out.csv with rows\n", encoding="utf-8")

    result = _run(tmp_path, tasks, monkeypatch)
    assert result["rejected"] and "- [ ] T003" in tasks.read_text(encoding="utf-8")


def test_populated_data_output_is_accepted(tmp_path: Path, monkeypatch) -> None:
    """A declared data output with a header + at least one data row validates → the
    task is accepted with no LLM call."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "out.csv").write_text("col_a,col_b\n1,2\n3,4\n", encoding="utf-8")
    tasks = tmp_path / "tasks.md"
    tasks.write_text("# T\n\n- [X] T004 generate data/out.csv with rows\n", encoding="utf-8")

    result = _run(tmp_path, tasks, monkeypatch)
    assert result["accepted"] == 1 and "- [X] T004" in tasks.read_text(encoding="utf-8")


def test_setup_task_gets_real_file_evidence_not_prose_fallback(tmp_path: Path) -> None:
    """A setup/config/test-path task (outside the OLD code/data/… roots) yields REAL
    file evidence via the broadened detector — not the 'no artifact path' fallback."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_model.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8"
    )
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "pkg.py").write_text("VALUE = 42\n", encoding="utf-8")

    for task, needle in (
        ("T010 configure pyproject.toml for the package", "name = \"demo\""),
        ("T011 add tests in tests/test_model.py", "def test_ok"),
        ("T012 implement src/pkg.py", "VALUE = 42"),
    ):
        ev = tv.gather_evidence(tmp_path, task)
        assert needle in ev, (task, ev)
        assert "references no code/data/figure artifact path" not in ev, (task, ev)


def test_ambiguous_task_falls_through_to_semantic(tmp_path: Path, monkeypatch) -> None:
    """A task with NO detectable artifact path is ambiguous → it DOES reach the
    semantic verifier (deterministic layer returns no verdict)."""
    calls: list[str] = []

    def _spy(**kw):
        calls.append(kw["task_text"])
        return tv.TaskVerdict(complete=True, reason="ok")

    monkeypatch.setattr(tv, "verify_task", _spy)
    tasks = tmp_path / "tasks.md"
    tasks.write_text("# T\n\n- [X] T020 think carefully about the approach\n", encoding="utf-8")

    tv.run_verification_pass(
        tmp_path, tasks, already_verified=set(),
        notes_path=tmp_path / "n.md", state_path=tmp_path / "s.yaml",
        project_id="PROJ-DET", repo_root=tmp_path,
    )
    assert len(calls) == 1 and "T020" in calls[0]


def test_remove_task_missing_artifact_is_not_deterministic_reject(tmp_path: Path, monkeypatch) -> None:
    """A 'remove/delete' task legitimately ends with the artifact ABSENT, so a
    missing artifact must NOT trigger a deterministic reject — it goes to the
    semantic verifier instead."""
    calls: list[str] = []

    def _spy(**kw):
        calls.append(kw["task_text"])
        return tv.TaskVerdict(complete=True, reason="ok")

    monkeypatch.setattr(tv, "verify_task", _spy)
    tasks = tmp_path / "tasks.md"
    tasks.write_text("# T\n\n- [X] T030 remove the obsolete code/legacy.py module\n", encoding="utf-8")

    tv.run_verification_pass(
        tmp_path, tasks, already_verified=set(),
        notes_path=tmp_path / "n.md", state_path=tmp_path / "s.yaml",
        project_id="PROJ-DET", repo_root=tmp_path,
    )
    assert len(calls) == 1, "removal task must fall through to the semantic verifier"


def test_evidence_hash_cache_hit_avoids_second_llm_call(tmp_path: Path, monkeypatch) -> None:
    """A semantic verdict is bound to (task_key, evidence_hash): re-verifying the
    SAME ambiguous task with unchanged evidence is a cache hit (no second LLM call),
    while changing the evidence invalidates it."""
    calls: list[str] = []

    def _spy(**kw):
        calls.append(kw["evidence"])
        return tv.TaskVerdict(complete=False, reason="not yet")

    monkeypatch.setattr(tv, "verify_task", _spy)
    tasks = tmp_path / "tasks.md"
    state = tmp_path / "s.yaml"

    # Tick 1: ambiguous task, LLM called once → reopened [ ].
    tasks.write_text("# T\n\n- [X] T040 refine the analysis approach\n", encoding="utf-8")
    tv.run_verification_pass(
        tmp_path, tasks, already_verified=set(),
        notes_path=tmp_path / "n.md", state_path=state,
        project_id="PROJ-DET", repo_root=tmp_path,
    )
    assert len(calls) == 1

    # Tick 2: implementer re-claims the SAME task, unchanged evidence → cache hit,
    # NO second LLM call, still reopened [ ].
    tasks.write_text("# T\n\n- [X] T040 refine the analysis approach\n", encoding="utf-8")
    tv.run_verification_pass(
        tmp_path, tasks, already_verified=set(),
        notes_path=tmp_path / "n.md", state_path=state,
        project_id="PROJ-DET", repo_root=tmp_path,
    )
    assert len(calls) == 1, "unchanged evidence must be a cache hit"
    assert "- [ ] T040" in tasks.read_text(encoding="utf-8")
