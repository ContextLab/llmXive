"""
Unit tests for the deduplication module.

Tests verify that:
1. Formula normalization works correctly
2. Deduplication retains the primary source (Science Advances)
3. Statistics are calculated correctly
"""
import pytest
from utils.dedup import normalize_formula, deduplicate_compositions, get_deduplication_stats

class TestNormalizeFormula:
    """Tests for formula normalization."""
    
    def test_simple_formula(self):
        """Test normalization of a simple formula."""
        assert normalize_formula("Fe2Ni3") == "Fe2Ni3"
    
    def test_sorted_elements(self):
        """Test that elements are sorted alphabetically."""
        assert normalize_formula("Ni3Fe2") == "Fe2Ni3"
    
    def test_fractions(self):
        """Test normalization of fractional formulas."""
        # Fe0.5Ni0.5 should normalize to FeNi
        assert normalize_formula("Fe0.5Ni0.5") == "FeNi"
    
    def test_empty_string(self):
        """Test handling of empty string."""
        assert normalize_formula("") == ""
    
    def test_whitespace(self):
        """Test that whitespace is removed."""
        assert normalize_formula(" Fe2 Ni3 ") == "Fe2Ni3"
    
    def test_case_insensitive(self):
        """Test that case is normalized."""
        assert normalize_formula("fe2ni3") == "Fe2Ni3"

class TestDeduplicateCompositions:
    """Tests for composition deduplication."""
    
    def test_no_duplicates(self):
        """Test that unique compositions are retained."""
        compositions = [
            {"formula": "Fe2Ni3", "source": "Science Advances", "value": 1},
            {"formula": "Fe3Ni4", "source": "Materials Project", "value": 2}
        ]
        result = deduplicate_compositions(compositions)
        assert len(result) == 2
    
    def test_duplicate_retains_primary_source(self):
        """Test that Science Advances is retained over other sources."""
        compositions = [
            {"formula": "Fe2Ni3", "source": "Materials Project", "value": 1},
            {"formula": "Fe2Ni3", "source": "Science Advances", "value": 2}
        ]
        result = deduplicate_compositions(compositions)
        assert len(result) == 1
        assert result[0]["source"] == "Science Advances"
        assert result[0]["value"] == 2
    
    def test_duplicate_retains_primary_source_reverse_order(self):
        """Test that Science Advances is retained even when listed second."""
        compositions = [
            {"formula": "Fe2Ni3", "source": "Science Advances", "value": 2},
            {"formula": "Fe2Ni3", "source": "Materials Project", "value": 1}
        ]
        result = deduplicate_compositions(compositions)
        assert len(result) == 1
        assert result[0]["source"] == "Science Advances"
    
    def test_fractional_formula_duplicates(self):
        """Test deduplication with fractional formulas that normalize to same formula."""
        compositions = [
            {"formula": "Fe0.5Ni0.5", "source": "Materials Project", "value": 1},
            {"formula": "FeNi", "source": "Science Advances", "value": 2}
        ]
        result = deduplicate_compositions(compositions)
        assert len(result) == 1
        assert result[0]["source"] == "Science Advances"
    
    def test_empty_list(self):
        """Test handling of empty list."""
        result = deduplicate_compositions([])
        assert result == []
    
    def test_multiple_groups(self):
        """Test deduplication with multiple formula groups."""
        compositions = [
            {"formula": "Fe2Ni3", "source": "Science Advances", "value": 1},
            {"formula": "Fe2Ni3", "source": "Materials Project", "value": 2},
            {"formula": "Co3Ni4", "source": "Materials Project", "value": 3},
            {"formula": "Co3Ni4", "source": "Science Advances", "value": 4}
        ]
        result = deduplicate_compositions(compositions)
        assert len(result) == 2
        # Both should be from Science Advances
        assert all(c["source"] == "Science Advances" for c in result)

class TestGetDeduplicationStats:
    """Tests for deduplication statistics."""
    
    def test_stats_no_duplicates(self):
        """Test stats when no duplicates exist."""
        original = [
            {"formula": "Fe2Ni3", "source": "Science Advances"},
            {"formula": "Co3Ni4", "source": "Materials Project"}
        ]
        deduplicated = [
            {"formula": "Fe2Ni3", "source": "Science Advances"},
            {"formula": "Co3Ni4", "source": "Materials Project"}
        ]
        stats = get_deduplication_stats(original, deduplicated)
        assert stats["original_count"] == 2
        assert stats["deduplicated_count"] == 2
        assert stats["duplicates_removed"] == 0
    
    def test_stats_with_duplicates(self):
        """Test stats when duplicates exist."""
        original = [
            {"formula": "Fe2Ni3", "source": "Science Advances"},
            {"formula": "Fe2Ni3", "source": "Materials Project"},
            {"formula": "Co3Ni4", "source": "Science Advances"}
        ]
        deduplicated = [
            {"formula": "Fe2Ni3", "source": "Science Advances"},
            {"formula": "Co3Ni4", "source": "Science Advances"}
        ]
        stats = get_deduplication_stats(original, deduplicated)
        assert stats["original_count"] == 3
        assert stats["deduplicated_count"] == 2
        assert stats["duplicates_removed"] == 1
        assert stats["formulas_with_duplicates"] == 1
    
    def test_stats_empty(self):
        """Test stats with empty lists."""
        stats = get_deduplication_stats([], [])
        assert stats["original_count"] == 0
        assert stats["deduplicated_count"] == 0
        assert stats["duplicates_removed"] == 0
        assert stats["deduplication_rate"] == 0.0