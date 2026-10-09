"""Exercise the workflow's actual Git sparse patterns and corpus guard."""

import importlib.util
from pathlib import Path
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "audit_corpus", ROOT / "scripts/ci/verify-audit-corpus.py",
)
corpus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corpus)


@pytest.mark.parametrize("audit", corpus.INPUTS)
def test_workflow_sparse_checkout_preserves_full_corpus_and_detects_loss(tmp_path, audit):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=tmp_path, text=True)

    inputs = [
        ".specify/templates/spec.md", "state/projects/PROJ-1.yaml",
        "projects/PROJ-1/specs/001-first/spec.md",
        "projects/PROJ-2/specs/002-second/contracts/nested/contract.yaml",
        "projects/PROJ-2/specs/002-second/config.yml",
        "papers/.supported.json", "papers/.style/llmxive.cls",
        "papers/PROJ-2/original-llmxive.pdf", "papers/top-level.pdf",
        "agents/prompts/personalities/reviewer.md", "scripts/verify_persona_evidence.py",
        "projects/PROJ-1/activity.jsonl", "projects/PROJ-2/activity.jsonl",
        "projects/PROJ-1/.audit/dispatches/old.jsonl",
        "projects/PROJ-2/.audit/dispatches/recent.jsonl",
    ]
    for name in [*inputs, "projects/PROJ-2/data/large.csv"]:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("actual tracked input\n")
    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", "corpus")
    expected = corpus.tracked_inputs(tmp_path, audit)
    expected_by_audit = {
        "speckit": inputs[:5], "pdf": inputs[5:9],
        "personality": inputs[9:13], "feedback-loop": inputs[11:],
    }
    assert set(expected) == set(expected_by_audit[audit])
    workflow = yaml.safe_load((ROOT / ".github/workflows/audit.yml").read_text())
    checkout = workflow["jobs"][f"audit-{audit}"]["steps"][0]["with"]
    assert checkout["sparse-checkout-cone-mode"] is False
    patterns = checkout["sparse-checkout"].splitlines()
    git("sparse-checkout", "set", "--no-cone", *patterns)
    assert corpus.verify(tmp_path, audit) == expected
    assert not (tmp_path / "projects/PROJ-2/data/large.csv").exists()
    (tmp_path / expected[-1]).unlink()
    with pytest.raises(ValueError, match="tracked audit inputs missing"):
        corpus.verify(tmp_path, audit)
