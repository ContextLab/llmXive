"""
Unit tests for baseline training logging operations.

Tests the logging functionality in code/training/log_baseline_operations.py
to ensure all metrics and exclusion counts are properly recorded.
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the code directory to the path
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from training.log_baseline_operations import (
    ensure_log_directory,
    log_smiles_exclusion_count,
    log_data_preprocessing_stats,
    log_split_statistics,
    log_baseline_training_metrics,
    log_model_save_operation,
    LOG_DIR,
    METRICS_FILE
)

import pytest

class TestBaselineLogging:
    """Test suite for baseline training logging operations."""
    
    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures."""
        # Create a temporary directory for logs
        self.test_log_dir = tmp_path / "data" / "logs"
        self.test_log_dir.mkdir(parents=True)
        
        # Mock the LOG_DIR and METRICS_FILE
        self.original_log_dir = LOG_DIR
        self.original_metrics_file = METRICS_FILE
        
        # Temporarily patch the constants
        with patch('training.log_baseline_operations.LOG_DIR', self.test_log_dir), \
             patch('training.log_baseline_operations.METRICS_FILE', str(self.test_log_dir / "baseline_training_metrics.json")):
            yield
    
    def test_ensure_log_directory_creates_directory(self):
        """Test that ensure_log_directory creates the log directory if it doesn't exist."""
        new_log_dir = self.test_log_dir / "new_subdir"
        
        with patch('training.log_baseline_operations.LOG_DIR', new_log_dir):
            ensure_log_directory()
            
            assert new_log_dir.exists()
            assert new_log_dir.is_dir()
    
    def test_log_smiles_exclusion_count(self):
        """Test logging of SMILES exclusion counts."""
        exclusion_log_path = self.test_log_dir / "exclusion_counts.json"
        
        log_smiles_exclusion_count(5, "Invalid SMILES")
        
        assert exclusion_log_path.exists()
        
        with open(exclusion_log_path, 'r') as f:
            exclusions = json.load(f)
        
        assert len(exclusions) == 1
        assert exclusions[0]["count"] == 5
        assert exclusions[0]["reason"] == "Invalid SMILES"
        assert "timestamp" in exclusions[0]
    
    def test_log_smiles_exclusion_count_multiple(self):
        """Test logging multiple exclusion counts."""
        exclusion_log_path = self.test_log_dir / "exclusion_counts.json"
        
        log_smiles_exclusion_count(5, "Invalid SMILES")
        log_smiles_exclusion_count(3, "Missing logS")
        
        with open(exclusion_log_path, 'r') as f:
            exclusions = json.load(f)
        
        assert len(exclusions) == 2
        assert exclusions[0]["count"] == 5
        assert exclusions[1]["count"] == 3
    
    def test_log_data_preprocessing_stats(self):
        """Test logging of preprocessing statistics."""
        log_path = self.test_log_dir / "preprocessing_stats.json"
        
        stats = {
            "total_molecules": 1000,
            "valid_molecules": 950,
            "features_extracted": 2048
        }
        
        log_data_preprocessing_stats(stats)
        
        assert log_path.exists()
        
        with open(log_path, 'r') as f:
            all_stats = json.load(f)
        
        assert len(all_stats) == 1
        assert all_stats[0]["total_molecules"] == 1000
        assert all_stats[0]["valid_molecules"] == 950
        assert "timestamp" in all_stats[0]
    
    def test_log_split_statistics(self):
        """Test logging of split statistics."""
        log_path = self.test_log_dir / "split_statistics.json"
        
        log_split_statistics(800, 160, 168)
        
        assert log_path.exists()
        
        with open(log_path, 'r') as f:
            splits = json.load(f)
        
        assert len(splits) == 1
        assert splits[0]["train_size"] == 800
        assert splits[0]["val_size"] == 160
        assert splits[0]["test_size"] == 168
        assert splits[0]["total_size"] == 1128
    
    def test_log_baseline_training_metrics(self):
        """Test logging of baseline training metrics."""
        metrics_file = self.test_log_dir / "baseline_training_metrics.json"
        
        log_baseline_training_metrics(
            r_squared=0.85,
            rmse=0.65,
            mae=0.52,
            training_time_seconds=45.3
        )
        
        assert metrics_file.exists()
        
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        assert metrics["r_squared"] == 0.85
        assert metrics["rmse"] == 0.65
        assert metrics["mae"] == 0.52
        assert metrics["training_time_seconds"] == 45.3
        assert "hyperparameters" in metrics
    
    def test_log_baseline_training_metrics_with_none(self):
        """Test that None values are excluded from metrics."""
        metrics_file = self.test_log_dir / "baseline_training_metrics.json"
        
        log_baseline_training_metrics(
            r_squared=0.85,
            rmse=0.65,
            mae=None,  # This should be excluded
            training_time_seconds=None  # This should be excluded
        )
        
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        assert "mae" not in metrics
        assert "training_time_seconds" not in metrics
        assert metrics["r_squared"] == 0.85
        assert metrics["rmse"] == 0.65
    
    def test_log_model_save_operation(self):
        """Test logging of model save operation."""
        log_path = self.test_log_dir / "model_operations.json"
        
        log_model_save_operation("models/baseline_rf.pkl", 2500000)
        
        assert log_path.exists()
        
        with open(log_path, 'r') as f:
            operations = json.load(f)
        
        assert len(operations) == 1
        assert operations[0]["model_path"] == "models/baseline_rf.pkl"
        assert operations[0]["model_size_bytes"] == 2500000
        assert abs(operations[0]["model_size_mb"] - 2.38) < 0.01
    
    def test_log_smiles_exclusion_count_creates_file_if_not_exists(self):
        """Test that exclusion log file is created if it doesn't exist."""
        exclusion_log_path = self.test_log_dir / "exclusion_counts.json"
        
        # Ensure file doesn't exist
        if exclusion_log_path.exists():
            exclusion_log_path.unlink()
        
        log_smiles_exclusion_count(5, "Invalid SMILES")
        
        assert exclusion_log_path.exists()
    
    def test_log_baseline_training_metrics_creates_file_if_not_exists(self):
        """Test that metrics file is created if it doesn't exist."""
        metrics_file = self.test_log_dir / "baseline_training_metrics.json"
        
        # Ensure file doesn't exist
        if metrics_file.exists():
            metrics_file.unlink()
        
        log_baseline_training_metrics(r_squared=0.85, rmse=0.65)
        
        assert metrics_file.exists()