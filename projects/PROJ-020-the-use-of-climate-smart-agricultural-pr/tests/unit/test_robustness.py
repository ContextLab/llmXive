"""
Unit tests for robustness checks (T035).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from analysis.robustness import run_leave_one_region_out, run_bootstrap_resampling

@pytest.fixture
def mock_data():
    """Generate a mock dataset for testing robustness functions."""
    np.random.seed(42)
    n = 500
    data = pd.DataFrame({
        "region": np.random.choice(["North", "South", "East", "West"], n),
        "country": np.random.choice(["KE", "IN", "VN"], n),
        "food_security_index": np.random.normal(50, 10, n),
        "csa_index": np.random.normal(0.5, 0.2, n),
        "digital_access": np.random.binomial(1, 0.4, n),
        "finance_access": np.random.binomial(1, 0.3, n),
        "age": np.random.normal(45, 12, n),
        "education_years": np.random.normal(8, 3, n),
        "household_size": np.random.normal(4, 2, n),
        "plot_size": np.random.exponential(2, n)
    })
    return data

def test_loro_structure(mock_data):
    """Test that LORO returns expected structure."""
    formula = "food_security_index ~ csa_index + digital_access"
    result = run_leave_one_region_out(
        mock_data, 
        formula, 
        region_column="region",
        random_effect="country"
    )
    
    assert "full_model" in result
    assert "loro_results" in result
    assert "stability_metrics" in result
    assert "n_regions" in result
    
    # Check that we have results for each region (or skipped ones)
    assert len(result["loro_results"]) > 0
    
    # Check stability metrics exist if we had successful folds
    if result["n_successful_folds"] > 1:
        assert "mean_coefficient" in result["stability_metrics"]
        assert "std_coefficient" in result["stability_metrics"]

def test_bootstrap_structure(mock_data):
    """Test that Bootstrap returns expected structure."""
    formula = "food_security_index ~ csa_index + digital_access"
    # Use small n_iterations for speed in unit test
    result = run_bootstrap_resampling(
        mock_data, 
        formula, 
        random_effect="country",
        n_iterations=10,
        seed=123
    )
    
    assert "summary" in result
    assert "distributions" in result
    assert "n_iterations_requested" in result
    assert result["n_iterations_requested"] == 10
    
    # Check that we have summary stats for coefficients
    assert "csa_index" in result["summary"]
    summary_item = result["summary"]["csa_index"]
    assert "mean" in summary_item
    assert "std" in summary_item
    assert "ci_95_lower" in summary_item
    assert "ci_95_upper" in summary_item

def test_loro_with_missing_region(mock_data):
    """Test LORO behavior when a region is missing from data."""
    # Filter data to remove one region
    filtered_data = mock_data[mock_data["region"] != "North"]
    
    formula = "food_security_index ~ csa_index"
    result = run_leave_one_region_out(
        filtered_data, 
        formula, 
        region_column="region",
        random_effect="country"
    )
    
    # Should still run, but n_regions will reflect unique regions in data
    assert result["n_regions"] == 3 # South, East, West
    assert len(result["loro_results"]) == 3

def test_invalid_column_loro(mock_data):
    """Test LORO fails gracefully with invalid region column."""
    with pytest.raises(ValueError):
        run_leave_one_region_out(
            mock_data,
            "food_security_index ~ csa_index",
            region_column="non_existent_column"
        )
