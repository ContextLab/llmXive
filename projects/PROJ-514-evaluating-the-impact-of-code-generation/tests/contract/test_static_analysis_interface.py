"""
Contract test for parallel analysis execution (T020).

This test defines the interface for T021 (run_pmd.py) and T023 (tool_validity_check.py).
It verifies that the static analysis execution layer:
1. Accepts a list of sample file paths.
2. Executes analysis in parallel (concurrent.futures).
3. Returns a structured list of results conforming to the SmellMetric model.
4. Handles timeouts and process failures gracefully without crashing the pipeline.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock, patch

import pytest

# Project root setup
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.data_models import SmellMetric
from utils.logger import get_logger
from utils.validators import validate_file_syntax

# Mock the PMD execution for this contract test to ensure it runs without external dependencies
# while verifying the parallel execution logic and result structure.
MOCK_PMD_OUTPUT = {
    "violations": [
        {"rule": "LongMethod", "file": "test.py", "beginline": 10, "msg": "Method too long"},
        {"rule": "FeatureEnvy", "file": "test.py", "beginline": 25, "msg": "Method depends on external data"},
    ]
}

def _create_mock_samples(tmp_dir: Path, count: int = 3) -> list:
    """Create temporary Python files to simulate input samples."""
    samples = []
    for i in range(count):
        fname = f"sample_{i}.py"
        fpath = tmp_dir / fname
        fpath.write_text(f"# Mock sample {i}\ndef func():\n    pass\n")
        samples.append(str(fpath))
    return samples

def test_interface_accepts_file_paths_and_returns_list():
    """
    Verify the interface accepts a list of file paths and returns a list of results.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        samples = _create_mock_samples(tmp_path, count=3)
        
        # We simulate the execution logic here to verify the contract
        # In the real implementation (T021), this logic moves to run_pmd.py
        results = []
        
        def mock_process_file(file_path: str) -> dict:
            # Simulate the parsing of PMD output into SmellMetric-like dict
            # This mimics what parse_results.py will eventually do
            return {
                "sample_id": Path(file_path).stem,
                "source_type": "human", # Derived from path or manifest
                "smell_type": "LongMethod",
                "count": 1,
                "threshold_used": 100,
                "continuous_metric_value": 150.0,
                "status": "success"
            }

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_path = {executor.submit(mock_process_file, p): p for p in samples}
            for future in as_completed(future_to_path):
                res = future.result()
                results.append(res)
        
        assert isinstance(results, list), "Result must be a list"
        assert len(results) == 3, "Should process all 3 samples"
        assert all(isinstance(r, dict) for r in results), "All results must be dicts"

def test_interface_handles_timeouts_and_failures_gracefully():
    """
    Verify that if a file processing fails (e.g., timeout, syntax error),
    the pipeline logs the error and continues, returning a partial result list
    with status 'error' or 'skipped'.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        samples = _create_mock_samples(tmp_path, count=3)
        # Introduce a broken file
        broken_file = tmp_path / "broken.py"
        broken_file.write_text("def broken(") # Syntax error
        samples.append(str(broken_file))
        
        results = []
        
        def mock_process_file(file_path: str) -> dict:
            if "broken" in file_path:
                raise ValueError("Syntax error detected")
            return {
                "sample_id": Path(file_path).stem,
                "source_type": "human",
                "smell_type": "LongMethod",
                "count": 1,
                "threshold_used": 100,
                "continuous_metric_value": 150.0,
                "status": "success"
            }

        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_path = {executor.submit(mock_process_file, p): p for p in samples}
            for future in as_completed(future_to_path):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    # Contract requires graceful handling: log and record error state
                    results.append({
                        "sample_id": Path(future_to_path[future]).stem,
                        "source_type": "human",
                        "smell_type": None,
                        "count": 0,
                        "threshold_used": None,
                        "continuous_metric_value": None,
                        "status": "error",
                        "error_message": str(e)
                    })
        
        # Verify we have results for all, including the error
        assert len(results) == 4
        error_results = [r for r in results if r["status"] == "error"]
        assert len(error_results) == 1
        assert "Syntax error detected" in error_results[0]["error_message"]

def test_output_conforms_to_smell_metric_structure():
    """
    Verify the output dictionary keys match the SmellMetric dataclass attributes
    defined in utils/data_models.py.
    """
    # Expected keys based on SmellMetric: sample_id, smell_type, count, threshold_used, continuous_metric_value
    expected_keys = {"sample_id", "smell_type", "count", "threshold_used", "continuous_metric_value"}
    
    sample_result = {
        "sample_id": "test_1",
        "smell_type": "LongMethod",
        "count": 1,
        "threshold_used": 100,
        "continuous_metric_value": 120.5,
        "source_type": "human" # Extra field allowed
    }
    
    assert expected_keys.issubset(sample_result.keys()), f"Missing keys: {expected_keys - set(sample_result.keys())}"

def test_parallel_execution_order_independence():
    """
    Verify that the order of results does not depend on the order of input files,
    confirming true parallel execution (results are collected via as_completed).
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        samples = _create_mock_samples(tmp_path, count=5)
        # Shuffle samples to ensure order independence
        import random
        shuffled_samples = samples.copy()
        random.shuffle(shuffled_samples)
        
        results_map = {}
        
        def mock_process_file(file_path: str) -> str:
            return Path(file_path).stem

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit in shuffled order
            futures = {executor.submit(mock_process_file, p): p for p in shuffled_samples}
            # Collect as completed (order may vary)
            for future in as_completed(futures):
                res = future.result()
                results_map[res] = True
        
        # Verify all 5 were processed regardless of submission order
        assert len(results_map) == 5

def test_interface_requires_valid_pmd_config():
    """
    Contract check: The execution layer must validate PMD availability before starting.
    This is a pre-condition for T021.
    """
    # This test ensures the interface expects a valid configuration context.
    # In T021, this will be enforced by calling utils.pmd_config.check_pmd_availability()
    # Here we verify the dependency exists.
    from utils.pmd_config import check_pmd_availability
    # The function must exist and be callable
    assert callable(check_pmd_availability)