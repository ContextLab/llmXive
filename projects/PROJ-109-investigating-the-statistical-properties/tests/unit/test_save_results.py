import pytest
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

from analysis.save_results import (
    save_statistics_to_json,
    load_convergence_stats,
    run_save_results_pipeline
)

class TestSaveResults:
    
    def test_save_statistics_to_json_creates_file(self, tmp_path):
        """Test that save_statistics_to_json creates a valid JSON file."""
        output_file = tmp_path / "test_stats.json"
        
        ks_data = {"test": {"statistic": 0.5, "pvalue": 0.01}}
        bh_data = {"test": {"pvalue": 0.01, "rejected": True}}
        spearman_data = {"mass_vs_shape": {"rho": 0.8, "pvalue": 0.001}}
        bullock_data = {"rmse": 0.15, "mean_diff": 0.05}
        conv_data = {"success_rate": 0.95, "total_fits": 100}
        
        save_statistics_to_json(
            ks_results=ks_data,
            bh_results=bh_data,
            spearman_results=spearman_data,
            bullock_results=bullock_data,
            convergence_stats=conv_data,
            output_path=output_file
        )
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        assert "ks_tests" in loaded
        assert "benjamini_hochberg_correction" in loaded
        assert "spearman_correlations" in loaded
        assert "bullock_comparison" in loaded
        assert "convergence_statistics" in loaded
        assert "metadata" in loaded
        assert loaded["ks_tests"]["test"]["statistic"] == 0.5
    
    def test_save_statistics_serializes_numpy_types(self, tmp_path):
        """Test that numpy types are serialized correctly."""
        output_file = tmp_path / "test_numpy.json"
        
        ks_data = {"np_test": {"statistic": np.float64(0.5), "pvalue": np.float32(0.01)}}
        bh_data = {"np_test": {"pvalue": np.int64(1), "rejected": True}}
        spearman_data = {"np_test": {"rho": np.float64(0.8), "pvalue": np.float64(0.001)}}
        bullock_data = {"rmse": np.float64(0.15), "mean_diff": np.float32(0.05)}
        conv_data = {"success_rate": 0.95, "total_fits": 100}
        
        # This should not raise a TypeError
        save_statistics_to_json(
            ks_results=ks_data,
            bh_results=bh_data,
            spearman_results=spearman_data,
            bullock_results=bullock_data,
            convergence_stats=conv_data,
            output_path=output_file
        )
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        
        # Verify values are preserved
        assert loaded["ks_tests"]["np_test"]["statistic"] == 0.5
    
    def test_load_convergence_stats_missing_file(self, tmp_path, monkeypatch):
        """Test that load_convergence_stats returns defaults when file is missing."""
        # Monkeypatch the RESULTS_DIR to tmp_path for this test
        import analysis.save_results as module
        original_results_dir = module.RESULTS_DIR
        module.RESULTS_DIR = tmp_path
        
        try:
            result = load_convergence_stats()
            
            assert "success_rate" in result
            assert result["success_rate"] == 0.0
            assert result["failed_fits"] == 0
        finally:
            module.RESULTS_DIR = original_results_dir
    
    def test_load_convergence_stats_existing_file(self, tmp_path, monkeypatch):
        """Test loading from an existing file."""
        conv_file = tmp_path / "convergence_stats.json"
        test_data = {"success_rate": 0.85, "failed_fits": 10, "total_fits": 100}
        
        with open(conv_file, 'w') as f:
            json.dump(test_data, f)
        
        import analysis.save_results as module
        original_results_dir = module.RESULTS_DIR
        module.RESULTS_DIR = tmp_path
        
        try:
            result = load_convergence_stats()
            assert result["success_rate"] == 0.85
            assert result["failed_fits"] == 10
        finally:
            module.RESULTS_DIR = original_results_dir