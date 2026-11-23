"""
Unit tests for MSE Validator module.

Tests:
- load_quantized_activations
- load_original_activations
- compute_mse
- compute_layerwise_mse
- analyze_variance_sensitivity
"""
import os
import sys
import json
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.mse_validator import (
    load_quantized_activations,
    load_original_activations,
    compute_mse,
    compute_layerwise_mse,
    analyze_variance_sensitivity,
    run_mse_validation
)
from config import Config


class TestComputeMSE:
    """Tests for compute_mse function."""

    def test_identical_arrays(self):
        """MSE should be 0 for identical arrays."""
        arr = np.array([1.0, 2.0, 3.0])
        mse = compute_mse(arr, arr)
        assert mse == 0.0

    def test_different_arrays(self):
        """MSE should be positive for different arrays."""
        original = np.array([1.0, 2.0, 3.0])
        quantized = np.array([1.1, 2.1, 3.1])
        mse = compute_mse(original, quantized)
        assert mse > 0.0
        # Expected: mean((0.1)^2, (0.1)^2, (0.1)^2) = 0.01
        assert np.isclose(mse, 0.01)

    def test_shape_mismatch(self):
        """Should raise ValueError for mismatched shapes."""
        arr1 = np.array([1.0, 2.0])
        arr2 = np.array([1.0, 2.0, 3.0])
        with pytest.raises(ValueError):
            compute_mse(arr1, arr2)

    def test_multidimensional(self):
        """Should work with multi-dimensional arrays."""
        original = np.random.randn(10, 20)
        quantized = original + np.random.randn(10, 20) * 0.1
        mse = compute_mse(original, quantized)
        assert mse > 0.0


class TestComputeLayerwiseMSE:
    """Tests for compute_layerwise_mse function."""

    def test_single_layer(self):
        """Test with single layer data."""
        data = {
            'activations': [
                {
                    'layer_name': 'layer1',
                    'original': [1.0, 2.0, 3.0],
                    'quantized': [1.1, 2.1, 3.1]
                }
            ]
        }
        result = compute_layerwise_mse(data)
        
        assert 'layer1' in result
        assert 'mean_mse' in result['layer1']
        assert result['layer1']['count'] == 1
        assert np.isclose(result['layer1']['mean_mse'], 0.01)

    def test_multiple_layers(self):
        """Test with multiple layers."""
        data = {
            'activations': [
                {'layer_name': 'layer1', 'original': [1.0, 2.0], 'quantized': [1.1, 2.1]},
                {'layer_name': 'layer1', 'original': [3.0, 4.0], 'quantized': [3.1, 4.1]},
                {'layer_name': 'layer2', 'original': [5.0, 6.0], 'quantized': [5.2, 6.2]}
            ]
        }
        result = compute_layerwise_mse(data)
        
        assert len(result) == 2
        assert result['layer1']['count'] == 2
        assert result['layer2']['count'] == 1

    def test_missing_keys(self):
        """Should skip entries with missing keys."""
        data = {
            'activations': [
                {'layer_name': 'layer1', 'original': [1.0], 'quantized': [1.1]},
                {'layer_name': 'layer1'},  # Missing original/quantized
                {'original': [1.0], 'quantized': [1.1]}  # Missing layer_name
            ]
        }
        result = compute_layerwise_mse(data)
        
        assert 'layer1' in result
        assert result['layer1']['count'] == 1  # Only first entry counted


class TestLoadQuantizedActivations:
    """Tests for load_quantized_activations function."""

    def test_load_valid_file(self):
        """Should load valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'activations': [{'layer_name': 'test', 'original': [1], 'quantized': [1]}]}, f)
            temp_path = Path(f.name)
        
        try:
            result = load_quantized_activations(temp_path)
            assert 'activations' in result
            assert len(result['activations']) == 1
        finally:
            temp_path.unlink()

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_quantized_activations(Path('/nonexistent/file.json'))

    def test_empty_file(self):
        """Should raise ValueError for empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{}')
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError):
                load_quantized_activations(temp_path)
        finally:
            temp_path.unlink()

    def test_missing_activations_key(self):
        """Should raise ValueError if 'activations' key is missing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'data': []}, f)
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(ValueError):
                load_quantized_activations(temp_path)
        finally:
            temp_path.unlink()


class TestAnalyzeVarianceSensitivity:
    """Tests for analyze_variance_sensitivity function."""

    def test_empty_layerwise_mse(self):
        """Should handle empty layerwise MSE."""
        result = analyze_variance_sensitivity({})
        assert result['total_layers'] == 0
        assert result['hypothesis_validation'] == 'insufficient_data'

    def test_with_clustering_report(self):
        """Should compute correlation when clustering report is provided."""
        layerwise_mse = {
            'layer1': {'mean_mse': 0.01},
            'layer2': {'mean_mse': 0.02},
            'layer3': {'mean_mse': 0.03}
        }
        clustering_report = {
            'variances': {
                'layer1': 1.0,
                'layer2': 2.0,
                'layer3': 3.0
            }
        }
        
        result = analyze_variance_sensitivity(layerwise_mse, clustering_report)
        
        assert result['total_layers'] == 3
        assert result['variance_sensitivity_correlation'] is not None
        assert 'pearson_r' in result['variance_sensitivity_correlation']
        assert 'p_value' in result['variance_sensitivity_correlation']

    def test_without_clustering_report(self):
        """Should work without clustering report (no correlation)."""
        layerwise_mse = {
            'layer1': {'mean_mse': 0.01},
            'layer2': {'mean_mse': 0.02}
        }
        
        result = analyze_variance_sensitivity(layerwise_mse)
        
        assert result['total_layers'] == 2
        assert result['variance_sensitivity_correlation'] is None
        assert result['hypothesis_validation'] == 'pending'


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_run_mse_validation_with_mock_data(self, tmp_path):
        """Test running full validation with mock data files."""
        # Create mock data files
        quantized_data = {
            'activations': [
                {
                    'layer_name': 'block1',
                    'original': [1.0, 2.0, 3.0, 4.0],
                    'quantized': [1.1, 2.1, 3.1, 4.1]
                },
                {
                    'layer_name': 'block2',
                    'original': [5.0, 6.0, 7.0, 8.0],
                    'quantized': [5.2, 6.2, 7.2, 8.2]
                }
            ]
        }
        
        quantized_file = tmp_path / 'quantized_activations.json'
        with open(quantized_file, 'w') as f:
            json.dump(quantized_data, f)
        
        # Create a mock clustering report
        clustering_data = {
            'variances': {
                'block1': 1.5,
                'block2': 2.5
            }
        }
        clustering_file = tmp_path / 'clustering_report.json'
        with open(clustering_file, 'w') as f:
            json.dump(clustering_data, f)
        
        # Create a mock config
        config = Config()
        config.data_processed = tmp_path
        
        # Run validation
        results = run_mse_validation(config)
        
        assert results['status'] == 'completed'
        assert results['summary']['total_layers_analyzed'] == 2
        assert 'layerwise_mse' in results
        assert 'block1' in results['layerwise_mse']
        assert 'block2' in results['layerwise_mse']