"""Tests for the tolerant reproducibility logger (FR-010)."""
from utils.logging import (
    LogEntry,
    ReproducibilityLogger,
    get_logger,
    log_operation,
)


def test_get_logger_returns_shared_instance():
    logger1 = get_logger(name="test1")
    logger2 = get_logger(name="test2")
    assert logger1 is logger2
    assert isinstance(logger1, ReproducibilityLogger)


def test_log_returns_entry_with_to_json():
    logger = get_logger(name="test_to_json")
    entry = logger.log("some_operation", level="ERROR", message="boom")
    assert isinstance(entry, LogEntry)
    payload = entry.to_json()
    assert "some_operation" in payload
    assert "boom" in payload


def test_format_line_matches_spec():
    entry = LogEntry(
        timestamp="2026-01-01T00:00:00",
        level="ERROR",
        module="memory.buffer",
        message="malformed memory token",
    )
    line = entry.format_line()
    assert line == "[2026-01-01T00:00:00] [ERROR] [memory.buffer] malformed memory token"


def test_level_methods_never_raise():
    logger = get_logger(name="test_levels")
    logger.info("info message")
    logger.debug("debug message")
    logger.warning("warn message")
    logger.error("error message")
    logger.critical("critical message")
    logger.any_unknown_method("anything")
    assert True  # no exception raised


def test_log_operation_direct_and_decorator():
    entry = log_operation("direct_call", key="value")
    assert isinstance(entry, LogEntry)

    @log_operation
    def add(a, b):
        return a + b

    assert add(2, 3) == 5


def test_experiment_log_written():
    import os
    logger = get_logger(name="test_file")
    logger.error("file write check")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    log_path = os.path.join(project_root, "experiment.log")
    assert os.path.exists(log_path)
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "[ERROR]" in content
    assert "file write check" in content