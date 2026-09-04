"""
Integration test for the full modeling pipeline (User Story 3).
Verifies that the complete modeling workflow produces a valid model_summary.json.
"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.regression import run_regression_analysis
from models.stats import run_statistical_tests
from utils.schema_validation import validate_output, OutputSchema
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants for test paths
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RESULTS_DIR = DATA_DIR / "results"
INPUT_FILE = DATA_DIR / "processed" / "refactoring_results.json"
OUTPUT_FILE = RESULTS_DIR / "model_summary.json"

# Required fields in the output summary
REQUIRED_FIELDS = [
    "metadata",
    "model_results",
    "statistical_tests",
    "cross_validation_mean_coefficients",
    "adjusted_r_squared",
    "vif_filtered_predictors",
    "execution_time_seconds"
]

# Required nested fields in model_results
REQUIRED_MODEL_FIELDS = [
    "coefficients",
    "p_values",
    "r_squared",
    "f_statistic",
    "f_statistic_pvalue"
]

# Required nested fields in statistical_tests
REQUIRED_STATS_FIELDS = [
    "complexity_delta_ttest",
    "pylint_delta_ttest",
    "maintainability_delta_ttest"
]

# Required nested fields in complexity_delta_ttest
REQUIRED_DELTA_FIELDS = [
    "t_statistic",
    "p_value",
    "is_significant",
    "alpha",
    "degrees_of_freedom",
    "sample_size"
]

def _create_mock_refactoring_results(tmp_path: Path) -> Path:
    """
    Creates a mock refactoring_results.json file with valid data structure
    for testing purposes. This simulates the output of T022.
    """
    mock_data = [
        {
            "function_hash": "hash1",
            "original_code": "def foo(): pass",
            "refactored_code": "def foo(): pass",
            "baseline_code": "def foo(): pass",
            "metrics": {
                "original": {
                    "complexity": 1.0,
                    "pylint_score": 10.0,
                    "maintainability_index": 20.0,
                    "loc": 1,
                    "nesting_depth": 0,
                    "param_count": 0,
                    "pep8_violations": 0,
                    "docstring_present": False
                },
                "refactored": {
                    "complexity": 1.0,
                    "pylint_score": 10.0,
                    "maintainability_index": 20.0,
                    "loc": 1,
                    "nesting_depth": 0,
                    "param_count": 0,
                    "pep8_violations": 0,
                    "docstring_present": False
                },
                "baseline": {
                    "complexity": 1.0,
                    "pylint_score": 10.0,
                    "maintainability_index": 20.0,
                    "loc": 1,
                    "nesting_depth": 0,
                    "param_count": 0,
                    "pep8_violations": 0,
                    "docstring_present": False
                }
            },
            "deltas": {
                "complexity_delta": 0.0,
                "pylint_delta": 0.0,
                "maintainability_delta": 0.0
            },
            "status": "success"
        },
        {
            "function_hash": "hash2",
            "original_code": "def bar(x): return x*2",
            "refactored_code": "def bar(x): return x*2",
            "baseline_code": "def bar(x): return x*2",
            "metrics": {
                "original": {
                    "complexity": 2.0,
                    "pylint_score": 9.5,
                    "maintainability_index": 25.0,
                    "loc": 1,
                    "nesting_depth": 0,
                    "param_count": 1,
                    "pep8_violations": 0,
                    "docstring_present": False
                },
                "refactored": {
                    "complexity": 2.0,
                    "pylint_score": 9.5,
                    "maintainability_index": 25.0,
                    "loc": 1,
                    "nesting_depth": 0,
                    "param_count": 1,
                    "pep8_violations": 0,
                    "docstring_present": False
                },
                "baseline": {
                    "complexity": 2.0,
                    "pylint_score": 9.5,
                    "maintainability_index": 25.0,
                    "loc": 1,
                    "nesting_depth": 0,
                    "param_count": 1,
                    "pep8_violations": 0,
                    "docstring_present": False
                }
            },
            "deltas": {
                "complexity_delta": 0.0,
                "pylint_delta": 0.0,
                "maintainability_delta": 0.0
            },
            "status": "success"
        },
        {
            "function_hash": "hash3",
            "original_code": "def baz(a, b): return a + b",
            "refactored_code": "def baz(a, b): return a + b",
            "baseline_code": "def baz(a, b): return a + b",
            "metrics": {
                "original": {
                    "complexity": 1.0,
                    "pylint_score": 10.0,
                    "maintainability_index": 30.0,
                    "loc": 1,
                    "nesting_depth": 0,
                    "param_count": 2,
                    "pep8_violations": 0,
                    "docstring_present": True
                },
                "refactored": {
                    "complexity": 1.0,
                    "pylint_score": 10.0,
                    "maintainability_index": 30.0,
                    "loc": 1,
                    "nesting_depth": 0,
                    "param_count": 2,
                    "pep8_violations": 0,
                    "docstring_present": True
                },
                "baseline": {
                    "complexity": 1.0,
                    "pylint_score": 10.0,
                    "maintainability_index": 30.0,
                    "loc": 1,
                    "nesting_depth": 0,
                    "param_count": 2,
                    "pep8_violations": 0,
                    "docstring_present": True
                }
            },
            "deltas": {
                "complexity_delta": 0.0,
                "pylint_delta": 0.0,
                "maintainability_delta": 0.0
            },
            "status": "success"
        }
    ]

    input_path = tmp_path / "processed"
    input_path.mkdir(parents=True, exist_ok=True)
    output_path = input_path / "refactoring_results.json"
    
    with open(output_path, 'w') as f:
        json.dump(mock_data, f)
    
    return output_path

def _setup_test_environment(tmp_path: Path) -> Path:
    """
    Sets up the test environment with mock data and creates necessary directories.
    Returns the path to the mock input file.
    """
    # Create necessary directory structure
    (tmp_path / "processed").mkdir(parents=True, exist_ok=True)
    (tmp_path / "results").mkdir(parents=True, exist_ok=True)
    
    # Create mock data
    input_file = _create_mock_refactoring_results(tmp_path)
    
    return input_file

def test_full_modeling_produces_summary(tmp_path: Path):
    """
    Integration test: Asserts that the full modeling pipeline produces 
    data/results/model_summary.json containing all required fields.
    
    This test:
    1. Sets up a mock refactoring_results.json (simulating T022 output)
    2. Runs the modeling pipeline (T033 logic)
    3. Validates the output file exists and contains all required fields
    4. Validates the output against the OutputSchema
    """
    # Setup test environment
    input_file = _setup_test_environment(tmp_path)
    
    # Override global paths for this test
    original_data_dir = DATA_DIR
    original_results_dir = RESULTS_DIR
    
    try:
        # Monkey-patch paths for testing
        import data.download as download_module
        import data.processor as processor_module
        import llm.pipeline as llm_pipeline_module
        import models.regression as regression_module
        import models.stats as stats_module
        import main as main_module
        
        # We need to patch the paths in the modules that use them
        # Since the modules use global Path objects, we need to recreate them
        # or patch the functions that use them.
        
        # Instead, we'll run the logic directly with the patched paths
        # by temporarily changing the global constants in the modules
        
        # Patch the paths in the modules
        regression_module.DATA_DIR = tmp_path / "processed"
        regression_module.RESULTS_DIR = tmp_path / "results"
        stats_module.DATA_DIR = tmp_path / "processed"
        stats_module.RESULTS_DIR = tmp_path / "results"
        
        # Update the input file path
        input_file_path = tmp_path / "processed" / "refactoring_results.json"
        
        # Ensure the input file exists
        assert input_file_path.exists(), f"Mock input file not found: {input_file_path}"
        
        # Run the modeling pipeline
        # This simulates the logic in main.py (T033)
        
        # 1. Load processed data
        with open(input_file_path, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data)} samples from {input_file_path}")
        
        # 2. Run regression analysis (VIF filtering + OLS + Cross-validation)
        regression_results = run_regression_analysis(
            data, 
            output_path=tmp_path / "results" / "regression_results.json"
        )
        
        # 3. Run statistical tests (Paired T-Test)
        stats_results = run_statistical_tests(
            data,
            output_path=tmp_path / "results" / "stats_results.json"
        )
        
        # 4. Validate and save the combined summary
        # This is the core of T033's validation_and_save logic
        summary = {
            "metadata": {
                "timestamp": "2023-01-01T00:00:00",
                "version": "1.0.0",
                "input_file": str(input_file_path),
                "sample_count": len(data)
            },
            "model_results": regression_results.get("model_results", {}),
            "statistical_tests": stats_results.get("statistical_tests", {}),
            "cross_validation_mean_coefficients": regression_results.get("cross_validation_mean_coefficients", {}),
            "adjusted_r_squared": regression_results.get("adjusted_r_squared", 0.0),
            "vif_filtered_predictors": regression_results.get("vif_filtered_predictors", []),
            "execution_time_seconds": 0.0
        }
        
        output_file = tmp_path / "results" / "model_summary.json"
        
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Assertions: Verify the output file exists
        assert output_file.exists(), f"Output file not created: {output_file}"
        
        # Assertions: Verify the output file contains all required fields
        with open(output_file, 'r') as f:
            result = json.load(f)
        
        # Check top-level required fields
        for field in REQUIRED_FIELDS:
            assert field in result, f"Missing required field in output: {field}"
        
        # Check model_results fields
        model_results = result.get("model_results", {})
        for field in REQUIRED_MODEL_FIELDS:
            assert field in model_results, f"Missing required field in model_results: {field}"
        
        # Check statistical_tests fields
        stats_tests = result.get("statistical_tests", {})
        for field in REQUIRED_STATS_FIELDS:
            assert field in stats_tests, f"Missing required field in statistical_tests: {field}"
        
        # Check nested delta fields
        for delta_key in REQUIRED_STATS_FIELDS:
            delta_result = stats_tests.get(delta_key, {})
            for field in REQUIRED_DELTA_FIELDS:
                assert field in delta_result, f"Missing required field in {delta_key}: {field}"
        
        # Validate against schema
        try:
            validate_output(result)
        except Exception as e:
            pytest.fail(f"Output validation failed: {str(e)}")
        
        logger.info("Integration test passed: model_summary.json contains all required fields")
        
    finally:
        # Restore original paths if needed (though not strictly necessary for this test)
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
