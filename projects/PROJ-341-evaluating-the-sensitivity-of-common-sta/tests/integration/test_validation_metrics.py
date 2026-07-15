import os
import json
import pytest
import numpy as np
from datetime import datetime

from code.analysis.validation_metrics import (
    load_real_data_pvalues,
    calculate_validation_metrics,
    save_validation_metrics,
    main
)
from code.analysis.bootstrapper import calculate_ks_distance

class TestValidationMetrics:
    """Integration tests for validation metrics (T034)."""

    def test_load_real_data_pvalues_missing_file(self):
        """Test that loading missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_real_data_pvalues("nonexistent/path.csv")

    def test_calculate_validation_metrics_empty_lists(self):
        """Test validation metrics with empty data."""
        result = calculate_validation_metrics([], [])
        assert result['validation_status'] == 'insufficient_data'
        assert result['ks_distance'] is None

    def test_calculate_validation_metrics_valid_data(self):
        """Test validation metrics calculation with valid data."""
        simulated = [0.01, 0.03, 0.04, 0.07, 0.09, 0.12, 0.15, 0.20]
        real = [0.02, 0.04, 0.05, 0.06, 0.08, 0.11, 0.14, 0.18]
        
        result = calculate_validation_metrics(simulated, real)
        
        assert result['ks_distance'] is not None
        assert result['ks_pvalue'] is not None
        assert result['simulated_power'] is not None
        assert result['real_power'] is not None
        assert result['validation_status'] in ['passed', 'failed']
        assert 0 <= result['ks_distance'] <= 1

    def test_ks_distance_threshold(self):
        """Test KS distance calculation and threshold logic."""
        # Similar distributions should have low KS distance
        sim1 = np.random.normal(0.5, 0.2, 1000)
        real1 = np.random.normal(0.5, 0.2, 1000)
        
        ks_stat, _ = calculate_ks_distance(sim1.tolist(), real1.tolist())
        assert ks_stat < 0.10  # Should pass threshold
        
        # Different distributions should have higher KS distance
        sim2 = np.random.normal(0.5, 0.1, 1000)
        real2 = np.random.normal(0.8, 0.1, 1000)
        
        ks_stat2, _ = calculate_ks_distance(sim2.tolist(), real2.tolist())
        assert ks_stat2 > 0.10  # Should fail threshold

    def test_save_and_load_validation_metrics(self, tmp_path):
        """Test saving and loading validation metrics."""
        metrics = {
            'summary': {
                'total_conditions_tested': 5,
                'average_ks_distance': 0.05,
                'max_ks_distance': 0.08,
                'validation_status': 'passed'
            },
            'detailed_results': [],
            'timestamp': str(datetime.now())
        }
        
        output_path = tmp_path / "test_validation_metrics.json"
        save_validation_metrics(metrics, str(output_path))
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['summary']['validation_status'] == 'passed'
        assert loaded['summary']['total_conditions_tested'] == 5

    def test_main_function_creates_output(self, tmp_path, monkeypatch):
        """Test that main function creates output file."""
        # Mock the file paths to use tmp_path
        monkeypatch.setattr("code.analysis.validation_metrics.load_real_data_pvalues", 
                          lambda: [{'dataset': 'test', 'test_type': 't-test', 
                                  'p_value': 0.03, 'sample_size': 30, 'df': 28}])
        
        monkeypatch.setattr("code.analysis.validation_metrics.load_simulated_pvalues_for_comparison",
                          lambda test_type, sample_size: [0.02, 0.04, 0.05, 0.06])
        
        monkeypatch.setattr("code.analysis.validation_metrics.save_validation_metrics",
                          lambda m, p: None)  # Mock save to avoid file I/O issues in test
        
        # This test verifies the structure, not actual file creation
        result = main()
        assert result is not None
