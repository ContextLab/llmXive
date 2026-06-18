"""Basic sanity tests for the reproducibility logging utilities."""

import importlib
import sys

import pytest

# Reload the module to ensure a fresh global logger for each test run.
@pytest.fixture(autouse=True)
def reload_logs_module():
    if "reproducibility.logs" in sys.modules:
        importlib.reload(sys.modules["reproducibility.logs"])
    else:
        importlib.import_module("reproducibility.logs")
    yield
    # Cleanup after test.
    if "reproducibility.logs" in sys.modules:
        del sys.modules["reproducibility.logs"]

from reproducibility.logs import get_logger, log_operation, LogEntry


def test_get_logger_returns_same_instance():
    logger1 = get_logger()
    logger2 = get_logger("another_name")
    assert logger1 is logger2
    assert isinstance(logger1, type(logger2))


def test_log_operation_direct_call_creates_entry():
    logger = get_logger()
    initial_count = len(logger.entries)
    entry = log_operation("test_op", foo="bar")
    assert isinstance(entry, LogEntry)
    assert entry.operation == "test_op"
    assert entry.parameters == {"foo": "bar"}
    assert len(logger.entries) == initial_count + 1
    # JSON round‑trip sanity check.
    json_str = entry.to_json()
    assert isinstance(json_str, str)
    assert '"operation": "test_op"' in json_str


def test_log_operation_decorator_preserves_functionality():
    @log_operation
    def add(a, b):
        return a + b

    result = add(2, 3)
    assert result == 5
    # The decorator should not have logged anything (our tolerant logger
    # only logs when called directly). Ensure no new entry was added.
    logger = get_logger()
    assert all(e.operation != "add" for e in logger.entries)


def test_logger_has_noop_levels():
    logger = get_logger()
    # These calls should not raise.
    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warn")
    logger.error("error")
    logger.critical("critical")


def test_operation_logs_generator_creates_file(tmp_path, monkeypatch):
    # Redirect the output path to a temporary location.
    from reproducibility.operation_logs_generator import (
        _OUTPUT_MD,
        generate_operation_logs_md,
    )

    monkeypatch.setattr(
        "reproducibility.operation_logs_generator._OUTPUT_MD",
        tmp_path / "operation_logs.md",
    )

    # Ensure there is at least one log entry.
    logger = get_logger()
    logger.log("sample_op", x=1)

    output_path = generate_operation_logs_md()
    assert output_path.is_file()
    content = output_path.read_text()
    assert "sample_op" in content
    assert "x=1" in content


# The test suite can be expanded as needed; these basics ensure the
# logging utilities behave as specified by the contract.