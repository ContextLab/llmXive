import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the function to test
# Note: We are testing the logic inside process_tasks, specifically the stopping rule check
# Since process_tasks is not a standalone function but part of the main script,
# we will test the logic by mocking the generation part and checking the exit behavior.

from code_02_generate_cot import process_tasks

def test_stopping_rule_underpowered():
    """
    Test that if effective sample size < 40, the process halts with SystemExit(1).
    """
    # Create a temporary directory for test files
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"
        report_file = tmp_path / "stopping_rule_report.json"

        # Create a small dataset (e.g., 10 tasks)
        # We will mock the generation to succeed for all, so effective size = 10
        tasks = [
            {"id": f"task_{i}", "category": "Abstract Reasoning", "constraint": "Use logic", "problem_text": f"Problem {i}"}
            for i in range(10)
        ]
        with open(input_file, "w") as f:
            for t in tasks:
                f.write(json.dumps(t) + "\n")

        # Mock the model loading and generation to return success immediately
        # We need to mock the internal functions: load_quantized_model, check_memory_usage, generate_cot_trace
        with patch('code_02_generate_cot.load_quantized_model') as mock_model, \
             patch('code_02_generate_cot.check_memory_usage') as mock_memory, \
             patch('code_02_generate_cot.generate_cot_trace') as mock_gen:
            
            mock_model.return_value = (MagicMock(), MagicMock()) # model, tokenizer
            mock_memory.return_value = False # No memory issues
            # Mock generation to return a valid trace, not timeout
            mock_gen.return_value = ("Generated trace content", False)

            # Run the function
            # We expect it to raise SystemExit(1) because 10 < 40
            with pytest.raises(SystemExit) as excinfo:
                process_tasks(
                    input_path=input_file,
                    output_path=output_file,
                    model_name="test_model",
                    device="cpu",
                    timeout_per_task=1
                )

            assert excinfo.value.code == 1

            # Verify the report was created
            assert report_file.exists(), "Stopping rule report should be created."
            
            with open(report_file) as f:
                report = json.load(f)
            
            assert report["status"] == "underpowered"
            assert report["effective_sample_size"] == 10
            assert report["minimum_valid_sample"] == 40
            assert "Underpowered" in report["message"]

def test_stopping_rule_passed():
    """
    Test that if effective sample size >= 40, the process completes successfully.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        input_file = tmp_path / "input.jsonl"
        output_file = tmp_path / "output.jsonl"

        # Create a dataset of 50 tasks
        tasks = [
            {"id": f"task_{i}", "category": "Abstract Reasoning", "constraint": "Use logic", "problem_text": f"Problem {i}"}
            for i in range(50)
        ]
        with open(input_file, "w") as f:
            for t in tasks:
                f.write(json.dumps(t) + "\n")

        with patch('code_02_generate_cot.load_quantized_model') as mock_model, \
             patch('code_02_generate_cot.check_memory_usage') as mock_memory, \
             patch('code_02_generate_cot.generate_cot_trace') as mock_gen:
            
            mock_model.return_value = (MagicMock(), MagicMock())
            mock_memory.return_value = False
            mock_gen.return_value = ("Generated trace content", False)

            # Should not raise SystemExit
            try:
                process_tasks(
                    input_path=input_file,
                    output_path=output_file,
                    model_name="test_model",
                    device="cpu",
                    timeout_per_task=1
                )
            except SystemExit:
                pytest.fail("Process should not exit with code 1 when sample size >= 40")

            # Verify output file exists and has content
            assert output_file.exists()
            with open(output_file) as f:
                lines = f.readlines()
            assert len(lines) == 50