"""A red generated fixture is not reproduction of the recorded filesystem bug."""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from llmxive.repair import runner


def collision_evidence():
    return {"source": "errors", "failures": [{
        "project_id": "PROJ-770-example", "fingerprint": "filesystem_file_exists",
        "last_error": "[Errno 17] File exists: '/runner/projects/PROJ-770-example/code'",
        "filesystem_observations": [{"path": "projects/PROJ-770-example/code", "kind": "file"}],
    }]}


@pytest.mark.parametrize("case", ["actual_caller", "fixture_validation", "fixture_raise", "wrong_path"])
def test_original_collision_required_before_candidate(tmp_path, monkeypatch, case):
    source = "src/llmxive/example.py"
    related = "tests/unit/test_example.py"
    regression = "tests/unit/test_repair_example.py"
    for name, text in {
        source: "VALUE = 0\ndef existing(path): path.mkdir()\n",
        "src/llmxive/__init__.py": "", related: "def test_existing(): pass\n",
    }.items():
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    action = {
        "actual_caller": "existing(path)",
        "wrong_path": "existing(path)",
        "fixture_raise": "raise FileExistsError(17, 'File exists', str(path))",
        "fixture_validation": "Fixture(number='invalid')",
    }[case]
    collision = "wrong-directory" if case == "wrong_path" else "code"
    test = ("from llmxive.example import existing\nfrom pydantic import BaseModel\n"
            "class Fixture(BaseModel):\n    number: int\n"
            "def test_original_failure(tmp_path):\n"
            f"    path = tmp_path/'{collision}'\n"
            "    path.write_bytes(b'original research bytes')\n"
            f"    {action}\n")
    replies = iter([
        {"paths": [source, related], "problem": "recorded writer collision"},
        {"edits": {source: [{"old": "VALUE = 0", "new": "VALUE = 1"}]},
         "files": {regression: test}, "regression": regression,
         "related_tests": [related], "_producer_model": "fixture"},
    ])
    monkeypatch.setattr(runner, "_ask", lambda *a, **k: next(replies))
    calls = []

    def isolated(source_dir, tests, log, **kwargs):
        calls.append(source_dir.name)
        if source_dir.name == "candidate":
            raise RuntimeError("valid reproduction reached candidate")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "pytest_evidence", *tests],
            cwd=source_dir, env=dict(os.environ, PYTHONPATH=(
                str(Path(runner.__file__).parent)+os.pathsep+str(source_dir/"src"))),
            capture_output=True, text=True, timeout=30,
        )
        log.write_text(result.stdout+result.stderr)
        assert result.returncode == 1
        return result.returncode

    monkeypatch.setattr(runner, "isolated_tests", isolated)
    expected = "valid reproduction reached candidate" if case == "actual_caller" else "original FileExistsError"
    with pytest.raises(RuntimeError, match=expected):
        runner.run(tmp_path, collision_evidence(), tmp_path/"output")
    assert calls == (["baseline", "candidate"] if case == "actual_caller" else ["baseline"])


@pytest.mark.parametrize("change", ["missing_error", "unknown_error", "missing_observation",
                                   "directory_observation", "project_root", "multiple_errors"])
def test_targeted_class_cannot_silently_lose_anchor(tmp_path, monkeypatch, change):
    evidence = collision_evidence()
    failure = evidence["failures"][0]
    if change == "missing_error":
        failure.pop("last_error")
    elif change == "unknown_error":
        failure["last_error"] = "unknown error"
    elif change == "missing_observation":
        failure["filesystem_observations"] = []
    elif change == "directory_observation":
        failure["filesystem_observations"][0]["kind"] = "directory"
    elif change == "project_root":
        failure["last_error"] = "[Errno 17] File exists: '/runner/projects/PROJ-770-example'"
    else:
        evidence["failures"].append(dict(failure))
    monkeypatch.setattr(runner, "_ask", lambda *a, **k: pytest.fail("unsupported anchor reached model"))
    with pytest.raises(ValueError, match="unsupported filesystem collision reproduction anchor"):
        runner.run(tmp_path, evidence, tmp_path/"output")
    assert json.loads((tmp_path/"output/evidence.json").read_text()) == evidence


def test_retry_diagnostics_cannot_replace_original_anchor():
    evidence = collision_evidence()
    original = copy.deepcopy(evidence)
    anchor = runner.original_failure_anchor(evidence)
    evidence.update(previous_attempt_failure="candidate did not pass",
                    test_diagnostics={"after.log": "ValidationError: invalid generated fixture"})
    rendered = json.loads(runner.render_evidence(evidence))
    assert rendered["failures"] == original["failures"]
    assert "previous_attempt_failure" not in rendered and "test_diagnostics" not in rendered
    feedback = rendered["candidate_retry_feedback"]
    assert feedback["test_diagnostics"]["after.log"].startswith("ValidationError")
    assert "not a new production defect" in feedback["purpose"]
    assert runner.original_failure_anchor(evidence) == anchor


def test_default_scheduled_selection_ranks_one_original_error_and_reaches_model(tmp_path, monkeypatch):
    errors = tmp_path/"state/advance_errors"
    errors.mkdir(parents=True)
    saved = {}
    for project, count, date in [("PROJ-770-example", 107, "2026-10-09"),
                                 ("PROJ-771-older", 107, "2026-10-08"),
                                 ("PROJ-772-less-frequent", 1, "2026-10-10")]:
        record = collision_evidence()["failures"][0]
        record.update(project_id=project, consecutive_count=count, last_seen=date,
                      status="retry_scheduled",
                      last_error=f"[Errno 17] File exists: '/runner/projects/{project}/code'")
        record.pop("filesystem_observations")  # supplied afresh by default selection
        file = errors/(project+".json")
        file.write_text(json.dumps(record))
        saved[file] = file.read_bytes()
        blocker = tmp_path/"projects"/project/"code"
        blocker.parent.mkdir(parents=True)
        blocker.write_bytes(b"current research bytes")
    output = tmp_path/"output"
    monkeypatch.setattr(sys, "argv", ["repair", "--repo", str(tmp_path), "--output", str(output)])
    calls = []

    def ask(prompt, **kwargs):
        calls.append(prompt)
        evidence = json.loads(prompt.split("\nEVIDENCE:\n")[1].split("\nFILES:\n")[0])
        assert [f["project_id"] for f in evidence["failures"]] == ["PROJ-770-example"]
        assert evidence["original_failure_anchor"]["project_relative_path"] == "code"
        return {"skip": "selection and anchor integration probe"}

    monkeypatch.setattr(runner, "_ask", ask)
    assert runner.main() == 0
    assert len(calls) == 1
    assert len(json.loads((output/"evidence.json").read_text())["failures"]) == 1
    assert all(file.read_bytes() == original for file, original in saved.items())


@pytest.mark.parametrize("changes", [{"filename": None}, {"os_errno": None},
                                     {"filename": "/tmp/wrong"}])
def test_missing_or_wrong_collision_metadata_fails_closed(tmp_path, changes):
    source = tmp_path/"src/llmxive/example.py"
    source.parent.mkdir(parents=True)
    source.write_text("def existing(): pass\n")
    record = {"phase": "call", "exception": "FileExistsError", "import_error": False,
              "frames": ["src/llmxive/example.py"], "filename": "/tmp/code", "os_errno": 17}
    record.update(changes)
    log = tmp_path/"before.log"
    log.write_text("REPAIR_PYTEST_FAILURES="+json.dumps([record]))
    with pytest.raises(RuntimeError, match="original FileExistsError"):
        runner.validate_baseline_failure(log, tmp_path, anchor=runner.original_failure_anchor(collision_evidence()))
