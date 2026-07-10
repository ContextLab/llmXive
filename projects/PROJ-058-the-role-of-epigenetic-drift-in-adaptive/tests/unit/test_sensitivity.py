"""
Unit tests for the sensitivity analysis logic in code/analysis/sensitivity.py.

This module validates the threshold sweep logic, ensuring that:
1. The sensitivity sweep correctly iterates over [3, 4, 5] generations.
2. Filtering by generation threshold correctly subsets the data.
3. The stability check logic (rho differences, significance counts) works as expected.
4. The main entry point produces the expected output structure.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# Add the project root to the path to allow imports from 'code'
# Assuming this test runs from the project root or tests/unit
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.analysis.sensitivity import (
    load_correlation_results,
    filter_by_generation_threshold,
    run_sensitivity_sweep,
    save_results,
    run_sensitivity_analysis,
    main
)
from code.analysis.stability_check import check_significance_count, calculate_max_rho_diff

# Mock data fixtures
MOCK_CORRELATION_RESULTS = {
    "metadata": {
        "source": "test_discovery",
        "timestamp": "2026-01-01T00:00:00Z"
    },
    "results": [
        {
            "dataset_id": "GEO-001",
            "condition": "fluctuating",
            "rho": 0.65,
            "p_value": 0.01,
            "n_generations": 5,
            "samples": 20
        },
        {
            "dataset_id": "GEO-002",
            "condition": "constant",
            "rho": 0.12,
            "p_value": 0.45,
            "n_generations": 4,
            "samples": 15
        },
        {
            "dataset_id": "GEO-003",
            "condition": "fluctuating",
            "rho": 0.78,
            "p_value": 0.001,
            "n_generations": 6,
            "samples": 25
        },
        {
            "dataset_id": "GEO-004",
            "condition": "fluctuating",
            "rho": 0.05,
            "p_value": 0.80,
            "n_generations": 3,
            "samples": 10
        },
        {
            "dataset_id": "GEO-005",
            "condition": "constant",
            "rho": 0.22,
            "p_value": 0.30,
            "n_generations": 2,
            "samples": 8
        }
    ]
}

@pytest.fixture
def temp_correlation_file(tmp_path):
    """Creates a temporary JSON file with mock correlation results."""
    file_path = tmp_path / "correlation_results.json"
    with open(file_path, 'w') as f:
        json.dump(MOCK_CORRELATION_RESULTS, f)
    return file_path

@pytest.fixture
def temp_output_dir(tmp_path):
    """Creates a temporary directory for output files."""
    return tmp_path / "output"

def test_filter_by_generation_threshold():
    """Test that filtering by generation threshold works correctly."""
    results = MOCK_CORRELATION_RESULTS["results"]
    
    # Filter for >= 3 generations
    filtered_3 = filter_by_generation_threshold(results, min_gen=3)
    assert len(filtered_3) == 4  # GEO-001, GEO-002, GEO-003, GEO-004
    assert all(r["n_generations"] >= 3 for r in filtered_3)
    
    # Filter for >= 5 generations
    filtered_5 = filter_by_generation_threshold(results, min_gen=5)
    assert len(filtered_5) == 2  # GEO-001, GEO-003
    assert all(r["n_generations"] >= 5 for r in filtered_5)
    
    # Filter for >= 10 generations (should be empty)
    filtered_10 = filter_by_generation_threshold(results, min_gen=10)
    assert len(filtered_10) == 0

def test_run_sensitivity_sweep_structure():
    """Test that the sweep produces results for exactly 3, 4, and 5 generations."""
    # Create a temporary input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(MOCK_CORRELATION_RESULTS, f)
        input_path = f.name
    
    try:
        output_path = tempfile.mktemp(suffix='_sensitivity.json')
        
        # Run the sweep
        run_sensitivity_sweep(input_path, output_path)
        
        # Load and verify results
        with open(output_path, 'r') as f:
            sweep_results = json.load(f)
        
        assert "sweep_results" in sweep_results
        assert len(sweep_results["sweep_results"]) == 3
        
        thresholds = [r["threshold"] for r in sweep_results["sweep_results"]]
        assert sorted(thresholds) == [3, 4, 5]
        
        # Verify each result has the expected keys
        for res in sweep_results["sweep_results"]:
            assert "threshold" in res
            assert "count" in res
            assert "significant_count" in res
            assert "rhos" in res
            assert "max_rho_diff" in res
            assert "status" in res
        
    finally:
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_run_sensitivity_sweep_values():
    """Test that the sweep calculates correct counts and rhos for specific thresholds."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(MOCK_CORRELATION_RESULTS, f)
        input_path = f.name
    
    try:
        output_path = tempfile.mktemp(suffix='_sensitivity.json')
        run_sensitivity_sweep(input_path, output_path)
        
        with open(output_path, 'r') as f:
            sweep_results = json.load(f)
        
        # Find result for threshold 3
        res_3 = next(r for r in sweep_results["sweep_results"] if r["threshold"] == 3)
        assert res_3["count"] == 4  # GEO-001, 002, 003, 004
        # Significant (p < 0.05): GEO-001 (0.01), GEO-003 (0.001) -> 2
        assert res_3["significant_count"] == 2
        assert 0.65 in res_3["rhos"]
        assert 0.78 in res_3["rhos"]
        
        # Find result for threshold 5
        res_5 = next(r for r in sweep_results["sweep_results"] if r["threshold"] == 5)
        assert res_5["count"] == 2  # GEO-001, GEO-003
        assert res_5["significant_count"] == 2
        
    finally:
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_stability_check_logic():
    """Test the stability check functions used by the sweep."""
    rhos_low = [0.1, 0.2, 0.15]
    rhos_high = [0.6, 0.7, 0.65]
    
    # Max diff should be 0.15
    max_diff = calculate_max_rho_diff(rhos_low)
    assert abs(max_diff - 0.15) < 1e-6
    
    max_diff_high = calculate_max_rho_diff(rhos_high)
    assert abs(max_diff_high - 0.1) < 1e-6
    
    # Significance count
    p_values_low = [0.06, 0.04, 0.10]
    sig_count = check_significance_count(p_values_low)
    assert sig_count == 1

def test_main_entry_point():
    """Test that the main function runs end-to-end and writes output."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(MOCK_CORRELATION_RESULTS, f)
        input_path = f.name
    
    try:
        output_path = tempfile.mktemp(suffix='_sensitivity.json')
        
        # Mock sys.argv to simulate CLI execution
        with patch('sys.argv', ['main', input_path, output_path]):
            # Capture stdout to ensure no errors
            with patch('sys.stdout'):
                main()
        
        assert os.path.exists(output_path), "Output file was not created"
        
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert "sweep_results" in result
        assert "metadata" in result
        
    finally:
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_empty_dataset_handling():
    """Test that the sweep handles datasets with no matching generations gracefully."""
    empty_results = {"results": []}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(empty_results, f)
        input_path = f.name
    
    try:
        output_path = tempfile.mktemp(suffix='_sensitivity.json')
        run_sensitivity_sweep(input_path, output_path)
        
        with open(output_path, 'r') as f:
            sweep_results = json.load(f)
        
        # Should still have 3 entries, but with count 0
        assert len(sweep_results["sweep_results"]) == 3
        for res in sweep_results["sweep_results"]:
            assert res["count"] == 0
            assert res["status"] == "NO_DATA"
        
    finally:
        os.unlink(input_path)
        if os.path.exists(output_path):
            os.unlink(output_path)

def test_missing_file_handling():
    """Test that the function raises an appropriate error for missing input."""
    with pytest.raises(FileNotFoundError):
        load_correlation_results("non_existent_file.json")

def test_run_sensitivity_analysis_integration():
    """Integration test for the full analysis pipeline."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_file = Path(tmp_dir) / "input.json"
        output_file = Path(tmp_dir) / "output.json"
        
        with open(input_file, 'w') as f:
            json.dump(MOCK_CORRELATION_RESULTS, f)
        
        # Run the full analysis
        run_sensitivity_analysis(str(input_file), str(output_file))
        
        # Verify output
        assert output_file.exists()
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "sweep_results" in data
        assert "stability_flags" in data
        # Verify stability flags are present
        assert "unstable_thresholds" in data["stability_flags"]
        assert "significant_count_status" in data["stability_flags"]