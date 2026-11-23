"""
Unit tests for the deduplication utilities.
"""

import pytest
from code.utils.dedup import (
    normalize_formula,
    get_source_priority,
    deduplicate_compositions,
    get_deduplication_stats
)


class TestNormalizeFormula:
    """Tests for formula normalization to Hill system."""

    def test_simple_organic(self):
        """Test organic compound with C and H."""
        assert normalize_formula("C2H6") == "C2H6"
        assert normalize_formula("CH4") == "CH4"
        assert normalize_formula("C6H12O6") == "C6H12O6"

    def test_organic_with_other_elements(self):
        """Test organic compound with C, H, and other elements."""
        # C first, H second, then alphabetical
        assert normalize_formula("C2H5OH") == "C2H6O"
        assert normalize_formula("CH3COOH") == "C2H4O2"

    def test_inorganic_no_carbon(self):
        """Test inorganic compounds without carbon."""
        # Elements sorted alphabetically
        assert normalize_formula("H2O") == "H2O"
        assert normalize_formula("Fe3O4") == "Fe3O4"
        assert normalize_formula("NaCl") == "ClNa"  # C not present, alphabetical
        assert normalize_formula("H2SO4") == "H2O4S"  # H, O, S alphabetical

    def test_no_count(self):
        """Test formula without explicit counts (defaults to 1)."""
        assert normalize_formula("H2O") == "H2O"
        assert normalize_formula("CO") == "CO"

    def test_empty_formula(self):
        """Test empty or None formula."""
        assert normalize_formula("") == ""
        assert normalize_formula(None) is None

    def test_case_sensitivity(self):
        """Test that element symbols are case-sensitive."""
        # Element symbols should be preserved as-is
        assert normalize_formula("Fe") == "Fe"
        assert normalize_formula("Cu") == "Cu"

    def test_complex_formula(self):
        """Test complex multi-element formula."""
        # C, H, then alphabetical
        result = normalize_formula("C2H5NO2")
        assert result.startswith("C")
        assert "H" in result


class TestGetSourcePriority:
    """Tests for source priority assignment."""

    def test_science_advances(self):
        """Test Science Advances gets highest priority."""
        assert get_source_priority("Science Advances") == 1
        assert get_source_priority("sciadv.aaq1566") == 1
        assert get_source_priority("10.1126/sciadv.aaq1566") == 1

    def test_materials_project(self):
        """Test Materials Project gets second priority."""
        assert get_source_priority("Materials Project") == 2
        assert get_source_priority("mp-1234") == 2

    def test_synthetic(self):
        """Test synthetic data gets third priority."""
        assert get_source_priority("synthetic") == 3
        assert get_source_priority("generated") == 3

    def test_unknown(self):
        """Test unknown sources get lowest priority."""
        assert get_source_priority("unknown") == 4
        assert get_source_priority(None) == 4

    def test_case_insensitive(self):
        """Test that priority is case-insensitive."""
        assert get_source_priority("SCIENCE ADVANCES") == 1
        assert get_source_priority("materials project") == 2


class TestDeduplicateCompositions:
    """Tests for the main deduplication function."""

    def test_empty_list(self):
        """Test with empty input."""
        result, stats = deduplicate_compositions([])
        assert result == []
        assert stats['total'] == 0
        assert stats['unique'] == 0
        assert stats['duplicates_removed'] == 0

    def test_no_duplicates(self):
        """Test with no duplicates."""
        data = [
            {'formula': 'H2O', 'source': 'Science Advances'},
            {'formula': 'Fe3O4', 'source': 'Materials Project'},
        ]
        result, stats = deduplicate_compositions(data)
        assert len(result) == 2
        assert stats['duplicates_removed'] == 0

    def test_duplicates_removed(self):
        """Test that duplicates are correctly identified and removed."""
        data = [
            {'formula': 'H2O', 'source': 'Science Advances', 'id': 1},
            {'formula': 'H2O', 'source': 'Materials Project', 'id': 2},
            {'formula': 'Fe3O4', 'source': 'Science Advances', 'id': 3},
        ]
        result, stats = deduplicate_compositions(data)
        assert len(result) == 2
        assert stats['duplicates_removed'] == 1
        # Should keep Science Advances for H2O
        h2o_record = [r for r in result if r['formula'] == 'H2O'][0]
        assert h2o_record['source'] == 'Science Advances'

    def test_hill_normalization_removes_duplicates(self):
        """Test that Hill normalization correctly identifies duplicates."""
        # C2H6 and CH3CH3 should be the same after normalization
        data = [
            {'formula': 'C2H6', 'source': 'Science Advances', 'id': 1},
            {'formula': 'CH3CH3', 'source': 'Materials Project', 'id': 2},
        ]
        result, stats = deduplicate_compositions(data)
        assert len(result) == 1
        assert stats['duplicates_removed'] == 1
        # Should keep Science Advances
        assert result[0]['source'] == 'Science Advances'

    def test_invalid_input(self):
        """Test with invalid input type."""
        with pytest.raises(ValueError):
            deduplicate_compositions("not a list")

    def test_non_dict_records(self):
        """Test handling of non-dict records."""
        data = [
            {'formula': 'H2O', 'source': 'Science Advances'},
            "not a dict",
            {'formula': 'Fe3O4', 'source': 'Materials Project'},
        ]
        result, stats = deduplicate_compositions(data)
        # Should skip the non-dict record
        assert len(result) == 2

    def test_missing_formula(self):
        """Test handling of records with missing formula."""
        data = [
            {'source': 'Science Advances'},
            {'formula': 'H2O', 'source': 'Materials Project'},
        ]
        result, stats = deduplicate_compositions(data)
        # Should skip the record with missing formula
        assert len(result) == 1


class TestGetDeduplicationStats:
    """Tests for statistics generation."""

    def test_normal_case(self):
        """Test normal statistics calculation."""
        stats = get_deduplication_stats(100, 80)
        assert stats['original_count'] == 100
        assert stats['deduplicated_count'] == 80
        assert stats['duplicates_removed'] == 20
        assert stats['reduction_percentage'] == 20.0

    def test_no_duplicates(self):
        """Test when no duplicates are removed."""
        stats = get_deduplication_stats(100, 100)
        assert stats['duplicates_removed'] == 0
        assert stats['reduction_percentage'] == 0.0

    def test_all_duplicates(self):
        """Test when all records are duplicates."""
        stats = get_deduplication_stats(100, 10)
        assert stats['duplicates_removed'] == 90
        assert stats['reduction_percentage'] == 90.0

    def test_empty_input(self):
        """Test with zero original count."""
        stats = get_deduplication_stats(0, 0)
        assert stats['original_count'] == 0
        assert stats['deduplicated_count'] == 0
        assert stats['duplicates_removed'] == 0
        assert stats['reduction_percentage'] == 0.0
