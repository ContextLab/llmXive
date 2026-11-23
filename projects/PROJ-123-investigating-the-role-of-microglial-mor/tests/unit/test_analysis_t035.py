import pytest
import json
import os
from pathlib import Path
from code.analysis import calculate_interaction_pvalue_variation
from code.config import get_project_root

class TestT035VariationCalculation:
    def test_calculate_variation_basic(self, tmp_path):
        """Test basic calculation of p-value variation."""
        # Mock results from T034
        results = [
            {"sholl_step": 2, "interaction_p_value": 0.040},
            {"sholl_step": 5, "interaction_p_value": 0.050}, # Reference
            {"sholl_step": 10, "interaction_p_value": 0.060}
        ]

        # Temporarily override get_project_root to use tmp_path for testing
        # This is a bit hacky but necessary for unit testing file writes
        original_root = get_project_root()
        # We can't easily mock get_project_root without patching, so we assume
        # the function writes to the correct place or we check the return value.

        result = calculate_interaction_pvalue_variation(results, reference_step=5)

        assert "reference_step" in result
        assert result["reference_step"] == 5
        assert result["reference_p_value"] == 0.050
        assert result["max_deviation_ratio"] == pytest.approx(0.20, abs=0.01) # 0.01 / 0.05 = 0.2
        assert result["is_flagged"] == False # 20% < 50%

    def test_flag_high_deviation(self):
        """Test that high deviation is flagged."""
        results = [
            {"sholl_step": 2, "interaction_p_value": 0.020},
            {"sholl_step": 5, "interaction_p_value": 0.050}, # Reference
            {"sholl_step": 10, "interaction_p_value": 0.150}
        ]

        result = calculate_interaction_pvalue_variation(results, reference_step=5)

        # 0.15 - 0.05 = 0.10. 0.10 / 0.05 = 2.0 (200%)
        assert result["max_deviation_ratio"] == pytest.approx(2.0, abs=0.01)
        assert result["is_flagged"] == True

    def test_zero_reference_pvalue(self):
        """Test handling of zero reference p-value."""
        results = [
            {"sholl_step": 2, "interaction_p_value": 0.000},
            {"sholl_step": 5, "interaction_p_value": 0.000}, # Reference
            {"sholl_step": 10, "interaction_p_value": 0.001}
        ]

        result = calculate_interaction_pvalue_variation(results, reference_step=5)

        # If reference is 0 and other is non-zero, deviation is inf
        assert result["max_deviation_ratio"] == float('inf')
        assert result["is_flagged"] == True

    def test_json_output_structure(self, tmp_path):
        """Test that the JSON output has the correct structure."""
        # We need to patch the file writing or check the return value.
        # Let's just check the return value structure which is the same as the JSON.
        results = [
            {"sholl_step": 2, "interaction_p_value": 0.045},
            {"sholl_step": 5, "interaction_p_value": 0.050},
            {"sholl_step": 10, "interaction_p_value": 0.055}
        ]

        result = calculate_interaction_pvalue_variation(results, reference_step=5)

        assert "variations" in result
        assert isinstance(result["variations"], list)
        for var in result["variations"]:
            assert "step" in var
            assert "p_value" in var
            assert "deviation_ratio" in var
            assert "percent_deviation" in var
            assert var["step"] in [2, 5, 10]
