"""
Unit tests for the failure_classifier module.
"""

import pytest
import json
import tempfile
from pathlib import Path
import sys

# Ensure parent directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from analysis.failure_classifier import classify_failure, FailureCategory, process_results


class TestClassifyFailure:
    """Tests for the classify_failure function."""

    def test_missing_context_import_error(self):
        log = "ImportError: No module named 'pandas'"
        category, reason = classify_failure(log)
        assert category == FailureCategory.MISSING_CONTEXT
        assert "Missing context" in reason

    def test_missing_context_name_error(self):
        log = "NameError: name 'variable_x' is not defined"
        category, reason = classify_failure(log)
        assert category == FailureCategory.MISSING_CONTEXT
        assert "Missing context" in reason

    def test_missing_context_file_not_found(self):
        log = "FileNotFoundError: [Errno 2] No such file or directory: 'data.csv'"
        category, reason = classify_failure(log)
        assert category == FailureCategory.MISSING_CONTEXT
        assert "Missing context" in reason

    def test_reasoning_error_assertion(self):
        log = "AssertionError: Expected 5 but got 3"
        category, reason = classify_failure(log)
        assert category == FailureCategory.REASONING_ERROR
        assert "Reasoning error" in reason

    def test_reasoning_error_value_error(self):
        log = "ValueError: invalid literal for int() with base 10: 'abc'"
        category, reason = classify_failure(log)
        assert category == FailureCategory.REASONING_ERROR
        assert "Reasoning error" in reason

    def test_timeout_detected(self):
        log = "TimeLimitExceeded: Execution took too long"
        category, reason = classify_failure(log)
        assert category == FailureCategory.TIMEOUT
        assert "Timeout" in reason

    def test_system_error_memory(self):
        log = "MemoryError: Unable to allocate memory"
        category, reason = classify_failure(log)
        assert category == FailureCategory.SYSTEM_ERROR
        assert "System error" in reason

    def test_success_detected(self):
        log = "All tests passed successfully."
        category, reason = classify_failure(log)
        assert category == FailureCategory.SUCCESS
        assert "success" in reason.lower()

    def test_no_log_provided(self):
        category, reason = classify_failure(None)
        assert category == FailureCategory.UNKNOWN
        assert "No log provided" in reason

    def test_unknown_failure(self):
        log = "Some generic error occurred that doesn't match patterns"
        category, reason = classify_failure(log)
        assert category == FailureCategory.UNKNOWN
        assert "No specific failure pattern" in reason


class TestProcessResults:
    """Tests for the process_results function."""

    def test_process_baseline_jsonl(self):
        # Create temporary input file
        input_data = [
            {"id": 1, "status": "failed", "sandbox_log": "ImportError: No module named 'numpy'"},
            {"id": 2, "status": "failed", "sandbox_log": "AssertionError: Test failed"},
            {"id": 3, "status": "success", "sandbox_log": "Tests passed"},
            {"id": 4, "status": "failed", "sandbox_log": "TimeLimitExceeded"},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"

            with open(input_path, "w") as f:
                for record in input_data:
                    f.write(json.dumps(record) + "\n")

            counts = process_results(input_path, output_path)

            # Verify counts
            assert counts["missing_context"] == 1
            assert counts["reasoning_error"] == 1
            assert counts["success"] == 1
            assert counts["timeout"] == 1

            # Verify output file structure
            with open(output_path, "r") as f:
                output_records = [json.loads(line) for line in f]

            assert len(output_records) == 4
            assert "failure_classification" in output_records[0]
            assert output_records[0]["failure_classification"]["category"] == "missing_context"
            assert output_records[1]["failure_classification"]["category"] == "reasoning_error"
            assert output_records[2]["failure_classification"]["category"] == "success"
            assert output_records[3]["failure_classification"]["category"] == "timeout"

    def test_missing_input_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"

            with pytest.raises(FileNotFoundError):
                process_results(input_path, output_path)