"""
Unit tests for the analysis module (T023).
Tests MSE calculation logic and aggregation.
"""
import pytest
import json
import tempfile
from pathlib import Path
import numpy as np
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from src.analysis import (
    calculate_mse_single,
    compute_mse_metrics,
    load_inference_results
)

class TestMSECalculation:
    """Test MSE calculation for single signals."""

    def test_calculate_mse_single_basic(self):
        """Test basic MSE calculation."""
        injected = {
            'chirp_mass': 30.0,
            'spin': 0.5,
            'distance': 500.0
        }
        recovered = {
            'chirp_mass': 30.1,
            'spin': 0.48,
            'distance': 505.0
        }
        
        mse = calculate_mse_single(injected, recovered)
        
        # Check chirp mass MSE: (30.0 - 30.1)^2 = 0.01
        assert abs(mse['chirp_mass'] - 0.01) < 1e-6
        # Check spin MSE: (0.5 - 0.48)^2 = 0.0004
        assert abs(mse['spin'] - 0.0004) < 1e-6
        # Check distance MSE: (500.0 - 505.0)^2 = 25.0
        assert abs(mse['distance'] - 25.0) < 1e-6

    def test_calculate_mse_single_perfect_recovery(self):
        """Test MSE calculation with perfect recovery (should be 0)."""
        injected = {
            'chirp_mass': 25.0,
            'spin': 0.3,
            'distance': 300.0
        }
        recovered = {
            'chirp_mass': 25.0,
            'spin': 0.3,
            'distance': 300.0
        }
        
        mse = calculate_mse_single(injected, recovered)
        
        assert mse['chirp_mass'] == 0.0
        assert mse['spin'] == 0.0
        assert mse['distance'] == 0.0

    def test_calculate_mse_single_missing_params(self):
        """Test MSE calculation with missing parameters."""
        injected = {
            'chirp_mass': 30.0,
            'spin': 0.5
        }
        recovered = {
            'chirp_mass': 30.1,
            'distance': 500.0
        }
        
        mse = calculate_mse_single(injected, recovered)
        
        # chirp_mass should be calculated
        assert not np.isnan(mse['chirp_mass'])
        # spin is missing in recovered -> nan
        assert np.isnan(mse['spin'])
        # distance is missing in injected -> nan
        assert np.isnan(mse['distance'])

class TestMSEAggregation:
    """Test MSE aggregation across multiple signals."""

    def test_compute_mse_metrics_basic(self):
        """Test MSE metrics computation with sample data."""
        # Create sample inference results
        sample_results = [
            {
                'bit_depth': 8,
                'snr_bin': '8-14',
                'snr': 10.0,
                'converged': True,
                'injected_params': {
                    'chirp_mass': 30.0,
                    'spin': 0.5,
                    'distance': 500.0,
                    'snr': 10.0
                },
                'posterior_means': {
                    'chirp_mass': 30.2,
                    'spin': 0.48,
                    'distance': 510.0
                }
            },
            {
                'bit_depth': 16,
                'snr_bin': '30-50',
                'snr': 40.0,
                'converged': True,
                'injected_params': {
                    'chirp_mass': 25.0,
                    'spin': 0.3,
                    'distance': 200.0,
                    'snr': 40.0
                },
                'posterior_means': {
                    'chirp_mass': 25.05,
                    'spin': 0.29,
                    'distance': 202.0
                }
            },
            {
                'bit_depth': 8,
                'snr_bin': '8-14',
                'snr': 9.0,
                'converged': False,  # Non-converged, should be skipped
                'injected_params': {
                    'chirp_mass': 35.0,
                    'spin': 0.7,
                    'distance': 800.0,
                    'snr': 9.0
                },
                'posterior_means': {
                    'chirp_mass': 40.0,
                    'spin': 0.1,
                    'distance': 900.0
                }
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_file = tmpdir_path / 'inference_test.json'
            output_file = tmpdir_path / 'mse_test.json'
            
            # Write sample results
            with open(input_file, 'w') as f:
                json.dump(sample_results, f)
            
            # Compute metrics
            metrics = compute_mse_metrics(input_file, output_file)
            
            # Check output file exists
            assert output_file.exists()
            
            # Check global metrics
            assert metrics['global']['total_converged'] == 2  # One was non-converged
            
            # Check aggregation by bit depth
            assert '8' in metrics['aggregated_by_bit_depth']
            assert '16' in metrics['aggregated_by_bit_depth']
            assert metrics['aggregated_by_bit_depth']['8']['count'] == 1
            assert metrics['aggregated_by_bit_depth']['16']['count'] == 1
            
            # Check aggregation by SNR bin
            assert '8-14' in metrics['aggregated_by_snr_bin']
            assert '30-50' in metrics['aggregated_by_snr_bin']
            assert metrics['aggregated_by_snr_bin']['8-14']['count'] == 1
            assert metrics['aggregated_by_snr_bin']['30-50']['count'] == 1

    def test_compute_mse_metrics_empty_results(self):
        """Test MSE metrics computation with empty results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_file = tmpdir_path / 'inference_empty.json'
            output_file = tmpdir_path / 'mse_empty.json'
            
            # Write empty results
            with open(input_file, 'w') as f:
                json.dump([], f)
            
            # Compute metrics
            metrics = compute_mse_metrics(input_file, output_file)
            
            # Check output file exists
            assert output_file.exists()
            
            # Check global metrics
            assert metrics['global']['total_converged'] == 0
            assert np.isnan(metrics['global']['chirp_mass_mse'])

    def test_compute_mse_metrics_all_non_converged(self):
        """Test MSE metrics computation when all results are non-converged."""
        sample_results = [
            {
                'bit_depth': 8,
                'snr_bin': '8-14',
                'snr': 10.0,
                'converged': False,
                'injected_params': {
                    'chirp_mass': 30.0,
                    'spin': 0.5,
                    'distance': 500.0,
                    'snr': 10.0
                },
                'posterior_means': {
                    'chirp_mass': 35.0,
                    'spin': 0.1,
                    'distance': 600.0
                }
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_file = tmpdir_path / 'inference_nonconv.json'
            output_file = tmpdir_path / 'mse_nonconv.json'
            
            # Write sample results
            with open(input_file, 'w') as f:
                json.dump(sample_results, f)
            
            # Compute metrics
            metrics = compute_mse_metrics(input_file, output_file)
            
            # Check global metrics
            assert metrics['global']['total_converged'] == 0

class TestLoadInferenceResults:
    """Test loading of inference results."""

    def test_load_inference_results_list_format(self):
        """Test loading results in list format."""
        sample_data = [
            {'key': 'value1'},
            {'key': 'value2'}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_file = tmpdir_path / 'test.json'
            
            with open(input_file, 'w') as f:
                json.dump(sample_data, f)
            
            results = load_inference_results(input_file)
            
            assert isinstance(results, list)
            assert len(results) == 2
            assert results[0]['key'] == 'value1'

    def test_load_inference_results_dict_format(self):
        """Test loading results in dict format with 'results' key."""
        sample_data = {
            'results': [
                {'key': 'value1'},
                {'key': 'value2'}
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            input_file = tmpdir_path / 'test.json'
            
            with open(input_file, 'w') as f:
                json.dump(sample_data, f)
            
            results = load_inference_results(input_file)
            
            assert isinstance(results, list)
            assert len(results) == 2

    def test_load_inference_results_file_not_found(self):
        """Test loading results from non-existent file."""
        with pytest.raises(FileNotFoundError):
            load_inference_results(Path('/nonexistent/file.json'))