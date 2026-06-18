"""Tests for shared-module API-contract detection (the anti-oscillation fix).

When many scripts call a project-defined symbol incompatibly, the implementer
must fix the ONE definition tolerant of all callers — not the callers — or the
per-task loop oscillates forever. These pin: contract errors on a project symbol
are detected with the defining file + call sites; third-party-symbol misuse is
NOT (no local definition); and methods / missing-attributes resolve to the
owning class's file.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.execution.shared_contract import (
    defining_files,
    find_contract_issues,
    render_contract_feedback,
)


def _proj(tmp_path: Path) -> Path:
    p = tmp_path / "projects" / "PROJ-X"
    (p / "code" / "util").mkdir(parents=True)
    (p / "code" / "util" / "logs.py").write_text(
        "def log_it(*a, **k):\n    return None\n\nclass Logger:\n    def debug(self, m):\n        pass\n",
        encoding="utf-8",
    )
    (p / "code" / "a.py").write_text(
        "from util.logs import log_it\nlog_it(operation='x', logger=1)\n", encoding="utf-8"
    )
    (p / "code" / "b.py").write_text(
        "from util.logs import log_it\n@log_it\ndef f():\n    pass\n", encoding="utf-8"
    )
    return p


def test_detects_project_function_contract_error_with_call_sites(tmp_path: Path) -> None:
    p = _proj(tmp_path)
    failures = ["x.py -> rc=1\n    TypeError: log_it() got an unexpected keyword argument 'operation'"]
    issues = find_contract_issues(p, failures)
    assert len(issues) == 1
    i = issues[0]
    assert i.symbol == "log_it" and i.owner is None
    assert i.defining_file == "code/util/logs.py"
    joined = " ".join(i.call_sites)
    assert "a.py" in joined and "b.py" in joined  # both the call + the decorator usage
    # the defining module is a re-open target so the implementer fixes the ROOT.
    assert "code/util/logs.py" in defining_files(issues)
    assert "fix the DEFINITION" in render_contract_feedback(issues)


def test_method_and_missing_attribute_resolve_to_owning_class_file(tmp_path: Path) -> None:
    p = _proj(tmp_path)
    failures = [
        "y.py -> rc=1\n    TypeError: Logger.debug() takes 2 positional arguments but 3 were given",
        "z.py -> rc=1\n    AttributeError: 'Logger' object has no attribute 'warn'",
    ]
    issues = find_contract_issues(p, failures)
    files = {i.defining_file for i in issues}
    assert files == {"code/util/logs.py"}
    assert {(i.owner, i.symbol) for i in issues} == {("Logger", "debug"), ("Logger", "warn")}


def test_third_party_symbol_is_out_of_scope(tmp_path: Path) -> None:
    p = _proj(tmp_path)
    # read_csv is pandas, not defined in code/ -> not a shared-contract issue.
    failures = ["q.py -> rc=1\n    TypeError: read_csv() got an unexpected keyword argument 'foo'"]
    assert find_contract_issues(p, failures) == []


def test_missing_method_feedback_is_cumulative_not_rotating(tmp_path: Path) -> None:
    """The anti-rotation guidance: missing-method errors on a class must tell the
    implementer to ADD (not replace) and tolerate ALL method names at once.

    Pins the bug observed on PROJ-552: round 1 added ``.log`` but dropped the
    class's pre-existing ``.info``/``.debug``; round 2 then failed on those. The
    feedback must (a) group both method names under the one owning class, (b) warn
    against deleting existing definitions, and (c) offer a permissive fallback.
    """
    p = _proj(tmp_path)
    failures = [
        "a.py -> rc=1\n    AttributeError: 'Logger' object has no attribute 'info'",
        "b.py -> rc=1\n    AttributeError: 'Logger' object has no attribute 'debug'",
    ]
    fb = render_contract_feedback(find_contract_issues(p, failures))
    # cumulative / preserve-existing instruction
    assert "ADD, do not REPLACE" in fb
    assert "__getattr__" in fb  # the permissive-fallback escape hatch
    # both method names appear grouped under the single owning class
    assert "`info`" in fb and "`debug`" in fb
    assert fb.count("class `Logger`") == 1  # one cumulative block, not one-per-method
