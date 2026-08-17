"""
Unit tests for T024: code/analysis/save_metrics.py
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.save_metrics import run_save_metrics, save_matrices_to_npy
from code.config import Config

class TestSaveMetrics:
    @pytest.fixture
    def mock_metrics_data(self):
        """Mock data for network metrics."""
        return [
            {
                "subject_id": "sub-01",
                "modularity": 0.55,
                "global_efficiency": 0.42,
                "local_efficiency": 0.38,
                "matrix": [[1.0, 0.2], [0.2, 1.0]]
            },
            {
                "subject_id": "sub-02",
                "modularity": 0.60,
                "global_efficiency": 0.45,
                "local_efficiency": 0.40,
                "matrix": [[1.0, 0.3], [0.3, 1.0]]
            }
        ]

    def test_save_matrices_to_npy_creates_file(self, tmp_path):
        """Test that save_matrices_to_npy creates a .npy file."""
        matrix = [[1.0, 0.2], [0.2, 1.0]]
        output_dir = tmp_path / "matrices"
        output_dir.mkdir()
        
        save_matrices_to_npy("sub-test", matrix, output_dir)
        
        expected_file = output_dir / "sub-test_connectivity.npy"
        assert expected_file.exists()
        
        loaded = np.load(expected_file)
        assert loaded.shape == (2, 2)
        assert np.allclose(loaded, matrix)

    def test_run_save_metrics_writes_csv(self, tmp_path, monkeypatch, mock_metrics_data):
        """Test that run_save_metrics writes the CSV file."""
        # Mock Config to use tmp_path
        original_init = Config.__init__
        
        def mock_config_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self._metrics_path = tmp_path / "metrics"
        
        monkeypatch.setattr(Config, "__init__", mock_config_init)
        
        # Mock run_analysis to return mock data
        def mock_run_analysis():
            return mock_metrics_data
        
        # Patch the import in save_metrics module
        import code.analysis.save_metrics as sm_module
        original_run_analysis = sm_module.run_analysis
        sm_module.run_analysis = mock_run_analysis
        
        try:
            run_save_metrics()
            
            csv_path = tmp_path / "metrics" / "network_metrics.csv"
            assert csv_path.exists()
            
            # Verify content
            with open(csv_path, 'r') as f:
                import csv
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]['subject_id'] == 'sub-01'
                assert rows[1]['subject_id'] == 'sub-02'
        finally:
            sm_module.run_analysis = original_run_analysis

    def test_run_save_metrics_writes_matrices(self, tmp_path, monkeypatch, mock_metrics_data):
        """Test that run_save_metrics writes .npy files."""
        # Mock Config
        original_init = Config.__init__
        def mock_config_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self._metrics_path = tmp_path / "metrics"
        
        monkeypatch.setattr(Config, "__init__", mock_config_init)
        
        def mock_run_analysis():
            return mock_metrics_data
        
        import code.analysis.save_metrics as sm_module
        original_run_analysis = sm_module.run_analysis
        sm_module.run_analysis = mock_run_analysis
        
        try:
            run_save_metrics()
            
            matrices_dir = tmp_path / "metrics" / "matrices"
            assert matrices_dir.exists()
            
            file1 = matrices_dir / "sub-01_connectivity.npy"
            file2 = matrices_dir / "sub-02_connectivity.npy"
            
            assert file1.exists()
            assert file2.exists()
            
            loaded1 = np.load(file1)
            loaded2 = np.load(file2)
            
            assert np.allclose(loaded1, mock_metrics_data[0]['matrix'])
            assert np.allclose(loaded2, mock_metrics_data[1]['matrix'])
        finally:
            sm_module.run_analysis = original_run_analysis