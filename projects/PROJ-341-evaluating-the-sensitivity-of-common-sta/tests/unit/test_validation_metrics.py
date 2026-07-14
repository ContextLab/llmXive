"""
Unit tests for validation metrics calculation.
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import numpy as np

from code.analysis.validation_metrics import (
    load_real_data_pvalues,
    load_simulated_pvalues_for_comparison,
    calculate_real_data_power,
    calculate_validation_metrics,
    save_validation_metrics
)


class TestLoadRealDataPvalues:
    def test_load_empty_file(self, tmp_path):
        """Test loading an empty CSV file."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text("sample_size,effect_size,test_type,p_value,hypothesis\n")
        
        result = load_real_data_pvalues(str(csv_path))
        assert result == []
    
    def test_load_valid_data(self, tmp_path):
        """Test loading valid p-value data."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(
            "sample_size,effect_size,test_type,p_value,hypothesis\n"
            "30,0.5,t-test,0.03,H1\n"
            "30,0.5,t-test,0.07,H1\n"
        )
        
        result = load_real_data_pvalues(str(csv_path))
        assert len(result) == 2
        assert result[0]['p_value'] == 0.03
        assert result[1]['test_type'] == 't-test'
        assert result[0]['sample_size'] == 30


class TestLoadSimulatedPvalues:
    def test_filter_by_test_type(self, tmp_path):
        """Test filtering simulated p-values by test type."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(
            "sample_size,effect_size,test_type,p_value,hypothesis\n"
            "30,0.5,t-test,0.03,H1\n"
            "30,0.5,anova,0.04,H1\n"
        )
        
        result = load_simulated_pvalues_for_comparison(
            str(csv_path),
            test_type='t-test'
        )
        assert len(result) == 1
        assert result[0] == 0.03
    
    def test_filter_by_hypothesis(self, tmp_path):
        """Test filtering by hypothesis state."""
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(
            "sample_size,effect_size,test_type,p_value,hypothesis\n"
            "30,0.5,t-test,0.03,H1\n"
            "30,0.5,t-test,0.95,H0\n"
        )
        
        result = load_simulated_pvalues_for_comparison(
            str(csv_path),
            hypothesis='H1'
        )
        assert len(result) == 1
        assert result[0] == 0.03


class TestCalculateRealDataPower:
    def test_power_calculation(self):
        """Test power calculation with known values."""
        p_values = [0.01, 0.03, 0.04, 0.06, 0.95]
        alpha = 0.05
        
        result = calculate_real_data_power(p_values, alpha)
        
        # 3 out of 5 should be rejected (p < 0.05)
        assert result['power_estimate'] == 0.6
        assert result['n'] == 5
        assert result['ci_lower'] is not None
        assert result['ci_upper'] is not None
    
    def test_empty_pvalues(self):
        """Test with empty p-value list."""
        result = calculate_real_data_power([], alpha=0.05)
        assert result['power_estimate'] is None
        assert result['n'] == 0


class TestCalculateValidationMetrics:
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=MagicMock)
    def test_metrics_calculation_with_data(self, mock_open, mock_exists, tmp_path):
        """Test full metrics calculation with mock data."""
        # Mock file existence
        mock_exists.side_effect = lambda x: x.endswith(('.csv', '.json'))
        
        # Mock CSV content for p_values_raw.csv
        csv_content = [
            ['sample_size', 'effect_size', 'test_type', 'p_value', 'hypothesis'],
            ['30', '0.5', 't-test', '0.03', 'H1'],
            ['30', '0.5', 't-test', '0.02', 'H1'],
            ['30', '0.5', 't-test', '0.04', 'H1'],
            ['30', '0.5', 't-test', '0.06', 'H0'],
            ['30', '0.5', 't-test', '0.95', 'H0'],
        ]
        
        # Mock real data p-values
        real_csv_content = [
            ['sample_size', 'effect_size', 'test_type', 'p_value', 'hypothesis'],
            ['30', '0.5', 't-test', '0.03', 'H1'],
            ['30', '0.5', 't-test', '0.04', 'H1'],
        ]
        
        # Mock real power data
        real_power_content = {
            't-test': {'power_estimate': 0.65}
        }
        
        # Setup mock file reads
        def mock_file_read(*args, **kwargs):
            file_path = args[0] if args else kwargs.get('file', '')
            if 'p_values_raw.csv' in file_path:
                return mock_open.return_value.__enter__.return_value
            elif 'real_data_pvalues.csv' in file_path:
                return mock_open.return_value.__enter__.return_value
            elif 'real_data_power.json' in file_path:
                json_mock = MagicMock()
                json_mock.__enter__.return_value.read.return_value = json.dumps(real_power_content)
                return json_mock
            return mock_open.return_value.__enter__.return_value
        
        mock_open.side_effect = mock_file_read
        
        # Mock CSV reader
        with patch('csv.DictReader') as mock_reader:
            mock_reader.side_effect = [
                iter(csv_content[1:]),  # Simulated p-values
                iter(real_csv_content[1:]),  # Real p-values
            ]
            
            metrics = calculate_validation_metrics(
                simulated_pvalues_path="dummy.csv",
                real_pvalues_path="dummy.csv",
                real_power_path="dummy.json"
            )
            
            assert 'ks_distances' in metrics
            assert 'power_comparisons' in metrics
            assert 'overall_status' in metrics


class TestSaveValidationMetrics:
    def test_save_metrics(self, tmp_path):
        """Test saving metrics to JSON file."""
        metrics = {
            'overall_status': 'validation_passed',
            'ks_distances': {'t-test': {'H0': {'status': 'pass'}}},
            'details': {'total_real_tests': 10}
        }
        
        output_path = tmp_path / "metrics.json"
        result = save_validation_metrics(metrics, str(output_path))
        
        assert result is True
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            saved = json.load(f)
        
        assert saved['overall_status'] == 'validation_passed'
        assert saved['ks_distances']['t-test']['H0']['status'] == 'pass'