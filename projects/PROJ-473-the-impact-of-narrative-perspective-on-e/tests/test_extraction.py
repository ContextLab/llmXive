"""
Unit tests for perspective extraction functions.
"""
import pytest
from code.extraction import calculate_pronoun_density, calculate_narrator_distance_score, extract_perspective_features

class TestPronounDensity:
    def test_empty_text(self):
        """Test handling of empty text."""
        result = calculate_pronoun_density("")
        assert result["first_person_density"] == 0.0
        assert result["third_person_density"] == 0.0
        assert result["first_person_count"] == 0

    def test_none_text(self):
        """Test handling of None text."""
        result = calculate_pronoun_density(None)
        assert result["first_person_density"] == 0.0

    def test_first_person_pronouns(self):
        """Test detection of first-person pronouns."""
        text = "I went to the store. We saw him there. My friend was with us."
        result = calculate_pronoun_density(text)
        assert result["first_person_count"] >= 3  # I, We, My, us
        assert result["first_person_density"] > 0

    def test_third_person_pronouns(self):
        """Test detection of third-person pronouns."""
        text = "He went to the store. She saw it there. Their friend was with them."
        result = calculate_pronoun_density(text)
        assert result["third_person_count"] >= 4  # He, She, it, Their, them
        assert result["third_person_density"] > 0

    def test_mixed_pronouns(self):
        """Test text with both first and third person."""
        text = "I saw him walking. She told me about it."
        result = calculate_pronoun_density(text)
        assert result["first_person_count"] >= 2  # I, me
        assert result["third_person_count"] >= 3  # him, She, it

    def test_non_english_text(self):
        """Test that non-English text returns zeros."""
        text = "Bonjour, je suis content. Comment allez-vous?"
        result = calculate_pronoun_density(text)
        assert result.get("skipped", False) or result["first_person_density"] == 0.0

    def test_realistic_story(self):
        """Test with a realistic short story excerpt."""
        text = """
        I walked through the forest, wondering what lay ahead. The trees whispered secrets
        to me, and I felt a strange connection to the land. He had told me stories about
        this place, but I never believed them until now. She would have been proud to see
        me here, standing alone in the moonlight.
        """
        result = calculate_pronoun_density(text)
        assert result["first_person_count"] > result["third_person_count"]
        assert result["first_person_density"] > 0.05

class TestNarratorDistance:
    def test_close_distance(self):
        """Test that first-person text has low distance score."""
        text = "I walked down the street. I felt happy. My heart was full."
        score = calculate_narrator_distance_score(text)
        assert score < 0.5

    def test_far_distance(self):
        """Test that third-person text has high distance score."""
        text = "He walked down the street. She felt happy. Their hearts were full."
        score = calculate_narrator_distance_score(text)
        assert score > 0.5

    def test_empty_text(self):
        """Test empty text returns neutral score."""
        score = calculate_narrator_distance_score("")
        assert score == 0.5

class TestExtractPerspectiveFeatures:
    def test_short_text(self):
        """Test that very short text returns error."""
        result = extract_perspective_features("Too short")
        assert result["error"] == "text_too_short"

    def test_normal_text(self):
        """Test normal text extraction."""
        text = "I walked down the street. I felt happy. My heart was full of joy."
        result = extract_perspective_features(text)
        assert result["error"] is None
        assert result["perspective_type"] == "first_person"
        assert result["narrator_distance_score"] is not None

    def test_edge_case_50_chars(self):
        """Test text exactly at the 50 character boundary."""
        text = "A" * 50
        result = extract_perspective_features(text)
        # Should not error but may have zero pronouns
        assert "error" not in result or result["error"] != "text_too_short"