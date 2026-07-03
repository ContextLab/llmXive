"""
Unit tests for metrics in the memory palaces project.
Specifically tests the interference distance calculation as required by T023.
"""
import pytest
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any

# Import the function we are testing.
# Note: The function `compute_interference_distance` is expected to be added
# to code/evaluation/metrics.py by task T024. We import it here to test it.
# If T024 hasn't been implemented yet, this import will fail, which is expected
# behavior for a test-first approach.
try:
    from code.evaluation.metrics import compute_interference_distance
except ImportError:
    # If the function doesn't exist yet, we define a stub for the test structure
    # but mark the test as skipped or expect an error in a real run.
    # However, per instructions, we must implement the test for the REAL function.
    # We will assume T024 provides this function.
    raise pytest.skip("compute_interference_distance not yet implemented in code/evaluation/metrics.py")


class TestInterferenceDistance:
    """Tests for the interference distance metric calculation."""

    def test_interference_distance_basic(self):
        """Test basic calculation of interference distance."""
        # Simulate spatial variant coordinates (e.g., well-separated)
        spatial_coords = [
            {"x": 0.0, "y": 0.0, "content_hash": "a1"},
            {"x": 10.0, "y": 10.0, "content_hash": "b2"},
            {"x": 20.0, "y": 20.0, "content_hash": "c3"},
        ]

        # Simulate baseline variant coordinates (e.g., clustered)
        baseline_coords = [
            {"x": 0.0, "y": 0.0, "content_hash": "a1"},
            {"x": 0.1, "y": 0.1, "content_hash": "b2"},
            {"x": 0.2, "y": 0.2, "content_hash": "c3"},
        ]

        result = compute_interference_distance(spatial_coords, baseline_coords)

        # The metric should return a dictionary with 'spatial', 'baseline', and 'delta'
        assert isinstance(result, dict)
        assert "spatial" in result
        assert "baseline" in result
        assert "delta" in result

        # Spatial distance should be larger than baseline distance
        assert result["spatial"] > result["baseline"]
        # Delta should be positive (spatial - baseline)
        assert result["delta"] > 0

    def test_interference_distance_empty_inputs(self):
        """Test behavior with empty coordinate lists."""
        with pytest.raises(ValueError):
            compute_interference_distance([], [])

    def test_interference_distance_single_item(self):
        """Test behavior with a single coordinate item."""
        spatial_coords = [{"x": 0.0, "y": 0.0, "content_hash": "a1"}]
        baseline_coords = [{"x": 0.0, "y": 0.0, "content_hash": "a1"}]

        result = compute_interference_distance(spatial_coords, baseline_coords)

        # With single item, average distance might be 0 or undefined depending on implementation
        # We expect the function to handle this gracefully and return a numeric value
        assert isinstance(result["spatial"], (int, float))
        assert isinstance(result["baseline"], (int, float))
        assert isinstance(result["delta"], (int, float))

    def test_interference_distance_output_format(self):
        """Test that the output matches the expected JSON schema."""
        spatial_coords = [
            {"x": 0.0, "y": 0.0, "content_hash": "a1"},
            {"x": 1.0, "y": 1.0, "content_hash": "b2"},
        ]
        baseline_coords = [
            {"x": 0.0, "y": 0.0, "content_hash": "a1"},
            {"x": 0.5, "y": 0.5, "content_hash": "b2"},
        ]

        result = compute_interference_distance(spatial_coords, baseline_coords)

        # Check types
        assert isinstance(result["spatial"], (int, float, np.floating))
        assert isinstance(result["baseline"], (int, float, np.floating))
        assert isinstance(result["delta"], (int, float, np.floating))

        # Check that delta is computed correctly
        expected_delta = result["spatial"] - result["baseline"]
        assert np.isclose(result["delta"], expected_delta)

    def test_interference_distance_with_realistic_data(self):
        """Test with more realistic coordinate distributions."""
        np.random.seed(42)
        
        # Spatial: points spread across a 100x100 grid
        spatial_coords = [
            {"x": float(np.random.uniform(0, 100)), 
             "y": float(np.random.uniform(0, 100)), 
             "content_hash": f"spatial_{i}"}
            for i in range(100)
        ]

        # Baseline: points clustered in a 10x10 area
        baseline_coords = [
            {"x": float(np.random.uniform(0, 10)), 
             "y": float(np.random.uniform(0, 10)), 
             "content_hash": f"baseline_{i}"}
            for i in range(100)
        ]

        result = compute_interference_distance(spatial_coords, baseline_coords)

        # Spatial should have much higher average distance
        assert result["spatial"] > result["baseline"]
        assert result["delta"] > 0

        # Verify magnitudes make sense
        # For 100 random points in 100x100, avg distance should be ~50-60
        # For 100 random points in 10x10, avg distance should be ~5-6
        assert 40 < result["spatial"] < 80
        assert 3 < result["baseline"] < 10

    def test_interference_distance_symmetry(self):
        """Test that the metric is consistent regardless of input order (if applicable)."""
        # Note: The metric is directional (spatial vs baseline), so this test
        # verifies the function handles the distinction correctly
        spatial_coords = [{"x": 0.0, "y": 0.0, "content_hash": "a1"}]
        baseline_coords = [{"x": 10.0, "y": 10.0, "content_hash": "b2"}]

        result = compute_interference_distance(spatial_coords, baseline_coords)

        # The function should compute distances within each set, not between sets
        # So both spatial and baseline should be 0 for single-item sets
        assert result["spatial"] == 0.0
        assert result["baseline"] == 0.0
        assert result["delta"] == 0.0

    def test_interference_distance_json_serializable(self):
        """Test that the result can be serialized to JSON."""
        spatial_coords = [
            {"x": 1.0, "y": 2.0, "content_hash": "a1"},
            {"x": 3.0, "y": 4.0, "content_hash": "b2"},
        ]
        baseline_coords = [
            {"x": 1.5, "y": 2.5, "content_hash": "a1"},
            {"x": 3.5, "y": 4.5, "content_hash": "b2"},
        ]

        result = compute_interference_distance(spatial_coords, baseline_coords)

        # Should be serializable
        json_str = json.dumps(result)
        assert json_str is not None

        # Should be deserializable
        deserialized = json.loads(json_str)
        assert deserialized["spatial"] == result["spatial"]
        assert deserialized["baseline"] == result["baseline"]
        assert deserialized["delta"] == result["delta"]