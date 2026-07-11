"""
Unit tests for accuracy calculation and retry logic in the InferenceRunner.
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import sys
import os

# Ensure code/src is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference import InferenceRunner


class MockProcess:
    """Mock subprocess.Popen to simulate llama.cpp execution."""
    def __init__(self, return_codes, stdout_output, delay=0):
        self.return_codes = return_codes
        self.stdout_output = stdout_output
        self.delay = delay
        self._call_count = 0
        self.returncode = return_codes[0] if return_codes else 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def wait(self):
        if self.delay:
            time.sleep(self.delay)
        self.returncode = self.return_codes[self._call_count] if self._call_count < len(self.return_codes) else 0
        self._call_count += 1
        return self.returncode

    def communicate(self):
        return (self.stdout_output[self._call_count - 1] if self._call_count <= len(self.stdout_output) else b"", b"")


class TestAccuracyCalculation:
    """Tests for the accuracy calculation logic."""

    def test_accuracy_calculation_exact_match(self):
        """Test that exact matches yield 100% accuracy."""
        runner = InferenceRunner()
        examples = [
            {"input": "Q1", "expected": "A", "generated": "A"},
            {"input": "Q2", "expected": "B", "generated": "B"},
        ]
        accuracy = runner.calculate_accuracy(examples)
        assert accuracy == 1.0, f"Expected 1.0, got {accuracy}"

    def test_accuracy_calculation_partial_match(self):
        """Test that partial matches yield correct percentage."""
        runner = InferenceRunner()
        examples = [
            {"input": "Q1", "expected": "A", "generated": "A"},
            {"input": "Q2", "expected": "B", "generated": "C"},
            {"input": "Q3", "expected": "D", "generated": "D"},
        ]
        accuracy = runner.calculate_accuracy(examples)
        assert accuracy == 2/3, f"Expected 0.666..., got {accuracy}"

    def test_accuracy_calculation_no_match(self):
        """Test that no matches yield 0% accuracy."""
        runner = InferenceRunner()
        examples = [
            {"input": "Q1", "expected": "A", "generated": "B"},
            {"input": "Q2", "expected": "C", "generated": "D"},
        ]
        accuracy = runner.calculate_accuracy(examples)
        assert accuracy == 0.0, f"Expected 0.0, got {accuracy}"

    def test_accuracy_calculation_empty_list(self):
        """Test that empty list yields 0% accuracy (or handles gracefully)."""
        runner = InferenceRunner()
        examples = []
        accuracy = runner.calculate_accuracy(examples)
        assert accuracy == 0.0, f"Expected 0.0 for empty list, got {accuracy}"

    def test_accuracy_calculation_case_insensitivity(self):
        """Test that accuracy calculation is case-insensitive for expected vs generated."""
        runner = InferenceRunner()
        examples = [
            {"input": "Q1", "expected": "A", "generated": "a"},
            {"input": "Q2", "expected": "B", "generated": "b"},
        ]
        accuracy = runner.calculate_accuracy(examples)
        assert accuracy == 1.0, f"Expected 1.0 (case-insensitive), got {accuracy}"

    def test_accuracy_calculation_whitespace_normalization(self):
        """Test that whitespace is normalized before comparison."""
        runner = InferenceRunner()
        examples = [
            {"input": "Q1", "expected": "A", "generated": "  A  "},
            {"input": "Q2", "expected": "B", "generated": "B\n"},
        ]
        accuracy = runner.calculate_accuracy(examples)
        assert accuracy == 1.0, f"Expected 1.0 (whitespace normalized), got {accuracy}"


class TestRetryLogic:
    """Tests for the retry logic in InferenceRunner."""

    @patch('src.inference.subprocess.Popen')
    def test_retry_on_failure_success_after_attempts(self, mock_popen):
        """Test that the runner retries on failure and succeeds eventually."""
        # Simulate 2 failures, then 1 success
        mock_process = MockProcess(
            return_codes=[1, 1, 0],  # 2 failures, 1 success
            stdout_output=[b"Error", b"Error", b"Success\nAnswer: X"],
            delay=0.01
        )
        mock_popen.return_value = mock_process

        runner = InferenceRunner(max_retries=3, base_wait_time=0.01)
        result = runner.run_inference("test_prompt")

        # Should have called Popen 3 times
        assert mock_popen.call_count == 3
        assert result["success"] is True
        assert result["output"].strip() == "Success\nAnswer: X"

    @patch('src.inference.subprocess.Popen')
    def test_retry_exhaustion(self, mock_popen):
        """Test that the runner fails after exhausting retries."""
        # Simulate 3 failures
        mock_process = MockProcess(
            return_codes=[1, 1, 1],
            stdout_output=[b"Error", b"Error", b"Error"],
            delay=0.01
        )
        mock_popen.return_value = mock_process

        runner = InferenceRunner(max_retries=3, base_wait_time=0.01)
        result = runner.run_inference("test_prompt")

        # Should have called Popen 3 times
        assert mock_popen.call_count == 3
        assert result["success"] is False
        assert "max retries" in result["error"].lower()

    @patch('src.inference.subprocess.Popen')
    def test_retry_with_delay(self, mock_popen):
        """Test that retry logic includes a delay between attempts."""
        mock_process = MockProcess(
            return_codes=[1, 0],
            stdout_output=[b"Error", b"Success"],
            delay=0.01
        )
        mock_popen.return_value = mock_process

        runner = InferenceRunner(max_retries=2, base_wait_time=0.05)
        start_time = time.time()
        result = runner.run_inference("test_prompt")
        elapsed = time.time() - start_time

        # Should have called Popen 2 times
        assert mock_popen.call_count == 2
        # Should have waited at least base_wait_time (0.05s)
        assert elapsed >= 0.04, f"Expected delay of at least 0.05s, got {elapsed}s"
        assert result["success"] is True

    @patch('src.inference.subprocess.Popen')
    def test_no_retry_on_success_first_try(self, mock_popen):
        """Test that no retries occur if the first attempt succeeds."""
        mock_process = MockProcess(
            return_codes=[0],
            stdout_output=[b"Success"],
            delay=0
        )
        mock_popen.return_value = mock_process

        runner = InferenceRunner(max_retries=3, base_wait_time=0.01)
        result = runner.run_inference("test_prompt")

        # Should have called Popen only once
        assert mock_popen.call_count == 1
        assert result["success"] is True

    @patch('src.inference.subprocess.Popen')
    def test_retry_handles_timeout_exception(self, mock_popen):
        """Test that retry logic handles subprocess timeout exceptions."""
        def side_effect(*args, **kwargs):
            if side_effect.call_count < 2:
                side_effect.call_count += 1
                raise TimeoutError("Process timed out")
            return MockProcess(
                return_codes=[0],
                stdout_output=[b"Success"],
                delay=0
            )

        side_effect.call_count = 0
        mock_popen.side_effect = side_effect

        runner = InferenceRunner(max_retries=2, base_wait_time=0.01)
        result = runner.run_inference("test_prompt")

        # Should have called Popen 2 times
        assert mock_popen.call_count == 2
        assert result["success"] is True


class TestInferenceRunnerIntegration:
    """Integration-style tests for the InferenceRunner."""

    def test_run_inference_parses_json_output(self):
        """Test that the runner correctly parses JSON output from the model."""
        # This is a unit test that mocks the subprocess but verifies the parsing logic
        runner = InferenceRunner()
        
        # Mock the run_inference logic to return a specific JSON string
        mock_output = '{"answer": "42", "confidence": 0.9}'
        examples = [{"input": "Q", "expected": "42", "generated": mock_output}]
        
        # Manually test the parsing logic
        parsed = runner._parse_model_output(mock_output)
        assert parsed["answer"] == "42"
        assert parsed["confidence"] == 0.9

    def test_run_inference_handles_non_json_output(self):
        """Test that the runner handles non-JSON output gracefully."""
        runner = InferenceRunner()
        
        mock_output = "The answer is 42."
        parsed = runner._parse_model_output(mock_output)
        
        # Should return the raw output in a field if not JSON
        assert "raw_output" in parsed
        assert parsed["raw_output"] == "The answer is 42."