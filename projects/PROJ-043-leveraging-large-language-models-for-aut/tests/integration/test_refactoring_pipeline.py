"""
Integration tests for the refactoring pipeline.
Verifies that batch processing handles errors gracefully without crashing.
"""
import json
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from llm.pipeline import load_processed_data, process_refactoring_batch, save_results
from utils.logging import LLMRefactoringError
from models.entities import FunctionSample

# Constants for test paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"


def create_mock_processed_data(tmp_path: Path) -> str:
    """
    Creates a temporary JSON file with mock processed data.
    Includes one valid function and one function that will trigger an error.
    """
    data = [
        {
            "code": "def valid_func():\n    return 42",
            "hash": "abc123",
            "metrics": {
                "loc": 2,
                "nesting_depth": 0,
                "param_count": 0,
                "pep8_violations": 0,
                "pep8_adherence_score": 1.0,
                "docstring_present": False
            }
        },
        {
            "code": "def invalid_func():\n    return 42",
            "hash": "def456",
            "metrics": {
                "loc": 2,
                "nesting_depth": 0,
                "param_count": 0,
                "pep8_violations": 0,
                "pep8_adherence_score": 1.0,
                "docstring_present": False
            }
        }
    ]
    file_path = tmp_path / "raw_metrics.json"
    with open(file_path, "w") as f:
        json.dump(data, f)
    return str(file_path)


@pytest.fixture
def mock_refactor_single_function():
    """
    Mocks the refactor_single_function to simulate:
    1. A successful refactoring for the first call.
    2. A failure (LLMRefactoringError) for the second call.
    """
    call_count = 0

    def side_effect(func_sample, **kwargs):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # Simulate success
            return {
                "original_code": func_sample.code,
                "refactored_code": "def valid_func():\n    return 42 # Refactored",
                "status": "Success",
                "hash": func_sample.hash
            }
        else:
            # Simulate failure for the second item
            raise LLMRefactoringError("API Timeout or Model Error")

    with patch("llm.pipeline.refactor_single_function", side_effect=side_effect):
        yield


def test_batch_processing_handles_errors():
    """
    Asserts that a single failed refactoring does not crash the batch
    and the failed item is marked as "Refactoring Failed" in the results.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        input_file = create_mock_processed_data(tmp_path)

        # Ensure output directory exists
        output_file = tmp_path / "refactoring_results.json"

        # Load data
        data = load_processed_data(input_file)
        assert len(data) == 2

        # Process batch with mocked failure
        # We need to patch the specific function used inside process_refactoring_batch
        # The pipeline module imports refactor_single_function locally or uses it directly.
        # Based on the API surface provided, process_refactoring_batch calls refactor_single_function.
        
        results = process_refactoring_batch(data, output_file, batch_size=2)

        # Verify the results list has the same length as input
        assert len(results) == 2

        # Verify the first one succeeded
        assert results[0]["status"] == "Success"
        assert "refactored_code" in results[0]

        # Verify the second one failed gracefully
        failed_item = results[1]
        assert failed_item["status"] == "Refactoring Failed"
        assert "error_message" in failed_item
        assert "LLMRefactoringError" in failed_item["error_message"] or "API Timeout" in failed_item["error_message"]

        # Verify the output file was created and contains valid JSON
        assert output_file.exists()
        with open(output_file, "r") as f:
            saved_results = json.load(f)
        
        assert len(saved_results) == 2
        assert saved_results[1]["status"] == "Refactoring Failed"