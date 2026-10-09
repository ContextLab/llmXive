"""Repair failures leave usable evidence; independent reviews avoid the author."""
import json
import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.repair import runner


def test_malformed_model_response_is_retained_and_redacted(tmp_path, monkeypatch):
    monkeypatch.setenv("GH_TOKEN", "secret-test-token-value")
    monkeypatch.setattr(runner, "chat_with_fallback", lambda *a, **k:
                        ChatResponse(text="malformed secret-test-token-value", model="m", backend="dartmouth"))
    response = tmp_path / "response.txt"
    with pytest.raises(json.JSONDecodeError):
        runner._ask("diagnose", response_path=response)
    assert response.read_text() == "malformed <redacted>"


def test_invalid_selection_keeps_evidence_and_phase(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "_ask", lambda *a, **k: {"paths": [], "problem": "observed failure"})
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="1-6"):
        runner.run(tmp_path, {"error": "observed failure"}, output)
    assert json.loads((output / "evidence.json").read_text())["error"] == "observed failure"
    assert json.loads((output / "selection.json").read_text())["problem"] == "observed failure"
    assert json.loads((output / "progress.json").read_text())["phase"] == "selecting_files"


def test_no_input_produces_downloadable_result(tmp_path, monkeypatch):
    output = tmp_path / "output"
    monkeypatch.setattr(sys, "argv", ["repair", "--repo", str(tmp_path), "--output", str(output)])
    monkeypatch.setattr(runner, "select_evidence", lambda *a: None)
    assert runner.main() == 0
    assert json.loads((output / "result.json").read_text())["status"] == "no_candidate"


@pytest.mark.parametrize("author", ["openai.gpt-oss-120b", "zai-org.glm-5.3"])
def test_validated_candidate_uses_different_reviewer(tmp_path, monkeypatch, author):
    source = "src/llmxive/example.py"
    regression = "tests/unit/test_repair_example.py"
    related = "tests/unit/test_example.py"
    for name, text in {
        source: "def result(): return 0\n",
        "src/llmxive/__init__.py": "",
        related: "from llmxive.example import result\ndef test_existing(): assert isinstance(result(), int)\n",
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    responses = iter([
        {"paths": [source, related], "problem": "wrong result"},
        {"title": "Repair result", "explanation": "Correct the observed result", "_producer_model": author,
         "files": {source: "def result(): return 1\n",
                   regression: "from llmxive.example import result\ndef test_regression(): assert result() == 1\n"},
         "regression": regression, "related_tests": [related]},
    ])
    monkeypatch.setattr(runner, "_ask", lambda *a, **k: next(responses))

    # Exercise real before/after pytest behavior; Docker isolation is separately
    # covered by the production workflow. This test checks review routing.
    def local_tests(repo, tests, log, **kwargs):
        result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *tests],
                                cwd=repo, text=True, capture_output=True, timeout=30,
                                env={"PATH": os.environ["PATH"], "PYTHONPATH": str(repo / "src"),
                                     "PYTHONDONTWRITEBYTECODE": "1"})
        log.write_text(result.stdout + result.stderr)
        return result.returncode

    monkeypatch.setattr(runner, "isolated_tests", local_tests)
    seen = []

    def review(*args, **kwargs):
        seen.append(kwargs["model"])
        assert kwargs["model"] != author
        return SimpleNamespace(model=kwargs["model"], text='{"accept": true, "reason": "regression reproduced"}')

    monkeypatch.setattr(runner, "chat_with_fallback", review)
    result = runner.run(tmp_path, {"error": "result returned zero"}, tmp_path / "output")
    assert result["status"] == "validated_candidate"
    assert result["before_exit"] == 1 and result["after_exit"] == 0
    assert result["reviewer_model"] == seen[0] != author
