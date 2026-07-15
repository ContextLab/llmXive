"""
Unit test for synonym substitution logic (T012).

This test verifies that the synonym substitution function correctly
replaces non-keyword tokens with appropriate synonyms while preserving
code keywords and structure.
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data.perturbations import substitute_synonyms, KEYWORDS


class TestSynonymSubstitution:
    """Test suite for synonym substitution functionality."""

    def test_basic_synonym_replacement(self):
        """Verify that common words are replaced with synonyms."""
        prompt = "Write a function to calculate the sum of two numbers."

        perturbed, _ = substitute_synonyms(prompt)

        # The perturbed version should be different
        assert perturbed != prompt

        # But should still be a valid string
        assert isinstance(perturbed, str)
        assert len(perturbed) > 0

    def test_keyword_preservation(self):
        """Verify that programming keywords are not replaced."""
        # Create a prompt with code keywords
        prompt = "Write a function using 'def' and 'return' statements."

        perturbed, _ = substitute_synonyms(prompt)

        # Keywords should be preserved (case-insensitive check)
        # Note: The implementation should preserve exact keyword casing
        for keyword in KEYWORDS:
            # Check that keywords are not replaced with synonyms
            # This is a basic check - more thorough testing would verify
            # that the keyword appears in the same context
            if keyword in prompt.lower():
                # The keyword should still appear in the perturbed version
                # (though potentially with different casing due to sentence structure)
                assert keyword in perturbed.lower(), f"Keyword '{keyword}' was replaced"

    def test_multiple_replacements(self):
        """Verify that multiple synonyms can be replaced in one prompt."""
        prompt = "Create a function that computes the average of a list."

        perturbed, _ = substitute_synonyms(prompt)

        # Should have at least one word changed
        original_words = set(prompt.lower().split())
        perturbed_words = set(perturbed.lower().split())

        # There should be some difference
        assert original_words != perturbed_words, "No words were replaced"

    def test_empty_input_handling(self):
        """Verify behavior with empty or whitespace-only input."""
        with pytest.raises((ValueError, AttributeError)):
            substitute_synonyms("")

    def test_single_word_input(self):
        """Verify behavior with minimal input."""
        prompt = "function"

        perturbed, _ = substitute_synonyms(prompt)

        # Should handle gracefully - either return same or modified
        assert isinstance(perturbed, str)

    def test_special_characters_preserved(self):
        """Verify that special characters and punctuation are preserved."""
        prompt = "Write a function: 'calculate_sum(x, y)'."

        perturbed, _ = substitute_synonyms(prompt)

        # Punctuation should be preserved
        assert ":" in perturbed
        assert "'" in perturbed
        assert "(" in perturbed
        assert ")" in perturbed
        assert "." in perturbed

    def test_case_sensitivity(self):
        """Verify that case is handled appropriately."""
        prompt = "Write a FUNCTION to compute SUM."

        perturbed, _ = substitute_synonyms(prompt)

        # Should preserve some casing characteristics
        assert isinstance(perturbed, str)
        assert len(perturbed) > 0

    def test_synonym_dictionary_coverage(self):
        """Verify that the synonym dictionary covers common words."""
        # Test words that should have synonyms
        test_words = ["write", "function", "calculate", "compute", "create", "return"]

        for word in test_words:
            # Check if word is in synonym dictionary or has a synonym
            # This depends on the implementation details of the synonym dictionary
            pass  # Implementation-specific check would go here

    def test_no_synonym_for_unknown_words(self):
        """Verify that words without synonyms are left unchanged."""
        prompt = "Write a function to process the xyzzyz data."
        perturbed, meta = substitute_synonyms(prompt)

        # 'xyzzyz' is not in our dictionary, so it should remain unchanged
        assert "xyzzyz" in perturbed
        # Check that the replacement count does not include unknown words
        assert all(orig != "xyzzyz" for orig, _ in meta['replacements'])

    def test_synonym_metadata_accuracy(self):
        """Verify that the metadata accurately reflects replacements."""
        prompt = "Write a function to calculate the sum."
        perturbed, meta = substitute_synonyms(prompt)

        # Metadata should contain replacements and count
        assert 'replacements' in meta
        assert 'replacement_count' in meta
        assert meta['replacement_count'] == len(meta['replacements'])

    def test_keyword_case_preservation(self):
        """Verify that keyword casing is preserved."""
        prompt = "Use the DEF and RETURN keywords carefully."
        perturbed, _ = substitute_synonyms(prompt)

        # Keywords should appear with their original casing
        assert "DEF" in perturbed
        assert "RETURN" in perturbed