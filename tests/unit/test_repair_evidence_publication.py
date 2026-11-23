"""Generated runner artifacts must satisfy the unchanged publication contract."""
import json
from types import SimpleNamespace

import pytest

from llmxive.repair import runner
from llmxive.repair.publish import apply


@pytest.mark.parametrize("tamper", [False, True])
def test_runner_evidence_can_be_verified_by_publisher(tmp_path, monkeypatch, tamper):
    repo = tmp_path / "repo"
    output = tmp_path / "evidence"
    source = "src/llmxive/example.py"
    related = "tests/unit/test_example.py"
    regression = "tests/unit/test_repair_example.py"
    for name, contents in {
        source: "VALUE = 0\n",
        related: "def test_existing(): pass\n",
        "src/llmxive/pipeline/graph.py":
            'STAGE_TO_AGENT = {Stage.IN_PROGRESS: "implementer"}\n',
    }.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents)
    proposal = {
        "title": "Example repair", "explanation": "Integration fixture",
        "edits": {source: [{"old": "VALUE = 0", "new": "VALUE = 1"}]},
        "files": {regression: "def test_regression(): pass\n"},
        "regression": regression, "related_tests": [related],
        "_producer_model": "author-model",
    }
    replies = iter([{"paths": [source, related], "problem": "fixture"}, proposal])
    monkeypatch.setattr(runner, "_ask", lambda *a, **k: next(replies))
    exits = iter([1, 0, 0])

    def isolated(source_dir, tests, log, **kwargs):
        code = next(exits)
        # This contract test uses explicit test-result fixtures; production
        # collects these fields from the separately mounted pytest plugin.
        failures = [{"phase": "call", "exception": "AssertionError", "import_error": False,
                     "frames": [regression]}] if code else []
        log.write_text(f"Fixture isolated-test exit: {code}\nREPAIR_PYTEST_FAILURES="
                       + json.dumps(failures) + "\n")
        return code

    monkeypatch.setattr(runner, "isolated_tests", isolated)
    monkeypatch.setattr(runner, "chat_with_fallback", lambda *a, **k: SimpleNamespace(
        text='{"accept": true, "reason": "fixture"}', model="reviewer-model"))
    monkeypatch.setenv("PRE_COMMIT_ALLOW_NO_CONFIG", "1")
    evidence = {"source": "errors", "failures": [{"stage": "in_progress"}]}
    result = runner.run(repo, evidence, output)
    assert result["status"] == "validated_candidate"
    # Source-derived hints remain separately inspectable; raw input is retained.
    assert json.loads((output / "evidence.json").read_text()) == evidence
    assert json.loads((output / "dispatch-context.json").read_text())["routes"]
    assert (repo / source).read_text() == "VALUE = 0\n"
    if tamper:
        (output / "evidence.json").write_text('{"source": "altered"}')
        with pytest.raises(ValueError, match="evidence or review changed"):
            apply(repo, output)
        assert (repo / source).read_text() == "VALUE = 0\n"
        assert not (repo / regression).exists()
    else:
        apply(repo, output)
        assert (repo / source).read_text() == "VALUE = 1\n"
        assert (repo / regression).is_file()
