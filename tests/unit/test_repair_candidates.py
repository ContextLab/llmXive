"""Boundaries of automatic repair proposals; no model execution in these tests."""

import hashlib
import json
from pathlib import Path

import pytest

from llmxive.repair.publish import apply
from llmxive.repair.runner import safe_path, validate_proposal


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
