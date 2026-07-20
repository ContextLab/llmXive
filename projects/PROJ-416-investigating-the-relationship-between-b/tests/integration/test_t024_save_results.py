"""
Integration test for T024: Save connectivity matrices and metrics.
Verifies that save_results.py correctly writes .npy files and the CSV.
"""
import os
import csv
import json
import tempfile
from pathlib import Path
import numpy as np
import pytest

# Import the functions to test
# Note: Adjusting import path to match project structure (code/analysis)
import sys
from pathlib import Path

# Ensure the code directory is in the path
code_root = Path(__file__).parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from analysis.save_results import (
    ensure_directories,
    save_matrix_to_npy,
    save_metrics_to_csv,
    run_save_results
)
from config import Config

class TestT024SaveResults:
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_metrics_data(self):
        """Generate sample metrics data simulating the output of network analysis."""
        subject_1_id = "sub-001"
        subject_2_id = "sub-002"
        
        # Create dummy 5x5 connectivity matrices
        matrix_1 = np.random.rand(5, 5)
        matrix_2 = np.random.rand(5, 5)
        
        return [
            {
                "subject_id": subject_1_id,
                "matrix": matrix_1,
                "modularity_q": 0.45,
                "global_efficiency": 0.32,
                "local_efficiency": 0.28,
                "fd_mean": 0.15
            },
            {
                "subject_id": subject_2_id,
                "matrix": matrix_2,
                "modularity_q": 0.51,
                "global_efficiency": 0.35,
                "local_efficiency": 0.30,
                "fd_mean": 0.22
            }
        ]

    def test_ensure_directories(self, temp_output_dir):
        """Test that ensure_directories creates the required folders."""
        ensure_directories(temp_output_dir)
        
        assert temp_output_dir.exists()
        assert (temp_output_dir / "matrices").exists()

    def test_save_matrix_to_npy(self, temp_output_dir, sample_metrics_data):
        """Test saving a single matrix to .npy."""
        item = sample_metrics_data[0]
        file_path = save_matrix_to_npy(item["subject_id"], item["matrix"], temp_output_dir)
        
        expected_path = temp_output_dir / "matrices" / f"{item['subject_id']}_connectivity.npy"
        assert file_path == str(expected_path)
        assert expected_path.exists()
        
        # Verify content
        loaded_matrix = np.load(expected_path)
        np.testing.assert_array_equal(loaded_matrix, item["matrix"])

    def test_save_metrics_to_csv(self, temp_output_dir, sample_metrics_data):
        """Test saving metrics to CSV."""
        csv_path = temp_output_dir / "network_metrics.csv"
        save_metrics_to_csv(sample_metrics_data, csv_path)
        
        assert csv_path.exists()
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        
        # Check specific values for subject 1
        sub1_row = next(r for r in rows if r['subject_id'] == 'sub-001')
        assert float(sub1_row['modularity_q']) == pytest.approx(0.45, rel=0.01)
        assert float(sub1_row['fd_mean']) == pytest.approx(0.15, rel=0.01)
        
        # Check that matrix column is NOT in CSV
        assert 'matrix' not in sub1_row

    def test_run_save_results_end_to_end(self, temp_output_dir, sample_metrics_data):
        """End-to-end test of run_save_results."""
        # Mock config to use temp directory
        class MockConfig:
            OUTPUT_DIR = str(temp_output_dir)
        
        config = MockConfig()
        
        run_save_results(sample_metrics_data, config)
        
        # Verify CSV exists
        csv_path = temp_output_dir / "network_metrics.csv"
        assert csv_path.exists()
        
        # Verify matrices exist
        for item in sample_metrics_data:
            matrix_path = temp_output_dir / "matrices" / f"{item['subject_id']}_connectivity.npy"
            assert matrix_path.exists()
    
    def test_handles_nan_values(self, temp_output_dir):
        """Test that NaN values in metrics are handled correctly in CSV."""
        data_with_nan = [
            {
                "subject_id": "sub-nan",
                "matrix": np.eye(3),
                "modularity_q": float('nan'),
                "global_efficiency": 0.5,
                "local_efficiency": float('inf'),
                "fd_mean": 0.1
            }
        ]
        
        csv_path = temp_output_dir / "test_nan.csv"
        save_metrics_to_csv(data_with_nan, csv_path)
        
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            row = next(reader)
        
        # NaN and Inf should be saved as empty strings or handled gracefully
        # The implementation converts them to empty strings
        assert row['modularity_q'] == ""
        assert row['local_efficiency'] == ""
        assert row['global_efficiency'] == "0.5"
        assert row['fd_mean'] == "0.1"
        assert row['subject_id'] == "sub-nan"