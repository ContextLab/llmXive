"""
Unit tests for the Holm-Bonferroni correction implementation.

These tests verify that the step-down correction logic produces
the exact expected adjusted p-values for known inputs.
"""

import pytest
import json
import tempfile
from pathlib import Path
from code.analysis.holm_bonferroni import (
    calculate_holm_bonferroni,
    load_p_values_from_json,
    write_holm_results,
    run_holm_bonferroni_pipeline,
    HolmBonferroniResult
)


class TestHolmBonferroniCalculation:
    """Tests for the core calculation logic."""

    def test_empty_input(self):
        """Test that empty input returns an empty list."""
        results = calculate_holm_bonferroni([])
        assert results == []

    def test_single_p_value(self):
        """Test correction for a single p-value."""
        p_values = [("MetricA", 0.03)]
        results = calculate_holm_bonferroni(p_values)
        
        assert len(results) == 1
        assert results[0].metric_name == "MetricA"
        assert results[0].original_p_value == 0.03
        # For m=1, adjusted = 1 * 0.03 = 0.03
        assert results[0].adjusted_p_value == pytest.approx(0.03)
        assert results[0].is_significant is True
        assert results[0].rank == 1

    def test_two_p_values(self):
        """Test correction for two p-values."""
        # Input: p1=0.04, p2=0.01
        # Sorted: (0.01, 0.04)
        # Rank 1 (0.01): adj = 2 * 0.01 = 0.02
        # Rank 2 (0.04): adj = max(0.02, 1 * 0.04) = 0.04
        p_values = [("MetricA", 0.04), ("MetricB", 0.01)]
        results = calculate_holm_bonferroni(p_values)
        
        assert len(results) == 2
        
        # First result should be MetricB (rank 1)
        assert results[0].metric_name == "MetricB"
        assert results[0].adjusted_p_value == pytest.approx(0.02)
        assert results[0].is_significant is True
        
        # Second result should be MetricA (rank 2)
        assert results[1].metric_name == "MetricA"
        assert results[1].adjusted_p_value == pytest.approx(0.04)
        assert results[1].is_significant is True

    def test_three_p_values_known_output(self):
        """
        Test with three p-values where the expected output is known.
        
        Input: 
          MetricA: 0.05
          MetricB: 0.01
          MetricC: 0.03
        
        Sorted:
          1. MetricB (0.01)
          2. MetricC (0.03)
          3. MetricA (0.05)
        
        Calculations (m=3):
          Rank 1 (MetricB): 3 * 0.01 = 0.03
          Rank 2 (MetricC): max(0.03, 2 * 0.03) = 0.06
          Rank 3 (MetricA): max(0.06, 1 * 0.05) = 0.06 (monotonicity enforced)
        
        Expected Adjusted:
          MetricB: 0.03 (Sig)
          MetricC: 0.06 (Not Sig)
          MetricA: 0.06 (Not Sig)
        """
        p_values = [
            ("MetricA", 0.05),
            ("MetricB", 0.01),
            ("MetricC", 0.03)
        ]
        results = calculate_holm_bonferroni(p_values)
        
        assert len(results) == 3
        
        # Check MetricB (Rank 1)
        metric_b = next(r for r in results if r.metric_name == "MetricB")
        assert metric_b.rank == 1
        assert metric_b.adjusted_p_value == pytest.approx(0.03)
        assert metric_b.is_significant is True
        
        # Check MetricC (Rank 2)
        metric_c = next(r for r in results if r.metric_name == "MetricC")
        assert metric_c.rank == 2
        assert metric_c.adjusted_p_value == pytest.approx(0.06)
        assert metric_c.is_significant is False
        
        # Check MetricA (Rank 3)
        metric_a = next(r for r in results if r.metric_name == "MetricA")
        assert metric_a.rank == 3
        assert metric_a.adjusted_p_value == pytest.approx(0.06) # Monotonicity
        assert metric_a.is_significant is False

    def test_monotonicity_enforcement(self):
        """
        Test that adjusted p-values are monotonically non-decreasing.
        
        Scenario: p-values that would violate monotonicity without enforcement.
        Input: 0.01, 0.005, 0.002
        Sorted: 0.002 (Rank 1), 0.005 (Rank 2), 0.01 (Rank 3)
        
        Raw Holm:
          Rank 1: 3 * 0.002 = 0.006
          Rank 2: 2 * 0.005 = 0.010
          Rank 3: 1 * 0.01 = 0.010
        
        This example is already monotonic, so let's try a case where it's not:
        Input: 0.04, 0.01, 0.001
        Sorted: 0.001 (R1), 0.01 (R2), 0.04 (R3)
        
        Raw Holm:
          R1: 3 * 0.001 = 0.003
          R2: 2 * 0.01 = 0.02
          R3: 1 * 0.04 = 0.04
        
        Still monotonic. Let's try:
        Input: 0.001, 0.002, 0.003
        Sorted: 0.001, 0.002, 0.003
        R1: 3*0.001 = 0.003
        R2: 2*0.002 = 0.004
        R3: 1*0.003 = 0.003 -> Violation! Must be max(0.004, 0.003) = 0.004
        """
        p_values = [
            ("M1", 0.001),
            ("M2", 0.002),
            ("M3", 0.003)
        ]
        results = calculate_holm_bonferroni(p_values)
        
        # M1 (Rank 1)
        assert results[0].adjusted_p_value == pytest.approx(0.003)
        # M2 (Rank 2)
        assert results[1].adjusted_p_value == pytest.approx(0.004)
        # M3 (Rank 3) -> Should be 0.004 due to monotonicity, not 0.003
        assert results[2].adjusted_p_value == pytest.approx(0.004)
        
        # Verify monotonicity
        adj_values = [r.adjusted_p_value for r in results]
        assert adj_values == sorted(adj_values)

    def test_cap_at_one(self):
        """Test that adjusted p-values do not exceed 1.0."""
        p_values = [
            ("M1", 0.9),
            ("M2", 0.8),
            ("M3", 0.7)
        ]
        # Sorted: 0.7, 0.8, 0.9
        # R1 (0.7): 3 * 0.7 = 2.1 -> Cap at 1.0
        # R2 (0.8): 2 * 0.8 = 1.6 -> Cap at 1.0 (and monotonicity)
        # R3 (0.9): 1 * 0.9 = 0.9 -> Monotonicity forces 1.0
        
        results = calculate_holm_bonferroni(p_values)
        
        for r in results:
            assert r.adjusted_p_value <= 1.0
            assert r.adjusted_p_value >= 0.0

class TestHolmBonferroniIO:
    """Tests for loading and saving functions."""

    def test_load_p_values_flat_json(self):
        """Test loading from a flat JSON structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"SART": 0.03, "Ospan": 0.15}, f)
            temp_path = Path(f.name)

        try:
            p_values = load_p_values_from_json(temp_path)
            assert len(p_values) == 2
            assert ("SART", 0.03) in p_values
            assert ("Ospan", 0.15) in p_values
        finally:
            temp_path.unlink()

    def test_load_p_values_nested_json(self):
        """Test loading from a nested JSON structure."""
        data = {
            "results": [
                {"metric": "SART", "p_value": 0.03},
                {"metric": "Ospan", "p_value": 0.15}
            ]
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            p_values = load_p_values_from_json(temp_path)
            assert len(p_values) == 2
            assert ("SART", 0.03) in p_values
            assert ("Ospan", 0.15) in p_values
        finally:
            temp_path.unlink()

    def test_write_holm_results(self):
        """Test writing results to a JSON file."""
        results = [
            HolmBonferroniResult("M1", 0.03, 0.06, True, 1),
            HolmBonferroniResult("M2", 0.15, 0.30, False, 2)
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            write_holm_results(results, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert data["total_tests"] == 2
            assert data["significant_count"] == 1
            assert len(data["results"]) == 2

    def test_run_pipeline(self):
        """Test the full pipeline execution."""
        input_data = {"SART": 0.03, "Ospan": 0.15}
        
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.json"
            output_path = Path(tmpdir) / "output.json"
            
            with open(input_path, 'w') as f:
                json.dump(input_data, f)
            
            summary = run_holm_bonferroni_pipeline(input_path, output_path)
            
            assert output_path.exists()
            assert summary["total_tests"] == 2
            assert summary["significant_tests"] >= 0

class TestHolmBonferroniEdgeCases:
    """Tests for edge cases and error handling."""

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for missing input."""
        with pytest.raises(FileNotFoundError):
            load_p_values_from_json(Path("/nonexistent/path.json"))

    def test_invalid_json_structure(self):
        """Test handling of JSON with no valid p-values."""
        data = {"invalid": "structure"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="No valid p-values found"):
                load_p_values_from_json(temp_path)
        finally:
            temp_path.unlink()

    def test_p_value_greater_than_one(self):
        """Test behavior with p-values > 1 (should be capped)."""
        p_values = [("M1", 1.5)]
        results = calculate_holm_bonferroni(p_values)
        assert results[0].adjusted_p_value == 1.0

    def test_p_value_zero(self):
        """Test behavior with p-value = 0."""
        p_values = [("M1", 0.0)]
        results = calculate_holm_bonferroni(p_values)
        assert results[0].adjusted_p_value == 0.0
        assert results[0].is_significant is True