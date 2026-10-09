"""A runtime import failure is not evidence of the observed caller's defect."""
import os
import subprocess
import sys

import pytest

from llmxive.repair import runner


@pytest.mark.parametrize("missing", ["symbol", "module", None])
def test_runtime_import_failure_stops_before_candidate(tmp_path, monkeypatch, missing):
    source = "src/llmxive/example.py"
    regression = "tests/unit/test_repair_example.py"
    related = "tests/unit/test_example.py"
    for name, text in {source: "VALUE = 0\ndef existing(path): path.mkdir()\n", "src/llmxive/__init__.py": "",
                       related: "def test_existing(): pass\n"}.items():
        path = tmp_path/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    import_line = ("from llmxive.example import new_helper" if missing == "symbol"
                   else "import llmxive.new_helper_module")
    regression_text = f"def test_existing_caller():\n    {import_line}\n"
    if missing is None:
        regression_text = ("from llmxive.example import existing\n"
                           "def test_existing_caller(tmp_path):\n"
                           "    path = tmp_path/'collision'\n"
                           "    path.write_text('original bytes')\n"
                           "    existing(path)\n")
    replies = iter([
        {"paths": [source, related], "problem": "fixture collision"},
        {"edits": {source: [{"old": "VALUE = 0", "new": "def new_helper(): pass"}]},
         "files": {regression: regression_text},
         "regression": regression, "related_tests": [related], "_producer_model": "fixture"},
    ])
    monkeypatch.setattr(runner, "_ask", lambda *a, **k: next(replies))
    calls = []

    def isolated(source_dir, tests, log, **kwargs):
        calls.append(source_dir.name)
        if missing is None and source_dir.name == "candidate":
            raise RuntimeError("valid reproduction reached candidate")
        assert source_dir.name == "baseline", "invalid reproduction reached candidate tests"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *tests],
            cwd=source_dir, env=dict(os.environ, PYTHONPATH=str(source_dir/"src")),
            capture_output=True, text=True, timeout=30,
        )
        log.write_text(result.stdout + result.stderr)
        assert result.returncode == 1  # Runtime import failure, not collection exit 2.
        return result.returncode

    monkeypatch.setattr(runner, "isolated_tests", isolated)
    expected = "baseline import failure" if missing else "valid reproduction reached candidate"
    with pytest.raises(RuntimeError, match=expected):
        runner.run(tmp_path, {}, tmp_path/"evidence")
    assert calls == (["baseline"] if missing else ["baseline", "candidate"])
