import os
import json
import pytest
import tempfile
import pandas as pd
from pathlib import Path

# Add code to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis import run_baseline_analysis
from utils import setup_logging
from config import get_config

setup_logging("INFO")

@pytest.fixture
def temp_raw_dir():
    """Create a temporary directory with sample CSV data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample dataset
        data = {
            "group": ["A", "B", "A", "B", "A", "B"] * 10,
            "outcome": [1.2, 2.1, 1.5, 2.3, 1.1, 2.0] * 10,
            "predictor": [10, 20, 15, 25, 12, 22] * 10
        }
        df = pd.DataFrame(data)
        filepath = os.path.join(tmpdir, "test_dataset.csv")
        df.to_csv(filepath, index=False)
        yield tmpdir

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_baseline_analysis_produces_valid_json(temp_raw_dir, temp_output_dir):
    """
    Integration test: Verify baseline analysis script produces baseline_metrics.json
    with valid p-values (0 < p < 1) and finite CIs.
    """
    output_file = os.path.join(temp_output_dir, "baseline_metrics.json")
    
    # Run analysis
    success = run_baseline_analysis(raw_dir=temp_raw_dir, output_path=output_file)
    
    assert success is True, "Baseline analysis should return True"
    assert os.path.exists(output_file), "Output file should exist"
    
    # Load and validate
    with open(output_file, 'r') as f:
        data = json.load(f)
    
    assert "datasets" in data, "Output should contain 'datasets' key"
    assert len(data["datasets"]) > 0, "Should have at least one dataset"
    
    for ds in data["datasets"]:
        assert "analysis" in ds, f"Dataset {ds.get('dataset_name')} missing 'analysis'"
        t_test = ds["analysis"].get("t_test", {})
        
        p_val = t_test.get("p_value")
        ci = t_test.get("ci")
        
        # Check p-value validity
        if p_val is not None:
            assert 0 < p_val < 1, f"P-value {p_val} should be between 0 and 1"
        
        # Check CI validity
        if ci is not None:
            assert len(ci) == 2, "CI should have 2 elements"
            assert all(isinstance(x, (int, float)) for x in ci), "CI elements should be numeric"
            assert all(not (x != x) for x in ci), "CI elements should be finite (not NaN)"

def test_baseline_analysis_with_config(temp_raw_dir, temp_output_dir):
    """
    Integration test: Verify baseline analysis works with config object.
    """
    config = get_config()
    output_file = os.path.join(temp_output_dir, "baseline_with_config.json")
    
    success = run_baseline_analysis(
        raw_dir=temp_raw_dir,
        output_path=output_file,
        config=config
    )
    
    assert success is True
    assert os.path.exists(output_file)

def test_baseline_analysis_empty_directory(temp_output_dir):
    """
    Integration test: Verify behavior with empty input directory.
    """
    empty_dir = os.path.join(temp_output_dir, "empty")
    os.makedirs(empty_dir)
    output_file = os.path.join(temp_output_dir, "empty_output.json")
    
    success = run_baseline_analysis(raw_dir=empty_dir, output_path=output_file)
    
    # Should return False or handle gracefully
    # Depending on implementation, it might return False or write empty JSON
    if success:
        with open(output_file, 'r') as f:
            data = json.load(f)
        assert "datasets" in data
        assert len(data["datasets"]) == 0
    else:
        assert not os.path.exists(output_file) or os.path.getsize(output_file) == 0