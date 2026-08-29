"""
Integration test for the full data pipeline (fetch -> analyze -> save).

This test verifies the end-to-end flow of:
1. Fetching a small subset of functions from the BigCode dataset.
2. Performing static analysis (metrics calculation).
3. Saving the results to a JSON file.

Constraints:
- Uses a small sample (10 functions) for speed.
- Does NOT make LLM API calls.
- Verifies that the output file exists and contains valid data.
- Fails loudly if the real dataset is inaccessible.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path

# Import pipeline components
from data.download import fetch_functions
from data.static_analysis import analyze_functions

# Import config for constants
from config import Config

# Import logger
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants for this test
TEST_SAMPLE_SIZE = 10
MIN_VALID_REQUIRED = 10
OUTPUT_FILENAME = "test_raw_metrics.json"

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_full_pipeline_fetch_analyze_save(temp_output_dir):
    """
    Integration test: Fetch -> Analyze -> Save.
    
    Steps:
    1. Fetch a small subset of functions from 'bigcode/the-stack-dedup'.
    2. Analyze them to compute structural metrics.
    3. Save the results to a JSON file.
    4. Verify the output file exists and contains the expected structure.
    """
    output_path = temp_output_dir / OUTPUT_FILENAME
    
    # Step 1: Fetch data
    # We use a small sample size to keep the test fast.
    # The fetch_functions function should raise an error if it cannot fetch real data.
    logger.info("Starting data fetch...")
    try:
        functions = fetch_functions(
            dataset_name="bigcode/the-stack-dedup",
            subset="python",
            max_samples=TEST_SAMPLE_SIZE,
            max_attempts=20, # Lower max attempts for testing speed
            min_valid=MIN_VALID_REQUIRED
        )
    except Exception as e:
        logger.error(f"Data fetch failed: {e}")
        pytest.fail(f"Failed to fetch real data from BigCode: {e}")
    
    assert len(functions) >= MIN_VALID_REQUIRED, f"Expected at least {MIN_VALID_REQUIRED} valid functions, got {len(functions)}"
    logger.info(f"Fetched {len(functions)} valid functions.")
    
    # Step 2: Analyze data
    logger.info("Starting static analysis...")
    try:
        analyzed_data = analyze_functions(functions)
    except Exception as e:
        logger.error(f"Static analysis failed: {e}")
        pytest.fail(f"Failed to analyze functions: {e}")
    
    assert len(analyzed_data) == len(functions), "Analysis output count mismatch"
    logger.info(f"Analyzed {len(analyzed_data)} functions.")
    
    # Verify structure of analyzed data
    for item in analyzed_data:
        assert "code" in item, "Missing 'code' field"
        assert "metrics" in item, "Missing 'metrics' field"
        assert "hash" in item, "Missing 'hash' field"
        
        metrics = item["metrics"]
        required_metrics = [
            "loc", "max_nesting", "param_count", "has_docstring",
            "cyclomatic_complexity", "pep8_score"
        ]
        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"
    
    # Step 3: Save data
    logger.info("Saving results...")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analyzed_data, f, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        pytest.fail(f"Failed to save results to {output_path}: {e}")
    
    assert output_path.exists(), f"Output file {output_path} was not created"
    logger.info(f"Results saved to {output_path}")
    
    # Step 4: Verify saved file
    logger.info("Verifying saved file...")
    with open(output_path, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    
    assert len(saved_data) == len(analyzed_data), "Saved data count mismatch"
    
    # Verify a few specific items to ensure integrity
    first_item = saved_data[0]
    assert isinstance(first_item["code"], str), "Code should be a string"
    assert isinstance(first_item["metrics"]["loc"], int), "LOC should be an integer"
    assert isinstance(first_item["metrics"]["has_docstring"], bool), "has_docstring should be a boolean"
    
    logger.info("Integration test passed successfully.")

def test_pipeline_handles_unparseable_code(temp_output_dir):
    """
    Test that the pipeline correctly handles and flags unparseable code.
    
    We inject a known unparseable snippet into the fetched data to verify
    that the static analysis step flags it correctly.
    """
    # Fetch a small sample first
    functions = fetch_functions(
        dataset_name="bigcode/the-stack-dedup",
        subset="python",
        max_samples=5,
        max_attempts=20,
        min_valid=5
    )
    
    # Inject a known unparseable function
    unparseable_func = {
        "code": "def broken(:\n    pass", # Syntax error
        "source_file": "test.py",
        "language": "python"
    }
    functions.append(unparseable_func)
    
    # Analyze
    analyzed_data = analyze_functions(functions)
    
    # Check that the unparseable function is flagged
    found_unparseable = False
    for item in analyzed_data:
        if item["hash"] == unparseable_func["code"].encode("utf-8").hex():
            found_unparseable = True
            assert item.get("parse_error") is not None, "Unparseable code should have a parse_error field"
            break
    
    assert found_unparseable, "Unparseable function was not detected in analysis results"
    logger.info("Unparseable code handling verified.")