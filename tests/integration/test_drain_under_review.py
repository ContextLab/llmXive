"""Drain the stranded ``[~]`` backlog (issue #1139, defect D6).

Exercises both the LLM-FREE reclassification core (:func:`task_verifier.drain_under_review`)
over a REAL mixed tasks.md and the maintenance script's end-to-end ``main`` against a
synthetic repo — no mocks; only real files.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from llmxive.agents import task_verifier as tv
from llmxive.state import project as project_store
from llmxive.state import unverifiable
from llmxive.types import Project, Stage

_MIXED = """\
# Tasks

- [~] T001 implement code/present.py
- [~] T002 create results/missing.json
- [~] T003 investigate the tradeoffs of the approach
- [~] T004 generate data/empty.csv with rows
- [X] T005 prior done in code/done.py
- [ ] T006 not started yet
"""


def _seed_project(tmp_path: Path, pid: str = "PROJ-401-drain") -> tuple[Path, Path]:
    """Create projects/<pid>/specs/001-x/tasks.md with the mixed marks + the
    referenced artifact files. Returns (project_dir, tasks_path)."""
    project_dir = tmp_path / "projects" / pid
    fdir = project_dir / "specs" / "001-x"
    (project_dir / "code").mkdir(parents=True, exist_ok=True)
    (project_dir / "code" / "present.py").write_text("X = 1\n", encoding="utf-8")
    (project_dir / "code" / "done.py").write_text("Y = 2\n", encoding="utf-8")
    fdir.mkdir(parents=True, exist_ok=True)
    tasks = fdir / "tasks.md"
    tasks.write_text(_MIXED, encoding="utf-8")
    return project_dir, tasks


def test_drain_reclassifies_mixed_marks(tmp_path: Path) -> None:
    project_dir, tasks = _seed_project(tmp_path)

    res = tv.drain_under_review(project_dir, tasks, apply=True)

    text = tasks.read_text(encoding="utf-8")
    # T001: artifact present → accepted [X]; T005 stays [X].
    assert "- [X] T001" in text and "- [X] T005" in text
    # T002 & T004: production task, artifact missing → reopened [ ]; T006 stays [ ].
    assert "- [ ] T002" in text and "- [ ] T004" in text and "- [ ] T006" in text
    # T003: ambiguous (no artifact path) → LEFT [~] for the semantic verifier.
    assert "- [~] T003" in text
    assert res["accepted"] == 1
    assert res["reopened"] == 2
    assert res["ambiguous"] == 1
    assert res["before"]["~"] == 4 and res["after"]["~"] == 1


def test_drain_dry_run_writes_nothing(tmp_path: Path) -> None:
    project_dir, tasks = _seed_project(tmp_path)
    original = tasks.read_text(encoding="utf-8")

    res = tv.drain_under_review(project_dir, tasks, apply=False)

    # The projected counts are computed, but the file on disk is UNCHANGED.
    assert tasks.read_text(encoding="utf-8") == original
    assert res["after"]["~"] == 1 and res["before"]["~"] == 4  # projection only


def test_drain_records_unverifiable_at_reject_cap(tmp_path: Path) -> None:
    """A ``[~]`` production task whose artifact is missing AND whose stored
    reject_count already reached REJECT_CAP is recorded UNVERIFIABLE (never accepted)."""
    project_dir, tasks = _seed_project(tmp_path)
    # Seed the reject-count state so T002 has already hit the cap.
    import yaml
    state = project_dir / ".specify" / "memory" / "task_verify.yaml"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(yaml.safe_dump({"T002": tv.REJECT_CAP}), encoding="utf-8")

    res = tv.drain_under_review(project_dir, tasks, apply=True)

    assert "T002" in res["unverifiable"]
    recorded = unverifiable.load("PROJ-401-drain", repo_root=tmp_path)
    assert [t["task_key"] for t in recorded] == ["T002"], recorded
    # T004 hit the same missing-artifact reopen but had NO cap count → NOT recorded.
    assert "- [ ] T004" in tasks.read_text(encoding="utf-8")


def test_drain_reopens_already_unverifiable_task(tmp_path: Path) -> None:
    project_dir, tasks = _seed_project(tmp_path)
    # T001's artifact exists (would normally accept) but it is already flagged
    # unverifiable → it must be reopened [ ], NOT accepted.
    unverifiable.record_unverifiable(
        "PROJ-401-drain", "T001", "prior failure", repo_root=tmp_path
    )

    tv.drain_under_review(project_dir, tasks, apply=True)

    text = tasks.read_text(encoding="utf-8")
    assert "- [ ] T001" in text and "- [X] T001" not in text


def test_script_main_end_to_end(tmp_path: Path, capsys) -> None:
    """The maintenance script enumerates in_progress projects and drains their
    ``[~]`` tasks: dry-run leaves tasks.md untouched, ``--apply`` reclassifies."""
    from scripts.maintenance import drain_under_review as script

    pid = "PROJ-402-cli"
    _project_dir, tasks = _seed_project(tmp_path, pid)
    now = datetime.now(UTC)
    project = Project(
        id=pid, title="X", field="computer science",
        current_stage=Stage.IN_PROGRESS, created_at=now, updated_at=now,
        speckit_research_dir="specs/001-x",
    )
    project_store.save(project, repo_root=tmp_path)

    original = tasks.read_text(encoding="utf-8")

    # Dry-run: prints a table, writes nothing.
    rc = script.main(["--repo-root", str(tmp_path)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "DRY-RUN" in out and pid in out
    assert tasks.read_text(encoding="utf-8") == original

    # Apply: reclassifies the [~] tasks.
    rc = script.main(["--repo-root", str(tmp_path), "--apply"])
    assert rc == 0
    text = tasks.read_text(encoding="utf-8")
    assert "- [X] T001" in text and "- [ ] T002" in text and "- [~] T003" in text
