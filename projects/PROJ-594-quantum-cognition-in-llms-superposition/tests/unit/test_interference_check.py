"""
Unit tests for interference_check.py (Task T036)
"""
import os
import sys
import json
import tempfile
import pytest
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from code.analysis.interference_check import load_interference_data, compute_spearman_correlation

class TestInterferenceCheck:
    def test_load_interference_data_valid(self, tmp_path):
        """Test loading valid interference data."""
        data = {
            "samples": [
                {"ambiguity_score": 0.8, "cross_term_value": -0.5},
                {"ambiguity_score": 0.2, "cross_term_value": 0.1},
                {"ambiguity_score": 0.9, "cross_term_value": -0.8}
            ]
        }
        input_file = tmp_path / "interference_validation.json"
        with open(input_file, "w") as f:
            json.dump(data, f)

        samples = load_interference_data(str(input_file))
        assert len(samples) == 3
        assert samples[0]["ambiguity_score"] == 0.8
        assert samples[0]["cross_term_value"] == -0.5

    def test_load_interference_data_missing_file(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            load_interference_data("/nonexistent/path/file.json")

    def test_load_interference_data_invalid_format(self, tmp_path):
        """Test error handling for invalid format."""
        data = {"wrong_key": []}
        input_file = tmp_path / "interference_validation.json"
        with open(input_file, "w") as f:
            json.dump(data, f)

        with pytest.raises(ValueError):
            load_interference_data(str(input_file))

    def test_compute_spearman_correlation_negative(self):
        """Test that negative correlation is detected correctly."""
        samples = [
            {"ambiguity_score": 0.1, "cross_term_value": 0.9},
            {"ambiguity_score": 0.3, "cross_term_value": 0.5},
            {"ambiguity_score": 0.5, "cross_term_value": 0.1},
            {"ambiguity_score": 0.7, "cross_term_value": -0.3},
            {"ambiguity_score": 0.9, "cross_term_value": -0.7}
        ]
        result = compute_spearman_correlation(samples)
        assert result["correlation_coefficient"] < 0
        assert result["p_value"] < 0.05
        assert result["sample_count"] == 5

    def test_compute_spearman_correlation_positive(self):
        """Test that positive correlation is detected (unexpected for this hypothesis)."""
        samples = [
            {"ambiguity_score": 0.1, "cross_term_value": -0.9},
            {"ambiguity_score": 0.3, "cross_term_value": -0.5},
            {"ambiguity_score": 0.5, "cross_term_value": 0.0},
            {"ambiguity_score": 0.7, "cross_term_value": 0.4},
            {"ambiguity_score": 0.9, "cross_term_value": 0.8}
        ]
        result = compute_spearman_correlation(samples)
        assert result["correlation_coefficient"] > 0

    def test_compute_spearman_correlation_no_correlation(self):
        """Test with random data showing no correlation."""
        np.random.seed(42)
        samples = [
            {"ambiguity_score": float(i), "cross_term_value": float(np.random.randn())}
            for i in range(100)
        ]
        result = compute_spearman_correlation(samples)
        assert abs(result["correlation_coefficient"]) < 0.3  # Likely small
        assert result["sample_count"] == 100
