"""Production regressions from the October audit, exercised against real files."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from llmxive.agents.task_verifier import _task_key
from llmxive.checks.pipeline_writes import unexpected_writes
from llmxive.execution.fabrication_guard import find_fabrication
from llmxive.speckit.implement_cmd import ImplementerAgent
from llmxive.speckit.task_lines import mark_task
from llmxive.web_data import _index_run_logs, _last_run_log, _project_authors


@pytest.mark.parametrize(
    "task_id", ["T003.5", "T012_fetch", "T008-CLI-EXPOSE", "T005C", "PT005C", "T016a"]
)
def test_task_identity_is_shared_and_marking_does_not_touch_siblings(task_id):
    text = f"- [ ] {task_id} update code/run.py\n  - [ ] **{task_id}_sibling** keep\n"
    assert ImplementerAgent()._next_incomplete(text)[0] == task_id
    assert _task_key(task_id + " update code/run.py") == task_id
    updated = mark_task(text, task_id, "X")
    assert updated.startswith(f"- [X] {task_id} ")
    assert f"[ ] **{task_id}_sibling**" in updated
    assert ImplementerAgent()._next_incomplete(updated)[0] == task_id + "_sibling"
    assert not ImplementerAgent()._all_complete(updated)


def test_task_completion_does_not_ignore_review_marks_or_empty_lists():
    assert not ImplementerAgent()._all_complete("")
    assert not ImplementerAgent()._all_complete("- [X] T001 done\n- [~] T002 waiting\n")


def test_discovery_recipe_cannot_accidentally_overwrite_repo_root(tmp_path, monkeypatch):
    from llmxive.librarian.data_source_discovery import _run_snippet

    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("platform")
    monkeypatch.setenv("GITHUB_TOKEN", "do-not-inherit")
    rc, out, err = _run_snippet(
        Path(sys.executable),
        "import os; from pathlib import Path; Path('README.md').write_text('dataset'); "
        "assert 'GITHUB_TOKEN' not in os.environ; print('isolated-cwd')",
    )
    assert rc == 0, err
    assert "isolated-cwd" in out
    assert (tmp_path / "README.md").read_text() == "platform"


def test_pipeline_commit_guard_rejects_platform_writes(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "README.md").write_text("platform")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "-qm",
            "initial",
        ],
        cwd=tmp_path,
        check=True,
    )
    (tmp_path / "README.md").write_text("dataset")
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "output.json").write_text("{}")
    assert unexpected_writes(tmp_path) == ["README.md"]


def test_negative_synthetic_statement_is_neither_fabrication_nor_authorization(tmp_path):
    (tmp_path / "code").mkdir()
    (tmp_path / "idea").mkdir()
    code = tmp_path / "code" / "loader.py"
    code.write_text("raise RuntimeError('synthetic data is strictly prohibited')\n")
    (tmp_path / "idea" / "idea.md").write_text("Use real measurements. No synthetic data.")
    assert find_fabrication(tmp_path) == []
    code.write_text("# generate synthetic data\nvalues = [1, 2, 3]\n")
    assert find_fabrication(tmp_path)


def test_dashboard_index_matches_direct_read_and_refreshes(tmp_path):
    month = tmp_path / "state" / "run-log" / "2026-10"
    month.mkdir(parents=True)
    (tmp_path / "projects" / "PROJ-001-test").mkdir(parents=True)
    entry = {
        "project_id": "PROJ-001-test",
        "outcome": "success",
        "model_name": "zai-org.glm-5.3",
        "agent_name": "implementer",
        "started_at": "2026-10-08T00:00:00Z",
        "ended_at": "2026-10-08T00:00:01Z",
    }
    log = month / "one.jsonl"
    log.write_text(json.dumps(entry) + "\ninvalid\n")
    index = _index_run_logs(tmp_path)
    assert _last_run_log(
        tmp_path, "PROJ-001-test", run_entries=index["PROJ-001-test"]
    ) == _last_run_log(tmp_path, "PROJ-001-test")
    assert _project_authors(
        tmp_path, "PROJ-001-test", run_entries=index["PROJ-001-test"]
    ) == _project_authors(tmp_path, "PROJ-001-test")
    log.write_text(json.dumps(entry) + "\n" + json.dumps(entry) + "\n")
    assert len(_index_run_logs(tmp_path)["PROJ-001-test"]) == 2


@pytest.mark.parametrize(
    "line,identity",
    [
        ("- [ ] [P] T025[US2] work", "T025"),
        ("- [ ] T015c\u2011Guard\u2011Test work", "T015c\u2011Guard\u2011Test"),
        ("- [ ] T035a: work", "T035a"),
        ("- [ ] [ ] T024 work", "T024"),
    ],
)
def test_legacy_task_variants_preserve_identity(line, identity):
    from llmxive.speckit.paper_implement_cmd import PaperImplementerAgent
    from llmxive.speckit.task_lines import validate_open_tasks

    validate_open_tasks(line)
    assert ImplementerAgent()._next_incomplete(line)[0] == identity
    assert PaperImplementerAgent()._next_incomplete(line)[0] == identity
    assert _task_key(line.split("] ", 1)[1]) == identity
    assert mark_task(line, identity, "X") == line.replace("[ ]", "[X]", 1)


def test_malformed_or_duplicate_tasks_fail_for_replanning():
    from llmxive.speckit.task_lines import TaskFormatError, validate_open_tasks

    for text in ("- [ ] Load the data", "- [ ] T001 work\n- [ ] T001 other"):
        with pytest.raises(TaskFormatError):
            validate_open_tasks(text)
    assert not ImplementerAgent()._all_complete("- [X] T001 done\n- [ ] Load data")


def test_activity_is_not_stage_advancement(tmp_path):
    from datetime import UTC, datetime

    from llmxive.agents.status_reporter import _collect_run_metrics

    now = datetime.now(UTC).isoformat()
    logs = tmp_path / "state/run-log/2026-10"
    logs.mkdir(parents=True)
    (logs / "calls.jsonl").write_text(json.dumps({"ended_at": now, "outcome": "success"}) + "\n")
    history = tmp_path / "state/projects"
    history.mkdir()
    (history / "PROJ-001.history.jsonl").write_text(
        "\n".join(
            json.dumps({"at": now, "from_stage": before, "to_stage": after})
            for before, after in [
                ("in_progress", "planned"),  # rework is not advancement
                ("in_progress", "research_complete"),
                ("paper_ingested", "reviewed_preprint"),  # separate track
            ]
        )
        + "\n"
    )
    metrics = _collect_run_metrics(tmp_path)
    assert metrics["successful_invocations_7d"] == 1
    assert metrics["advancement_rate_7d"] == 1


def test_exact_enumeration_does_not_search_for_unrelated_observations(tmp_path):
    from llmxive.execution.data_source import ensure_discovered_source, requires_external_data
    idea = tmp_path / "idea"
    idea.mkdir()
    assert requires_external_data(tmp_path)  # silence does not waive data requirements
    (idea / "fleshed_out.md").write_text(
        "Compute exact integer totients. No external dataset is needed. Validate by gcd."
    )
    assert not requires_external_data(tmp_path)
    assert ensure_discovered_source(tmp_path) is None  # no LLM/network call or fabricated source
