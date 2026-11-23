"""Missing outputs after import/setup errors must not launch a dataset search."""
import subprocess
import sys

import pytest

from llmxive.execution.analysis_runner import AnalysisRunResult, RunCommandResult
from llmxive.execution.stage import (
    _needs_verified_source,
    _terminal_error_line,
    _write_execution_feedback,
)


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


TRACEBACK = "Traceback (most recent call last):\n"

#: Every shape a failing command's captured tail takes, and whether the error it
#: DIED of establishes a missing external data source. A tail legitimately holds
#: non-terminal errors — a handled exception printed as a notice, and each link
#: of a chained traceback — so classification reads the terminal line only.
TERMINAL_CASES = [
    (
        "interpreter launch failure (no traceback)",
        "python -m code.io.record_env_hash -> rc=1\n"
        "/p/.venv/bin/python: No module named code.io.record_env_hash",
        "/p/.venv/bin/python: No module named code.io.record_env_hash",
        False,
    ),
    (
        "terminal ModuleNotFoundError",
        f"python run.py -> rc=1\n{TRACEBACK}"
        '  File "run.py", line 4, in <module>\n    import torch\n'
        "ModuleNotFoundError: No module named 'torch'",
        "ModuleNotFoundError: No module named 'torch'",
        False,
    ),
    (
        "terminal SyntaxError below a caret frame",
        'python run.py -> rc=1\n  File "run.py", line 3\n    def f(:\n         ^\n'
        "SyntaxError: invalid syntax",
        "SyntaxError: invalid syntax",
        False,
    ),
    (
        "handled ImportError notice, terminal data FileNotFoundError",
        f"python run.py -> rc=1\n"
        "WARNING: ImportError: No module named 'seaborn'; using matplotlib\n"
        f"{TRACEBACK}  File \"run.py\", line 20, in <module>\n"
        "    df = pd.read_csv('data/raw/source.csv')\n"
        "FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/source.csv'",
        "FileNotFoundError: [Errno 2] No such file or directory: 'data/raw/source.csv'",
        True,
    ),
    (
        "chained: setup error first, terminal source error",
        f"python run.py -> rc=1\n{TRACEBACK}    import torch\n"
        "ModuleNotFoundError: No module named 'torch'\n\n"
        "During handling of the above exception, another exception occurred:\n\n"
        f"{TRACEBACK}    fetch_remote_corpus()\n"
        "RuntimeError: corpus host refused the request (HTTP 451)",
        "RuntimeError: corpus host refused the request (HTTP 451)",
        True,
    ),
    (
        "chained: source error first, terminal setup error",
        f"python run.py -> rc=1\n{TRACEBACK}    open('data/raw/x.csv')\n"
        "FileNotFoundError: data/raw/x.csv\n\n"
        "During handling of the above exception, another exception occurred:\n\n"
        f"{TRACEBACK}    import fallback_loader\n"
        "ModuleNotFoundError: No module named 'fallback_loader'",
        "ModuleNotFoundError: No module named 'fallback_loader'",
        False,
    ),
    (
        "terminal setup error followed by stdout noise",
        f"python run.py -> rc=1\n{TRACEBACK}    import torch\n"
        "ModuleNotFoundError: No module named 'torch'\ndone\n",
        "ModuleNotFoundError: No module named 'torch'",
        False,
    ),
]


@pytest.mark.parametrize(
    "failure,terminal", [(c[1], c[2]) for c in TERMINAL_CASES],
    ids=[c[0] for c in TERMINAL_CASES],
)
def test_terminal_error_line_reads_the_error_the_command_died_of(failure, terminal):
    assert _terminal_error_line(failure) == terminal


@pytest.mark.parametrize(
    "failure,discover", [(c[1], c[3]) for c in TERMINAL_CASES],
    ids=[c[0] for c in TERMINAL_CASES],
)
def test_discovery_follows_the_terminal_error_not_an_earlier_one(failure, discover):
    """A setup error ABOVE the terminal error must not suppress discovery.

    Reviewer-flagged edge case for the import/setup suppression: the captured
    tail can hold an early matching exception followed by a different terminal
    exception, and scanning the whole tail suppressed the dataset search for a
    real data failure.
    """
    assert _needs_verified_source(result(), [failure]) is discover
