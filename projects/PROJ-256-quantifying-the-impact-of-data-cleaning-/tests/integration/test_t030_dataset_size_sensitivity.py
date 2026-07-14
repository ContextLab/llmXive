import os
import json
import pytest
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from t030_dataset_size_sensitivity import (
    bin_dataset_size,
    analyze_size_bin,
    run_sensitivity_analysis,
    calculate_p_value_shift
)

class TestDatasetSizeBinning:
    """Tests for dataset size binning logic."""

    def test_bin_dataset_size_small(self):
        """Test binning for small datasets (<50)."""
        assert bin_dataset_size(10) == 'small'
        assert bin_dataset_size(49) == 'small'

    def test_bin_dataset_size_medium(self):
        """Test binning for medium datasets (50-200)."""
        assert bin_dataset_size(50) == 'medium'
        assert bin_dataset_size(100) == 'medium'
        assert bin_dataset_size(200) == 'medium'

    def test_bin_dataset_size_large(self):
        """Test binning for large datasets (>200)."""
        assert bin_dataset_size(201) == 'large'
        assert bin_dataset_size(500) == 'large'
        assert bin_dataset_size(1000) == 'large'

class TestCalculatePValueShift:
    """Tests for p-value shift calculation."""

    def test_p_value_shift_positive(self):
        """Test positive shift calculation."""
        assert calculate_p_value_shift(0.1, 0.5) == 0.4

    def test_p_value_shift_negative(self):
        """Test negative shift (absolute value)."""
        assert calculate_p_value_shift(0.5, 0.1) == 0.4

    def test_p_value_shift_zero(self):
        """Test zero shift."""
        assert calculate_p_value_shift(0.05, 0.05) == 0.0

class TestAnalyzeSizeBin:
    """Tests for size bin analysis."""

    def test_empty_bin(self, caplog):
        """Test analysis of empty bin."""
        datasets = []
        baseline = {'datasets': []}
        cleaned = {'datasets': []}
        
        result = analyze_size_bin(datasets, 'small', baseline, cleaned)
        
        assert result['count'] == 0
        assert len(result['datasets']) == 0
        assert 'CONSTRAINT_VIOLATION' in caplog.text

    def test_bin_with_datasets(self):
        """Test analysis of bin with datasets."""
        datasets = [
            {'dataset_name': 'test1', 'dataset_size': 30, 'size_bin': 'small'}
        ]
        
        baseline = {
            'datasets': [{
                'dataset_name': 'test1',
                'dataset_size': 30,
                't_test': {'p_value': 0.1}
            }]
        }
        
        cleaned = {
            'datasets': [{
                'dataset_name': 'test1',
                'dataset_size': 30,
                'strategy': 'iqr',
                't_test': {'p_value': 0.5}
            }]
        }
        
        result = analyze_size_bin(datasets, 'small', baseline, cleaned)
        
        assert result['count'] == 1
        assert len(result['datasets']) == 1
        assert result['datasets'][0]['p_value_shift'] == 0.4

class TestRunSensitivityAnalysis:
    """Integration tests for the full sensitivity analysis."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    def test_run_sensitivity_analysis_creates_file(self, temp_dir):
        """Test that sensitivity analysis creates output file."""
        # Create mock metrics
        baseline_metrics = {
            'datasets': [
                {'dataset_name': 'small_ds', 'dataset_size': 30, 't_test': {'p_value': 0.1}},
                {'dataset_name': 'medium_ds', 'dataset_size': 100, 't_test': {'p_value': 0.05}},
                {'dataset_name': 'large_ds', 'dataset_size': 300, 't_test': {'p_value': 0.01}}
            ]
        }
        
        cleaned_metrics = {
            'datasets': [
                {'dataset_name': 'small_ds', 'dataset_size': 30, 'strategy': 'iqr', 't_test': {'p_value': 0.5}},
                {'dataset_name': 'medium_ds', 'dataset_size': 100, 'strategy': 'iqr', 't_test': {'p_value': 0.6}},
                {'dataset_name': 'large_ds', 'dataset_size': 300, 'strategy': 'iqr', 't_test': {'p_value': 0.2}}
            ]
        }
        
        output_path = os.path.join(temp_dir, 'sensitivity.json')
        
        result = run_sensitivity_analysis(
            baseline_metrics, 
            cleaned_metrics, 
            output_path
        )
        
        # Verify file was created
        assert os.path.exists(output_path)
        
        # Verify content
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert 'bins' in saved_data
        assert 'small' in saved_data['bins']
        assert 'medium' in saved_data['bins']
        assert 'large' in saved_data['bins']
        assert saved_data['summary']['total_datasets'] == 3