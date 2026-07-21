import pytest
import json
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from main import (
    estimate_ram_usage,
    determine_compute_strategy,
    save_compute_strategy,
    run_compute_feasibility_check,
    RAM_THRESHOLD_GB,
    STREAMING_MODE_FLAG,
    RAM_MODE_FLAG
)

class TestRAMEstimation:
    """Test RAM usage estimation logic."""
    
    def test_small_dataset_ram_mode(self):
        """Small dataset should use RAM mode."""
        # 100 subjects, 50 features = ~4MB
        estimated_gb = estimate_ram_usage(100, 50)
        assert estimated_gb < RAM_THRESHOLD_GB
    
    def test_large_dataset_streaming_mode(self):
        """Large dataset should trigger streaming mode."""
        # 10000 subjects, 500 features = ~4GB (close to threshold)
        estimated_gb = estimate_ram_usage(10000, 500)
        assert estimated_gb > RAM_THRESHOLD_GB
    
    def test_exact_threshold_boundary(self):
        """Test behavior at exact threshold."""
        # Calculate exact number for threshold
        # GB = (N * F * 8) / (1024^3)
        # N * F = (GB * 1024^3) / 8
        # For 6GB: N * F = (6 * 1024^3) / 8 ≈ 805,306,368
        # Let's test with N=10000, F=80531
        estimated_gb = estimate_ram_usage(10000, 80531)
        assert estimated_gb >= RAM_THRESHOLD_GB

class TestComputeStrategy:
    """Test compute strategy determination."""
    
    def test_determine_strategy_ram(self, tmp_path):
        """Test RAM mode decision."""
        config = {
            "num_subjects": 100,
            "num_features": 50
        }
        strategy = determine_compute_strategy({"data_raw": tmp_path}, config)
        assert strategy == RAM_MODE_FLAG
    
    def test_determine_strategy_streaming(self, tmp_path):
        """Test streaming mode decision."""
        config = {
            "num_subjects": 10000,
            "num_features": 500
        }
        strategy = determine_compute_strategy({"data_raw": tmp_path}, config)
        assert strategy == STREAMING_MODE_FLAG
    
    def test_save_compute_strategy(self, tmp_path):
        """Test saving compute strategy to JSON."""
        strategy = "STREAMING"
        details = {
            "ram_threshold_gb": 6.0,
            "num_subjects": 10000,
            "num_features": 500
        }
        
        paths = {
            "data_metadata": tmp_path / "metadata"
        }
        paths["data_metadata"].mkdir(parents=True, exist_ok=True)
        
        output_path = save_compute_strategy(paths, strategy, details)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data["strategy"] == strategy
        assert saved_data["details"]["num_subjects"] == 10000
        assert "timestamp" in saved_data

class TestComputeFeasibilityCheck:
    """Test the full T059 implementation."""
    
    def test_run_compute_feasibility_check_creates_artifact(self, tmp_path):
        """Verify T059 creates the required artifact."""
        config = {
            "num_subjects": 10000,
            "num_features": 500
        }
        
        paths = {
            "data_metadata": tmp_path / "metadata",
            "data_raw": tmp_path / "raw",
            "data_processed": tmp_path / "processed",
            "data_results": tmp_path / "results",
            "data_config": tmp_path / "config",
            "specs": tmp_path / "specs",
            "contracts": tmp_path / "contracts",
            "figures": tmp_path / "figures",
            "state": tmp_path / "state",
            "code": tmp_path / "code",
            "data": tmp_path / "data",
            "root": tmp_path
        }
        
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)
        
        strategy = run_compute_feasibility_check(paths, config)
        
        # Verify strategy is correct
        assert strategy == STREAMING_MODE_FLAG
        
        # Verify artifact exists
        artifact_path = paths["data_metadata"] / "compute_strategy.json"
        assert artifact_path.exists()
        
        # Verify content
        with open(artifact_path, 'r') as f:
            data = json.load(f)
        
        assert data["strategy"] == "STREAMING"
        assert "threshold_gb" in data
        assert "details" in data
        assert "timestamp" in data