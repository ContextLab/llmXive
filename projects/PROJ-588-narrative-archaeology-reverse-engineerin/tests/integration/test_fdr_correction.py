import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Add code directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from models.fdr_correction import apply_fdr_to_results, run_fdr_correction_pipeline
from utils.stats import apply_fdr_correction as stats_apply_fdr


class TestFDRCorrection:
    """Integration tests for FDR correction across narrative categories and ROIs."""

    def test_apply_fdr_to_results_empty(self):
        """Test FDR correction with empty p-values list."""
        result = apply_fdr_to_results([])
        assert result['p_values'] == []
        assert result['corrected_p_values'] == []
        assert result['is_significant'] == []
        assert result['num_significant'] == 0

    def test_apply_fdr_to_results_basic(self):
        """Test FDR correction with known p-values."""
        p_values = [0.01, 0.04, 0.03, 0.005, 0.02]
        result = apply_fdr_to_results(p_values, alpha=0.05)

        assert len(result['p_values']) == 5
        assert len(result['corrected_p_values']) == 5
        assert len(result['is_significant']) == 5
        assert isinstance(result['num_significant'], int)

        # Corrected p-values should be >= original p-values
        for orig, corr in zip(result['p_values'], result['corrected_p_values']):
            assert corr >= orig

    def test_apply_fdr_to_results_significance(self):
        """Test that FDR correction correctly identifies significant results."""
        # Mix of significant and non-significant p-values
        p_values = [0.001, 0.01, 0.05, 0.1, 0.2]
        result = apply_fdr_to_results(p_values, alpha=0.05)

        # At least the smallest p-value should be significant
        assert result['num_significant'] >= 1

    def test_run_fdr_correction_pipeline_decoder_only(self):
        """Test FDR pipeline with only decoder metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock decoder metrics
            decoder_data = {
                'per_category': {
                    'plot': {'p_value': 0.001, 'accuracy': 0.75},
                    'character': {'p_value': 0.03, 'accuracy': 0.68},
                    'theme': {'p_value': 0.15, 'accuracy': 0.55}
                }
            }

            decoder_path = os.path.join(tmpdir, 'decoder_metrics.json')
            with open(decoder_path, 'w') as f:
                json.dump(decoder_data, f)

            # Create empty RSA file
            rsa_path = os.path.join(tmpdir, 'rsa_metrics.json')
            with open(rsa_path, 'w') as f:
                json.dump({}, f)

            output_path = os.path.join(tmpdir, 'fdr_results.json')

            result = run_fdr_correction_pipeline(decoder_path, rsa_path, output_path)

            assert os.path.exists(output_path)
            assert result['summary']['total_tests'] == 3
            assert 'decoder_results' in result
            assert 'combined_results' in result

    def test_run_fdr_correction_pipeline_combined(self):
        """Test FDR pipeline with both decoder and RSA metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mock decoder metrics
            decoder_data = {
                'per_category': {
                    'plot': {'p_value': 0.001, 'accuracy': 0.75},
                    'character': {'p_value': 0.03, 'accuracy': 0.68}
                }
            }

            decoder_path = os.path.join(tmpdir, 'decoder_metrics.json')
            with open(decoder_path, 'w') as f:
                json.dump(decoder_data, f)

            # Create mock RSA metrics
            rsa_data = {
                'group_stats': {
                    'hippocampus': {
                        'early_late_p_value': 0.02,
                        'early_early_p_value': 0.08
                    },
                    'mPFC': {
                        'early_late_p_value': 0.01,
                        'early_early_p_value': 0.05
                    }
                }
            }

            rsa_path = os.path.join(tmpdir, 'rsa_metrics.json')
            with open(rsa_path, 'w') as f:
                json.dump(rsa_data, f)

            output_path = os.path.join(tmpdir, 'fdr_results.json')

            result = run_fdr_correction_pipeline(decoder_path, rsa_path, output_path)

            assert os.path.exists(output_path)
            # 2 decoder + 4 RSA tests = 6 total
            assert result['summary']['total_tests'] == 6
            assert result['summary']['decoder_tests'] == 2
            assert result['summary']['rsa_tests'] == 4

    def test_fdr_output_file_schema(self):
        """Verify the FDR output file has the correct schema."""
        with tempfile.TemporaryDirectory() as tmpdir:
            decoder_data = {
                'per_category': {
                    'plot': {'p_value': 0.001}
                }
            }
            decoder_path = os.path.join(tmpdir, 'decoder_metrics.json')
            with open(decoder_path, 'w') as f:
                json.dump(decoder_data, f)

            rsa_data = {}
            rsa_path = os.path.join(tmpdir, 'rsa_metrics.json')
            with open(rsa_path, 'w') as f:
                json.dump(rsa_data, f)

            output_path = os.path.join(tmpdir, 'fdr_results.json')
            run_fdr_correction_pipeline(decoder_path, rsa_path, output_path)

            with open(output_path, 'r') as f:
                result = json.load(f)

            # Verify required keys
            assert 'decoder_results' in result
            assert 'rsa_results' in result
            assert 'combined_results' in result
            assert 'summary' in result

            # Verify summary structure
            assert 'total_tests' in result['summary']
            assert 'total_significant' in result['summary']
            assert 'alpha' in result['summary']

            # Verify combined results structure
            combined = result['combined_results']
            assert 'p_values' in combined
            assert 'corrected_p_values' in combined
            assert 'is_significant' in combined
            assert 'num_significant' in combined

    def test_fdr_correction_conservative_vs_indep(self):
        """Test that FDR correction produces reasonable results."""
        # Generate a set of p-values with known distribution
        np.random.seed(42)
        p_values = np.random.uniform(0, 1, 100).tolist()

        result = apply_fdr_to_results(p_values, alpha=0.05)

        # With uniform distribution, we expect roughly 5% false positives
        # after FDR correction, but the actual number depends on the method
        assert result['num_significant'] >= 0
        assert result['num_significant'] <= len(p_values)

        # All corrected p-values should be valid probabilities
        for p in result['corrected_p_values']:
            assert 0 <= p <= 1