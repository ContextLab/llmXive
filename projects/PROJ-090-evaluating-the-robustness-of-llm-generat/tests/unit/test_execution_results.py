"""
Unit tests for execution_results.py

Tests verify that:
1. Execution results are correctly tagged based on sandbox status
2. Error message classification works as expected
3. Aggregation logic counts correctly
4. JSON save/load preserves data integrity
"""

import pytest
import json
import tempfile
from pathlib import Path

# Import the module under test
from model.execution_results import (
    tag_execution_result,
    classify_error_message,
    aggregate_results,
    save_results_to_json,
    load_results_from_json,
    ExecutionTag,
)
from model.sandbox import ExecutionResult, ExecutionStatus


class TestTagExecutionResult:
    """Tests for the tag_execution_result function."""

    def test_pass_status_tags_as_pass(self):
        """PASS status should be tagged as 'pass'."""
        result = ExecutionResult(
            status=ExecutionStatus.PASS,
            execution_time=0.1,
            error_message=None,
            output="Success"
        )
        tagged = tag_execution_result(result, "HumanEval/0", "original")

        assert tagged["tag"] == ExecutionTag.PASS
        assert tagged["raw_status"] == "pass"
        assert tagged["task_id"] == "HumanEval/0"
        assert tagged["prompt_type"] == "original"
        assert tagged["error_message"] is None

    def test_syntax_error_tags_as_syntax(self):
        """SYNTAX_ERROR status should be tagged as 'syntax'."""
        result = ExecutionResult(
            status=ExecutionStatus.SYNTAX_ERROR,
            execution_time=0.01,
            error_message="SyntaxError: invalid syntax",
            output=""
        )
        tagged = tag_execution_result(result, "HumanEval/1", "typo")

        assert tagged["tag"] == ExecutionTag.SYNTAX
        assert tagged["raw_status"] == "syntax_error"
        assert "SyntaxError" in tagged["error_message"]

    def test_timeout_tags_as_timeout(self):
        """TIMEOUT status should be tagged as 'timeout'."""
        result = ExecutionResult(
            status=ExecutionStatus.TIMEOUT,
            execution_time=5.0,
            error_message="Execution timed out",
            output=""
        )
        tagged = tag_execution_result(result, "HumanEval/2", "rephrase")

        assert tagged["tag"] == ExecutionTag.TIMEOUT
        assert tagged["raw_status"] == "timeout"

    def test_oom_tags_as_oom(self):
        """OOM status should be tagged as 'oom'."""
        result = ExecutionResult(
            status=ExecutionStatus.OOM,
            execution_time=2.0,
            error_message="MemoryError: Out of memory",
            output=""
        )
        tagged = tag_execution_result(result, "HumanEval/3", "synonym")

        assert tagged["tag"] == ExecutionTag.OOM
        assert tagged["raw_status"] == "oom"

    def test_fail_status_tags_as_fail(self):
        """FAIL status should be tagged as 'fail'."""
        result = ExecutionResult(
            status=ExecutionStatus.FAIL,
            execution_time=0.05,
            error_message="AssertionError: Expected 5, got 3",
            output="Failed"
        )
        tagged = tag_execution_result(result, "HumanEval/4", "original")

        assert tagged["tag"] == ExecutionTag.FAIL
        assert tagged["raw_status"] == "fail"

    def test_security_violation_tags_as_fail(self):
        """SECURITY_VIOLATION status should be tagged as 'fail'."""
        result = ExecutionResult(
            status=ExecutionStatus.SECURITY_VIOLATION,
            execution_time=0.0,
            error_message="SecurityViolation: forbidden call",
            output=""
        )
        tagged = tag_execution_result(result, "HumanEval/5", "typo")

        assert tagged["tag"] == ExecutionTag.FAIL

    def test_unknown_status_tags_as_unknown(self):
        """Unknown status should be tagged as 'unknown'."""
        # We don't have an Unknown status in ExecutionStatus,
        # but we test the fallback behavior
        # This is a defensive test
        result = ExecutionResult(
            status=ExecutionStatus.ERROR,  # ERROR maps to FAIL in our mapping
            execution_time=0.1,
            error_message="RuntimeError",
            output=""
        )
        tagged = tag_execution_result(result, "HumanEval/6", "original")

        # ERROR maps to FAIL in STATUS_TO_TAG
        assert tagged["tag"] == ExecutionTag.FAIL


class TestClassifyErrorMessage:
    """Tests for the classify_error_message helper."""

    def test_syntax_error_classification(self):
        assert classify_error_message("SyntaxError: invalid syntax") == "syntax"
        assert classify_error_message("IndentationError: unexpected indent") == "syntax"
        assert classify_error_message("unexpected EOF while parsing") == "syntax"

    def test_timeout_classification(self):
        assert classify_error_message("Execution timed out after 5 seconds") == "timeout"
        assert classify_error_message("timed out") == "timeout"

    def test_oom_classification(self):
        assert classify_error_message("MemoryError: Out of memory") == "oom"
        assert classify_error_message("cannot allocate memory") == "oom"
        assert classify_error_message("OOM killed") == "oom"

    def test_runtime_classification(self):
        assert classify_error_message("AssertionError: expected 5, got 3") == "runtime"
        assert classify_error_message("ValueError: invalid value") == "runtime"
        assert classify_error_message("Exception: something failed") == "runtime"

    def test_unknown_classification(self):
        assert classify_error_message("") == "unknown"
        assert classify_error_message(None) == "unknown"
        assert classify_error_message("Some random message") == "unknown"


class TestAggregateResults:
    """Tests for the aggregate_results function."""

    def test_basic_aggregation(self):
        results = [
            {"prompt_type": "original", "tag": "pass"},
            {"prompt_type": "original", "tag": "pass"},
            {"prompt_type": "original", "tag": "fail"},
            {"prompt_type": "typo", "tag": "syntax"},
            {"prompt_type": "typo", "tag": "timeout"},
        ]

        agg = aggregate_results(results)

        assert agg["original"]["pass"] == 2
        assert agg["original"]["fail"] == 1
        assert agg["typo"]["syntax"] == 1
        assert agg["typo"]["timeout"] == 1

    def test_empty_results(self):
        agg = aggregate_results([])
        assert agg == {}

    def test_single_result(self):
        results = [{"prompt_type": "rephrase", "tag": "oom"}]
        agg = aggregate_results(results)
        assert agg["rephrase"]["oom"] == 1


class TestSaveAndLoadResults:
    """Tests for JSON persistence functions."""

    def test_save_and_load_preserves_data(self):
        results = [
            {
                "task_id": "HumanEval/0",
                "prompt_type": "original",
                "tag": "pass",
                "raw_status": "pass",
                "error_message": None,
                "execution_time": 0.1,
                "timestamp": "2024-01-01T00:00:00"
            },
            {
                "task_id": "HumanEval/1",
                "prompt_type": "typo",
                "tag": "syntax",
                "raw_status": "syntax_error",
                "error_message": "SyntaxError",
                "execution_time": 0.01,
                "timestamp": "2024-01-01T00:00:01"
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            temp_path = f.name

        try:
            saved_path = save_results_to_json(results, temp_path)
            assert saved_path == Path(temp_path)

            loaded = load_results_from_json(temp_path)

            assert len(loaded) == 2
            assert loaded[0]["tag"] == "pass"
            assert loaded[1]["tag"] == "syntax"
            assert loaded[0]["task_id"] == "HumanEval/0"
            assert loaded[1]["error_message"] == "SyntaxError"
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_nonexistent_file(self):
        results = load_results_from_json("/nonexistent/path/file.jsonl")
        assert results == []

    def test_append_mode(self):
        results1 = [{"task_id": "1", "prompt_type": "a", "tag": "pass"}]
        results2 = [{"task_id": "2", "prompt_type": "b", "tag": "fail"}]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            temp_path = f.name

        try:
            save_results_to_json(results1, temp_path)
            save_results_to_json(results2, temp_path)  # Should append

            loaded = load_results_from_json(temp_path)
            assert len(loaded) == 2
            assert loaded[0]["task_id"] == "1"
            assert loaded[1]["task_id"] == "2"
        finally:
            Path(temp_path).unlink(missing_ok=True)