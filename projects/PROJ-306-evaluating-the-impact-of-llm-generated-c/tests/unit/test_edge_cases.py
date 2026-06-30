"""
Unit tests for edge cases: missing test suite, generation failure, and other error scenarios.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# Import functions from the project modules
from code.dataset_loader import validate_and_create_catalog
from code.llm_generator import generate_code
from code.coverage_runner import run_coverage, is_humaneval_task, save_coverage_report
from code.main import save_error_report, process_single_task
from code.error_handling import handle_syntax_error, handle_generation_failure, safe_execute_task
from code.analyzer import load_coverage_reports


class TestMissingTestSuite:
    """Tests for handling missing test suites in datasets."""

    def test_validate_catalog_missing_test_suite_field(self, tmp_path):
        """Test that validate_and_create_catalog handles missing test_suite in input data."""
        # Create a mock dataset entry without test_suite
        mock_data = [
            {
                "task_id": "test_1",
                "prompt": "def add(a, b): pass",
                "human_solution": "def add(a, b): return a + b",
                # Missing "test_suite"
                "difficulty": "easy"
            }
        ]

        # Create a temporary directory for output
        output_dir = tmp_path / "processed"
        output_dir.mkdir(parents=True, exist_ok=True)

        # The function should handle missing test_suite gracefully
        # It should either skip the entry or log a warning
        # We test that it doesn't crash
        try:
            # This might raise a KeyError if not handled, or return a partial catalog
            # We mock the file writing to avoid actual I/O
            with patch("builtins.open", mock_open()):
                result = validate_and_create_catalog(mock_data, str(output_dir))
                # If it returns, it handled the case
                assert result is not None
        except KeyError:
            # If it raises KeyError, that's a bug we need to catch
            pytest.fail("validate_and_create_catalog should handle missing test_suite gracefully")

    def test_run_coverage_missing_test_file(self, tmp_path):
        """Test that run_coverage handles missing test file gracefully."""
        generated_code_path = tmp_path / "generated_code.py"
        generated_code_path.write_text("def add(a, b): return a + b")

        test_file_path = tmp_path / "test_missing.py"
        # Do NOT create the test file

        # Run coverage - should fail gracefully or raise a specific error
        # We expect it to raise FileNotFoundError or similar
        with pytest.raises((FileNotFoundError, subprocess.CalledProcessError, SystemExit)):
            run_coverage(
                generated_code_path=str(generated_code_path),
                test_file_path=str(test_file_path),
                output_path=str(tmp_path / "coverage.json")
            )


class TestGenerationFailure:
    """Tests for handling LLM generation failures."""

    def test_generate_code_api_timeout(self, tmp_path):
        """Test that generate_code handles API timeout gracefully."""
        task_id = "test_timeout"
        prompt = "def multiply(a, b): pass"

        # Mock the API call to raise a timeout
        with patch("code.llm_generator.requests.post") as mock_post:
            mock_post.side_effect = Exception("API Timeout")

            result = generate_code(task_id, prompt, str(tmp_path))

            # Should return None or a failure indicator
            assert result is None

    def test_generate_code_invalid_response(self, tmp_path):
        """Test that generate_code handles invalid API response."""
        task_id = "test_invalid"
        prompt = "def subtract(a, b): pass"

        # Mock API response with invalid JSON
        with patch("code.llm_generator.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
            mock_post.return_value = mock_response

            result = generate_code(task_id, prompt, str(tmp_path))

            assert result is None

    def test_handle_generation_failure(self, tmp_path):
        """Test that handle_generation_failure creates proper error report."""
        task_id = "test_gen_failure"
        error_msg = "Model failed to generate code"

        error_report_path = tmp_path / "error_report.json"

        handle_generation_failure(task_id, error_msg, str(error_report_path))

        assert error_report_path.exists()

        with open(error_report_path) as f:
            report = json.load(f)

        assert report["task_id"] == task_id
        assert report["status"] == "failed"
        assert report["error_message"] == error_msg
        assert "timestamp" in report


class TestSyntaxError:
    """Tests for handling syntax errors in generated code."""

    def test_handle_syntax_error(self, tmp_path):
        """Test that handle_syntax_error creates proper error report."""
        task_id = "test_syntax"
        error_msg = "invalid syntax: unexpected EOF"

        error_report_path = tmp_path / "syntax_error.json"

        handle_syntax_error(task_id, error_msg, str(error_report_path))

        assert error_report_path.exists()

        with open(error_report_path) as f:
            report = json.load(f)

        assert report["task_id"] == task_id
        assert report["status"] == "failed"
        assert "SyntaxError" in report["error_message"]

    def test_process_single_task_syntax_error(self, tmp_path):
        """Test that process_single_task handles syntax errors during coverage."""
        # Create a generated file with syntax error
        generated_path = tmp_path / "syntax_error_code.py"
        generated_path.write_text("def broken(:")  # Invalid syntax

        test_path = tmp_path / "test_syntax.py"
        test_path.write_text("def test_pass(): pass")

        # Mock the catalog check to pass
        with patch("code.main.is_humaneval_task", return_value=False):
            result = process_single_task(
                task_id="test_syntax_err",
                generated_code_path=str(generated_path),
                test_file_path=str(test_path),
                output_dir=str(tmp_path),
                catalog_path=None
            )

            # Should return a failure status
            assert result["status"] == "failed"


class TestCoverageEdgeCases:
    """Tests for coverage reporting edge cases."""

    def test_save_coverage_report_missing_fields(self, tmp_path):
        """Test that save_coverage_report handles missing coverage fields."""
        task_id = "test_missing_cov"
        coverage_data = {
            "task_id": task_id,
            "line_coverage": None,  # Missing line coverage
            # Missing branch_coverage entirely
        }

        output_path = tmp_path / "coverage_missing.json"

        # Should handle None/missing values gracefully
        save_coverage_report(task_id, coverage_data, str(output_path))

        assert output_path.exists()

        with open(output_path) as f:
            report = json.load(f)

        assert report["task_id"] == task_id
        # Should have default values or None for missing fields
        assert report.get("line_coverage") is None

    def test_is_humaneval_task_variants(self):
        """Test is_humaneval_task with various task_id formats."""
        assert is_humaneval_task("HumanEval/0") is True
        assert is_humaneval_task("HumanEval/123") is True
        assert is_humaneval_task("MBPP/1") is False
        assert is_humaneval_task("custom_task") is False
        assert is_humaneval_task("human_eval/0") is False  # Case sensitive

    def test_load_coverage_reports_empty_directory(self, tmp_path):
        """Test load_coverage_reports with empty directory."""
        reports_dir = tmp_path / "coverage_reports"
        reports_dir.mkdir()

        reports = load_coverage_reports(str(reports_dir))

        assert reports == []


class TestSafeExecuteTask:
    """Tests for safe_execute_task wrapper."""

    def test_safe_execute_task_success(self, tmp_path):
        """Test safe_execute_task with successful execution."""
        def success_func():
            return {"result": "success"}

        result = safe_execute_task(success_func, "test_success", str(tmp_path))

        assert result["status"] == "success"
        assert result["result"] == "success"

    def test_safe_execute_task_exception(self, tmp_path):
        """Test safe_execute_task with raised exception."""
        def failing_func():
            raise ValueError("Test error")

        result = safe_execute_task(failing_func, "test_fail", str(tmp_path))

        assert result["status"] == "failed"
        assert "ValueError" in result["error_message"]

    def test_safe_execute_task_keyboard_interrupt(self, tmp_path):
        """Test safe_execute_task with KeyboardInterrupt."""
        def interrupt_func():
            raise KeyboardInterrupt()

        result = safe_execute_task(interrupt_func, "test_interrupt", str(tmp_path))

        assert result["status"] == "failed"
        assert "KeyboardInterrupt" in result["error_message"]


class TestErrorReportConsistency:
    """Tests to ensure error reports follow the expected schema."""

    def test_error_report_schema(self, tmp_path):
        """Test that error reports have required fields."""
        task_id = "test_schema"
        error_msg = "Test error for schema validation"

        error_path = tmp_path / "error.json"

        save_error_report(task_id, error_msg, str(error_path))

        with open(error_path) as f:
            report = json.load(f)

        required_fields = ["task_id", "status", "error_message", "timestamp"]
        for field in required_fields:
            assert field in report, f"Missing required field: {field}"

        assert report["status"] == "failed"