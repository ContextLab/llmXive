import pytest
import pandas as pd
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.aggregate_attribution import load_existing_stats, aggregate_attribution_results, update_stats_csv, save_results
from utils.exceptions import DataError

class TestAggregateAttribution:
    """
    Contract tests for T037: Aggregate attribution results.
    These tests verify the logic of aggregating attribution data and identifying
    topological features with std > 0.1.
    """

    def test_load_existing_stats_missing_file(self, tmp_path):
        """Test that load_existing_stats returns empty DataFrame if file missing."""
        missing_path = tmp_path / "nonexistent.csv"
        df = load_existing_stats(str(missing_path))
        assert df.empty
        assert isinstance(df, pd.DataFrame)

    def test_load_existing_stats_existing_file(self, tmp_path):
        """Test loading an existing stats file."""
        csv_path = tmp_path / "stats.csv"
        data = {
            "metric": ["test_metric"],
            "observed_value": [0.5],
            "p_value": [0.03]
        }
        df_input = pd.DataFrame(data)
        df_input.to_csv(csv_path, index=False)
        
        df_loaded = load_existing_stats(str(csv_path))
        assert not df_loaded.empty
        assert len(df_loaded) == 1
        assert df_loaded.iloc[0]["metric"] == "test_metric"

    def test_aggregate_attribution_results_empty_file(self, tmp_path):
        """Test aggregation with an empty attribution file."""
        attr_path = tmp_path / "attribution.json"
        attr_path.write_text(json.dumps({"attributions": []}))
        
        stats_df = pd.DataFrame()
        
        with pytest.raises(DataError, match="Attribution results file is empty"):
            aggregate_attribution_results(str(attr_path), stats_df)

    def test_aggregate_attribution_results_identifies_high_std(self, tmp_path):
        """Test that the function correctly identifies features with std > 0.1."""
        # Create mock attribution data where one feature has high variance
        # and another has low variance.
        # Feature A: [0.1, 0.2, 0.1, 0.2] -> low std
        # Feature B: [0.1, 1.5, 0.1, 2.0] -> high std
        attributions = [
            {"feature_A": 0.1, "feature_B": 0.1},
            {"feature_A": 0.2, "feature_B": 1.5},
            {"feature_A": 0.1, "feature_B": 0.1},
            {"feature_A": 0.2, "feature_B": 2.0},
        ]
        
        attr_path = tmp_path / "attribution.json"
        attr_path.write_text(json.dumps({"attributions": attributions}))
        
        stats_df = pd.DataFrame()
        
        updated_df, high_var_features = aggregate_attribution_results(str(attr_path), stats_df)
        
        assert len(high_var_features) == 1
        assert high_var_features[0]["feature"] == "feature_B"
        assert high_var_features[0]["std_dev"] > 0.1
        
        # Check that stats_df was updated
        assert not updated_df.empty
        assert "topological_features_significant_count" in updated_df["metric"].values
        count_row = updated_df[updated_df["metric"] == "topological_features_significant_count"]
        assert count_row.iloc[0]["observed_value"] == 1

    def test_aggregate_attribution_results_no_high_std(self, tmp_path):
        """Test when no features exceed the threshold."""
        attributions = [
            {"feature_A": 0.1, "feature_B": 0.1},
            {"feature_A": 0.11, "feature_B": 0.11},
            {"feature_A": 0.1, "feature_B": 0.1},
            {"feature_A": 0.11, "feature_B": 0.11},
        ]
        
        attr_path = tmp_path / "attribution.json"
        attr_path.write_text(json.dumps({"attributions": attributions}))
        
        stats_df = pd.DataFrame()
        
        updated_df, high_var_features = aggregate_attribution_results(str(attr_path), stats_df)
        
        assert len(high_var_features) == 0
        # The count row should exist with 0
        assert "topological_features_significant_count" in updated_df["metric"].values
        assert updated_df[updated_df["metric"] == "topological_features_significant_count"]["observed_value"].iloc[0] == 0

    def test_save_results(self, tmp_path):
        """Test saving detailed results to JSON."""
        features = [
            {"feature": "f1", "std_dev": 0.5},
            {"feature": "f2", "std_dev": 0.3}
        ]
        output_path = tmp_path / "details.json"
        
        save_results(features, str(output_path))
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["count"] == 2
        assert len(data["features"]) == 2
        assert data["threshold"] == 0.1