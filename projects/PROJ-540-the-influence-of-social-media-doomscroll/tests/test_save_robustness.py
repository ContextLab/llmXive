"""
Unit tests for the robustness results saving functionality (T027).
"""
import json
import tempfile
from pathlib import Path
import pytest

from save_robustness_results import save_robustness_results


class TestSaveRobustnessResults:
    """Test cases for the save_robustness_results function."""

    def test_save_results_creates_file(self, tmp_path):
        """Test that save_robustness_results creates the output file."""
        results = {
            "full_sample": {"coefficients": [1.0, 2.0]},
            "high_engagement_subset": {"coefficients": [1.5, 2.5]},
            "comparison": {"diff": 0.5}
        }
        output_path = tmp_path / "test_results.json"
        
        saved_path = save_robustness_results(results, output_path)
        
        assert saved_path.exists()
        assert saved_path == output_path

    def test_save_results_valid_json(self, tmp_path):
        """Test that the saved file contains valid JSON."""
        results = {
            "full_sample": {"coefficients": [1.0, 2.0], "p_values": [0.01, 0.02]},
            "high_engagement_subset": {"coefficients": [1.5, 2.5], "p_values": [0.03, 0.04]},
            "comparison": {"coefficient_diff": 0.5, "significance_change": "increased"},
            "metadata": {"threshold": 0.3, "n_full": 1000, "n_subset": 250}
        }
        output_path = tmp_path / "test_results.json"
        
        save_robustness_results(results, output_path)
        
        with open(output_path, 'r') as f:
            loaded_results = json.load(f)
        
        assert loaded_results == results

    def test_save_results_handles_numpy_types(self, tmp_path):
        """Test that numpy types are properly serialized."""
        import numpy as np
        results = {
            "full_sample": {"coefficient": np.float64(1.5), "p_value": np.float32(0.01)},
            "high_engagement_subset": {"coefficient": np.float64(2.0)},
            "comparison": {"diff": np.int64(5)}
        }
        output_path = tmp_path / "test_results.json"
        
        # Should not raise an error
        save_robustness_results(results, output_path)
        
        with open(output_path, 'r') as f:
            loaded_results = json.load(f)
        
        assert isinstance(loaded_results["full_sample"]["coefficient"], (int, float))
        assert isinstance(loaded_results["comparison"]["diff"], (int, float))

    def test_save_results_creates_directory_if_needed(self, tmp_path):
        """Test that save_robustness_results creates parent directories if needed."""
        results = {"test": "data"}
        output_path = tmp_path / "subdir" / "results.json"
        
        saved_path = save_robustness_results(results, output_path)
        
        assert saved_path.exists()
        assert saved_path.parent.exists()

    def test_save_results_empty_dict(self, tmp_path):
        """Test saving an empty dictionary."""
        results = {}
        output_path = tmp_path / "empty_results.json"
        
        saved_path = save_robustness_results(results, output_path)
        
        assert saved_path.exists()
        with open(output_path, 'r') as f:
            loaded_results = json.load(f)
        assert loaded_results == {}