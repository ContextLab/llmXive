"""
Unit tests for regex extraction of multiple-choice answers.

This module tests the logic used to parse model outputs into single-letter
choices (A, B, C, D) as required by User Story 2 (T027).
"""
import pytest
import re
import logging
from typing import Optional, Tuple, List

# Configure logging for the test run
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Implementation of the extraction logic (mirroring T027 requirements)
# ----------------------------------------------------------------------

class ExtractionError(Exception):
    """Raised when answer extraction fails or returns ambiguous results."""
    pass

def extract_answer(response_text: str) -> Optional[str]:
    """
    Extracts a single valid multiple-choice answer (A, B, C, D) from model output.

    Strategy:
    1. Normalize text to uppercase.
    2. Search for common patterns: "Answer: X", "Option X", "Choice X", or just "X." at end of sentence.
    3. Validate that exactly one valid option is found.
    4. If multiple options are found (e.g., "A, B"), return None and log anomaly.
    5. If no valid option is found, return None.

    Args:
        response_text: The raw string output from the LLM.

    Returns:
        The extracted letter ('A', 'B', 'C', or 'D') if successful, otherwise None.
    """
    if not response_text or not isinstance(response_text, str):
        logger.warning(f"Invalid input for answer extraction: {type(response_text)}")
        return None

    text_upper = response_text.upper().strip()

    # Pattern 1: Explicit "Answer: X" or "Answer: Option X"
    # Matches "Answer: A", "Answer: Option B", "Answer: (C)"
    patterns = [
        r'ANSWER\s*:\s*([A-D])',
        r'ANSWER\s*:\s*OPTION\s*([A-D])',
        r'ANSWER\s*:\s*\(([A-D])\)',
        r'ANSWER\s*:\s*([A-D])\)',
        r'OPTION\s*([A-D])',
        r'CHOICE\s*([A-D])',
        # Pattern 2: "The correct answer is X"
        r'IS\s+([A-D])\s*(?:\.|$)',
        # Pattern 3: Standalone letter at end of line, surrounded by whitespace or punctuation
        r'([A-D])\s*\.?\s*$',
    ]

    candidates: List[str] = []

    for pattern in patterns:
        matches = re.findall(pattern, text_upper)
        candidates.extend(matches)

    # Deduplicate while preserving order (though order doesn't strictly matter for validation)
    unique_candidates = list(dict.fromkeys(candidates))

    if len(unique_candidates) == 0:
        logger.warning(f"No answer pattern found in: '{response_text[:100]}...'")
        return None

    if len(unique_candidates) > 1:
        logger.warning(
            f"Ambiguous answer extraction: found multiple candidates {unique_candidates} "
            f"in text: '{response_text[:100]}...'. Marking as incorrect."
        )
        return None

    return unique_candidates[0]


# ----------------------------------------------------------------------
# Test Cases
# ----------------------------------------------------------------------

class TestAnswerExtraction:
    """Test suite for the answer extraction logic."""

    def test_extract_simple_answer(self):
        """Test extraction from a direct answer format."""
        response = "The correct answer is A."
        result = extract_answer(response)
        assert result == "A", f"Expected 'A', got {result}"

    def test_extract_answer_prefix(self):
        """Test extraction from 'Answer: X' format."""
        response = "Answer: B"
        result = extract_answer(response)
        assert result == "B", f"Expected 'B', got {result}"

    def test_extract_option_format(self):
        """Test extraction from 'Option C' format."""
        response = "I believe the correct option is C."
        result = extract_answer(response)
        assert result == "C", f"Expected 'C', got {result}"

    def test_extract_choice_format(self):
        """Test extraction from 'Choice D' format."""
        response = "Choice D is the most logical."
        result = extract_answer(response)
        assert result == "D", f"Expected 'D', got {result}"

    def test_extract_lowercase_input(self):
        """Test that lowercase input is handled correctly."""
        response = "the answer is b"
        result = extract_answer(response)
        assert result == "B", f"Expected 'B', got {result}"

    def test_extract_no_answer_found(self):
        """Test behavior when no answer pattern is present."""
        response = "I am not sure about this question."
        result = extract_answer(response)
        assert result is None, f"Expected None, got {result}"

    def test_extract_multiple_choices_returns_none(self):
        """
        Test that ambiguous outputs (e.g., 'A, B') return None and log anomaly.
        This corresponds to T028 requirements.
        """
        response = "The answer is A, B."
        result = extract_answer(response)
        assert result is None, f"Expected None for ambiguous input, got {result}"

    def test_extract_missing_prefix(self):
        """
        Test that answers without 'Answer:' prefix are still extracted if clear.
        Corresponds to T048b requirement.
        """
        response = "The correct option is C"
        result = extract_answer(response)
        assert result == "C", f"Expected 'C', got {result}"

    def test_extract_garbage_output(self):
        """
        Test that random non-alphanumeric text returns None.
        Corresponds to T048c requirement.
        """
        response = "!!!@@@### $$$ %%% ^^^ &&& ***"
        result = extract_answer(response)
        assert result is None, f"Expected None for garbage input, got {result}"

    def test_extract_multi_choice_output(self):
        """
        Test specific case 'Answer: A, B' returns None.
        Corresponds to T048a requirement.
        """
        response = "Answer: A, B"
        result = extract_answer(response)
        assert result is None, f"Expected None for multi-choice input, got {result}"

    def test_extract_empty_string(self):
        """Test handling of empty string."""
        result = extract_answer("")
        assert result is None, f"Expected None for empty string, got {result}"

    def test_extract_whitespace_only(self):
        """Test handling of whitespace only."""
        result = extract_answer("   \n\t   ")
        assert result is None, f"Expected None for whitespace, got {result}"

    def test_extract_invalid_option(self):
        """Test that invalid options (E, F, etc.) are ignored."""
        response = "The answer is E."
        result = extract_answer(response)
        assert result is None, f"Expected None for invalid option E, got {result}"

    def test_extract_trailing_punctuation(self):
        """Test extraction with various trailing punctuations."""
        test_cases = [
            ("Answer: A.", "A"),
            ("Answer: B!", "B"),
            ("Answer: C?", "C"),
            ("Answer: D", "D"),
        ]
        for response, expected in test_cases:
            result = extract_answer(response)
            assert result == expected, f"Failed for '{response}': expected {expected}, got {result}"