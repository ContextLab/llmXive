"""
Unit tests for statistics.py gradient distribution verification.
"""
import pytest
import json
import os
import tempfile
import numpy as np
from pathlib import Path
import sys

# Add code directory to path if needed
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from src.utils.statistics import (
    load_gradient_norms,
    extract_gradient_values,
    verify_gradient_distribution
)

@pytest.fixture
def temp_gradient_files():
    """Create temporary gradient norm files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create baseline data (normal distribution)
        baseline_path = os.path.join(tmpdir, "baseline.json")
        baseline_data = {
            "step_0": {"param_a": 1.0, "param_b": 1.2, "param_c": 0.9},
            "step_1": {"param_a": 1.1, "param_b": 1.3, "param_c": 1.0},
            "step_2": {"param_a": 1.05, "param_b": 1.15, "param_c": 0.95},
            "step_3": {"param_a": 1.02, "param_b": 1.25, "param_c": 0.98},
            "step_4": {"param_a": 0.98, "param_b": 1.18, "param_c": 1.02},
        }
        with open(baseline_path, 'w') as f:
            json.dump(baseline_data, f)
        
        # Create microcircuit data (slightly different distribution)
        micro_path = os.path.join(tmpdir, "microcircuit.json")
        micro_data = {
            "step_0": {"param_a": 1.5, "param_b": 1.7, "param_c": 1.4},
            "step_1": {"param_a": 1.6, "param_b": 1.8, "param_c": 1.5},
            "step_2": {"param_a": 1.55, "param_b": 1.75, "param_c": 1.45},
            "step_3": {"param_a": 1.52, "param_b": 1.78, "param_c": 1.48},
            "step_4": {"param_a": 1.48, "param_b": 1.72, "param_c": 1.52},
        }
        with open(micro_path, 'w') as f:
            json.dump(micro_data, f)
        
        yield {
            "baseline": baseline_path,
            "microcircuit": micro_path,
            "output": os.path.join(tmpdir, "report.md")
        }

def test_load_gradient_norms_file_exists(temp_gradient_files):
    """Test that load_gradient_norms successfully loads a valid file."""
    data = load_gradient_norms(temp_gradient_files["baseline"])
    assert isinstance(data, dict)
    assert "step_0" in data
    assert "param_a" in data["step_0"]

def test_load_gradient_norms_file_not_found():
    """Test that load_gradient_norms raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        load_gradient_norms("/nonexistent/path/file.json")

def test_extract_gradient_values_dict_structure(temp_gradient_files):
    """Test extracting values from dict-structured gradient data."""
    data = load_gradient_norms(temp_gradient_files["baseline"])
    values = extract_gradient_values(data)
    
    assert isinstance(values, np.ndarray)
    assert len(values) == 15  # 5 steps * 3 params
    assert np.all(values > 0)

def test_extract_gradient_values_empty_data():
    """Test extracting values from empty data."""
    values = extract_gradient_values({})
    assert isinstance(values, np.ndarray)
    assert len(values) == 0

def test_verify_gradient_distribution_creates_report(temp_gradient_files):
    """Test that verify_gradient_distribution creates a valid report file."""
    results = verify_gradient_distribution(
        temp_gradient_files["baseline"],
        temp_gradient_files["microcircuit"],
        temp_gradient_files["output"]
    )
    
    # Check report file exists
    assert os.path.exists(temp_gradient_files["output"])
    
    # Check results structure
    assert "baseline" in results
    assert "microcircuit" in results
    assert "ks_test" in results
    assert "distribution_overlap" in results
    
    # Check KS test results
    assert "statistic" in results["ks_test"]
    assert "p_value" in results["ks_test"]
    assert "is_significantly_different" in results["ks_test"]
    
    # Verify p-value is between 0 and 1
    assert 0 <= results["ks_test"]["p_value"] <= 1
    assert 0 <= results["ks_test"]["statistic"] <= 1

def test_verify_gradient_distribution_report_content(temp_gradient_files):
    """Test that the generated report contains expected content."""
    verify_gradient_distribution(
        temp_gradient_files["baseline"],
        temp_gradient_files["microcircuit"],
        temp_gradient_files["output"]
    )
    
    with open(temp_gradient_files["output"], 'r') as f:
        content = f.read()
    
    assert "Gradient Distribution Verification Report" in content
    assert "Kolmogorov-Smirnov" in content
    assert "P-value" in content
    assert "Baseline" in content
    assert "Microcircuit" in content

def test_verify_gradient_distribution_with_identical_data():
    """Test distribution comparison with identical data (should have high p-value)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create identical data
        data = {
            "step_0": {"p1": 1.0, "p2": 2.0},
            "step_1": {"p1": 1.5, "p2": 2.5},
            "step_2": {"p1": 1.2, "p2": 2.2},
        }
        
        file1 = os.path.join(tmpdir, "file1.json")
        file2 = os.path.join(tmpdir, "file2.json")
        output = os.path.join(tmpdir, "report.md")
        
        with open(file1, 'w') as f:
            json.dump(data, f)
        with open(file2, 'w') as f:
            json.dump(data, f)
        
        results = verify_gradient_distribution(file1, file2, output)
        
        # Identical distributions should have p-value near 1.0
        # (though with small sample sizes, it might not be exactly 1.0)
        assert results["ks_test"]["p_value"] > 0.1

def test_verify_gradient_distribution_with_different_data(temp_gradient_files):
    """Test distribution comparison with significantly different data."""
    results = verify_gradient_distribution(
        temp_gradient_files["baseline"],
        temp_gradient_files["microcircuit"],
        temp_gradient_files["output"]
    )
    
    # The microcircuit data has significantly higher values
    # This should result in a low p-value (significant difference)
    # Note: With small sample sizes, significance is not guaranteed,
    # but the statistic should reflect the difference
    assert results["ks_test"]["statistic"] > 0.1

def test_extract_gradient_values_list_structure():
    """Test extracting values from list-structured gradient data."""
    data = [
        {"norm": 1.0},
        {"norm": 1.5},
        {"norm": 1.2},
        2.0,
        2.5
    ]
    values = extract_gradient_values(data)
    
    assert isinstance(values, np.ndarray)
    assert len(values) == 5
    assert np.allclose(values, [1.0, 1.5, 1.2, 2.0, 2.5])

def test_extract_gradient_values_mixed_structure():
    """Test extracting values from mixed structure data."""
    data = {
        "step_0": [1.0, 1.5, 1.2],
        "step_1": {"p1": 2.0, "p2": 2.5}
    }
    values = extract_gradient_values(data)
    
    assert isinstance(values, np.ndarray)
    assert len(values) == 5
    assert np.allclose(sorted(values), sorted([1.0, 1.5, 1.2, 2.0, 2.5]))
