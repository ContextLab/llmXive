"""
Unit tests for T010b: Synthetic metrics computation.

Tests verify that:
1. The script correctly finds synthetic datasets
2. Metrics are computed for synthetic series
3. Output format matches expected schema
4. Error handling works for missing/invalid data
"""
import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.run_metrics_synthetic import find_synthetic_datasets, compute_metrics_for_synthetic_datasets
from src.data.metrics import MetricsError


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create synthetic directory
        synthetic_dir = tmpdir / "synthetic"
        synthetic_dir.mkdir()
        
        # Create test synthetic datasets
        # Dataset 1: fGn with H=0.7
        data1 = pd.DataFrame({
            'value': np.random.randn(100),
            'timestamp': pd.date_range('2020-01-01', periods=100, freq='H')
        })
        data1.to_csv(synthetic_dir / "fgn_h07_n100.csv", index=False)
        
        # Dataset 2: fGn with H=0.9
        data2 = pd.DataFrame({
            'value': np.random.randn(500),
            'timestamp': pd.date_range('2020-01-01', periods=500, freq='H')
        })
        data2.to_csv(synthetic_dir / "fgn_h09_n500.csv", index=False)
        
        yield tmpdir


class TestFindSyntheticDatasets:
    """Tests for find_synthetic_datasets function."""
    
    def test_finds_csv_files(self, temp_test_dir):
        """Test that CSV files are found correctly."""
        datasets = find_synthetic_datasets(temp_test_dir)
        assert len(datasets) == 2
        assert all(d.suffix == '.csv' for d in datasets)
        
    def test_empty_directory(self, temp_test_dir):
        """Test handling of empty synthetic directory."""
        # Remove all files
        for f in (temp_test_dir / "synthetic").glob("*"):
            f.unlink()
            
        datasets = find_synthetic_datasets(temp_test_dir)
        assert len(datasets) == 0
        
    def test_nonexistent_directory(self, temp_test_dir):
        """Test handling of nonexistent synthetic directory."""
        datasets = find_synthetic_datasets(temp_test_dir / "nonexistent")
        assert len(datasets) == 0


class TestComputeMetricsForSynthetic:
    """Tests for compute_metrics_for_synthetic_datasets function."""
    
    def test_computes_metrics_successfully(self, temp_test_dir):
        """Test that metrics are computed for all datasets."""
        datasets = find_synthetic_datasets(temp_test_dir)
        results = compute_metrics_for_synthetic_datasets(datasets)
        
        assert len(results) == 2
        assert "fgn_h07_n100" in results
        assert "fgn_h09_n500" in results
        
        # Check that metrics contain expected keys
        for dataset_name, metrics in results.items():
            assert "acf_lag1" in metrics
            assert "hurst_exponent" in metrics
            assert "spectral_peak_ratio" in metrics
            
    def test_handles_error_gracefully(self, temp_test_dir):
        """Test that errors are handled without crashing."""
        # Create an invalid file
        (temp_test_dir / "synthetic" / "invalid.csv").write_text("not,csv,data\n1,2,3")
        
        datasets = find_synthetic_datasets(temp_test_dir)
        results = compute_metrics_for_synthetic_datasets(datasets)
        
        # Should have 3 entries (2 valid + 1 invalid)
        assert len(results) == 3
        
        # Invalid dataset should have error
        assert "invalid" in results
        assert "error" in results["invalid"]


class TestOutputFormat:
    """Tests for output format validation."""
    
    def test_output_matches_schema(self, temp_test_dir):
        """Test that output format matches expected schema."""
        datasets = find_synthetic_datasets(temp_test_dir)
        results = compute_metrics_for_synthetic_datasets(datasets)
        
        # Verify structure
        assert isinstance(results, dict)
        
        for dataset_name, metrics in results.items():
            assert isinstance(metrics, dict)
            
            # Required metric fields
            assert "acf_lag1" in metrics
            assert "hurst_exponent" in metrics
            assert "spectral_peak_ratio" in metrics
            
            # Verify types
            assert isinstance(metrics["acf_lag1"], (int, float))
            assert isinstance(metrics["hurst_exponent"], (int, float))
            assert isinstance(metrics["spectral_peak_ratio"], (int, float))
            
            # Verify reasonable ranges (for synthetic data)
            assert -1.0 <= metrics["acf_lag1"] <= 1.0
            assert 0.0 <= metrics["hurst_exponent"] <= 1.0
            assert metrics["spectral_peak_ratio"] >= 0.0
            
    def test_json_serializable(self, temp_test_dir):
        """Test that results can be serialized to JSON."""
        datasets = find_synthetic_datasets(temp_test_dir)
        results = compute_metrics_for_synthetic_datasets(datasets)
        
        # Should not raise
        json_str = json.dumps(results)
        assert len(json_str) > 0
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed == results