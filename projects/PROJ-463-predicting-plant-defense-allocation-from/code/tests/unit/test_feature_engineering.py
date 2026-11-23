"""
Unit tests for feature engineering exclusion logic.
"""

import pytest
from src.analysis.feature_engineering import get_trait_synthesis_exclusion_list, TRAIT_SYNTHESIS_GENES


class TestFeatureEngineering:
    """Tests for trait synthesis gene exclusion."""

    def test_excludes_known_trait_genes(self):
        """Verify that known trait-synthesis genes are excluded."""
        input_genes = [
            "ACT2",
            "CYP79D16",
            "GAPDH",
            "CYP71A1",
            "UBQ10",
            "CYP83A1",
            "CYP96A3",
        ]
        expected = ["ACT2", "GAPDH", "UBQ10"]
        result = get_trait_synthesis_exclusion_list(input_genes)
        assert result == expected

    def test_excludes_all_cyp71a_series(self):
        """Verify all CYP71A1-32 are excluded."""
        input_genes = [f"CYP71A{i}" for i in range(1, 33)]
        result = get_trait_synthesis_exclusion_list(input_genes)
        assert len(result) == 0

    def test_excludes_specific_cyp_families(self):
        """Verify specific CYP families are excluded."""
        input_genes = [
            "CYP79D15", "CYP79D17",
            "CYP83B1",
            "CYP96A1", "CYP96A2",
        ]
        result = get_trait_synthesis_exclusion_list(input_genes)
        assert len(result) == 0

    def test_preserves_non_trait_genes(self):
        """Verify non-trait genes are preserved."""
        input_genes = [
            "ACT2", "ACT7", "GAPDH", "UBQ10", "EF1a",
            "TUB6", "SAND", "PP2A",
            "ARABIDOL", "LIGNIN_SYNTHASE",
        ]
        result = get_trait_synthesis_exclusion_list(input_genes)
        assert len(result) == len(input_genes)
        assert set(result) == set(input_genes)

    def test_empty_input(self):
        """Verify empty list handling."""
        result = get_trait_synthesis_exclusion_list([])
        assert result == []

    def test_no_trait_genes_in_input(self):
        """Verify list without trait genes is unchanged."""
        input_genes = ["ACT2", "GAPDH", "UBQ10"]
        result = get_trait_synthesis_exclusion_list(input_genes)
        assert result == input_genes

    def test_duplicates_handling(self):
        """Verify duplicate handling (duplicates are preserved in order)."""
        input_genes = ["CYP79D16", "ACT2", "CYP79D16", "GAPDH"]
        result = get_trait_synthesis_exclusion_list(input_genes)
        assert result == ["ACT2", "GAPDH"]

    def test_case_sensitivity(self):
        """Verify gene matching is case-sensitive (as per standard)."""
        input_genes = ["cyp79d16", "CYP79D16", "Act2"]
        # Lowercase 'cyp79d16' should NOT match the uppercase set key
        result = get_trait_synthesis_exclusion_list(input_genes)
        # Only the uppercase one should be removed
        assert result == ["cyp79d16", "Act2"]

    def test_trait_synthesis_set_definition(self):
        """Verify the static set contains the expected minimum genes."""
        assert "CYP79D16" in TRAIT_SYNTHESIS_GENES
        assert "CYP71A1" in TRAIT_SYNTHESIS_GENES
        assert "CYP71A32" in TRAIT_SYNTHESIS_GENES
        assert "CYP83A1" in TRAIT_SYNTHESIS_GENES
        assert "CYP96A3" in TRAIT_SYNTHESIS_GENES