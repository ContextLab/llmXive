"""Boundaries of automatic repair proposals; no model execution in these tests."""

import hashlib
import json
from pathlib import Path

import pytest

from llmxive.repair.publish import apply
from llmxive.repair.runner import safe_path, validate_proposal


def test_issue_selection_includes_recurring_reviewer_umbrella(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from llmxive.repair import runner

    issues = [
        {"number": 1474, "title": "Recurring: malformed reviewer responses block convergence",
         "body": "Observed failure", "url": "https://example.test/1474"},
        {"number": 2, "title": "New research idea", "body": "Unrelated"},
    ]
    monkeypatch.setattr(runner.subprocess, "run",
                        lambda *a, **k: SimpleNamespace(stdout=json.dumps(issues)))
    result = runner.select_evidence(tmp_path, "issues")
    assert [i["number"] for i in result["issues"]] == [1474]


def test_repair_prompt_keeps_later_issues_and_retry_feedback(tmp_path, monkeypatch):
    from llmxive.repair import runner

    evidence = {
        "source": "issues",
        "issues": [{"body": "Current problem\n" + "Historical incident\n" * 2000 +
                    "\nLatest concrete finding", "number": i, "title": f"Pipeline defect {i}"}
                   for i in range(5)],
        "previous_attempt_failure": "Regression did not reproduce the bug",
        "test_diagnostics": "setup\n" * 10000 + "AssertionError: expected a retained diagnosis",
    }
    captured = []

    def ask(prompt):
        captured.append(prompt)
        return {"skip": "diagnostic probe"}

    monkeypatch.setattr(runner, "_ask", ask)
    runner.run(tmp_path, evidence, tmp_path / "output")
    payload = captured[0].split("\nEVIDENCE:\n", 1)[1].split("\nFILES:\n", 1)[0]
    parsed = json.loads(payload)
    assert len(payload) <= 12000
    assert [i["number"] for i in parsed["issues"]] == list(range(5))
    assert all("Current problem" in i["body"] and "Latest concrete finding" in i["body"]
               for i in parsed["issues"])
    assert parsed["previous_attempt_failure"] == evidence["previous_attempt_failure"]
    assert parsed["test_diagnostics"].endswith("AssertionError: expected a retained diagnosis")
    assert json.loads((tmp_path / "output/evidence.json").read_text()) == evidence


@pytest.mark.parametrize(
    "path",
    [
        "../README.md",
        "/tmp/x.py",
        ".github/workflows/x.yml",
        "src/llmxive/../../x.py",
        "tests/unit/conftest.py",
        "src/llmxive/repair/runner.py",
        "projects/P/code/x.py",
    ],
)
def test_forbidden_paths(path):
    with pytest.raises(ValueError):
        safe_path(path)


def test_stale_candidate_and_existing_test_rewrite_rejected(tmp_path: Path):
    source = "src/llmxive/example.py"
    related = "tests/unit/test_example.py"
    regression = "tests/unit/test_repair_example.py"
    for rel in (source, related):
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("old\n")
    proposal = {
        "files": {source: "new\n", regression: "def test_regression(): pass\n"},
        "regression": regression,
        "related_tests": [related],
    }
    validate_proposal(proposal, tmp_path)
    output = tmp_path / "output"
    output.mkdir()
    result = {
        "status": "validated_candidate",
        "review": {"accept": True},
        "base_files": {source: hashlib.sha256(b"old\n").hexdigest(), regression: None},
    }
    evidence = {"error": "observed defect"}
    result["evidence_sha256"] = hashlib.sha256(
        json.dumps(evidence, sort_keys=True).encode()
    ).hexdigest()
    (output / "evidence.json").write_text(json.dumps(evidence))
    (output / "review.json").write_text(json.dumps(result["review"]))
    (output / "result.json").write_text(json.dumps(result))
    (output / "proposal.json").write_text(json.dumps(proposal))
    (tmp_path / source).write_text("new unrelated code\n")
    with pytest.raises(ValueError, match="platform changed"):
        apply(tmp_path, output)
    assert not (tmp_path / regression).exists()  # validate all before any mutation
    proposal["files"][related] = "weakened test"
    with pytest.raises(ValueError, match="cannot replace existing tests"):
        validate_proposal(proposal, tmp_path)
