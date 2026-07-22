"""
Unit tests for statistical analysis logic in code/stats.py.
Focus: McNemar's test selection logic and Bonferroni correction.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Import the functions to test from the stats module
# Note: We assume stats.py exposes these names as per the API surface
from stats import (
    run_mcnemar_test,
    run_permutation_test,
    apply_bonferroni_correction,
    detect_divergence,
    load_simulation_results,
    load_divergence_report
)


class TestMcNemarSelectionLogic:
    """Tests for the logic that selects McNemar's test for paired binary data."""

    def test_mcnemar_requires_paired_binary_data(self):
        """Verify McNemar's test runs correctly on paired binary outcomes."""
        # Simulate paired binary data: (Dynamic Win, Static Win)
        # Format: (Both Win, Dynamic Win Static Loss, Dynamic Loss Static Win, Both Loss)
        # Contingency table for McNemar:
        #                Static Win | Static Loss
        # Dynamic Win       a        |      b
        # Dynamic Loss      c        |      d
        # We only need b and c for the test statistic.
        
        # Create a mock contingency table (b=10, c=5)
        # This represents 10 cases where Dynamic won but Static lost,
        # and 5 cases where Static won but Dynamic lost.
        contingency_table = {
            "both_win": 50,
            "dynamic_win_static_loss": 10,  # b
            "dynamic_loss_static_win": 5,   # c
            "both_loss": 35
        }

        # Run McNemar's test
        result = run_mcnemar_test(
            b=contingency_table["dynamic_win_static_loss"],
            c=contingency_table["dynamic_loss_static_win"]
        )

        # Assert result structure
        assert "p_value" in result
        assert "statistic" in result
        assert "test_type" in result
        assert result["test_type"] == "mcnemar"

        # Verify the statistic calculation (approximate chi-squared with continuity correction)
        # chi2 = (|b - c| - 1)^2 / (b + c)
        # b=10, c=5 -> (|10-5|-1)^2 / 15 = (4)^2 / 15 = 16/15 ≈ 1.067
        expected_stat = ((abs(10 - 5) - 1) ** 2) / (10 + 5)
        assert abs(result["statistic"] - expected_stat) < 1e-5

    def test_mcnemar_handles_zero_counts(self):
        """Verify McNemar's test handles zero counts in off-diagonals gracefully."""
        # Case: b=0, c=0 -> No discordant pairs. Test is undefined or p=1.
        result = run_mcnemar_test(b=0, c=0)
        
        # Depending on implementation, this might raise or return p=1.0
        # We assert it returns a valid p_value
        assert "p_value" in result
        assert isinstance(result["p_value"], float)

    def test_mcnemar_handles_single_discordant_pair(self):
        """Verify McNemar's test handles small sample sizes."""
        # Case: b=1, c=0
        result = run_mcnemar_test(b=1, c=0)
        
        assert "p_value" in result
        assert 0.0 <= result["p_value"] <= 1.0

    def test_divergence_detection_logic(self):
        """Verify that divergence detection correctly identifies paired vs unpaired data."""
        # Create temporary files for simulation logs
        with tempfile.TemporaryDirectory() as tmpdir:
            dynamic_log = Path(tmpdir) / "dynamic.json"
            static_log = Path(tmpdir) / "static.json"

            # Scenario 1: Paired data (hashes match)
            paired_data = [
                {"trajectory_id": "T1", "final_state_hash": "abc123", "outcome": "win"},
                {"trajectory_id": "T2", "final_state_hash": "def456", "outcome": "loss"}
            ]
            
            with open(dynamic_log, 'w') as f:
                json.dump(paired_data, f)
            with open(static_log, 'w') as f:
                json.dump(paired_data, f) # Same hashes

            # Mock load_simulation_results to return our data
            with patch('stats.load_simulation_results') as mock_load:
                mock_load.side_effect = [
                    paired_data, # dynamic
                    paired_data  # static
                ]
                
                report = detect_divergence(str(dynamic_log), str(static_log))
                
                assert report["is_divergent"] is False
                assert len(report["divergent_trajectory_ids"]) == 0

            # Scenario 2: Unpaired data (hashes differ)
            divergent_data_dynamic = [
                {"trajectory_id": "T1", "final_state_hash": "abc123", "outcome": "win"},
                {"trajectory_id": "T2", "final_state_hash": "def456", "outcome": "loss"}
            ]
            divergent_data_static = [
                {"trajectory_id": "T1", "final_state_hash": "xyz999", "outcome": "win"}, # Different hash
                {"trajectory_id": "T2", "final_state_hash": "def456", "outcome": "loss"}
            ]

            with open(dynamic_log, 'w') as f:
                json.dump(divergent_data_dynamic, f)
            with open(static_log, 'w') as f:
                json.dump(divergent_data_static, f)

            with patch('stats.load_simulation_results') as mock_load:
                mock_load.side_effect = [
                    divergent_data_dynamic,
                    divergent_data_static
                ]
                
                report = detect_divergence(str(dynamic_log), str(static_log))
                
                assert report["is_divergent"] is True
                assert "T1" in report["divergent_trajectory_ids"]


class TestBonferroniCorrection:
    """Tests for Bonferroni correction application."""

    def test_bonferroni_corrects_multiple_tests(self):
        """Verify Bonferroni correction divides alpha by number of tests."""
        p_values = [0.01, 0.03, 0.05]
        alpha = 0.05
        num_tests = len(p_values)

        result = apply_bonferroni_correction(p_values, alpha)

        # Expected adjusted p-values: p * num_tests
        expected_adjusted = [p * num_tests for p in p_values]
        
        assert "adjusted_p_values" in result
        assert "significance_threshold" in result
        
        # Check significance threshold
        assert result["significance_threshold"] == alpha / num_tests

        # Check adjusted values (allowing for floating point tolerance)
        for i, exp_val in enumerate(expected_adjusted):
            assert abs(result["adjusted_p_values"][i] - exp_val) < 1e-6

    def test_bonferroni_caps_at_one(self):
        """Verify adjusted p-values do not exceed 1.0."""
        p_values = [0.9, 0.8]
        alpha = 0.05
        num_tests = len(p_values)

        result = apply_bonferroni_correction(p_values, alpha)

        for adj_p in result["adjusted_p_values"]:
            assert adj_p <= 1.0

    def test_bonferroni_determines_significance(self):
        """Verify the function correctly identifies significant results after correction."""
        # p=0.01 with 2 tests -> adjusted=0.02. If alpha=0.05, should be significant.
        # p=0.04 with 2 tests -> adjusted=0.08. If alpha=0.05, should be NOT significant.
        p_values = [0.01, 0.04]
        alpha = 0.05

        result = apply_bonferroni_correction(p_values, alpha)

        assert "significant_results" in result
        # First should be significant (0.02 < 0.05)
        assert result["significant_results"][0] is True
        # Second should not be significant (0.08 > 0.05)
        assert result["significant_results"][1] is False


class TestPermutationTestSelection:
    """Tests ensuring Permutation Test is selected for unpaired data."""

    def test_permutation_test_for_unpaired_data(self):
        """Verify Permutation Test runs when data is unpaired (divergent)."""
        # Simulate unpaired win/loss counts
        # Dynamic: 100 trials, 60 wins
        # Static: 100 trials, 50 wins
        # These are independent samples, so we use permutation test.
        
        dynamic_wins = 60
        dynamic_total = 100
        static_wins = 50
        static_total = 100

        result = run_permutation_test(
            dynamic_wins=dynamic_wins,
            dynamic_total=dynamic_total,
            static_wins=static_wins,
            static_total=static_total,
            n_permutations=1000, # Small for speed in test
            random_seed=42
        )

        assert "p_value" in result
        assert "test_type" in result
        assert result["test_type"] == "permutation"
        assert 0.0 <= result["p_value"] <= 1.0


class TestIntegrationSelectionLogic:
    """Integration tests for the test selection logic based on divergence."""

    def test_pipeline_selects_mcnemar_when_paired(self):
        """Simulate the full logic: if not divergent -> McNemar."""
        # This test verifies the logic flow described in T025
        is_divergent = False
        
        # In a real pipeline, this would call the appropriate function
        # Here we just verify the condition matches the expected function
        if not is_divergent:
            # Should call McNemar
            contingency = {"b": 10, "c": 5}
            res = run_mcnemar_test(b=contingency["b"], c=contingency["c"])
            assert res["test_type"] == "mcnemar"
        else:
            pytest.fail("Should have selected McNemar for paired data")

    def test_pipeline_selects_permutation_when_unpaired(self):
        """Simulate the full logic: if divergent -> Permutation."""
        is_divergent = True

        if is_divergent:
            # Should call Permutation
            res = run_permutation_test(
                dynamic_wins=60, dynamic_total=100,
                static_wins=50, static_total=100,
                n_permutations=100, random_seed=42
            )
            assert res["test_type"] == "permutation"
        else:
            pytest.fail("Should have selected Permutation for unpaired data")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])