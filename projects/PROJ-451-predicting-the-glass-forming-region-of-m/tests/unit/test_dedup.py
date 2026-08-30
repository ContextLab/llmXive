"""
Unit tests for the deduplication utilities in utils/dedup.py.
"""
import pytest
from utils.dedup import normalize_formula, get_source_priority, deduplicate_compositions, get_deduplication_stats


class TestNormalizeFormula:
    """Tests for the normalize_formula function."""

    def test_simple_formula(self):
        """Test normalization of a simple formula."""
        assert normalize_formula("Fe2O3") == "Fe2O3"

    def test_case_insensitive(self):
        """Test that case is normalized to uppercase."""
        assert normalize_formula("fe2o3") == "Fe2O3"

    def test_whitespace_handling(self):
        """Test that whitespace is removed."""
        assert normalize_formula("Fe 2 O 3") == "Fe2O3"

    def test_reordering(self):
        """Test that elements are sorted alphabetically."""
        # Fe2O3 -> O3Fe2 -> sorted: Fe2O3 (already sorted)
        # Let's try a non-sorted one: O3Fe2
        assert normalize_formula("O3Fe2") == "Fe2O3"

    def test_equimolar_normalization(self):
        """Test normalization of equimolar ratios."""
        # Fe20Co20Ni20 -> all counts are 20, ratio is 1:1:1
        # Should result in just the element symbols
        result = normalize_formula("Fe20Co20Ni20")
        # Elements should be Co, Fe, Ni in alphabetical order
        assert "Co" in result and "Fe" in result and "Ni" in result
        # Check no numbers if equimolar
        assert result == "CoFeNi"

    def test_empty_string(self):
        """Test handling of empty string."""
        assert normalize_formula("") == ""

    def test_none_input(self):
        """Test handling of None input."""
        assert normalize_formula(None) is None

    def test_complex_oxide(self):
        """Test a complex oxide formula."""
        # La2CuO4 -> La2CuO4 (already sorted? La, Cu, O -> Cu, La, O)
        result = normalize_formula("La2CuO4")
        # Expected: CuLa2O4 (sorted: Cu, La, O)
        assert result == "CuLa2O4"

    def test_decimal_counts(self):
        """Test handling of decimal counts (if supported)."""
        # This might not be common, but test robustness
        # Fe1.5O3 -> ratio 1.5:3 -> 1:2 -> FeO2
        result = normalize_formula("Fe1.5O3")
        # 1.5 and 3 -> divide by 1.5 -> 1 and 2
        assert result == "FeO2"


class TestGetSourcePriority:
    """Tests for the get_source_priority function."""

    def test_materials_project_high_priority(self):
        """Test that Materials Project gets high priority."""
        assert get_source_priority("Materials Project") == 3
        assert get_source_priority("mp-123") == 3

    def test_zenodo_medium_priority(self):
        """Test that Zenodo gets medium priority."""
        assert get_source_priority("Zenodo") == 2

    def test_synthetic_low_priority(self):
        """Test that synthetic data gets low priority."""
        assert get_source_priority("Synthetic") == 1
        assert get_source_priority("Generated") == 1

    def test_unknown_source(self):
        """Test that unknown sources get lowest priority."""
        assert get_source_priority("Unknown") == 0
        assert get_source_priority("") == 0

    def test_case_insensitive(self):
        """Test that priority is case-insensitive."""
        assert get_source_priority("materials project") == 3
        assert get_source_priority("ZENODO") == 2


class TestDeduplicateCompositions:
    """Tests for the deduplicate_compositions function."""

    def test_no_duplicates(self):
        """Test with no duplicates."""
        data = [
            {"composition": "Fe2O3", "source": "Zenodo"},
            {"composition": "CuO", "source": "Materials Project"}
        ]
        result, stats = deduplicate_compositions(data)
        assert len(result) == 2
        assert stats["duplicates_removed"] == 0

    def test_exact_duplicates_different_source(self):
        """Test with exact duplicates from different sources."""
        data = [
            {"composition": "Fe2O3", "source": "Zenodo"},
            {"composition": "Fe2O3", "source": "Materials Project"}
        ]
        result, stats = deduplicate_compositions(data)
        assert len(result) == 1
        assert result[0]["source"] == "Materials Project"  # Higher priority
        assert stats["duplicates_removed"] == 1

    def test_equimolar_duplicates(self):
        """Test with equimolar duplicates (different representations)."""
        data = [
            {"composition": "Fe20Co20Ni20", "source": "Synthetic"},
            {"composition": "CoFeNi", "source": "Materials Project"},
            {"composition": "NiCoFe", "source": "Zenodo"}
        ]
        result, stats = deduplicate_compositions(data)
        assert len(result) == 1
        assert result[0]["source"] == "Materials Project"
        assert stats["duplicates_removed"] == 2

    def test_empty_input(self):
        """Test with empty input list."""
        result, stats = deduplicate_compositions([])
        assert len(result) == 0
        assert stats["total_input"] == 0
        assert stats["total_output"] == 0

    def test_missing_formula(self):
        """Test with records missing formula."""
        data = [
            {"source": "Zenodo"},
            {"composition": "Fe2O3", "source": "Materials Project"}
        ]
        result, stats = deduplicate_compositions(data)
        # Should skip the one without formula
        assert len(result) == 1
        assert stats["total_input"] == 1  # Only one valid record processed

    def test_custom_keys(self):
        """Test with custom formula and source keys."""
        data = [
            {"formula": "Fe2O3", "origin": "Zenodo"},
            {"formula": "Fe2O3", "origin": "Materials Project"}
        ]
        result, stats = deduplicate_compositions(
            data,
            formula_key="formula",
            source_key="origin"
        )
        assert len(result) == 1
        assert result[0]["origin"] == "Materials Project"

    def test_stats_structure(self):
        """Test that stats dictionary has expected keys."""
        data = [
            {"composition": "Fe2O3", "source": "Zenodo"},
            {"composition": "Fe2O3", "source": "Materials Project"}
        ]
        _, stats = deduplicate_compositions(data)
        assert "total_input" in stats
        assert "total_output" in stats
        assert "duplicates_removed" in stats
        assert "by_source" in stats


class TestGetDeduplicationStats:
    """Tests for the get_deduplication_stats function."""

    def test_basic_stats(self):
        """Test basic stats calculation."""
        stats = get_deduplication_stats(
            input_count=100,
            output_count=80,
            removed_by_source={"Zenodo": 10, "Synthetic": 10}
        )
        assert stats["total_input"] == 100
        assert stats["total_output"] == 80
        assert stats["duplicates_removed"] == 20
        assert stats["removal_rate_percent"] == 20.0
        assert stats["removed_by_source"]["Zenodo"] == 10

    def test_zero_input(self):
        """Test with zero input count."""
        stats = get_deduplication_stats(0, 0)
        assert stats["removal_rate_percent"] == 0.0

    def test_no_removed_by_source(self):
        """Test with None removed_by_source."""
        stats = get_deduplication_stats(100, 90, None)
        assert stats["removed_by_source"] == {}