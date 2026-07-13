"""
Integration tests for T030: Dataset size sensitivity analysis.
"""
import os
import json
import pytest
import tempfile
from datetime import datetime

# Add code directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from t030_dataset_size_sensitivity import (
    bin_dataset_size,
    calculate_p_value_shift,
    analyze_size_bin,
    run_sensitivity_analysis
)

class TestDatasetSizeBinning:
    """Tests for dataset size binning logic."""
    
    def test_bin_dataset_size_small(self):
        """Test binning for small datasets (n < 50)."""
        assert bin_dataset_size(10) == 'small'
        assert bin_dataset_size(49) == 'small'
        assert bin_dataset_size(0) == 'small'
    
    def test_bin_dataset_size_medium(self):
        """Test binning for medium datasets (50 <= n <= 200)."""
        assert bin_dataset_size(50) == 'medium'
        assert bin_dataset_size(100) == 'medium'
        assert bin_dataset_size(200) == 'medium'
    
    def test_bin_dataset_size_large(self):
        """Test binning for large datasets (n > 200)."""
        assert bin_dataset_size(201) == 'large'
        assert bin_dataset_size(500) == 'large'
        assert bin_dataset_size(1000) == 'large'

class TestPValueShiftCalculation:
    """Tests for p-value shift calculation."""
    
    def test_calculate_p_value_shift(self):
        """Test absolute p-value shift calculation."""
        assert calculate_p_value_shift(0.05, 0.03) == 0.02
        assert calculate_p_value_shift(0.1, 0.2) == 0.1
        assert calculate_p_value_shift(0.01, 0.01) == 0.0

class TestSizeBinAnalysis:
    """Tests for size bin analysis logic."""
    
    def test_empty_bin(self):
        """Test analysis of empty bin."""
        baseline_metrics = {'datasets': []}
        cleaned_metrics = {'datasets': []}
        
        result = analyze_size_bin('small', [], baseline_metrics, cleaned_metrics)
        
        assert result['bin'] == 'small'
        assert result['count'] == 0
        assert result['avg_p_value_shift'] is None
        assert 'warning' in result
        assert 'Empty bin' in result['warning']
    
    def test_single_dataset_bin(self):
        """Test analysis with single dataset."""
        baseline_metrics = {
            'datasets': [{
                'dataset_name': 'test_ds',
                'p_value': 0.05,
                'ci_width': 0.2,
                'effect_size': 0.5
            }]
        }
        cleaned_metrics = {
            'datasets': [{
                'dataset_name': 'test_ds',
                'p_value': 0.03,
                'ci_width': 0.15,
                'effect_size': 0.6
            }]
        }
        
        datasets = [{'dataset_name': 'test_ds', 'dataset_size': 100, 'bin': 'medium'}]
        
        result = analyze_size_bin('medium', datasets, baseline_metrics, cleaned_metrics)
        
        assert result['bin'] == 'medium'
        assert result['count'] == 1
        assert result['avg_p_value_shift'] == 0.02
        assert result['avg_ci_width_change'] == 0.05
        assert result['avg_effect_size_delta'] == 0.1

class TestSensitivityAnalysisIntegration:
    """Integration tests for full sensitivity analysis."""
    
    def test_run_sensitivity_analysis_with_mock_data(self):
        """Test full sensitivity analysis with mock data files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock baseline metrics
            baseline_data = {
                'datasets': [
                    {
                        'dataset_name': 'small_ds',
                        'dataset_size': 30,
                        'p_value': 0.05,
                        'ci_width': 0.2,
                        'effect_size': 0.5
                    },
                    {
                        'dataset_name': 'medium_ds',
                        'dataset_size': 100,
                        'p_value': 0.1,
                        'ci_width': 0.3,
                        'effect_size': 0.7
                    },
                    {
                        'dataset_name': 'large_ds',
                        'dataset_size': 500,
                        'p_value': 0.01,
                        'ci_width': 0.1,
                        'effect_size': 0.9
                    }
                ]
            }
            
            baseline_path = os.path.join(tmpdir, 'baseline_metrics.json')
            with open(baseline_path, 'w') as f:
                json.dump(baseline_data, f)
            
            # Create mock cleaned metrics
            cleaned_data = {
                'datasets': [
                    {
                        'dataset_name': 'small_ds',
                        'dataset_size': 30,
                        'p_value': 0.04,
                        'ci_width': 0.18,
                        'effect_size': 0.55
                    },
                    {
                        'dataset_name': 'medium_ds',
                        'dataset_size': 100,
                        'p_value': 0.08,
                        'ci_width': 0.25,
                        'effect_size': 0.75
                    },
                    {
                        'dataset_name': 'large_ds',
                        'dataset_size': 500,
                        'p_value': 0.02,
                        'ci_width': 0.12,
                        'effect_size': 0.85
                    }
                ]
            }
            
            cleaned_path = os.path.join(tmpdir, 'cleaned_metrics.json')
            with open(cleaned_path, 'w') as f:
                json.dump(cleaned_data, f)
            
            output_path = os.path.join(tmpdir, 'sensitivity_analysis.json')
            
            # Run sensitivity analysis
            results = run_sensitivity_analysis(baseline_path, cleaned_path, output_path)
            
            # Verify results
            assert results is not None
            assert 'bin_results' in results
            assert len(results['bin_results']) == 3
            
            # Check that output file was created
            assert os.path.exists(output_path)
            
            # Verify output content
            with open(output_path, 'r') as f:
                output_data = json.load(f)
            
            assert 'summary' in output_data
            assert output_data['summary']['total_datasets'] == 3
            
            # Verify bin counts
            bin_counts = output_data['summary']['bin_counts']
            assert bin_counts['small'] == 1
            assert bin_counts['medium'] == 1
            assert bin_counts['large'] == 1

    def test_empty_bins_handling(self):
        """Test handling of empty bins."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock data with only large datasets
            baseline_data = {
                'datasets': [
                    {
                        'dataset_name': 'large_ds',
                        'dataset_size': 500,
                        'p_value': 0.01,
                        'ci_width': 0.1,
                        'effect_size': 0.9
                    }
                ]
            }
            
            baseline_path = os.path.join(tmpdir, 'baseline_metrics.json')
            with open(baseline_path, 'w') as f:
                json.dump(baseline_data, f)
            
            cleaned_data = {
                'datasets': [
                    {
                        'dataset_name': 'large_ds',
                        'dataset_size': 500,
                        'p_value': 0.02,
                        'ci_width': 0.12,
                        'effect_size': 0.85
                    }
                ]
            }
            
            cleaned_path = os.path.join(tmpdir, 'cleaned_metrics.json')
            with open(cleaned_path, 'w') as f:
                json.dump(cleaned_data, f)
            
            output_path = os.path.join(tmpdir, 'sensitivity_analysis.json')
            
            # Run sensitivity analysis
            results = run_sensitivity_analysis(baseline_path, cleaned_path, output_path)
            
            # Verify results
            assert results is not None
            assert len(results['bin_results']) == 3
            
            # Check that small and medium bins are empty
            for bin_result in results['bin_results']:
                if bin_result['bin'] in ['small', 'medium']:
                    assert bin_result['count'] == 0
                    assert bin_result['avg_p_value_shift'] is None
                    assert 'warning' in bin_result
                    assert 'Empty bin' in bin_result['warning']