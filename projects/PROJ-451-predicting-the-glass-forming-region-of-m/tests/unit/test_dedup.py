"""
Unit tests for utils/dedup.py
"""
import pytest
from code.utils.dedup import (
    normalize_formula,
    get_source_priority,
    deduplicate_compositions,
    get_deduplication_stats
)


class TestNormalizeFormula:
    """Tests for normalize_formula function"""
    
    def test_simple_integer_counts(self):
        """Test normalization of formula with integer counts"""
        result = normalize_formula("Zr50Cu40Al10")
        # Should be normalized to fractions: Zr0.5, Cu0.4, Al0.1
        assert "Zr0.5" in result
        assert "Cu0.4" in result
        assert "Al0.1" in result
        # Check alphabetical ordering
        assert result.index("Al") < result.index("Cu") < result.index("Zr")
    
    def test_decimal_counts(self):
        """Test normalization of formula with decimal counts"""
        result = normalize_formula("Zr0.5Cu0.4Al0.1")
        assert "Zr0.5" in result
        assert "Cu0.4" in result
        assert "Al0.1" in result
    
    def test_normalization_to_sum_one(self):
        """Test that different representations of same composition normalize to same result"""
        result1 = normalize_formula("Zr50Cu40Al10")
        result2 = normalize_formula("Zr0.5Cu0.4Al0.1")
        result3 = normalize_formula("Zr5Cu4Al1")
        assert result1 == result2 == result3
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly handled"""
        result1 = normalize_formula("Zr50Cu40Al10")
        result2 = normalize_formula(" Zr 50 Cu 40 Al 10 ")
        assert result1 == result2
    
    def test_invalid_input_empty(self):
        """Test that empty input raises ValueError"""
        with pytest.raises(ValueError):
            normalize_formula("")
    
    def test_invalid_input_none(self):
        """Test that None input raises ValueError"""
        with pytest.raises(ValueError):
            normalize_formula(None)
    
    def test_invalid_formula(self):
        """Test that unparseable formula raises ValueError"""
        with pytest.raises(ValueError):
            normalize_formula("InvalidFormula")
    
    def test_equal_parts_simple(self):
        """Test formula without explicit counts (equal parts assumption)"""
        result = normalize_formula("ZrCu")
        # Should normalize to Zr0.5Cu0.5
        assert "Zr0.5" in result
        assert "Cu0.5" in result


class TestGetSourcePriority:
    """Tests for get_source_priority function"""
    
    def test_materials_project_priority(self):
        """Test Materials Project has highest priority"""
        assert get_source_priority("Materials Project") == 3
        assert get_source_priority("mp-12345") == 3
    
    def test_zenodo_priority(self):
        """Test Zenodo has second priority"""
        assert get_source_priority("Zenodo") == 2
        assert get_source_priority("Science Advances") == 2
    
    def test_synthetic_priority(self):
        """Test Synthetic has third priority"""
        assert get_source_priority("synthetic") == 1
    
    def test_unknown_priority(self):
        """Test unknown source has lowest priority"""
        assert get_source_priority("unknown") == 0
        assert get_source_priority(None) == 0
    
    def test_case_insensitivity(self):
        """Test that priority is case-insensitive"""
        assert get_source_priority("MATERIALS PROJECT") == 3
        assert get_source_priority("materials project") == 3


class TestDeduplicateCompositions:
    """Tests for deduplicate_compositions function"""
    
    def test_no_duplicates(self):
        """Test deduplication with no duplicates"""
        compositions = [
            {"composition": "Zr50Cu40Al10", "source": "Zenodo"},
            {"composition": "Cu50Zr50", "source": "Materials Project"}
        ]
        result, stats = deduplicate_compositions(compositions)
        assert len(result) == 2
        assert stats["duplicates_removed"] == 0
        assert stats["duplicate_groups"] == 0
    
    def test_exact_duplicates(self):
        """Test deduplication with exact duplicates"""
        compositions = [
            {"composition": "Zr50Cu40Al10", "source": "Zenodo"},
            {"composition": "Zr50Cu40Al10", "source": "Zenodo"}
        ]
        result, stats = deduplicate_compositions(compositions)
        assert len(result) == 1
        assert stats["duplicates_removed"] == 1
        assert stats["duplicate_groups"] == 1
    
    def test_normalized_duplicates(self):
        """Test deduplication of formulas that normalize to same composition"""
        compositions = [
            {"composition": "Zr50Cu40Al10", "source": "Zenodo"},
            {"composition": "Zr0.5Cu0.4Al0.1", "source": "Materials Project"}
        ]
        result, stats = deduplicate_compositions(compositions)
        assert len(result) == 1
        assert stats["duplicates_removed"] == 1
        # Should keep Materials Project version (higher priority)
        assert result[0]["source"] == "Materials Project"
    
    def test_source_priority_selection(self):
        """Test that highest priority source is kept"""
        compositions = [
            {"composition": "Zr50Cu40Al10", "source": "Synthetic"},
            {"composition": "Zr0.5Cu0.4Al0.1", "source": "Materials Project"},
            {"composition": "Zr5Cu4Al1", "source": "Zenodo"}
        ]
        result, stats = deduplicate_compositions(compositions)
        assert len(result) == 1
        assert result[0]["source"] == "Materials Project"
    
    def test_empty_list(self):
        """Test deduplication with empty list"""
        result, stats = deduplicate_compositions([])
        assert len(result) == 0
        assert stats["total_input"] == 0
        assert stats["total_output"] == 0
    
    def test_missing_formula_key(self):
        """Test handling of records missing formula key"""
        compositions = [
            {"composition": "Zr50Cu40Al10", "source": "Zenodo"},
            {"source": "Materials Project"}  # Missing composition
        ]
        result, stats = deduplicate_compositions(compositions)
        # Should keep the valid one, skip the invalid
        assert len(result) == 1
    
    def test_duplicate_metadata(self):
        """Test that duplicate metadata is preserved"""
        compositions = [
            {"composition": "Zr50Cu40Al10", "source": "Zenodo", "id": 1},
            {"composition": "Zr0.5Cu0.4Al0.1", "source": "Materials Project", "id": 2}
        ]
        result, stats = deduplicate_compositions(compositions)
        assert len(result) == 1
        assert "_duplicate_sources" in result[0]
        assert result[0]["_duplicate_count"] == 1
        assert len(result[0]["_duplicate_sources"]) == 1


class TestGetDeduplicationStats:
    """Tests for get_deduplication_stats function"""
    
    def test_basic_stats(self):
        """Test basic statistics calculation"""
        stats = get_deduplication_stats(100, 80)
        assert stats["original_count"] == 100
        assert stats["deduplicated_count"] == 80
        assert stats["duplicates_removed"] == 20
        assert stats["duplicate_percentage"] == 20.0
        assert stats["retention_rate"] == 80.0
    
    def test_no_duplicates(self):
        """Test stats when no duplicates"""
        stats = get_deduplication_stats(100, 100)
        assert stats["duplicates_removed"] == 0
        assert stats["duplicate_percentage"] == 0.0
        assert stats["retention_rate"] == 100.0
    
    def test_all_duplicates(self):
        """Test stats when all are duplicates (edge case)"""
        stats = get_deduplication_stats(100, 10)
        assert stats["duplicates_removed"] == 90
        assert stats["duplicate_percentage"] == 90.0
        assert stats["retention_rate"] == 10.0
    
    def test_zero_input(self):
        """Test stats with zero input"""
        stats = get_deduplication_stats(0, 0)
        assert stats["duplicate_percentage"] == 0.0
        assert stats["retention_rate"] == 0.0
