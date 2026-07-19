import pytest
from metrics import calculate_dynamic_sample_size, is_wasted_call, calculate_cosine_similarity_proxy

def test_calculate_dynamic_sample_size_small():
    assert calculate_dynamic_sample_size(50, 1000) == 50

def test_calculate_dynamic_sample_size_medium():
    assert calculate_dynamic_sample_size(500, 1000) == 100  # 20% of 500

def test_calculate_dynamic_sample_size_large():
    assert calculate_dynamic_sample_size(5000, 1000) == 1000  # 10% of 5000, capped at 1000

def test_calculate_dynamic_sample_size_zero():
    assert calculate_dynamic_sample_size(0, 1000) == 0

def test_calculate_dynamic_sample_size_negative():
    assert calculate_dynamic_sample_size(-10, 1000) == 0

def test_is_wasted_call_above_threshold():
    assert is_wasted_call(0.96, 0.95) is True

def test_is_wasted_call_below_threshold():
    assert is_wasted_call(0.94, 0.95) is False

def test_is_wasted_call_at_threshold():
    assert is_wasted_call(0.95, 0.95) is False  # Strictly greater than

# Note: calculate_cosine_similarity_proxy requires actual text inputs and model loading
# Skipping integration-style test for now unless specific text inputs are provided
