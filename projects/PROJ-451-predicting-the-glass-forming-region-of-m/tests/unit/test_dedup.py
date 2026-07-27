"""
Unit tests for utils/dedup.py
Verifies deduplication logic and source retention.
Note: This is a TDD 'write test' task; tests are designed to pass once utils/dedup.py is correctly implemented.
"""
import pytest
from utils.dedup import normalize_formula, get_source_priority, deduplicate_compositions, get_deduplication_stats
import pandas as pd

class TestNormalizeFormula:
    def test_normalize_simple_element(self):
        """Test normalization of a single element."""
        assert normalize_formula("Fe") == "Fe"

    def test_normalize_compound(self):
        """Test normalization of a compound formula."""
        # H2O should normalize to H2O (sorted keys, but H comes before O)
        assert normalize_formula("H2O") == "H2O"
        assert normalize_formula("OH2") == "H2O"

    def test_normalize_with_fractions(self):
        """Test normalization with fractional subscripts."""
        # Normalize should handle standard chemical formulas
        assert normalize_formula("NaCl") == "NaCl"
        assert normalize_formula("ClNa") == "NaCl"

    def test_normalize_case_sensitivity(self):
        """Ensure element symbols are handled case-insensitively for sorting but preserved correctly."""
        # Standard chemical notation: Capital first, lowercase second
        assert normalize_formula("fe") == "Fe" # Should ideally handle case, but standard is Capitalized
        # If input is already valid, it should remain valid
        assert normalize_formula("Fe") == "Fe"

    def test_normalize_complex_formula(self):
        """Test complex alloy formula normalization."""
        # Example: Zr50Cu40Ni10
        assert normalize_formula("Cu40Zr50Ni10") == "Cu40Ni10Zr50"

class TestGetSourcePriority:
    def test_materials_project_priority(self):
        """Materials Project should have highest priority."""
        assert get_source_priority("materials_project") > get_source_priority("zenodo")
        assert get_source_priority("materials_project") > get_source_priority("synthetic")

    def test_zenodo_priority(self):
        """Zenodo should have higher priority than synthetic."""
        assert get_source_priority("zenodo") > get_source_priority("synthetic")

    def test_unknown_source(self):
        """Unknown sources should have lowest priority."""
        assert get_source_priority("unknown") == 0
        assert get_source_priority("synthetic") > 0

class TestDeduplicateCompositions:
    def test_no_duplicates(self):
        """Test dataset with no duplicates."""
        data = [
            {"formula": "Fe", "phase": "amorphous", "source": "zenodo"},
            {"formula": "Cu", "phase": "crystalline", "source": "materials_project"},
        ]
        df = pd.DataFrame(data)
        result = deduplicate_compositions(df)
        assert len(result) == 2

    def test_simple_duplicate(self):
        """Test dataset with one duplicate formula from different sources."""
        data = [
            {"formula": "Fe", "phase": "amorphous", "source": "zenodo"},
            {"formula": "Fe", "phase": "crystalline", "source": "materials_project"},
        ]
        df = pd.DataFrame(data)
        result = deduplicate_compositions(df)
        # Should keep only one, preferably from materials_project
        assert len(result) == 1
        assert result.iloc[0]["source"] == "materials_project"

    def test_multiple_duplicates_same_source(self):
        """Test dataset with duplicates from the same source."""
        data = [
            {"formula": "Fe", "phase": "amorphous", "source": "zenodo"},
            {"formula": "Fe", "phase": "crystalline", "source": "zenodo"},
        ]
        df = pd.DataFrame(data)
        result = deduplicate_compositions(df)
        assert len(result) == 1

    def test_formula_ordering(self):
        """Test that formula order doesn't affect deduplication."""
        data = [
            {"formula": "CuZr", "phase": "amorphous", "source": "zenodo"},
            {"formula": "ZrCu", "phase": "crystalline", "source": "materials_project"},
        ]
        df = pd.DataFrame(data)
        result = deduplicate_compositions(df)
        assert len(result) == 1
        # Should prefer materials_project
        assert result.iloc[0]["source"] == "materials_project"

    def test_source_retention(self):
        """Verify that the highest priority source is retained."""
        data = [
            {"formula": "Ni", "phase": "amorphous", "source": "synthetic"},
            {"formula": "Ni", "phase": "crystalline", "source": "zenodo"},
            {"formula": "Ni", "phase": "crystalline", "source": "materials_project"},
        ]
        df = pd.DataFrame(data)
        result = deduplicate_compositions(df)
        assert len(result) == 1
        assert result.iloc[0]["source"] == "materials_project"

    def test_empty_dataframe(self):
        """Test deduplication on an empty dataframe."""
        df = pd.DataFrame(columns=["formula", "phase", "source"])
        result = deduplicate_compositions(df)
        assert len(result) == 0

class TestGetDeduplicationStats:
    def test_stats_calculation(self):
        """Test that stats are calculated correctly."""
        data = [
            {"formula": "Fe", "phase": "amorphous", "source": "zenodo"},
            {"formula": "Fe", "phase": "crystalline", "source": "materials_project"},
            {"formula": "Cu", "phase": "crystalline", "source": "materials_project"},
        ]
        df = pd.DataFrame(data)
        result = deduplicate_compositions(df)
        stats = get_deduplication_stats(df, result)

        assert "original_count" in stats
        assert "deduplicated_count" in stats
        assert "removed_count" in stats
        assert stats["original_count"] == 3
        assert stats["deduplicated_count"] == 2
        assert stats["removed_count"] == 1

    def test_stats_no_duplicates(self):
        """Test stats when no duplicates exist."""
        data = [
            {"formula": "Fe", "phase": "amorphous", "source": "zenodo"},
            {"formula": "Cu", "phase": "crystalline", "source": "materials_project"},
        ]
        df = pd.DataFrame(data)
        result = deduplicate_compositions(df)
        stats = get_deduplication_stats(df, result)

        assert stats["removed_count"] == 0