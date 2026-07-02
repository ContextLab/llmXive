"""
Integration test for full execution pipeline (US2).

This test verifies the end-to-end flow of:
1. Loading generated prompt variants and code samples from data/processed/prompt_variants.parquet
2. Executing the code against HumanEval unit tests using the runner
3. Capturing execution results (pass/fail, exceptions, timeouts)
4. Aggregating results and writing to data/results/execution_outcomes.csv

It uses a small, fixed subset of HumanEval problems to ensure tractability.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any

import pytest
import pandas as pd

# Add code directory to path for imports
code_root = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from models.data_models import ComplexityLabel, ExecutionStatus
from data.storage import load_variants_from_parquet
from execution.runner import run_code_with_tests, execute_batch
from utils.logger import setup_logging, get_logger

logger = get_logger(__name__)


@pytest.fixture(scope="module")
def sample_data_dir():
    """
    Create a temporary directory with a minimal mock dataset for testing.
    This avoids dependency on the full HumanEval generation pipeline for this unit.
    """
    temp_dir = tempfile.mkdtemp()
    data_processed = Path(temp_dir) / "data" / "processed"
    data_processed.mkdir(parents=True)

    # Create a minimal parquet file with 2 problems, 2 variants each
    # Using real HumanEval problem IDs and synthetic (but valid) code snippets
    data = {
        "problem_id": ["HumanEval/0", "HumanEval/0", "HumanEval/1", "HumanEval/1"],
        "complexity_label": ["simple", "complex", "simple", "complex"],
        "prompt_text": [
            "Write a function to check if a number is even.",
            "Write a function to check if a number is even. Ensure it handles negative numbers and zero. Add type hints. Include a docstring.",
            "Write a function to check if a number is even.",
            "Write a function to check if a number is even. Ensure it handles negative numbers and zero. Add type hints. Include a docstring.",
        ],
        "generated_code": [
            "def is_even(n):\n    return n % 2 == 0",
            "def is_even(n: int) -> bool:\n    \"\"\"Check if n is even.\"\"\"\n    return n % 2 == 0",
            "def has_close_elements(numbers: List[float], threshold: float) -> bool:\n    for idx, elem in enumerate(numbers):\n        for idx2, elem2 in enumerate(numbers):\n            if idx != idx2:\n                distance = abs(elem - elem2)\n                if distance < threshold:\n                    return True\n    return False",
            "def has_close_elements(numbers: List[float], threshold: float) -> bool:\n    \"\"\"Check if any two numbers in the list are closer than threshold.\"\"\"\n    for idx, elem in enumerate(numbers):\n        for idx2, elem2 in enumerate(numbers):\n            if idx != idx2:\n                distance = abs(elem - elem2)\n                if distance < threshold:\n                    return True\n    return False",
        ],
        "token_count": [20, 45, 20, 45],
        "structural_element_count": [1, 3, 1, 3],
    }

    df = pd.DataFrame(data)
    parquet_path = data_processed / "prompt_variants.parquet"
    df.to_parquet(parquet_path)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


def test_execution_pipeline_end_to_end(sample_data_dir):
    """
    Integration test: Load data -> Run execution -> Verify outputs.
    """
    data_processed = Path(sample_data_dir) / "data" / "processed"
    data_results = Path(sample_data_dir) / "data" / "results"
    data_results.mkdir(parents=True)

    parquet_path = data_processed / "prompt_variants.parquet"
    assert parquet_path.exists(), "Mock parquet file not created"

    # Load data
    variants = load_variants_from_parquet(parquet_path)
    assert len(variants) == 4, "Expected 4 variants in mock data"

    # Define a minimal test suite for the mock code
    # We simulate HumanEval test cases inline for this integration test
    test_suites = {
        "HumanEval/0": [
            "assert is_even(2) == True",
            "assert is_even(3) == False",
            "assert is_even(0) == True",
            "assert is_even(-2) == True",
        ],
        "HumanEval/1": [
            "assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False",
            "assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True",
        ],
    }

    execution_results = []
    problem_ids = list(set(v.problem_id for v in variants))

    for variant in variants:
        problem_id = variant.problem_id
        code = variant.generated_code
        test_cases = test_suites.get(problem_id, [])

        if not test_cases:
            logger.warning(f"No test cases found for {problem_id}, skipping execution")
            continue

        result = run_code_with_tests(code, test_cases, timeout_seconds=5)
        execution_results.append(result)

    assert len(execution_results) > 0, "No execution results generated"

    # Verify results structure
    for res in execution_results:
        assert res.status in [ExecutionStatus.PASS, ExecutionStatus.FAIL, ExecutionStatus.TIMEOUT, ExecutionStatus.ERROR]
        assert res.problem_id is not None
        assert res.complexity_label is not None

    # Write results to CSV (simulating T030)
    results_df = pd.DataFrame([
        {
            "problem_id": r.problem_id,
            "complexity_label": r.complexity_label,
            "status": r.status.value,
            "error_type": r.error_type,
            "execution_time_ms": r.execution_time_ms,
        }
        for r in execution_results
    ])

    output_csv = data_results / "execution_outcomes.csv"
    results_df.to_csv(output_csv, index=False)

    assert output_csv.exists(), "Execution outcomes CSV not written"

    # Verify content
    loaded_results = pd.read_csv(output_csv)
    assert len(loaded_results) == len(execution_results), "CSV row count mismatch"
    assert "status" in loaded_results.columns, "Missing 'status' column"
    assert "complexity_label" in loaded_results.columns, "Missing 'complexity_label' column"

    logger.info(f"Integration test passed. Results written to {output_csv}")


def test_timeout_handling(sample_data_dir):
    """
    Test that the runner correctly handles timeouts.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        data_processed = Path(temp_dir) / "data" / "processed"
        data_processed.mkdir(parents=True)

        # Create a variant with infinite loop code
        data = {
            "problem_id": ["HumanEval/999"],
            "complexity_label": ["simple"],
            "prompt_text": ["Write infinite loop"],
            "generated_code": ["while True: pass"],
            "token_count": [10],
            "structural_element_count": [1],
        }
        df = pd.DataFrame(data)
        df.to_parquet(data_processed / "prompt_variants.parquet")

        variants = load_variants_from_parquet(data_processed / "prompt_variants.parquet")
        variant = variants[0]

        # Test with a very short timeout
        result = run_code_with_tests(variant.generated_code, ["assert True"], timeout_seconds=1)

        assert result.status == ExecutionStatus.TIMEOUT, f"Expected TIMEOUT, got {result.status}"
        logger.info("Timeout handling test passed")
    finally:
        shutil.rmtree(temp_dir)


def test_syntax_error_handling(sample_data_dir):
    """
    Test that the runner correctly handles syntax errors.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        data_processed = Path(temp_dir) / "data" / "processed"
        data_processed.mkdir(parents=True)

        # Create a variant with syntax error
        data = {
            "problem_id": ["HumanEval/998"],
            "complexity_label": ["simple"],
            "prompt_text": ["Write broken code"],
            "generated_code": ["def broken(:"],
            "token_count": [10],
            "structural_element_count": [1],
        }
        df = pd.DataFrame(data)
        df.to_parquet(data_processed / "prompt_variants.parquet")

        variants = load_variants_from_parquet(data_processed / "prompt_variants.parquet")
        variant = variants[0]

        result = run_code_with_tests(variant.generated_code, ["assert True"], timeout_seconds=5)

        assert result.status == ExecutionStatus.ERROR, f"Expected ERROR, got {result.status}"
        assert result.error_type == "SyntaxError", f"Expected SyntaxError, got {result.error_type}"
        logger.info("Syntax error handling test passed")
    finally:
        shutil.rmtree(temp_dir)