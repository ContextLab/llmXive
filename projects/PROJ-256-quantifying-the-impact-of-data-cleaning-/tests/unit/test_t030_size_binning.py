"""
Unit tests for T030: Dataset Size Binning Sensitivity Analysis.
"""
import pytest
import json
import os
import tempfile
from code.t030_dataset_size_sensitivity import (
    bin_dataset_size,
    analyze_size_bin,
    run_sensitivity_analysis,
    load_baseline_metrics,
    load_cleaned_metrics
)

class TestBinDatasetSize:
    def test_bin_small(self):
        assert bin_dataset_size(10) == 'small'
        assert bin_dataset_size(49) == 'small'

    def test_bin_medium(self):
        assert bin_dataset_size(50) == 'medium'
        assert bin_dataset_size(200) == 'medium'
        assert bin_dataset_size(150) == 'medium'

    def test_bin_large(self):
        assert bin_dataset_size(201) == 'large'
        assert bin_dataset_size(1000) == 'large'

class TestAnalyzeSizeBin:
    def test_analyze_bin_empty(self):
        result = analyze_size_bin([], [], 'small')
        assert result['dataset_count'] == 0
        assert result['avg_p_shift'] is None

    def test_analyze_bin_with_data(self):
        baseline = [
            {'dataset_name': 'ds1', 'dataset_size': 30, 'p_value': 0.05, 'ci_width': 0.2},
            {'dataset_name': 'ds2', 'dataset_size': 100, 'p_value': 0.03, 'ci_width': 0.15}
        ]
        cleaned = [
            {'dataset_name': 'ds1', 'dataset_size': 30, 'p_value': 0.06, 'ci_width': 0.22},
            {'dataset_name': 'ds2', 'dataset_size': 100, 'p_value': 0.04, 'ci_width': 0.14}
        ]
        
        # Small bin
        small_result = analyze_size_bin(baseline, cleaned, 'small')
        assert small_result['dataset_count'] == 1
        assert small_result['datasets'][0]['dataset_id'] == 'ds1'
        assert abs(small_result['datasets'][0]['p_shift'] - 0.01) < 0.0001
        
        # Medium bin
        medium_result = analyze_size_bin(baseline, cleaned, 'medium')
        assert medium_result['dataset_count'] == 1
        assert medium_result['datasets'][0]['dataset_id'] == 'ds2'

class TestRunSensitivityAnalysis:
    def test_run_analysis(self):
        baseline = {
            'datasets': [
                {'dataset_name': 'small_ds', 'dataset_size': 20, 'p_value': 0.1, 'ci_width': 0.5},
                {'dataset_name': 'med_ds', 'dataset_size': 100, 'p_value': 0.2, 'ci_width': 0.3},
                {'dataset_name': 'large_ds', 'dataset_size': 500, 'p_value': 0.3, 'ci_width': 0.1}
            ]
        }
        cleaned = {
            'datasets': [
                {'dataset_name': 'small_ds', 'dataset_size': 20, 'p_value': 0.12, 'ci_width': 0.55},
                {'dataset_name': 'med_ds', 'dataset_size': 100, 'p_value': 0.18, 'ci_width': 0.32},
                {'dataset_name': 'large_ds', 'dataset_size': 500, 'p_value': 0.28, 'ci_width': 0.11}
            ]
        }
        
        result = run_sensitivity_analysis(baseline, cleaned)
        
        assert 'bins' in result
        assert 'summary' in result
        assert result['summary']['total_datasets_analyzed'] == 3
        assert result['bins']['small']['dataset_count'] == 1
        assert result['bins']['medium']['dataset_count'] == 1
        assert result['bins']['large']['dataset_count'] == 1

class TestLoadFunctions:
    def test_load_missing_file(self):
        assert load_baseline_metrics('nonexistent.json') is None
        assert load_cleaned_metrics('nonexistent.json') is None

    def test_load_valid_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'datasets': []}, f)
            temp_path = f.name
        
        try:
            result = load_baseline_metrics(temp_path)
            assert result == {'datasets': []}
        finally:
            os.unlink(temp_path)
