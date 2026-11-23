import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys_path = str(project_root / "code")
if sys_path not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_path)

from analysis.aggregate_attribution import (
    aggregate_attribution_results,
    load_existing_stats,
    update_stats_csv,
    SIGNIFICANCE_STD_THRESHOLD
)
from utils.exceptions import DataError

@pytest.fixture
def sample_attribution_data():
    """Create sample attribution data for testing."""
    return [
        {
            "sample_id": 1,
            "feature_importance": {
                "degree": 0.25,
                "clustering": 0.15,
                "density": 0.10,
                "path_length": 0.05
            }
        },
        {
            "sample_id": 2,
            "feature_importance": {
                "degree": 0.30,
                "clustering": 0.12,
                "density": 0.08,
                "path_length": 0.07
            }
        },
        {
            "sample_id": 3,
            "feature_importance": {
                "degree": 0.20,
                "clustering": 0.18,
                "density": 0.12,
                "path_length": 0.03
            }
        }
    ]

@pytest.fixture
def sample_stats_data():
    """Create sample stats data for testing."""
    return [
        {
            "metric": "permutation_p_value",
            "observed_value": 0.03,
            "p_value": 0.03,
            "corrected_p_value": 0.06,
            "vif_score": 1.2,
            "fwer": 0.06
        }
    ]

def test_aggregate_attribution_results_basic(sample_attribution_data):
    """Test basic aggregation of attribution results."""
    result = aggregate_attribution_results(sample_attribution_data)
    
    assert "mean_importance" in result
    assert "std_importance" in result
    assert "topological_features_significant" in result
    assert "threshold_used" in result
    
    # Check that all features are present
    expected_features = {"degree", "clustering", "density", "path_length"}
    assert set(result["mean_importance"].keys()) == expected_features
    assert set(result["std_importance"].keys()) == expected_features

def test_aggregate_attribution_significance_threshold(sample_attribution_data):
    """Test that features are correctly identified based on std threshold."""
    result = aggregate_attribution_results(sample_attribution_data)
    
    # All features should have some std
    for feat, std in result["std_importance"].items():
        assert std >= 0.0
        
    # Check that features with std > threshold are included
    significant = result["topological_features_significant"]
    for feat_data in significant:
        assert feat_data["std_importance"] > SIGNIFICANCE_STD_THRESHOLD

def test_aggregate_attribution_empty_data():
    """Test that empty data raises appropriate error."""
    with pytest.raises(DataError):
        aggregate_attribution_results([])

def test_update_stats_csv(sample_stats_data, sample_attribution_data):
    """Test updating stats CSV with new topological feature data."""
    aggregated = aggregate_attribution_results(sample_attribution_data)
    updated_stats = update_stats_csv(aggregated, sample_stats_data)
    
    # Should have original stats + new topological feature stats
    original_count = len(sample_stats_data)
    significant_count = len(aggregated["topological_features_significant"])
    
    assert len(updated_stats) == original_count + significant_count
    
    # Check that new stats have correct structure
    new_stats = updated_stats[original_count:]
    for stat in new_stats:
        assert "metric" in stat
        assert stat["metric"].startswith("topological_std_")
        assert "observed_value" in stat
        assert stat["observed_value"] > SIGNIFICANCE_STD_THRESHOLD

def test_load_existing_stats_file_not_found(tmp_path):
    """Test loading stats when file doesn't exist."""
    with patch("analysis.aggregate_attribution.STATS_FILE", tmp_path / "nonexistent.csv"):
        stats = load_existing_stats()
        assert stats == []

def test_load_existing_stats_invalid_file(tmp_path):
    """Test loading stats from invalid file."""
    invalid_csv = tmp_path / "stats.csv"
    invalid_csv.write_text("invalid, csv, content\nwithout, proper, headers")
    
    with patch("analysis.aggregate_attribution.STATS_FILE", invalid_csv):
        stats = load_existing_stats()
        assert stats == []

def test_aggregate_attribution_single_sample(sample_attribution_data):
    """Test aggregation with single sample."""
    single_sample = [sample_attribution_data[0]]
    result = aggregate_attribution_results(single_sample)
    
    # With single sample, std should be 0 for all features
    for std in result["std_importance"].values():
        assert std == 0.0
        
    # No features should be significant
    assert len(result["topological_features_significant"]) == 0

def test_aggregate_attribution_all_significant(tmp_path):
    """Test with data where all features are significant."""
    # Create data with high variance
    high_variance_data = [
        {"sample_id": i, "feature_importance": {
            "feat1": 0.1 * i,
            "feat2": 0.2 * i,
            "feat3": 0.3 * i
        }}
        for i in range(10)
    ]
    
    result = aggregate_attribution_results(high_variance_data)
    
    # All features should have std > threshold
    assert len(result["topological_features_significant"]) == 3

def test_integration_full_flow(sample_attribution_data, sample_stats_data, tmp_path):
    """Test the full flow of aggregation and stats update."""
    # Mock file paths
    with patch("analysis.aggregate_attribution.ATTRIBUTION_FILE", tmp_path / "attribution.json"), \
         patch("analysis.aggregate_attribution.STATS_FILE", tmp_path / "stats.csv"), \
         patch("analysis.aggregate_attribution.RESULTS_DIR", tmp_path):
         
         # Save mock attribution data
         attr_file = tmp_path / "attribution.json"
         with open(attr_file, 'w') as f:
             json.dump(sample_attribution_data, f)
         
         # Save mock stats data
         stats_file = tmp_path / "stats.csv"
         df = pd.DataFrame(sample_stats_data)
         df.to_csv(stats_file, index=False)
         
         # Run aggregation
         from analysis.aggregate_attribution import main
         import sys
         
         # Capture return code
         return_code = main()
         
         assert return_code == 0
         
         # Verify output files exist
         assert (tmp_path / "attribution_aggregated.json").exists()
         assert (tmp_path / "stats.csv").exists()
         assert (tmp_path / "topological_features_report.json").exists()
         
         # Verify stats file has updated content
         updated_df = pd.read_csv(tmp_path / "stats.csv")
         assert len(updated_df) > len(sample_stats_data)
         
         # Verify aggregated results
         with open(tmp_path / "attribution_aggregated.json") as f:
             agg_results = json.load(f)
         
         assert "topological_features_significant" in agg_results
         assert agg_results["significant_features_count"] > 0