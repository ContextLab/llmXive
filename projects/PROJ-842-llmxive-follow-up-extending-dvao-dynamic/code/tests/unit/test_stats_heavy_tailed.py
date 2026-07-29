"""
Unit tests for heavy-tailed Pareto validation in stats.py
"""
import pytest
import numpy as np
import os
import json
import tempfile
from src.analysis.stats import validate_heavy_tailed_pareto, validate_heavy_tailed
from src.environment.synthetic_mdp import generate_heavy_tailed_mdp

class TestHeavyTailedParetoValidation:
    """Tests for validate_heavy_tailed_pareto function."""

    def test_validate_heavy_tailed_returns_tuple(self):
        """Test that function returns a tuple of (float, bool)."""
        deviation, passed = validate_heavy_tailed_pareto(
            n_objectives=5,
            seed=42,
            threshold_percent=10.0
        )
        assert isinstance(deviation, float)
        assert isinstance(passed, bool)

    def test_validate_heavy_tailed_creates_output_file(self):
        """Test that output file is created at specified path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.json")
            validate_heavy_tailed_pareto(
                n_objectives=5,
                seed=42,
                threshold_percent=10.0,
                output_path=output_path
            )
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                results = json.load(f)
            assert "threshold_passed" in results
            assert "deviation_metric_percent" in results

    def test_validate_heavy_tailed_contains_required_keys(self):
        """Test that output contains all required keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.json")
            validate_heavy_tailed_pareto(
                n_objectives=5,
                seed=42,
                threshold_percent=10.0,
                output_path=output_path
            )
            with open(output_path, 'r') as f:
                results = json.load(f)
            
            required_keys = [
                "n_objectives", "seed", "threshold_percent",
                "average_distance", "max_distance", "frontier_norm",
                "deviation_metric_percent", "threshold_passed",
                "distribution_type", "degrees_of_freedom"
            ]
            for key in required_keys:
                assert key in results, f"Missing key: {key}"

    def test_validate_heavy_tailed_deterministic_with_seed(self):
        """Test that results are deterministic with same seed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path1 = os.path.join(tmpdir, "test1.json")
            output_path2 = os.path.join(tmpdir, "test2.json")
            
            validate_heavy_tailed_pareto(
                n_objectives=5,
                seed=42,
                threshold_percent=10.0,
                output_path=output_path1
            )
            validate_heavy_tailed_pareto(
                n_objectives=5,
                seed=42,
                threshold_percent=10.0,
                output_path=output_path2
            )
            
            with open(output_path1, 'r') as f1, open(output_path2, 'r') as f2:
                results1 = json.load(f1)
                results2 = json.load(f2)
            
            assert results1["deviation_metric_percent"] == results2["deviation_metric_percent"]
            assert results1["threshold_passed"] == results2["threshold_passed"]

    def test_validate_heavy_tailed_threshold_logic(self):
        """Test that threshold_passed reflects the deviation metric correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_results.json")
            deviation, passed = validate_heavy_tailed_pareto(
                n_objectives=5,
                seed=42,
                threshold_percent=10.0,
                output_path=output_path
            )
            
            with open(output_path, 'r') as f:
                results = json.load(f)
            
            expected_passed = deviation <= 10.0
            assert passed == expected_passed
            assert results["threshold_passed"] == expected_passed

    def test_validate_heavy_tailed_with_custom_objectives(self):
        """Test with different number of objectives."""
        for n_obj in [2, 5, 10]:
            deviation, passed = validate_heavy_tailed_pareto(
                n_objectives=n_obj,
                seed=42,
                threshold_percent=10.0
            )
            assert isinstance(deviation, float)
            assert isinstance(passed, bool)

    def test_validate_heavy_tailed_wrapper_function(self):
        """Test the validate_heavy_tailed wrapper function."""
        deviation, passed = validate_heavy_tailed(
            n_objectives=5,
            seed=42,
            threshold_percent=10.0
        )
        assert isinstance(deviation, float)
        assert isinstance(passed, bool)
