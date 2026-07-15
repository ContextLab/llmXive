"""
Unit tests for code/mwq_scoring.py
"""
import pytest
import numpy as np

# Import the module under test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mwq_scoring import score_mwq, validate_mwq_response


class TestValidateMWQResponse:
    def test_valid_response_length(self):
        """Test that a response with correct number of items passes validation."""
        # MWQ typically has 10 items (check spec for exact count)
        valid_response = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        assert validate_mwq_response(valid_response) is True

    def test_invalid_response_length_too_short(self):
        """Test that a response with too few items fails validation."""
        short_response = [1, 2, 3, 4, 5]
        
        with pytest.raises(ValueError):
            validate_mwq_response(short_response)

    def test_invalid_response_length_too_long(self):
        """Test that a response with too many items fails validation."""
        long_response = list(range(1, 15))
        
        with pytest.raises(ValueError):
            validate_mwq_response(long_response)

    def test_invalid_response_values(self):
        """Test that response with values outside 1-5 range fails validation."""
        invalid_response = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # 6 is out of range
        
        with pytest.raises(ValueError):
            validate_mwq_response(invalid_response)

    def test_negative_values(self):
        """Test that response with negative values fails validation."""
        invalid_response = [-1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        with pytest.raises(ValueError):
            validate_mwq_response(invalid_response)


class TestScoreMWQ:
    def test_score_calculation_simple(self):
        """Test basic score calculation with all items scored positively."""
        # Assuming items 1-10, all scored positively for simplicity
        # In real MWQ, some items are reverse-scored
        response = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        
        score = score_mwq(response)
        # If all items are 1 and positively scored, total should be 10
        assert score == 10

    def test_score_calculation_max(self):
        """Test score calculation with all maximum values."""
        response = [5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
        
        score = score_mwq(response)
        # If all items are 5 and positively scored, total should be 50
        assert score == 50

    def test_score_with_reverse_scoring(self):
        """Test that reverse scoring is applied correctly."""
        # Assume item 1 is reverse-scored: 1->5, 2->4, 3->3, 4->2, 5->1
        # Response: [1, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        # Reverse-scored item 1: 1 -> 5
        # Other items: 3 each
        # Total: 5 + 9*3 = 5 + 27 = 32
        response = [1, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        
        score = score_mwq(response)
        assert score == 32

    def test_score_with_mixed_values(self):
        """Test score calculation with mixed response values."""
        response = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
        
        score = score_mwq(response)
        # Item 1 (reverse): 1 -> 5
        # Item 6 (assume positive): 1
        # Total: 5 + 2 + 3 + 4 + 5 + 1 + 2 + 3 + 4 + 5 = 34
        assert score == 34

    def test_score_invalid_response_length(self):
        """Test that scoring fails with invalid response length."""
        invalid_response = [1, 2, 3, 4, 5]
        
        with pytest.raises(ValueError):
            score_mwq(invalid_response)

    def test_score_float_responses(self):
        """Test that float responses are handled correctly."""
        response = [1.5, 2.5, 3.5, 4.5, 5.0, 1.0, 2.0, 3.0, 4.0, 5.0]
        
        score = score_mwq(response)
        # Should handle floats gracefully
        assert isinstance(score, (int, float))
        assert score > 0