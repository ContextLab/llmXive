"""
Unit tests for the failure_classifier module.
"""
import pytest
import json
import tempfile
from pathlib import Path
import sys
from analysis.failure_classifier import classify_failure, FailureCategory, process_results


class TestClassifyFailure:
    """Tests for the classify_failure function."""

    def test_detects_file_not_found(self):
        """Test that 'file not found' is classified as missing_context."""
        log = "Error: File not found: /path/to/file.py"
        result = classify_failure(log)
        assert result == FailureCategory.MISSING_CONTEXT.value

    def test_detects_cannot_locate(self):
        """Test that 'cannot locate' is classified as missing_context."""
        log = "RuntimeError: Cannot locate the specified module."
        result = classify_failure(log)
        assert result == FailureCategory.MISSING_CONTEXT.value

    def test_detects_not_in_context(self):
        """Test that 'not in context' is classified as missing_context."""
        log = "The file src/utils.py is not in context."
        result = classify_failure(log)
        assert result == FailureCategory.MISSING_CONTEXT.value

    def test_detects_reasoning_error(self):
        """Test that logic errors are classified as reasoning_error."""
        log = "The model produced incorrect logic for the sorting algorithm."
        result = classify_failure(log)
        assert result == FailureCategory.REASONING_ERROR.value

    def test_detects_hallucination(self):
        """Test that hallucination is classified as reasoning_error."""
        log = "The model hallucinated a function that does not exist."
        result = classify_failure(log)
        assert result == FailureCategory.REASONING_ERROR.value

    def test_empty_log(self):
        """Test that empty log returns unknown."""
        log = ""
        result = classify_failure(log)
        assert result == FailureCategory.UNKNOWN.value

    def test_unknown_error(self):
        """Test that generic errors return unknown."""
        log = "A generic error occurred."
        result = classify_failure(log)
        assert result == FailureCategory.UNKNOWN.value

    def test_priority_missing_over_reasoning(self):
        """Test that missing context takes priority if both keywords appear."""
        # This is an edge case: if a file is not found, it's missing context,
        # even if the error message also says "logic failed to load".
        log = "File not found, logic failed to load."
        result = classify_failure(log)
        assert result == FailureCategory.MISSING_CONTEXT.value


class TestProcessResults:
    """Tests for the process_results function."""

    def test_process_single_file(self):
        """Test processing a single JSONL file with mixed errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"

            # Create input data
            records = [
                {"id": 1, "status": "failed", "error_message": "File not found"},
                {"id": 2, "status": "failed", "error_message": "Logic error"},
                {"id": 3, "status": "failed", "error_message": "Generic error"},
                {"id": 4, "status": "passed", "output": "Success"}
            ]

            with open(input_path, 'w') as f:
                for r in records:
                    f.write(json.dumps(r) + '\n')

            counts = process_results(str(input_path), str(output_path))

            # Verify counts
            assert counts[FailureCategory.MISSING_CONTEXT.value] == 1
            assert counts[FailureCategory.REASONING_ERROR.value] == 1
            assert counts[FailureCategory.UNKNOWN.value] == 1

            # Verify output file
            with open(output_path, 'r') as f:
                lines = f.readlines()

            assert len(lines) == 4
            data = json.loads(lines[0])
            assert data['failure_category'] == FailureCategory.MISSING_CONTEXT.value
            data = json.loads(lines[1])
            assert data['failure_category'] == FailureCategory.REASONING_ERROR.value

    def test_file_not_found_raises(self):
        """Test that process_results raises FileNotFoundError for missing input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "nonexistent.jsonl"
            output_path = Path(tmpdir) / "output.jsonl"

            with pytest.raises(FileNotFoundError):
                process_results(str(input_path), str(output_path))