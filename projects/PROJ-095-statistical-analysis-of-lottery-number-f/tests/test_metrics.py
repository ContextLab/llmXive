import pytest
from metrics import calculate_birthday_ratio, calculate_consecutive_ratio
from constants import BIRTHDAY_THRESHOLD, NUMBERS_PER_DRAW

class TestCalculateBirthdayRatio:
    """Unit tests for calculate_birthday_ratio (T014 context)"""

    def test_all_birthdays(self):
        """All numbers are <= 31, ratio should be 1.0"""
        draw = [1, 2, 3, 4, 5, 6]
        assert calculate_birthday_ratio(draw) == 1.0

    def test_no_birthdays(self):
        """All numbers are > 31, ratio should be 0.0"""
        draw = [32, 33, 34, 35, 36, 37]
        assert calculate_birthday_ratio(draw) == 0.0

    def test_mixed_birthdays(self):
        """Half birthdays, half not"""
        draw = [1, 2, 30, 32, 40, 49]
        # 3 out of 6 are birthdays
        assert calculate_birthday_ratio(draw) == 0.5

    def test_single_birthday(self):
        """Only one birthday in draw"""
        draw = [32, 33, 34, 35, 36, 1]
        assert calculate_birthday_ratio(draw) == 1/6

    def test_empty_draw(self):
        """Empty draw should handle gracefully (though unlikely in real data)"""
        with pytest.raises((ValueError, IndexError)):
            calculate_birthday_ratio([])


class TestCalculateConsecutiveRatio:
    """Unit tests for calculate_consecutive_ratio (T015)"""

    def test_perfect_sequence(self):
        """Perfect consecutive sequence [1,2,3,4,5,6] -> 5 pairs / 5 possible = 1.0"""
        draw = [1, 2, 3, 4, 5, 6]
        # Sorted: [1,2,3,4,5,6]
        # Consecutive pairs: (1,2), (2,3), (3,4), (4,5), (5,6) -> 5 pairs
        # Total possible adjacent pairs in 6 items: 5
        assert calculate_consecutive_ratio(draw) == 1.0

    def test_no_consecutive(self):
        """No consecutive numbers -> 0.0"""
        draw = [1, 3, 5, 7, 9, 11]
        # Sorted: [1,3,5,7,9,11]
        # Differences: 2, 2, 2, 2, 2 -> No consecutive (diff != 1)
        assert calculate_consecutive_ratio(draw) == 0.0

    def test_partial_consecutive(self):
        """Partial consecutive: [1, 2, 5, 6, 10, 11] -> 3 pairs / 5 = 0.6"""
        draw = [1, 2, 5, 6, 10, 11]
        # Sorted: [1,2,5,6,10,11]
        # Pairs: (1,2)->yes, (2,5)->no, (5,6)->yes, (6,10)->no, (10,11)->yes
        # Total consecutive: 3
        # Total pairs: 5
        assert calculate_consecutive_ratio(draw) == 0.6

    def test_reverse_order(self):
        """Reverse order [6,5,4,3,2,1] should sort and yield 1.0"""
        draw = [6, 5, 4, 3, 2, 1]
        assert calculate_consecutive_ratio(draw) == 1.0

    def test_single_gap(self):
        """One gap in sequence: [1,2,3,5,6,7] -> 4 pairs / 5 = 0.8"""
        draw = [1, 2, 3, 5, 6, 7]
        # Sorted: [1,2,3,5,6,7]
        # Pairs: (1,2)->yes, (2,3)->yes, (3,5)->no, (5,6)->yes, (6,7)->yes
        # Total consecutive: 4
        assert calculate_consecutive_ratio(draw) == 0.8

    def test_empty_draw(self):
        """Empty draw should handle gracefully"""
        with pytest.raises((ValueError, IndexError)):
            calculate_consecutive_ratio([])

    def test_single_element(self):
        """Single element draw (edge case) -> 0 pairs, 0 possible -> 0.0 or handle error"""
        # With 1 element, there are 0 adjacent pairs.
        # The function should handle this by returning 0.0 or raising an error.
        # Based on logic: pairs = len(draw) - 1 = 0. If pairs == 0, return 0.0.
        draw = [10]
        assert calculate_consecutive_ratio(draw) == 0.0