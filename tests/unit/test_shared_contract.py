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
    _TOLERANT_LOGGING_SKELETON,
    accumulate_contract_issues,
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


def test_locals_decorator_error_maps_to_enclosing_function(tmp_path: Path) -> None:
    """``X.<locals>.Y() takes ...`` is a closure/decorator arity error; the
    fixable definition is the ENCLOSING function ``X`` (``log_operation``), NOT the
    inner closure ``Y`` (``decorator``). Pins PROJ-552's undetected log_operation bug.
    """
    p = _proj(tmp_path)
    (p / "code" / "util" / "logs.py").write_text(
        "def log_it(*a, **k):\n    def decorator(f):\n        return f\n    return decorator\n",
        encoding="utf-8",
    )
    failures = [
        "x.py -> rc=1\n    TypeError: log_it.<locals>.decorator() takes 1 positional argument but 2 were given"
    ]
    issues = find_contract_issues(p, failures)
    syms = {(i.symbol, i.owner) for i in issues}
    assert ("log_it", None) in syms  # the enclosing function is the target
    assert "decorator" not in {i.symbol for i in issues}  # not the inner closure


def test_ledger_accumulates_contracts_across_rounds(tmp_path: Path) -> None:
    """The anti-thrash ledger: a symbol flagged in round 1 must still be rendered
    in round 2 even if round 2's traceback only mentions a different symbol — so
    the implementer cannot silently drop a previously-satisfied contract.
    """
    p = _proj(tmp_path)
    mem = p / ".specify" / "memory"
    # round 1: only log_it fails
    r1 = accumulate_contract_issues(
        mem, p, find_contract_issues(p, ["x.py\n    TypeError: log_it() takes no arguments"])
    )
    assert ("log_it", None) in {(i.symbol, i.owner) for i in r1}
    # round 2: a DIFFERENT symbol fails; ledger must still carry log_it forward
    r2 = accumulate_contract_issues(
        mem,
        p,
        find_contract_issues(p, ["y.py\n    AttributeError: 'Logger' object has no attribute 'debug'"]),
    )
    syms = {(i.symbol, i.owner) for i in r2}
    assert ("log_it", None) in syms  # carried forward despite not failing this round
    assert ("debug", "Logger") in syms  # plus the new one
    assert (mem / "contract_ledger.json").exists()


def test_logging_battleground_offers_tolerant_reference_skeleton(tmp_path: Path) -> None:
    """When the contract battleground is a logging module, the feedback hands the
    implementer a complete, self-contained, tolerant reference. Pins PROJ-552's
    endless logs.py thrash (the implementer kept reaching for stdlib logging)."""
    p = _proj(tmp_path)  # _proj's defining file is code/util/logs.py (stem contains 'log')
    fb = render_contract_feedback(
        find_contract_issues(
            p, ["a.py\n    TypeError: log_it() takes no arguments"]
        )
    )
    assert "KNOWN-GOOD REFERENCE" in fb
    assert "Do NOT reach for the stdlib `logging` module" in fb
    assert "ReproducibilityLogger" in fb and "def log_operation" in fb


def test_tolerant_logging_skeleton_executes_and_absorbs_every_call_shape() -> None:
    """The shipped skeleton must be valid, importable Python that never raises on
    the call shapes seen on PROJ-552 — else it would be useless advice."""
    ns: dict = {}
    exec(compile(_TOLERANT_LOGGING_SKELETON, "skeleton", "exec"), ns)
    get_logger, log_operation = ns["get_logger"], ns["log_operation"]
    assert get_logger() is get_logger("name")  # singleton, tolerant of a name arg
    assert get_logger().log("test", "verification").to_json()  # 2 positional, returns LogEntry
    get_logger().info("x"); get_logger().debug("y", k=1)  # __getattr__ no-ops
    assert log_operation(operation="o", input_file="f").to_json()  # kw direct call
    assert log_operation("o").to_json()  # positional direct call

    @log_operation
    def double(n):  # decorator use
        return n * 2

    assert double(21) == 42
