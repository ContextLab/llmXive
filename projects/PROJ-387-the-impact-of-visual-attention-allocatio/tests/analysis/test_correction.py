"""
Tests for Bonferroni correction functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.correction import apply_bonferroni_correction, save_correction_results


class TestBonferroniCorrection:
    """Test cases for Bonferroni correction logic."""

    def test_basic_correction(self):
        """Test basic Bonferroni correction with known values."""
        raw_results = [
            {"metric": "fixation_duration", "valence": "positive", "p_raw": 0.01},
            {"metric": "fixation_duration", "valence": "neutral", "p_raw": 0.05},
            {"metric": "fixation_duration", "valence": "negative", "p_raw": 0.10},
            {"metric": "saccade_amplitude", "valence": "positive", "p_raw": 0.03},
            {"metric": "saccade_amplitude", "valence": "neutral", "p_raw": 0.20},
            {"metric": "saccade_amplitude", "valence": "negative", "p_raw": 0.005},
            {"metric": "gaze_distribution", "valence": "positive", "p_raw": 0.08},
            {"metric": "gaze_distribution", "valence": "neutral", "p_raw": 0.15},
            {"metric": "gaze_distribution", "valence": "negative", "p_raw": 0.02},
        ]

        corrected = apply_bonferroni_correction(raw_results, n_tests=9)

        # Check that all corrected values are present and correct
        assert len(corrected) == 9
        assert corrected[0]['p_corrected'] == 0.09  # 0.01 * 9
        assert corrected[1]['p_corrected'] == 0.45  # 0.05 * 9
        assert corrected[2]['p_corrected'] == 0.90  # 0.10 * 9
        assert corrected[5]['p_corrected'] == 0.045  # 0.005 * 9

    def test_capping_at_one(self):
        """Test that corrected p-values are capped at 1.0."""
        raw_results = [
            {"metric": "test", "valence": "test", "p_raw": 0.20},
            {"metric": "test", "valence": "test", "p_raw": 0.50},
        ]

        corrected = apply_bonferroni_correction(raw_results, n_tests=9)

        assert corrected[0]['p_corrected'] == 1.0  # 0.20 * 9 = 1.8, capped to 1.0
        assert corrected[1]['p_corrected'] == 1.0  # 0.50 * 9 = 4.5, capped to 1.0

    def test_preserves_original_data(self):
        """Test that original data is preserved in corrected results."""
        raw_results = [
            {
                "metric": "fixation_duration",
                "valence": "positive",
                "p_raw": 0.01,
                "coef": 0.5,
                "extra_field": "test_value"
            }
        ]

        corrected = apply_bonferroni_correction(raw_results, n_tests=9)

        assert corrected[0]['metric'] == "fixation_duration"
        assert corrected[0]['valence'] == "positive"
        assert corrected[0]['p_raw'] == 0.01
        assert corrected[0]['coef'] == 0.5
        assert corrected[0]['extra_field'] == "test_value"
        assert corrected[0]['p_corrected'] == 0.09

    def test_save_correction_results(self):
        """Test saving correction results to JSON file."""
        corrected_results = [
            {
                "metric": "fixation_duration",
                "valence": "positive",
                "p_raw": 0.01,
                "p_corrected": 0.09
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_correction.json"
            save_correction_results(corrected_results, output_path)

            assert output_path.exists()

            with open(output_path, 'r') as f:
                data = json.load(f)

            assert data['correction_method'] == 'Bonferroni'
            assert data['n_tests'] == 9
            assert data['association_label'] == 'associational'
            assert len(data['results']) == 1
            assert data['results'][0]['p_corrected'] == 0.09

    def test_empty_results(self):
        """Test handling of empty results list."""
        raw_results = []
        corrected = apply_bonferroni_correction(raw_results, n_tests=9)
        assert len(corrected) == 0

    def test_single_result(self):
        """Test correction with a single result."""
        raw_results = [
            {"metric": "test", "valence": "test", "p_raw": 0.05}
        ]
        corrected = apply_bonferroni_correction(raw_results, n_tests=9)
        assert len(corrected) == 1
        assert corrected[0]['p_corrected'] == 0.45