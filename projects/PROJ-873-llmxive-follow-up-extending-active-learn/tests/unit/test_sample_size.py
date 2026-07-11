import pytest
from metrics import calculate_dynamic_sample_size

def test_calculate_dynamic_sample_size_less_than_bound():
    """Test when total flagged is less than the upper bound."""
    total_flagged = 500
    upper_bound = 1000
    expected = 500
    result = calculate_dynamic_sample_size(total_flagged, upper_bound)
    assert result == expected

def test_calculate_dynamic_sample_size_greater_than_bound():
    """Test when total flagged is greater than the upper bound."""
    total_flagged = 2500
    upper_bound = 1000
    expected = 1000
    result = calculate_dynamic_sample_size(total_flagged, upper_bound)
    assert result == expected

def test_calculate_dynamic_sample_size_equal_to_bound():
    """Test when total flagged equals the upper bound."""
    total_flagged = 1000
    upper_bound = 1000
    expected = 1000
    result = calculate_dynamic_sample_size(total_flagged, upper_bound)
    assert result == expected

def test_calculate_dynamic_sample_size_zero_flagged():
    """Test when there are no flagged calls."""
    total_flagged = 0
    upper_bound = 1000
    expected = 0
    result = calculate_dynamic_sample_size(total_flagged, upper_bound)
    assert result == expected

def test_calculate_dynamic_sample_size_negative_flagged():
    """Test that negative flagged calls raise an error."""
    with pytest.raises(ValueError):
        calculate_dynamic_sample_size(-10, 1000)

def test_calculate_dynamic_sample_size_zero_bound():
    """Test that zero upper bound raises an error."""
    with pytest.raises(ValueError):
        calculate_dynamic_sample_size(100, 0)

def test_calculate_dynamic_sample_size_custom_bound():
    """Test with a custom upper bound."""
    total_flagged = 50
    upper_bound = 25
    expected = 25
    result = calculate_dynamic_sample_size(total_flagged, upper_bound)
    assert result == expected
