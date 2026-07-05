"""
Unit tests for the validator module.
"""
import pytest
from code.utils.validator import (
    _normalize_text,
    calculate_title_token_overlap,
    validate_title_token_overlap,
    validate_data_entries,
    ValidationError
)


class TestNormalizeText:
    def test_basic_normalization(self):
        text = "Hello World!"
        tokens = _normalize_text(text)
        assert "hello" in tokens
        assert "world" in tokens
        assert len(tokens) == 2

    def test_empty_string(self):
        assert _normalize_text("") == set()
        assert _normalize_text(None) == set()

    def test_punctuation_removal(self):
        text = "Test, Case. With; Punctuation!"
        tokens = _normalize_text(text)
        assert "test" in tokens
        assert "case" in tokens
        assert "with" in tokens
        assert "punctuation" in tokens
        assert "," not in tokens

    def test_single_char_filtering(self):
        text = "A B C I"
        tokens = _normalize_text(text)
        # Single characters are filtered out
        assert tokens == set()


class TestCalculateTitleTokenOverlap:
    def test_identical_sets(self):
        set1 = {"a", "b", "c"}
        set2 = {"a", "b", "c"}
        assert calculate_title_token_overlap(set1, set2) == 1.0

    def test_disjoint_sets(self):
        set1 = {"a", "b"}
        set2 = {"c", "d"}
        assert calculate_title_token_overlap(set1, set2) == 0.0

    def test_partial_overlap(self):
        set1 = {"a", "b", "c"}
        set2 = {"b", "c", "d"}
        # Intersection: {b, c} (2)
        # Union: {a, b, c, d} (4)
        # Score: 0.5
        assert calculate_title_token_overlap(set1, set2) == 0.5

    def test_empty_sets(self):
        assert calculate_title_token_overlap(set(), set()) == 0.0
        assert calculate_title_token_overlap({"a"}, set()) == 0.0
        assert calculate_title_token_overlap(set(), {"a"}) == 0.0


class TestValidateTitleTokenOverlap:
    def test_pass_high_overlap(self):
        entry = {
            "id": "entry1",
            "title": "Perovskite Stability Analysis",
            "citation": "Perovskite Stability Analysis via TGA"
        }
        # Tokens: {perovskite, stability, analysis} vs {perovskite, stability, analysis, via, tga}
        # Intersection: 3, Union: 5 -> 0.6 (Wait, 'via' and 'tga' are extra)
        # Let's adjust to ensure > 0.7
        entry = {
            "id": "entry2",
            "title": "Thermal Decomposition Study",
            "citation": "Study on Thermal Decomposition"
        }
        # T: {thermal, decomposition, study}
        # C: {study, on, thermal, decomposition}
        # I: {thermal, decomposition, study} (3)
        # U: {thermal, decomposition, study, on} (4)
        # Score: 0.75
        assert validate_title_token_overlap(entry, threshold=0.7) is True

    def test_fail_low_overlap(self):
        entry = {
            "id": "entry3",
            "title": "Solar Cell Efficiency",
            "citation": "Unrelated Battery Research"
        }
        with pytest.raises(ValidationError, match="validation failed"):
            validate_title_token_overlap(entry, threshold=0.7)

    def test_missing_title(self):
        entry = {
            "id": "entry4",
            "citation": "Some citation"
        }
        with pytest.raises(ValidationError, match="Missing 'title'"):
            validate_title_token_overlap(entry)

    def test_missing_citation(self):
        entry = {
            "id": "entry5",
            "title": "Some title"
        }
        with pytest.raises(ValidationError, match="Missing citation"):
            validate_title_token_overlap(entry)

    def test_alternative_citation_field(self):
        entry = {
            "id": "entry6",
            "title": "Test Title",
            "source_title": "Test Title Research"
        }
        # T: {test, title}
        # C: {test, title, research}
        # I: 2, U: 3 -> 0.666 (Fail at 0.7)
        # Let's make it pass
        entry = {
            "id": "entry7",
            "title": "Test Title",
            "source_title": "Test Title"
        }
        assert validate_title_token_overlap(entry, threshold=0.7) is True


class TestValidateDataEntries:
    def test_all_pass(self):
        entries = [
            {"id": "1", "title": "A", "citation": "A"},
            {"id": "2", "title": "B", "citation": "B"}
        ]
        result = validate_data_entries(entries, threshold=0.7)
        assert len(result) == 2

    def test_one_fails(self):
        entries = [
            {"id": "1", "title": "A", "citation": "A"},
            {"id": "2", "title": "X", "citation": "Y"} # Low overlap
        ]
        with pytest.raises(ValidationError):
            validate_data_entries(entries, threshold=0.7)

    def test_empty_list(self):
        assert validate_data_entries([], threshold=0.7) == []