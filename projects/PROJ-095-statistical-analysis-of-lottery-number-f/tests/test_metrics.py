"""
Unit tests for metrics.py functions.
Specifically tests calculate_birthday_ratio with known inputs.
"""
import pytest
import sys
import os

# Add the code directory to the path to allow imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from metrics import calculate_birthday_ratio


class TestCalculateBirthdayRatio:
    """Tests for the calculate_birthday_ratio function."""

    def test_all_birthdays_low_numbers(self):
        """
        Test case where all numbers are <= 31 (BIRTHDAY_THRESHOLD).
        Expected: All 6 are birthdays. Pairs = 6*5/2 = 15. Ratio = 15/15 = 1.0.
        Input: [1, 2, 3, 4, 5, 6]
        """
        draw_numbers = [1, 2, 3, 4, 5, 6]
        result = calculate_birthday_ratio(draw_numbers)
        assert result == 1.0, f"Expected 1.0 for [1,2,3,4,5,6], got {result}"

    def test_no_birthdays_high_numbers(self):
        """
        Test case where all numbers are > 31 (BIRTHDAY_THRESHOLD).
        Expected: 0 birthdays. Pairs = 0. Ratio = 0/15 = 0.0.
        Input: [32, 33, 34, 35, 36, 37]
        """
        draw_numbers = [32, 33, 34, 35, 36, 37]
        result = calculate_birthday_ratio(draw_numbers)
        assert result == 0.0, f"Expected 0.0 for [32,33,34,35,36,37], got {result}"

    def test_mixed_birthdays(self):
        """
        Test case with mixed numbers.
        Input: [1, 2, 3, 32, 33, 34]
        Birthdays: [1, 2, 3] (3 numbers)
        Pairs of birthdays: 3 * 2 / 2 = 3
        Total possible pairs: 6 * 5 / 2 = 15
        Expected Ratio: 3 / 15 = 0.2
        """
        draw_numbers = [1, 2, 3, 32, 33, 34]
        result = calculate_birthday_ratio(draw_numbers)
        expected = 3 / 15
        assert result == expected, f"Expected {expected} for mixed input, got {result}"

    def test_single_birthday(self):
        """
        Test case with only 1 birthday number.
        Input: [1, 32, 33, 34, 35, 36]
        Birthdays: [1] (1 number)
        Pairs: 0
        Expected Ratio: 0.0
        """
        draw_numbers = [1, 32, 33, 34, 35, 36]
        result = calculate_birthday_ratio(draw_numbers)
        assert result == 0.0, f"Expected 0.0 for single birthday, got {result}"

    def test_boundary_condition_31(self):
        """
        Test the boundary: 31 is a birthday, 32 is not.
        Input: [31, 31, 31, 32, 32, 32] (assuming duplicates possible in logic check)
        But standard draws are unique. Let's test unique boundary.
        Input: [31, 30, 29, 32, 33, 34]
        Birthdays: [31, 30, 29] -> 3 numbers -> 3 pairs.
        Total pairs: 15.
        Expected: 0.2
        """
        draw_numbers = [29, 30, 31, 32, 33, 34]
        result = calculate_birthday_ratio(draw_numbers)
        expected = 3 / 15
        assert result == expected, f"Expected {expected} for boundary test, got {result}"

    def test_empty_list(self):
        """Test handling of an empty list (edge case)."""
        draw_numbers = []
        result = calculate_birthday_ratio(draw_numbers)
        # Based on typical implementation, 0 pairs / 0 total pairs should be 0.0 or handled gracefully
        assert result == 0.0, f"Expected 0.0 for empty list, got {result}"

    def test_single_number(self):
        """Test handling of a single number (edge case)."""
        draw_numbers = [15]
        result = calculate_birthday_ratio(draw_numbers)
        # 1 birthday, 0 pairs. Total pairs 0. Ratio 0.0.
        assert result == 0.0, f"Expected 0.0 for single number, got {result}"