"""
Unit tests for validation_metrics.py (Task T034).
"""
import os
import json
import tempfile
import pytest
import numpy as np

# Mock the dependencies that might not be fully set up
import sys
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.analysis.validation_metrics import calculate_validation_metrics, save_validation_metrics


class TestCalculateValidationMetrics:
    """Tests for calculate_validation_metrics function."""
    
    def test_single_dataset_passed(self, tmp_path):
        """Test with a single dataset that passes validation."""
        power_data = {
            'dataset_id': 'test_dataset',
            'ks_distance': 0.05,
            'power_estimate': 0.85
        }
        
        power_file = tmp_path / "real_data_power.json"
        with open(power_file, 'w') as f:
            json.dump(power_data, f)
        
        with patch('code.analysis.validation_metrics.REAL_DATA_POWER_PATH', str(power_file)):
            metrics = calculate_validation_metrics(str(power_file))
            
        assert metrics['total_datasets'] == 1
        assert metrics['passed_validation_count'] == 1
        assert metrics['avg_ks_distance'] == 0.05
        assert len(metrics['details']) == 1
        assert metrics['details'][0]['passed_validation'] is True
        
    def test_multiple_datasets_mixed_results(self, tmp_path):
        """Test with multiple datasets, some passing and some failing."""
        power_data = [
            {'dataset_id': 'ds1', 'ks_distance': 0.05, 'power_estimate': 0.8},
            {'dataset_id': 'ds2', 'ks_distance': 0.15, 'power_estimate': 0.6},
            {'dataset_id': 'ds3', 'ks_distance': 0.08, 'power_estimate': 0.9}
        ]
        
        power_file = tmp_path / "real_data_power.json"
        with open(power_file, 'w') as f:
            json.dump(power_data, f)
            
        metrics = calculate_validation_metrics(str(power_file))
        
        assert metrics['total_datasets'] == 3
        assert metrics['passed_validation_count'] == 2  # ds1 and ds3
        assert abs(metrics['avg_ks_distance'] - (0.05 + 0.15 + 0.08) / 3) < 1e-6
        
    def test_empty_results(self, tmp_path):
        """Test with empty results list."""
        power_data = []
        
        power_file = tmp_path / "real_data_power.json"
        with open(power_file, 'w') as f:
            json.dump(power_data, f)
            
        metrics = calculate_validation_metrics(str(power_file))
        
        assert metrics['total_datasets'] == 0
        assert metrics['passed_validation_count'] == 0
        assert metrics['avg_ks_distance'] == 0.0
        
    def test_k_distance_threshold_boundary(self, tmp_path):
        """Test boundary condition where KS distance equals exactly 0.10."""
        power_data = {
            'dataset_id': 'boundary_test',
            'ks_distance': 0.10,
            'power_estimate': 0.75
        }
        
        power_file = tmp_path / "real_data_power.json"
        with open(power_file, 'w') as f:
            json.dump(power_data, f)
            
        metrics = calculate_validation_metrics(str(power_file))
        
        # 0.10 should pass (<= 0.10)
        assert metrics['passed_validation_count'] == 1
        assert metrics['details'][0]['passed_validation'] is True
        

class TestSaveValidationMetrics:
    """Tests for save_validation_metrics function."""
    
    def test_save_and_reload(self, tmp_path):
        """Test that metrics can be saved and reloaded correctly."""
        metrics = {
            'total_datasets': 2,
            'passed_validation_count': 1,
            'avg_ks_distance': 0.12,
            'details': [
                {'dataset_id': 'a', 'ks_distance': 0.1, 'passed_validation': True},
                {'dataset_id': 'b', 'ks_distance': 0.14, 'passed_validation': False}
            ]
        }
        
        output_file = tmp_path / "validation_metrics.json"
        save_validation_metrics(metrics, str(output_file))
        
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            loaded = json.load(f)
            
        assert loaded['total_datasets'] == metrics['total_datasets']
        assert loaded['passed_validation_count'] == metrics['passed_validation_count']
        assert abs(loaded['avg_ks_distance'] - metrics['avg_ks_distance']) < 1e-6
        
    def test_creates_directory(self, tmp_path):
        """Test that function creates output directory if it doesn't exist."""
        metrics = {'total_datasets': 1, 'passed_validation_count': 1, 'avg_ks_distance': 0.0}
        
        nested_path = tmp_path / "subdir" / "output.json"
        save_validation_metrics(metrics, str(nested_path))
        
        assert nested_path.exists()