import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np

# Import the module under test
from validation_gate import (
    validate_correlation_against_threshold,
    compute_p_value_and_ci,
    load_correlation_data,
    generate_validation_report,
    run_validation_gate_pipeline,
    FR_009_CORRELATION_THRESHOLD
)


class TestValidateCorrelationAgainstThreshold:
    """Tests for the validation threshold logic."""

    def test_correlation_above_threshold_passes(self):
        """Correlation >= threshold should return True."""
        assert validate_correlation_against_threshold(0.6, 0.6) is True
        assert validate_correlation_against_threshold(0.7, 0.6) is True
        assert validate_correlation_against_threshold(0.99, 0.6) is True

    def test_correlation_below_threshold_fails(self):
        """Correlation < threshold should return False."""
        assert validate_correlation_against_threshold(0.59, 0.6) is False
        assert validate_correlation_against_threshold(0.5, 0.6) is False
        assert validate_correlation_against_threshold(0.0, 0.6) is False

    def test_negative_correlation_fails(self):
        """Negative correlation should fail against positive threshold."""
        assert validate_correlation_against_threshold(-0.5, 0.6) is False

    def test_custom_threshold(self):
        """Custom threshold should be respected."""
        assert validate_correlation_against_threshold(0.8, 0.75) is True
        assert validate_correlation_against_threshold(0.7, 0.75) is False


class TestComputePValueAndCI:
    """Tests for statistical computation functions."""

    def test_perfect_positive_correlation(self):
        """Perfect positive correlation should yield p=0."""
        result = compute_p_value_and_ci(1.0, 100)
        assert result['p_value'] == 0.0
        assert result['ci_lower'] is None  # Fisher transform undefined at 1.0
        assert result['ci_upper'] is None

    def test_perfect_negative_correlation(self):
        """Perfect negative correlation should yield p=0."""
        result = compute_p_value_and_ci(-1.0, 100)
        assert result['p_value'] == 0.0

    def test_realistic_correlation(self):
        """Realistic correlation should produce valid statistics."""
        result = compute_p_value_and_ci(0.6, 50)
        assert 0 < result['p_value'] < 1
        assert result['ci_lower'] is not None
        assert result['ci_upper'] is not None
        assert result['ci_lower'] < 0.6 < result['ci_upper']

    def test_small_sample_size(self):
        """Small sample size should return error."""
        result = compute_p_value_and_ci(0.5, 2)
        assert 'error' in result
        assert result['p_value'] == 1.0

    def test_confidence_interval_width(self):
        """Larger sample size should produce narrower CI."""
        ci_small = compute_p_value_and_ci(0.5, 20)
        ci_large = compute_p_value_and_ci(0.5, 100)
        
        width_small = ci_small['ci_upper'] - ci_small['ci_lower']
        width_large = ci_large['ci_upper'] - ci_large['ci_lower']
        
        assert width_large < width_small


class TestLoadCorrelationData:
    """Tests for data loading functions."""

    def test_load_valid_json(self):
        """Should load valid JSON correlation data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({'correlation': 0.65, 'sample_size': 50}, f)
            temp_path = f.name

        try:
            data = load_correlation_data(temp_path)
            assert data['correlation'] == 0.65
            assert data['sample_size'] == 50
        finally:
            os.unlink(temp_path)

    def test_file_not_found(self):
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_correlation_data('nonexistent_file.json')

    def test_invalid_json(self):
        """Should raise JSONDecodeError for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('not valid json')
            temp_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError):
                load_correlation_data(temp_path)
        finally:
            os.unlink(temp_path)


class TestGenerateValidationReport:
    """Tests for report generation."""

    def test_pass_case(self):
        """Should generate PASS report for valid correlation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'report.md')
            data = {
                'correlation': 0.65,
                'sample_size': 50,
                'feature_name': 'authority_density',
                'metric_name': 'pearson_r'
            }
            
            result = generate_validation_report(data, 0.6, output_path)
            
            assert result['status'] == 'PASS'
            assert result['is_valid'] is True
            assert os.path.exists(output_path)
            
            # Verify report content
            with open(output_path, 'r') as f:
                content = f.read()
                assert 'Validation Status: **PASS**' in content
                assert 'FR-009' in content
                assert '0.65' in content

    def test_fail_case(self):
        """Should generate FAIL report for invalid correlation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'report.md')
            data = {
                'correlation': 0.45,
                'sample_size': 50,
                'feature_name': 'authority_density',
                'metric_name': 'pearson_r'
            }
            
            result = generate_validation_report(data, 0.6, output_path)
            
            assert result['status'] == 'FAIL'
            assert result['is_valid'] is False
            
            with open(output_path, 'r') as f:
                content = f.read()
                assert 'Validation Status: **FAIL**' in content
                assert 'Recommended Actions' in content

    def test_default_threshold(self):
        """Should use default threshold if not specified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'report.md')
            data = {
                'correlation': FR_009_CORRELATION_THRESHOLD + 0.05,
                'sample_size': 50
            }
            
            result = generate_validation_report(data, output_path=output_path)
            assert result['is_valid'] is True


class TestRunValidationGatePipeline:
    """Integration tests for the full pipeline."""

    def test_full_pipeline_success(self):
        """Should complete successfully with valid data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            correlation_file = os.path.join(tmpdir, 'correlation.json')
            output_file = os.path.join(tmpdir, 'report.md')
            
            # Create valid correlation data
            with open(correlation_file, 'w') as f:
                json.dump({
                    'correlation': 0.7,
                    'sample_size': 60,
                    'feature_name': 'authority_density'
                }, f)
            
            result = run_validation_gate_pipeline(
                correlation_file=correlation_file,
                output_file=output_file
            )
            
            assert result['status'] == 'PASS'
            assert os.path.exists(output_file)

    def test_pipeline_missing_input(self):
        """Should fail gracefully when input is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, 'report.md')
            
            with pytest.raises(FileNotFoundError):
                run_validation_gate_pipeline(
                    correlation_file='nonexistent.json',
                    output_file=output_file
                )

    def test_pipeline_malformed_data(self):
        """Should fail when data is malformed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            correlation_file = os.path.join(tmpdir, 'correlation.json')
            output_file = os.path.join(tmpdir, 'report.md')
            
            # Create invalid data (missing correlation key)
            with open(correlation_file, 'w') as f:
                json.dump({'sample_size': 50}, f)
            
            with pytest.raises(ValueError):
                run_validation_gate_pipeline(
                    correlation_file=correlation_file,
                    output_file=output_file
                )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
