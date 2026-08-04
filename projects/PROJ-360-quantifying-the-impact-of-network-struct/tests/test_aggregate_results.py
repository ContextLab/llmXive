import pytest
import json
import os
import tempfile
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from aggregate_results import aggregate_cv_results, save_aggregated_results, update_state_artifact_hash

class TestAggregateCVResults:
    def test_aggregate_mean_std(self):
        """Test basic aggregation of R2 and RMSE."""
        cv_results = [
            {'r2': 0.5, 'rmse': 10.0},
            {'r2': 0.6, 'rmse': 12.0},
            {'r2': 0.4, 'rmse': 11.0}
        ]
        
        result = aggregate_cv_results(cv_results)
        
        assert abs(result['r2_mean'] - 0.5) < 1e-6
        assert abs(result['r2_std'] - 0.08165) < 1e-3 # approx
        assert abs(result['rmse_mean'] - 11.0) < 1e-6
        assert abs(result['rmse_std'] - 0.8165) < 1e-3
    
    def test_aggregate_weak_r2_interpretation(self):
        """Test that weak R2 triggers interpretation string."""
        cv_results = [
            {'r2': 0.1, 'rmse': 20.0},
            {'r2': 0.15, 'rmse': 19.0}
        ]
        
        result = aggregate_cv_results(cv_results)
        
        assert 'r2_interpretation' in result
        assert "Weak predictive power" in result['r2_interpretation']
        assert result['r2_mean'] < 0.30
    
    def test_aggregate_strong_r2_no_interpretation(self):
        """Test that strong R2 does not trigger interpretation string."""
        cv_results = [
            {'r2': 0.8, 'rmse': 5.0},
            {'r2': 0.85, 'rmse': 4.5}
        ]
        
        result = aggregate_cv_results(cv_results)
        
        assert 'r2_interpretation' not in result
    
    def test_aggregate_empty_list(self):
        """Test handling of empty input."""
        result = aggregate_cv_results([])
        
        assert result['r2_mean'] == 0.0
        assert result['r2_std'] == 0.0
        assert "No data available" in result['r2_interpretation']

class TestSaveAggregatedResults:
    def test_save_to_json(self):
        """Test saving results to a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.json")
            results = {
                "r2_mean": 0.5,
                "r2_std": 0.1,
                "rmse_mean": 10.0,
                "rmse_std": 1.0
            }
            
            save_aggregated_results(results, output_path)
            
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            
            assert loaded['r2_mean'] == 0.5
            assert loaded['r2_std'] == 0.1