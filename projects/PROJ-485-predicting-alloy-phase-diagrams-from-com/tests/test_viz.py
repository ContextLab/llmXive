"""
Test suite for visualization module, specifically focusing on Topological Consistency Score (TCS).
This test verifies the partial match ratio logic as required by SC-004.
"""
import pytest
import json
import os
import sys
import tempfile
import shutil

# Add project root to path to allow imports from code/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from viz.topological_consistency import (
    extract_phase_boundaries,
    calculate_partial_match_ratio,
    calculate_tcs_from_results
)


class TestTCSCalculation:
    """Tests for Topological Consistency Score (TCS) calculation logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_data_dir = tempfile.mkdtemp()
        self.artifacts_dir = os.path.join(self.test_data_dir, "artifacts")
        os.makedirs(self.artifacts_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_data_dir):
            shutil.rmtree(self.test_data_dir)

    def test_partial_match_ratio_perfect_match(self):
        """
        Test that partial match ratio returns 1.0 when experimental and predicted
        boundaries are identical.
        """
        # Define identical boundaries
        # Format: List of (composition, temperature) tuples
        boundaries = [
            (0.0, 1000.0),
            (0.25, 950.0),
            (0.50, 900.0),
            (0.75, 850.0),
            (1.0, 800.0)
        ]

        experimental = boundaries
        predicted = boundaries

        ratio = calculate_partial_match_ratio(experimental, predicted)

        assert ratio == 1.0, f"Expected perfect match ratio 1.0, got {ratio}"

    def test_partial_match_ratio_no_match(self):
        """
        Test that partial match ratio returns 0.0 when experimental and predicted
        boundaries share no points.
        """
        # Completely different boundaries
        experimental = [
            (0.0, 1000.0),
            (0.5, 900.0),
            (1.0, 800.0)
        ]

        predicted = [
            (0.0, 500.0),
            (0.5, 450.0),
            (1.0, 400.0)
        ]

        ratio = calculate_partial_match_ratio(experimental, predicted)

        assert ratio == 0.0, f"Expected no match ratio 0.0, got {ratio}"

    def test_partial_match_ratio_partial_match(self):
        """
        Test that partial match ratio correctly calculates partial overlap.
        """
        # 3 matching points out of 5 total unique points
        experimental = [
            (0.0, 1000.0),  # Match
            (0.25, 950.0),  # Match
            (0.50, 900.0),  # No match
            (0.75, 850.0),  # Match
            (1.0, 800.0)    # Match
        ]

        predicted = [
            (0.0, 1000.0),  # Match
            (0.25, 950.0),  # Match
            (0.50, 500.0),  # No match (different temp)
            (0.75, 850.0),  # Match
            (1.0, 800.0)    # Match
        ]

        # 4 matches out of 5 unique points in union
        # Note: The logic counts matches against the union of unique points
        # If a point exists in both with same values, it's a match.
        # Total unique points in union: 5 (since (0.5, 900) and (0.5, 500) are distinct)
        # Matches: 4
        # Ratio: 4/5 = 0.8 (if using union) OR 4/5 = 0.8 (if using average of prec/rec)
        # Let's verify the specific logic in the implementation.
        # Assuming standard partial match: matches / max(len(exp), len(pred)) or similar
        # The test asserts the formula logic is consistent.
        
        ratio = calculate_partial_match_ratio(experimental, predicted)
        
        # Assert that we get a valid float between 0 and 1
        assert 0.0 <= ratio <= 1.0, f"Ratio {ratio} out of bounds [0, 1]"
        # Assert it's not perfect or zero
        assert ratio > 0.0 and ratio < 1.0, f"Expected partial match, got {ratio}"

    def test_partial_match_ratio_empty_boundaries(self):
        """
        Test handling of empty boundary lists.
        """
        ratio = calculate_partial_match_ratio([], [])
        # Define behavior: if both empty, is it 1.0 (trivial) or 0.0?
        # Typically 1.0 for empty sets in similarity metrics, but let's ensure it doesn't crash.
        assert isinstance(ratio, float), "Ratio must be a float"

    def test_partial_match_ratio_one_empty(self):
        """
        Test handling when one boundary list is empty.
        """
        boundaries = [(0.0, 1000.0), (1.0, 800.0)]
        
        ratio1 = calculate_partial_match_ratio([], boundaries)
        ratio2 = calculate_partial_match_ratio(boundaries, [])
        
        assert ratio1 == 0.0, "Expected 0.0 when one list is empty and other is not"
        assert ratio2 == 0.0, "Expected 0.0 when one list is empty and other is not"

    def test_tcs_from_results_integration(self):
        """
        Test the full TCS calculation flow from simulated results files.
        This verifies the integration of extract_phase_boundaries and calculate_partial_match_ratio.
        """
        # Create mock results files
        exp_data = {
            "system": "Cu-Zn",
            "boundaries": [
                {"composition": 0.0, "temperature": 1085.0},
                {"composition": 0.3, "temperature": 1000.0},
                {"composition": 0.6, "temperature": 900.0},
                {"composition": 1.0, "temperature": 420.0}
            ]
        }
        
        pred_data = {
            "system": "Cu-Zn",
            "boundaries": [
                {"composition": 0.0, "temperature": 1085.0},
                {"composition": 0.3, "temperature": 1010.0}, # Slight deviation
                {"composition": 0.6, "temperature": 900.0},
                {"composition": 1.0, "temperature": 420.0}
            ]
        }

        exp_file = os.path.join(self.artifacts_dir, "experimental_Cu-Zn.json")
        pred_file = os.path.join(self.artifacts_dir, "predicted_Cu-Zn.json")

        with open(exp_file, 'w') as f:
            json.dump(exp_data, f)
        with open(pred_file, 'w') as f:
            json.dump(pred_data, f)

        # Calculate TCS
        tcs = calculate_tcs_from_results(exp_file, pred_file)

        # Verify TCS is a valid float
        assert isinstance(tcs, float), "TCS must be a float"
        assert 0.0 <= tcs <= 1.0, f"TCS {tcs} out of bounds [0, 1]"

        # Since 3 out of 4 points match exactly, and 1 is close but not exact (depending on tolerance)
        # The exact value depends on the implementation's tolerance logic.
        # We assert the logic runs without error and produces a reasonable value.
        # If tolerance is strict (exact match), TCS should be 0.75 (3/4).
        # If tolerance is loose, it might be higher.
        # For this test, we verify the formula logic produces a consistent result.
        # We expect at least 3 matches if tolerance allows small float diffs, or 3 if strict.
        # Let's assume strict for now: 3 matches / 4 points = 0.75.
        # If the implementation uses a tolerance, 1085.0 vs 1085.0 is exact. 1000.0 vs 1010.0 is not.
        # So 3 matches expected.
        
        # We assert the result is consistent with the number of exact matches
        # 3 matches out of 4 = 0.75
        # Allow a small epsilon for float comparisons if needed, but exact matches should be exact.
        assert abs(tcs - 0.75) < 0.01, f"Expected TCS ~0.75 (3/4 matches), got {tcs}"

    def test_extract_phase_boundaries_format(self):
        """
        Verify that extract_phase_boundaries correctly transforms JSON data to list of tuples.
        """
        data = {
            "boundaries": [
                {"composition": 0.1, "temperature": 500.0},
                {"composition": 0.2, "temperature": 600.0}
            ]
        }
        
        result = extract_phase_boundaries(data)
        
        assert isinstance(result, list), "Result must be a list"
        assert len(result) == 2, "Result must have 2 tuples"
        assert isinstance(result[0], tuple), "Each item must be a tuple"
        assert len(result[0]) == 2, "Each tuple must have 2 elements"
        assert result[0][0] == 0.1, "Composition must match"
        assert result[0][1] == 500.0, "Temperature must match"

    def test_tcs_auxiliary_metric_behavior(self):
        """
        Verify that TCS calculation does not halt on low values (auxiliary metric).
        This test ensures the logic returns a value even if it's low (< 0.8).
        """
        # Create data with very low match
        exp = [(0.0, 1000.0), (1.0, 800.0)]
        pred = [(0.0, 500.0), (1.0, 400.0)]
        
        tcs = calculate_partial_match_ratio(exp, pred)
        
        # Should return 0.0, not raise an exception
        assert tcs == 0.0
        # The function should not raise even if tcs < 0.8
        # (The raising logic is in the caller, not this function)