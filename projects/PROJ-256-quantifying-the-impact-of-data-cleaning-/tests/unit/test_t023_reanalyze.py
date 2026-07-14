import os
import json
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the functions to test
from t023_reanalyze_variants import find_cleaned_datasets, analyze_cleaned_variant

@pytest.fixture
def temp_processed_dir(tmp_path):
    """Create a temporary processed directory with mock cleaned datasets."""
    # Create mock CSV files
    (tmp_path / "har_dataset_outlier_removed.csv").write_text("a,b,target\n1,2,3\n4,5,6\n")
    (tmp_path / "shopper_mean_imputed.csv").write_text("x,y,target\n7,8,9\n10,11,12\n")
    return tmp_path

def test_find_cleaned_datasets(temp_processed_dir):
    """Test that find_cleaned_datasets correctly identifies cleaned files."""
    results = find_cleaned_datasets(str(temp_processed_dir))
    
    assert len(results) == 2
    
    # Check that both files are found
    filenames = [r["filename"] for r in results]
    assert "har_dataset_outlier_removed.csv" in filenames
    assert "shopper_mean_imputed.csv" in filenames
    
    # Check extracted info
    for r in results:
        assert "dataset_name" in r
        assert "strategy" in r
        assert "filepath" in r
        assert os.path.exists(r["filepath"])

def test_analyze_cleaned_variant_with_t_test(temp_processed_dir):
    """Test analysis of a cleaned dataset with t-test."""
    # Create a dataset with two groups
    data = {
        "feature": [1, 2, 3, 10, 11, 12],
        "group": ["A", "A", "A", "B", "B", "B"],
        "target": [10, 12, 11, 20, 22, 21]
    }
    df = pd.DataFrame(data)
    test_file = temp_processed_dir / "test_ttest_outlier_removed.csv"
    df.to_csv(test_file, index=False)
    
    result = analyze_cleaned_variant(
        filepath=str(test_file),
        dataset_name="test_ttest",
        strategy="outlier_removed",
        config={"RANDOM_SEED": 42},
        outcome_col="target",
        group_col="group"
    )
    
    assert "dataset_name" in result
    assert result["dataset_name"] == "test_ttest"
    assert "analysis" in result
    assert "t_test" in result["analysis"]
    assert 0 < result["analysis"]["t_test"]["p_value"] < 1
    assert result["analysis"]["t_test"]["effect_size_cohen_d"] > 0
    assert len(result["analysis"]["t_test"]["ci_95"]) == 2

def test_analyze_cleaned_variant_regression(temp_processed_dir):
    """Test analysis of a cleaned dataset with regression."""
    # Create a dataset with a clear linear relationship
    np.random.seed(42)
    x = np.random.randn(50)
    y = 2 * x + np.random.randn(50) * 0.1
    data = {"feature": x, "target": y}
    df = pd.DataFrame(data)
    test_file = temp_processed_dir / "test_reg_mean_imputed.csv"
    df.to_csv(test_file, index=False)
    
    result = analyze_cleaned_variant(
        filepath=str(test_file),
        dataset_name="test_reg",
        strategy="mean_imputed",
        config={"RANDOM_SEED": 42},
        outcome_col="target",
        group_col=None
    )
    
    assert "dataset_name" in result
    assert "analysis" in result
    assert "regression" in result["analysis"]
    assert result["analysis"]["regression"]["r_squared"] > 0.9  # Should be high
    assert result["analysis"]["regression"]["coefficient"] > 1.5  # Should be close to 2

def test_analyze_cleaned_variant_missing_outcome(temp_processed_dir):
    """Test handling of missing outcome column."""
    data = {"feature": [1, 2, 3], "other": [4, 5, 6]}
    df = pd.DataFrame(data)
    test_file = temp_processed_dir / "test_missing_outlier_removed.csv"
    df.to_csv(test_file, index=False)
    
    result = analyze_cleaned_variant(
        filepath=str(test_file),
        dataset_name="test_missing",
        strategy="outlier_removed",
        config={"RANDOM_SEED": 42},
        outcome_col="nonexistent",
        group_col=None
    )
    
    assert "error" in result
    assert "nonexistent" in result["error"]

def test_find_cleaned_datasets_empty_dir(tmp_path):
    """Test find_cleaned_datasets with no matching files."""
    results = find_cleaned_datasets(str(tmp_path))
    assert results == []
