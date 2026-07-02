"""
Unit tests for 03_compute_sensitivity.py
"""
import json
import math
import tempfile
from pathlib import Path

import pytest

from code.utils.logging_config import setup_logging
from code._03_compute_sensitivity import (
    compute_observed_power,
    compute_mdes,
    process_extracted_params
)


@pytest.fixture(autouse=True)
def setup_logging_fixture():
    """Setup logging for tests."""
    setup_logging()


class TestComputeObservedPower:
    def test_valid_parameters(self):
        """Test power calculation with valid parameters."""
        # N=100, d=0.2 should yield power ~0.17-0.30 depending on exact calculation
        power = compute_observed_power(sample_size=100, effect_size=0.2)
        assert 0.0 <= power <= 1.0
        assert power > 0.0  # Should have some power with N=100

    def test_large_effect_size(self):
        """Test with large effect size - should have high power."""
        power = compute_observed_power(sample_size=100, effect_size=1.0)
        assert power > 0.8  # Large effect should yield high power

    def test_zero_sample_size(self):
        """Test with zero sample size - should return 0.0."""
        power = compute_observed_power(sample_size=0, effect_size=0.5)
        assert power == 0.0

    def test_negative_sample_size(self):
        """Test with negative sample size - should return 0.0."""
        power = compute_observed_power(sample_size=-10, effect_size=0.5)
        assert power == 0.0

    def test_negative_effect_size(self):
        """Test with negative effect size - should handle gracefully."""
        power = compute_observed_power(sample_size=100, effect_size=-0.5)
        assert 0.0 <= power <= 1.0

    def test_clamping(self):
        """Test that power is clamped to [0, 1]."""
        # Very large sample and effect should theoretically exceed 1 but get clamped
        power = compute_observed_power(sample_size=10000, effect_size=5.0)
        assert power <= 1.0
        assert power >= 0.0


class TestComputeMDES:
    def test_valid_parameters(self):
        """Test MDES calculation with valid parameters."""
        mdes = compute_mdes(sample_size=100)
        assert mdes > 0.0
        assert not math.isnan(mdes)

    def test_zero_sample_size(self):
        """Test with zero sample size - should return NaN."""
        mdes = compute_mdes(sample_size=0)
        assert math.isnan(mdes)

    def test_negative_sample_size(self):
        """Test with negative sample size - should return NaN."""
        mdes = compute_mdes(sample_size=-10)
        assert math.isnan(mdes)

    def test_larger_sample_reduces_mdes(self):
        """Test that larger sample size reduces MDES."""
        mdes_small = compute_mdes(sample_size=50)
        mdes_large = compute_mdes(sample_size=200)
        assert mdes_large < mdes_small


class TestProcessExtractedParams:
    def test_process_valid_data(self):
        """Test processing of valid extracted parameters."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = [
                {
                    'dataset_id': 'test_001',
                    'sample_size': 100,
                    'effect_size': 0.3,
                    'metric_type': "Cohen's d",
                    'status': 'success'
                },
                {
                    'dataset_id': 'test_002',
                    'sample_size': 50,
                    'effect_size': 0.5,
                    'metric_type': "Cohen's d",
                    'status': 'success'
                }
            ]
            json.dump(test_data, f)
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            results = process_extracted_params(input_path, output_path)
            
            assert len(results) == 2
            
            # Check first result
            assert results[0]['dataset_id'] == 'test_001'
            assert results[0]['status'] == 'success'
            assert results[0]['observed_power'] is not None
            assert results[0]['mdes'] is not None
            assert results[0]['threshold_met'] is not None
            
            # Check output file was created
            assert Path(output_path).exists()
            
            # Verify output file content
            with open(output_path, 'r') as f:
                saved_results = json.load(f)
            assert len(saved_results) == 2
            
        finally:
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

    def test_skip_failed_extraction(self):
        """Test that failed extractions are skipped."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = [
                {
                    'dataset_id': 'test_failed',
                    'sample_size': None,
                    'effect_size': None,
                    'metric_type': None,
                    'status': 'unparseable'
                }
            ]
            json.dump(test_data, f)
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            results = process_extracted_params(input_path, output_path)
            
            assert len(results) == 1
            assert results[0]['status'] == 'skipped'
            assert results[0]['observed_power'] is None
            
        finally:
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

    def test_missing_input_file(self):
        """Test that missing input file raises FileNotFoundError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        try:
            with pytest.raises(FileNotFoundError):
                process_extracted_params('/nonexistent/path.json', output_path)
        finally:
            Path(output_path).unlink(missing_ok=True)