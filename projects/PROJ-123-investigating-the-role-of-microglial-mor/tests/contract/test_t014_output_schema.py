"""
Contract test for T014 output schema.
Verifies that skeletonize_and_count returns the expected tuple structure.
"""
import numpy as np
import pytest
from code.morphometry import skeletonize_and_count

def test_return_type_tuple():
    """Verify return type is a tuple."""
    image = np.zeros((10, 10), dtype=np.uint8)
    image[5, :] = 255
    result = skeletonize_and_count(image)
    assert isinstance(result, tuple)

def test_return_length_two():
    """Verify tuple has exactly 2 elements."""
    image = np.zeros((10, 10), dtype=np.uint8)
    image[5, :] = 255
    result = skeletonize_and_count(image)
    assert len(result) == 2

def test_first_element_is_skeleton_array():
    """Verify first element is a numpy array (skeleton)."""
    image = np.zeros((10, 10), dtype=np.uint8)
    image[5, :] = 255
    result = skeletonize_and_count(image)
    skeleton, count = result
    assert isinstance(skeleton, np.ndarray)
    assert skeleton.dtype == bool or skeleton.dtype == np.uint8

def test_second_element_is_integer_count():
    """Verify second element is an integer (branch count)."""
    image = np.zeros((10, 10), dtype=np.uint8)
    image[5, :] = 255
    result = skeletonize_and_count(image)
    skeleton, count = result
    assert isinstance(count, int)
    assert count >= 0

def test_skeleton_shape_matches_input():
    """Verify skeleton shape matches input shape."""
    image = np.zeros((20, 30), dtype=np.uint8)
    image[10, :] = 255
    result = skeletonize_and_count(image)
    skeleton, count = result
    assert skeleton.shape == image.shape

def test_branch_count_non_negative():
    """Verify branch count is non-negative."""
    image = np.random.rand(50, 50) > 0.5
    result = skeletonize_and_count(image)
    skeleton, count = result
    assert count >= 0