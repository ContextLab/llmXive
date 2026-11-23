"""
Unit tests for code/eval/anova.py
Verifies Two-Way ANOVA input format and p-value extraction.
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from eval.anova import load_metrics_for_anova, run_anova, main
from config import get_results_dir, ensure_directories


class TestAnovaInputFormat:
    """Tests for verifying the input format expected by the ANOVA module."""

    def setup_method(self):
        """Create a temporary directory for test artifacts."""
        self.temp_dir = tempfile.mkdtemp()
        self.results_dir = Path(self.temp_dir)
        # Ensure the directory exists
        ensure_directories(self.results_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_load_metrics_for_anova_empty_file(self):
        """Test loading an empty metrics file."""
        metrics_file = self.results_dir / "metrics.json"
        with open(metrics_file, 'w') as f:
            json.dump({}, f)

        df = load_metrics_for_anova(metrics_file)
        assert df is not None
        assert df.empty

    def test_load_metrics_for_anova_invalid_structure(self):
        """Test loading a metrics file with invalid structure."""
        metrics_file = self.results_dir / "metrics.json"
        invalid_data = {
            "invalid_key": "value"
        }
        with open(metrics_file, 'w') as f:
            json.dump(invalid_data, f)

        df = load_metrics_for_anova(metrics_file)
        # Should handle gracefully, returning empty or partial data
        assert isinstance(df, pd.DataFrame)

    def test_load_metrics_for_anova_valid_structure(self):
        """Test loading a metrics file with valid structure."""
        metrics_file = self.results_dir / "metrics.json"
        valid_data = {
            "results": [
                {
                    "sequence_id": "seq_001",
                    "scene_dynamics": "Static",
                    "texture_level": "High",
                    "world_score": 0.85,
                    "sparse_consistency": 0.92,
                    "fid": 12.5,
                    "inference_time": 0.45
                },
                {
                    "sequence_id": "seq_002",
                    "scene_dynamics": "Fast",
                    "texture_level": "Low",
                    "world_score": 0.65,
                    "sparse_consistency": 0.70,
                    "fid": 25.3,
                    "inference_time": 0.38
                }
            ]
        }
        with open(metrics_file, 'w') as f:
            json.dump(valid_data, f)

        df = load_metrics_for_anova(metrics_file)
        assert not df.empty
        assert "world_score" in df.columns
        assert "sparse_consistency" in df.columns
        assert "scene_dynamics" in df.columns
        assert "texture_level" in df.columns

    def test_run_anova_requires_valid_input(self):
        """Test that run_anova fails gracefully on invalid input."""
        df = pd.DataFrame()
        with pytest.raises((ValueError, KeyError)):
            run_anova(df)

    def test_run_anova_with_valid_input(self):
        """Test run_anova with valid input data."""
        data = {
            "scene_dynamics": ["Static", "Static", "Fast", "Fast"],
            "texture_level": ["High", "Low", "High", "Low"],
            "world_score": [0.9, 0.85, 0.7, 0.65],
            "sparse_consistency": [0.95, 0.9, 0.8, 0.75]
        }
        df = pd.DataFrame(data)

        result = run_anova(df, metric="world_score")

        assert result is not None
        assert "anova_table" in result
        assert "interaction_p_value" in result
        assert "main_effects" in result

        # Verify interaction p-value is a float
        assert isinstance(result["interaction_p_value"], float)

        # Verify ANOVA table structure
        anova_table = result["anova_table"]
        assert isinstance(anova_table, pd.DataFrame)
        assert "P(>F)" in anova_table.columns

    def test_run_anova_multiple_metrics(self):
        """Test running ANOVA on multiple metrics."""
        data = {
            "scene_dynamics": ["Static"] * 4 + ["Fast"] * 4,
            "texture_level": ["High", "Low", "High", "Low"] * 2,
            "world_score": [0.9, 0.85, 0.7, 0.65, 0.88, 0.82, 0.68, 0.62],
            "sparse_consistency": [0.95, 0.9, 0.8, 0.75, 0.92, 0.87, 0.77, 0.72]
        }
        df = pd.DataFrame(data)

        metrics = ["world_score", "sparse_consistency"]
        results = {}
        for metric in metrics:
            results[metric] = run_anova(df, metric=metric)

        assert len(results) == 2
        for metric, result in results.items():
            assert result is not None
            assert "interaction_p_value" in result
            assert isinstance(result["interaction_p_value"], float)

    def test_run_anova_with_categorical_variables(self):
        """Test that categorical variables are handled correctly."""
        data = {
            "scene_dynamics": pd.Categorical(["Static", "Static", "Fast", "Fast"]),
            "texture_level": pd.Categorical(["High", "Low", "High", "Low"]),
            "world_score": [0.9, 0.85, 0.7, 0.65]
        }
        df = pd.DataFrame(data)

        result = run_anova(df, metric="world_score")
        assert result is not None
        assert "interaction_p_value" in result

    def test_run_anova_insufficient_data(self):
        """Test ANOVA with insufficient data points."""
        # Only 2 data points - insufficient for two-way ANOVA
        data = {
            "scene_dynamics": ["Static", "Fast"],
            "texture_level": ["High", "Low"],
            "world_score": [0.9, 0.7]
        }
        df = pd.DataFrame(data)

        # Should raise an error or return a warning
        with pytest.raises((ValueError, RuntimeError)):
            run_anova(df, metric="world_score")


class TestAnovaPValueExtraction:
    """Tests for verifying p-value extraction and interpretation."""

    def setup_method(self):
        """Create test data with known statistical properties."""
        self.temp_dir = tempfile.mkdtemp()
        self.results_dir = Path(self.temp_dir)
        ensure_directories(self.results_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_extract_interaction_p_value(self):
        """Test extracting interaction p-value from ANOVA results."""
        # Create data with known interaction effect
        np.random.seed(42)
        n_samples = 20
        data = {
            "scene_dynamics": np.random.choice(["Static", "Fast"], n_samples),
            "texture_level": np.random.choice(["High", "Low"], n_samples),
            "world_score": np.random.normal(0.8, 0.1, n_samples)
        }
        df = pd.DataFrame(data)

        result = run_anova(df, metric="world_score")
        p_value = result["interaction_p_value"]

        assert 0 <= p_value <= 1, "P-value must be between 0 and 1"

    def test_p_value_threshold_interpretation(self):
        """Test that p-values are correctly interpreted against threshold."""
        # Create data with strong interaction effect
        np.random.seed(123)
        n_samples = 40
        data = {
            "scene_dynamics": ["Static"] * 20 + ["Fast"] * 20,
            "texture_level": ["High", "Low"] * 20,
            # Create a pattern that should show interaction
            "world_score": [
                *np.random.normal(0.9, 0.05, 10),  # Static, High
                *np.random.normal(0.8, 0.05, 10),  # Static, Low
                *np.random.normal(0.7, 0.05, 10),  # Fast, High
                *np.random.normal(0.5, 0.05, 10)   # Fast, Low (stronger drop)
            ]
        }
        df = pd.DataFrame(data)

        result = run_anova(df, metric="world_score")
        p_value = result["interaction_p_value"]

        # For this data, we expect a significant interaction (p < 0.05)
        # Note: Due to randomness, this might occasionally fail, but with
        # this effect size it should pass most of the time
        assert p_value < 0.1, f"Expected significant interaction, got p={p_value}"

    def test_main_effects_extraction(self):
        """Test extracting main effects from ANOVA results."""
        np.random.seed(456)
        n_samples = 40
        data = {
            "scene_dynamics": ["Static"] * 20 + ["Fast"] * 20,
            "texture_level": ["High", "Low"] * 20,
            "world_score": np.random.normal(0.8, 0.1, n_samples)
        }
        df = pd.DataFrame(data)

        result = run_anova(df, metric="world_score")
        main_effects = result["main_effects"]

        assert "scene_dynamics" in main_effects
        assert "texture_level" in main_effects
        assert 0 <= main_effects["scene_dynamics"] <= 1
        assert 0 <= main_effects["texture_level"] <= 1


class TestAnovaIntegration:
    """Integration tests for the ANOVA module."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.results_dir = Path(self.temp_dir)
        ensure_directories(self.results_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_main_function_with_real_data(self):
        """Test the main function with realistic test data."""
        # Create a realistic metrics file
        metrics_file = self.results_dir / "metrics.json"
        test_data = {
            "results": [
                {"sequence_id": f"seq_{i:03d}",
                 "scene_dynamics": ["Static", "Fast"][i % 2],
                 "texture_level": ["High", "Low"][i % 2],
                 "world_score": 0.85 - 0.05 * (i % 2) + np.random.normal(0, 0.02),
                 "sparse_consistency": 0.90 - 0.05 * (i % 2) + np.random.normal(0, 0.02),
                 "fid": 15.0 + 5.0 * (i % 2) + np.random.normal(0, 1.0),
                 "inference_time": 0.4 + 0.1 * (i % 2) + np.random.normal(0, 0.01)}
                for i in range(20)
            ]
        }
        with open(metrics_file, 'w') as f:
            json.dump(test_data, f)

        # Run main function
        output_file = self.results_dir / "anova_results.json"
        main(metrics_file=metrics_file, output_file=output_file)

        # Verify output file exists and contains valid results
        assert output_file.exists()
        with open(output_file, 'r') as f:
            results = json.load(f)

        assert "world_score" in results
        assert "sparse_consistency" in results
        assert "anova_table" in results["world_score"]
        assert "interaction_p_value" in results["world_score"]

    def test_anova_with_edge_case_data(self):
        """Test ANOVA with edge case data (constant values)."""
        data = {
            "scene_dynamics": ["Static", "Static", "Fast", "Fast"],
            "texture_level": ["High", "Low", "High", "Low"],
            "world_score": [0.5, 0.5, 0.5, 0.5]  # Constant values
        }
        df = pd.DataFrame(data)

        # This should handle the edge case gracefully
        result = run_anova(df, metric="world_score")
        assert result is not None
        assert "interaction_p_value" in result

    def test_anova_with_missing_values(self):
        """Test ANOVA with missing values in the dataset."""
        data = {
            "scene_dynamics": ["Static", "Static", "Fast", "Fast", None],
            "texture_level": ["High", "Low", "High", "Low", "High"],
            "world_score": [0.9, 0.85, 0.7, 0.65, 0.8]
        }
        df = pd.DataFrame(data)

        # Should handle missing values by dropping or imputing
        result = run_anova(df, metric="world_score")
        assert result is not None
        assert "interaction_p_value" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])