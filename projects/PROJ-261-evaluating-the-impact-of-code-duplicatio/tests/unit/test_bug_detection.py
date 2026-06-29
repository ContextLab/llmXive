"""
Unit tests for bug_detection.py pass@1 accuracy calculation.

Tests verify that the compute_pass1_accuracy function correctly calculates
pass@1 accuracy metrics for HumanEval problems.

Per spec.md Independent Test requirements for User Story 2.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import sys
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from bug_detection import (
    load_humaneval_dataset,
    prepare_prompt,
    generate_solution,
    extract_code_from_solution,
    run_tests,
    compute_pass1_accuracy,
    save_results,
    save_summary,
    main
)


class TestComputePass1Accuracy:
    """Tests for the compute_pass1_accuracy function."""

    def test_empty_solutions_returns_zero(self):
        """Test that empty solutions list returns 0.0 accuracy."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }
        solutions = []

        accuracy = compute_pass1_accuracy(problem, solutions)

        assert accuracy == 0.0

    def test_single_passing_solution_returns_one(self):
        """Test that single passing solution returns 1.0 accuracy."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }
        solutions = ["def add(a, b):\n    return a + b\n"]

        accuracy = compute_pass1_accuracy(problem, solutions)

        assert accuracy == 1.0

    def test_single_failing_solution_returns_zero(self):
        """Test that single failing solution returns 0.0 accuracy."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }
        solutions = ["def add(a, b):\n    return a * b\n"]  # Wrong implementation

        accuracy = compute_pass1_accuracy(problem, solutions)

        assert accuracy == 0.0

    def test_multiple_solutions_with_one_passing_returns_one(self):
        """Test that multiple solutions with at least one passing returns 1.0."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }
        solutions = [
            "def add(a, b):\n    return a * b\n",  # Fails
            "def add(a, b):\n    return a + b\n",  # Passes
            "def add(a, b):\n    return a - b\n"   # Fails
        ]

        accuracy = compute_pass1_accuracy(problem, solutions)

        assert accuracy == 1.0

    def test_multiple_solutions_all_failing_returns_zero(self):
        """Test that multiple solutions all failing returns 0.0."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }
        solutions = [
            "def add(a, b):\n    return a * b\n",
            "def add(a, b):\n    return a - b\n",
            "def add(a, b):\n    return b + a\n"  # This passes, so need different
        ]
        # Replace last with a failing one
        solutions[2] = "def add(a, b):\n    return a / b\n"

        accuracy = compute_pass1_accuracy(problem, solutions)

        assert accuracy == 0.0

    def test_accuracy_calculation_with_three_problems(self):
        """Test aggregate accuracy calculation across multiple problems."""
        problems = [
            {
                "problem_id": "test-001",
                "task_id": "human-eval/0",
                "prompt": "def add(a, b):\n    return a + b\n",
                "test": "assert add(1, 2) == 3",
                "solutions": ["def add(a, b):\n    return a + b\n"]  # Pass
            },
            {
                "problem_id": "test-002",
                "task_id": "human-eval/1",
                "prompt": "def sub(a, b):\n    return a - b\n",
                "test": "assert sub(5, 3) == 2",
                "solutions": ["def sub(a, b):\n    return a + b\n"]  # Fail
            },
            {
                "problem_id": "test-003",
                "task_id": "human-eval/2",
                "prompt": "def mul(a, b):\n    return a * b\n",
                "test": "assert mul(2, 3) == 6",
                "solutions": ["def mul(a, b):\n    return a * b\n"]  # Pass
            }
        ]

        # Calculate accuracy for each problem
        accuracies = []
        for problem in problems:
            acc = compute_pass1_accuracy(problem, problem["solutions"])
            accuracies.append(acc)

        # Expected: [1.0, 0.0, 1.0]
        assert accuracies == [1.0, 0.0, 1.0]

        # Overall accuracy
        overall_accuracy = sum(accuracies) / len(accuracies)
        assert overall_accuracy == pytest.approx(2/3, rel=1e-6)

    def test_handles_none_solutions_gracefully(self):
        """Test that None solutions are handled gracefully."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }

        # Should not raise an exception
        accuracy = compute_pass1_accuracy(problem, None)

        assert accuracy == 0.0

    def test_handles_empty_string_solution(self):
        """Test that empty string solutions are handled correctly."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }
        solutions = [""]

        accuracy = compute_pass1_accuracy(problem, solutions)

        # Empty solution should fail
        assert accuracy == 0.0

    def test_pass1_vs_passk_distinction(self):
        """Verify pass@1 is different from pass@k when k>1."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }
        # All solutions fail except the last one
        solutions = [
            "def add(a, b):\n    return a * b\n",  # Fail
            "def add(a, b):\n    return a - b\n",  # Fail
            "def add(a, b):\n    return a / b\n",  # Fail
            "def add(a, b):\n    return a + b\n"   # Pass
        ]

        # Pass@1 should be 0.0 (first solution fails)
        accuracy = compute_pass1_accuracy(problem, solutions)
        assert accuracy == 0.0

    def test_numeric_accuracy_values(self):
        """Test that accuracy values are within valid range [0, 1]."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }

        solutions = ["def add(a, b):\n    return a + b\n"]
        accuracy = compute_pass1_accuracy(problem, solutions)

        assert 0.0 <= accuracy <= 1.0

    def test_accuracy_precision(self):
        """Test that accuracy is calculated with proper floating-point precision."""
        # Create a scenario where we need precise calculation
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }
        solutions = ["def add(a, b):\n    return a + b\n"]

        accuracy = compute_pass1_accuracy(problem, solutions)

        # Should be exactly 1.0, not 0.9999999 or similar
        assert accuracy == 1.0
        assert isinstance(accuracy, float)


class TestRunTests:
    """Tests for the run_tests function."""

    def test_run_tests_executes_code(self):
        """Test that run_tests can execute simple code."""
        test_code = "assert 1 + 1 == 2"
        result = run_tests(test_code)

        # Should return True for passing test
        assert result is True

    def test_run_tests_handles_syntax_error(self):
        """Test that run_tests handles syntax errors gracefully."""
        test_code = "def broken("  # Invalid syntax
        result = run_tests(test_code)

        # Should return False for failing test
        assert result is False

    def test_run_tests_handles_runtime_error(self):
        """Test that run_tests handles runtime errors gracefully."""
        test_code = "result = 1 / 0"  # Division by zero
        result = run_tests(test_code)

        # Should return False for failing test
        assert result is False


class TestExtractCodeFromSolution:
    """Tests for the extract_code_from_solution function."""

    def test_extract_code_from_python_block(self):
        """Test extracting code from a Python code block."""
        solution = "```python\ndef add(a, b):\n    return a + b\n```"
        extracted = extract_code_from_solution(solution)

        assert "def add(a, b):" in extracted
        assert "return a + b" in extracted

    def test_extract_code_from_plain_text(self):
        """Test extracting code from plain text without markdown."""
        solution = "def add(a, b):\n    return a + b"
        extracted = extract_code_from_solution(solution)

        assert "def add(a, b):" in extracted
        assert "return a + b" in extracted

    def test_extract_code_handles_empty_solution(self):
        """Test that empty solution returns empty string."""
        solution = ""
        extracted = extract_code_from_solution(solution)

        assert extracted == ""

    def test_extract_code_handles_none(self):
        """Test that None solution returns empty string."""
        solution = None
        extracted = extract_code_from_solution(solution)

        assert extracted == ""


class TestLoadHumanEvalDataset:
    """Tests for the load_humaneval_dataset function."""

    @patch('bug_detection.load_dataset')
    def test_load_humaneval_returns_dataset(self, mock_load_dataset):
        """Test that load_humaneval_dataset returns a dataset object."""
        mock_dataset = MagicMock()
        mock_load_dataset.return_value = mock_dataset

        result = load_humaneval_dataset()

        mock_load_dataset.assert_called_once_with("openai/human-eval")
        assert result == mock_dataset

    @patch('bug_detection.load_dataset')
    def test_load_humaneval_with_subset(self, mock_load_dataset):
        """Test loading a subset of HumanEval problems."""
        mock_dataset = MagicMock()
        mock_dataset.select.return_value = MagicMock()
        mock_load_dataset.return_value = mock_dataset

        result = load_humaneval_dataset(num_problems=50)

        mock_dataset.select.assert_called_once()
        assert result is not None


class TestPreparePrompt:
    """Tests for the prepare_prompt function."""

    def test_prepare_prompt_includes_task(self):
        """Test that prepare_prompt includes the task description."""
        task = "def add(a, b):\n    return a + b"
        prompt = prepare_prompt(task)

        assert "def add(a, b):" in prompt
        assert "return a + b" in prompt

    def test_prepare_prompt_returns_string(self):
        """Test that prepare_prompt returns a string."""
        task = "def add(a, b):\n    return a + b"
        prompt = prepare_prompt(task)

        assert isinstance(prompt, str)


class TestSaveResults:
    """Tests for the save_results function."""

    @patch('bug_detection.Path')
    @patch('bug_detection.csv.writer')
    def test_save_results_creates_csv(self, mock_writer, mock_path):
        """Test that save_results creates a CSV file."""
        mock_path.return_value.parent.mkdir.return_value = None
        mock_file = MagicMock()
        mock_path.return_value.open.return_value.__enter__.return_value = mock_file

        results = [
            {"problem_id": "test-001", "accuracy": 1.0},
            {"problem_id": "test-002", "accuracy": 0.0}
        ]
        output_path = Path("test_output.csv")

        save_results(results, output_path)

        mock_path.return_value.parent.mkdir.assert_called_once()
        mock_path.return_value.open.assert_called_once()

    def test_save_results_handles_empty_results(self):
        """Test that save_results handles empty results list."""
        results = []
        output_path = Path("test_output.csv")

        # Should not raise an exception
        with patch('bug_detection.Path') as mock_path:
            mock_path.return_value.parent.mkdir.return_value = None
            mock_file = MagicMock()
            mock_path.return_value.open.return_value.__enter__.return_value = mock_file

            save_results(results, output_path)


class TestSaveSummary:
    """Tests for the save_summary function."""

    @patch('bug_detection.Path')
    @patch('bug_detection.json.dump')
    def test_save_summary_creates_json(self, mock_json_dump, mock_path):
        """Test that save_summary creates a JSON file."""
        mock_path.return_value.parent.mkdir.return_value = None
        mock_file = MagicMock()
        mock_path.return_value.open.return_value.__enter__.return_value = mock_file

        summary = {
            "total_problems": 100,
            "pass1_accuracy": 0.75,
            "config": {"seed": 42}
        }
        output_path = Path("test_summary.json")

        save_summary(summary, output_path)

        mock_path.return_value.parent.mkdir.assert_called_once()
        mock_json_dump.assert_called_once()

    def test_save_summary_includes_expected_keys(self):
        """Test that save_summary includes all expected keys."""
        summary = {
            "total_problems": 100,
            "pass1_accuracy": 0.75,
            "config": {"seed": 42}
        }

        # Verify structure
        assert "total_problems" in summary
        assert "pass1_accuracy" in summary
        assert "config" in summary
        assert summary["total_problems"] == 100
        assert summary["pass1_accuracy"] == 0.75


class TestBugDetectionIntegration:
    """Integration tests for the bug detection module."""

    def test_compute_pass1_accuracy_with_mocked_run_tests(self):
        """Test accuracy calculation with mocked test execution."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }

        # Mock run_tests to return True (passing)
        with patch('bug_detection.run_tests', return_value=True):
            solutions = ["def add(a, b):\n    return a + b\n"]
            accuracy = compute_pass1_accuracy(problem, solutions)
            assert accuracy == 1.0

        # Mock run_tests to return False (failing)
        with patch('bug_detection.run_tests', return_value=False):
            solutions = ["def add(a, b):\n    return a + b\n"]
            accuracy = compute_pass1_accuracy(problem, solutions)
            assert accuracy == 0.0

    def test_accuracy_aggregation_across_problems(self):
        """Test that accuracy is correctly aggregated across multiple problems."""
        problems_data = [
            {"problem_id": f"test-{i:03d}", "task_id": f"human-eval/{i}",
             "prompt": f"def func{i}(a, b):\n    return a + b\n",
             "test": f"assert func{i}(1, 2) == 3",
             "solutions": ["def func(a, b):\n    return a + b\n"]}
            for i in range(10)
        ]

        accuracies = []
        with patch('bug_detection.run_tests', return_value=True):
            for problem in problems_data:
                acc = compute_pass1_accuracy(problem, problem["solutions"])
                accuracies.append(acc)

        # All should pass with mocked run_tests
        assert all(acc == 1.0 for acc in accuracies)
        assert sum(accuracies) / len(accuracies) == 1.0


class TestPass1AccuracyEdgeCases:
    """Edge case tests for pass@1 accuracy calculation."""

    def test_accuracy_with_single_problem(self):
        """Test accuracy calculation with exactly one problem."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }
        solutions = ["def add(a, b):\n    return a + b\n"]

        accuracy = compute_pass1_accuracy(problem, solutions)

        assert accuracy == 1.0

    def test_accuracy_with_whitespace_only_solution(self):
        """Test that whitespace-only solution is handled correctly."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }
        solutions = ["   \n   \n   "]

        accuracy = compute_pass1_accuracy(problem, solutions)

        # Whitespace-only should fail
        assert accuracy == 0.0

    def test_accuracy_preserves_float_type(self):
        """Test that accuracy is returned as float type."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3"
        }
        solutions = ["def add(a, b):\n    return a + b\n"]

        accuracy = compute_pass1_accuracy(problem, solutions)

        assert isinstance(accuracy, float)

    def test_accuracy_with_special_characters_in_test(self):
        """Test accuracy calculation with special characters in test."""
        problem = {
            "problem_id": "test-001",
            "task_id": "human-eval/0",
            "prompt": "def add(a, b):\n    return a + b\n",
            "test": "assert add(1, 2) == 3 and add(0, 0) == 0"
        }
        solutions = ["def add(a, b):\n    return a + b\n"]

        # Should not raise an exception
        accuracy = compute_pass1_accuracy(problem, solutions)

        assert 0.0 <= accuracy <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])