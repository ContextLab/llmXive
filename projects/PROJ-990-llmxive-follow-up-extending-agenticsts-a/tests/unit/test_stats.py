"""
Unit tests for stats.py (T021 & T024a).
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import tempfile
import os

# Import the functions we want to test
from code.stats import (
    compute_aggregates,
    detect_divergence,
    load_simulation_results
)

class TestComputeAggregates:
    def test_aggregates_calculation(self):
        """Test that win_rate and avg_tokens are calculated correctly."""
        data = {
            "dynamic": pd.DataFrame({
                "win": [1, 1, 0],
                "tokens_used": [100, 200, 150],
                "trajectory_id": ["t1", "t2", "t3"]
            }),
            "static": pd.DataFrame({
                "win": [1, 0, 0],
                "tokens_used": [300, 300, 300],
                "trajectory_id": ["t1", "t2", "t3"]
            })
        }
        
        result_df = compute_aggregates(data)
        
        # Check dynamic: win_rate = 2/3, avg_tokens = 150
        dynamic_row = result_df[result_df['condition'] == 'dynamic'].iloc[0]
        assert abs(dynamic_row['win_rate'] - (2/3)) < 0.001
        assert abs(dynamic_row['avg_tokens'] - 150.0) < 0.001
        
        # Check static: win_rate = 1/3, avg_tokens = 300
        static_row = result_df[result_df['condition'] == 'static'].iloc[0]
        assert abs(static_row['win_rate'] - (1/3)) < 0.001
        assert abs(static_row['avg_tokens'] - 300.0) < 0.001

    def test_empty_dataframe_handling(self):
        """Test that empty dataframes are handled gracefully."""
        data = {
            "dynamic": pd.DataFrame(columns=["win", "tokens_used", "trajectory_id"]),
            "static": pd.DataFrame(columns=["win", "tokens_used", "trajectory_id"])
        }
        
        result_df = compute_aggregates(data)
        assert result_df.empty

class TestDetectDivergence:
    def test_divergence_detected(self):
        """Test that divergence is detected when outcomes differ."""
        dynamic_df = pd.DataFrame({
            "trajectory_id": ["t1", "t2", "t3"],
            "win": [1, 1, 0]
        })
        static_df = pd.DataFrame({
            "trajectory_id": ["t1", "t2", "t3"],
            "win": [1, 0, 0]  # t2 differs
        })
        
        results = {
            "dynamic": dynamic_df,
            "static": static_df
        }
        
        divergence_data = detect_divergence(results)
        
        assert divergence_data['is_divergent'] is True
        assert divergence_data['divergence_count'] == 1
        assert divergence_data['total_pairs'] == 3
        assert abs(divergence_data['divergence_rate'] - (1/3)) < 0.001

    def test_no_divergence(self):
        """Test that divergence is False when outcomes match."""
        dynamic_df = pd.DataFrame({
            "trajectory_id": ["t1", "t2", "t3"],
            "win": [1, 0, 1]
        })
        static_df = pd.DataFrame({
            "trajectory_id": ["t1", "t2", "t3"],
            "win": [1, 0, 1]
        })
        
        results = {
            "dynamic": dynamic_df,
            "static": static_df
        }
        
        divergence_data = detect_divergence(results)
        
        assert divergence_data['is_divergent'] is False
        assert divergence_data['divergence_count'] == 0

    def test_missing_data(self):
        """Test behavior when one condition is missing."""
        results = {
            "dynamic": pd.DataFrame({"trajectory_id": ["t1"], "win": [1]}),
            "static": pd.DataFrame() # Empty
        }
        
        divergence_data = detect_divergence(results)
        
        assert divergence_data['is_divergent'] is False
        assert 'reason' in divergence_data

class TestLoadSimulationResults:
    def test_load_from_temp_files(self):
        """Test loading results from temporary CSV files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            
            # Create dummy CSV files
            (tmp_path / "dynamic_results.csv").write_text("win,tokens_used,trajectory_id\n1,100,t1\n0,200,t2")
            (tmp_path / "static_results.csv").write_text("win,tokens_used,trajectory_id\n1,300,t1\n0,300,t2")
            
            results = load_simulation_results(tmp_path)
            
            assert "dynamic" in results
            assert "static" in results
            assert len(results["dynamic"]) == 2
            assert len(results["static"]) == 2