"""Missing outputs after import/setup errors must not launch a dataset search."""
import subprocess
import sys

import pytest

from llmxive.execution.analysis_runner import AnalysisRunResult, RunCommandResult
from llmxive.execution.stage import _needs_verified_source, _write_execution_feedback


def result(**changes):
    values = dict(ok=False, reason="missing data outputs after failed execution",
                  declared_missing=["data/results.csv"], artifacts_produced=[])
    values.update(changes)
    return AnalysisRunResult(**values)


def test_real_module_launch_failure_keeps_feedback_without_search(tmp_path, monkeypatch):
    # Reproduce the observed python -m failure without executing generated code.
    run = subprocess.run([sys.executable, "-I", "-m", "llmxive_nonexistent_probe.module"],
                         cwd=tmp_path, capture_output=True, text=True, check=False)
    assert run.returncode != 0 and "No module named" in run.stderr
    failures = ["python -m llmxive_nonexistent_probe.module -> rc=1\n" + run.stderr]
    calls = []
    monkeypatch.setattr("llmxive.execution.data_source.ensure_discovered_source",
                        lambda p: calls.append(p) or {})
    memory = tmp_path / ".specify" / "memory"
    memory.mkdir(parents=True)
    res = result(commands=[RunCommandResult("python -m llmxive_nonexistent_probe.module",
                 False, run.returncode, 0.01, False, run.stderr)])
    _write_execution_feedback(memory, res, failures=failures)
    assert calls == []
    feedback = (memory / "execution_feedback.md").read_text()
    assert "No module named" in feedback and "data/results.csv" in feedback
    assert not res.ok


@pytest.mark.parametrize("tail", [
    "ModuleNotFoundError: No module named 'code.io'",
    "/project/.venv/bin/python: No module named code.io.record_env_hash",
    "ImportError: cannot import name 'run' from 'local_module'",
    "SyntaxError: invalid syntax",
    "IndentationError: unexpected indent",
    "NameError: name 'pd' is not defined",
    "UnboundLocalError: local variable 'x' referenced before assignment",
])
def test_setup_failure_does_not_imply_missing_external_data(tail):
    assert not _needs_verified_source(result(), ["python code/run.py -> rc=1\n  " + tail])


@pytest.mark.parametrize("changes,failures", [
    ({}, []),
    ({}, ["python run.py -> rc=1\nFileNotFoundError: data/raw/source.csv"]),
    ({}, ["python run.py -> rc=1\nKeyError: 'expected_dataset_field'"]),
    ({}, ["python a.py -> rc=1\nNameError: 'x'", "python b.py -> rc=1\nunknown failure"]),
    ({}, ["python run.py -> rc=1\nModuleNotFoundError: x\nConnectionError: source unavailable"]),
    ({"fabrication": ["invented input measurements"]}, ["ModuleNotFoundError: x"]),
    ({"hollow": ["data/results.csv: empty measured values"]}, ["NameError: x"]),
])
def test_positive_or_uncertain_data_signals_retain_discovery(changes, failures):
    assert _needs_verified_source(result(**changes), failures)
