"""
Unit tests for Holm-Bonferroni correction logic.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path

from code.analysis.holm_bonferroni import (
    calculate_holm_bonferroni,
    HolmBonferroniResult,
    load_p_values_from_json,
    write_holm_results,
    run_holm_bonferroni_pipeline
)


class TestCalculateHolmBonferroni:
    """Tests for the core correction algorithm."""

    def test_empty_input(self):
        """Test behavior with empty list."""
        result = calculate_holm_bonferroni([])
        assert result == []

    def test_single_test(self):
        """Test with a single p-value. Correction factor should be 1."""
        p_values = [{"metric_name": "TestA", "p_value": 0.03}]
        result = calculate_holm_bonferroni(p_values)
        
        assert len(result) == 1
        assert result[0].metric_name == "TestA"
        assert result[0].raw_p_value == 0.03
        # Single test: 0.03 * 1 = 0.03
        assert result[0].corrected_p_value == 0.03
        assert result[0].rank == 1
        assert result[0].is_significant is True  # 0.03 < 0.05

    def test_two_tests_simple(self):
        """Test with two p-values."""
        p_values = [
            {"metric_name": "A", "p_value": 0.04},
            {"metric_name": "B", "p_value": 0.01}
        ]
        result = calculate_holm_bonferroni(p_values)
        
        # Sorted order: B (0.01), A (0.04)
        assert len(result) == 2
        
        # Rank 1: B
        # p_adj = 0.01 * (2 - 0) = 0.02
        b_res = next(r for r in result if r.metric_name == "B")
        assert b_res.rank == 1
        assert b_res.corrected_p_value == 0.02
        assert b_res.is_significant is True
        
        # Rank 2: A
        # p_adj = 0.04 * (2 - 1) = 0.04
        # Must be >= previous (0.02), which it is.
        a_res = next(r for r in result if r.metric_name == "A")
        assert a_res.rank == 2
        assert a_res.corrected_p_value == 0.04
        assert a_res.is_significant is True

    def test_monotonicity_enforcement(self):
        """Test that corrected p-values are non-decreasing."""
        # Create a case where naive multiplication would decrease
        # p1 = 0.01 (rank 1, factor 3) -> 0.03
        # p2 = 0.015 (rank 2, factor 2) -> 0.03
        # p3 = 0.014 (rank 3, factor 1) -> 0.014 (NAIVE: would be < 0.03)
        # But we sort first:
        # Sorted: 0.01, 0.014, 0.015
        # Rank 1 (0.01): 0.01 * 3 = 0.03
        # Rank 2 (0.014): 0.014 * 2 = 0.028 -> capped to 0.03 (monotonicity)
        # Rank 3 (0.015): 0.015 * 1 = 0.015 -> capped to 0.03
        
        p_values = [
            {"metric_name": "C", "p_value": 0.015},
            {"metric_name": "A", "p_value": 0.01},
            {"metric_name": "B", "p_value": 0.014}
        ]
        
        result = calculate_holm_bonferroni(p_values)
        
        # Check order
        assert result[0].metric_name == "A" # 0.01
        assert result[1].metric_name == "B" # 0.014
        assert result[2].metric_name == "C" # 0.015

        # Check monotonicity
        prev = 0.0
        for r in result:
            assert r.corrected_p_value >= prev, "Corrected p-values must be non-decreasing"
            prev = r.corrected_p_value

    def test_significance_threshold(self):
        """Test that significance is correctly determined against alpha."""
        p_values = [
            {"metric_name": "Sig", "p_value": 0.01},
            {"metric_name": "NonSig", "p_value": 0.06}
        ]
        result = calculate_holm_bonferroni(p_values, alpha=0.05)
        
        sig_res = next(r for r in result if r.metric_name == "Sig")
        non_sig_res = next(r for r in result if r.metric_name == "NonSig")
        
        # Sig: 0.01 * 2 = 0.02 < 0.05 -> True
        assert sig_res.is_significant is True
        # NonSig: 0.06 * 1 = 0.06 > 0.05 -> False
        assert non_sig_res.is_significant is False

    def test_p_value_clamping(self):
        """Test that corrected p-values do not exceed 1.0."""
        p_values = [
            {"metric_name": "HighP", "p_value": 0.9}
        ]
        # With m=1, factor=1 -> 0.9
        # Let's try m=2 where p=0.6
        p_values = [
            {"metric_name": "A", "p_value": 0.6},
            {"metric_name": "B", "p_value": 0.9}
        ]
        # Sorted: A(0.6), B(0.9)
        # A: 0.6 * 2 = 1.2 -> clamp to 1.0
        # B: 0.9 * 1 = 0.9 -> max(0.9, 1.0) = 1.0
        
        result = calculate_holm_bonferroni(p_values)
        
        a_res = next(r for r in result if r.metric_name == "A")
        b_res = next(r for r in result if r.metric_name == "B")
        
        assert a_res.corrected_p_value == 1.0
        assert b_res.corrected_p_value == 1.0


class TestLoadPValuesFromJson:
    """Tests for JSON loading."""

    def test_valid_json(self):
        """Test loading valid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"metric_name": "M1", "p_value": 0.05}], f)
            path = f.name

        try:
            data = load_p_values_from_json(path)
            assert len(data) == 1
            assert data[0]['metric_name'] == "M1"
            assert data[0]['p_value'] == 0.05
        finally:
            os.unlink(path)

    def test_missing_file(self):
        """Test error on missing file."""
        with pytest.raises(FileNotFoundError):
            load_p_values_from_json("/nonexistent/path.json")

    def test_invalid_structure(self):
        """Test handling of invalid JSON structure."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"not": "a list"}, f)
            path = f.name

        try:
            with pytest.raises(ValueError):
                load_p_values_from_json(path)
        finally:
            os.unlink(path)

    def test_missing_keys(self):
        """Test handling of items missing keys."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"metric_name": "M1"}, {"p_value": 0.1}], f)
            path = f.name

        try:
            data = load_p_values_from_json(path)
            # Should return empty list or filtered list
            assert len(data) == 0
        finally:
            os.unlink(path)


class TestWriteHolmResults:
    """Tests for writing results."""

    def test_write_and_read(self):
        """Test writing results and reading them back."""
        results = [
            HolmBonferroniResult("M1", 0.01, 0.02, True, 1),
            HolmBonferroniResult("M2", 0.04, 0.04, True, 2)
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            path = f.name

        try:
            write_holm_results(results, path)
            
            with open(path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]['metric_name'] == "M1"
            assert data[0]['corrected_p_value'] == 0.02
            assert data[1]['metric_name'] == "M2"
        finally:
            os.unlink(path)


class TestRunHolmBonferroniPipeline:
    """Integration tests for the pipeline function."""

    def test_pipeline_end_to_end(self):
        """Test the full pipeline from input file to output file."""
        input_data = [
            {"metric_name": "SART", "p_value": 0.02},
            {"metric_name": "Ospan", "p_value": 0.04},
            {"metric_name": "PSS", "p_value": 0.06}
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='_input.json', delete=False) as f_in:
            json.dump(input_data, f_in)
            input_path = f_in.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='_output.json', delete=False) as f_out:
            output_path = f_out.name

        try:
            results = run_holm_bonferroni_pipeline(input_path, output_path, alpha=0.05)
            
            assert len(results) == 3
            
            # Verify file exists
            assert os.path.exists(output_path)
            
            # Verify content
            with open(output_path, 'r') as f:
                saved = json.load(f)
            
            assert len(saved) == 3
            # Check monotonicity in saved file
            prev = 0.0
            for item in saved:
                assert item['corrected_p_value'] >= prev
                prev = item['corrected_p_value']
        finally:
            os.unlink(input_path)
            os.unlink(output_path)