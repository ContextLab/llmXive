"""
Unit tests for code/utils/convex_hull.py
"""

import numpy as np
import pytest
from scipy.spatial import ConvexHull as SciPyConvexHull

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.convex_hull import ConvexHullWrapper, compute_convex_hull, test_points_in_hull


def test_simple_2d_square():
    """Test with a simple 2D square."""
    points = np.array([
        [0, 0],
        [1, 0],
        [1, 1],
        [0, 1]
    ])
    wrapper = compute_convex_hull(points)

    # Point inside
    inside_point = np.array([[0.5, 0.5]])
    assert wrapper.is_inside(inside_point)[0] is True

    # Point outside
    outside_point = np.array([[2, 2]])
    assert wrapper.is_inside(outside_point)[0] is False

    # Point on edge (should be inside)
    edge_point = np.array([[0.5, 0]])
    assert wrapper.is_inside(edge_point)[0] is True

    # Point on vertex
    vertex_point = np.array([[0, 0]])
    assert wrapper.is_inside(vertex_point)[0] is True


def test_simple_3d_cube():
    """Test with a simple 3D cube."""
    points = np.array([
        [0, 0, 0],
        [1, 0, 0],
        [1, 1, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 1],
        [1, 1, 1],
        [0, 1, 1]
    ])
    wrapper = compute_convex_hull(points)

    inside = np.array([[0.5, 0.5, 0.5]])
    assert wrapper.is_inside(inside)[0] is True

    outside = np.array([[1.5, 0.5, 0.5]])
    assert wrapper.is_inside(outside)[0] is False


def test_dimension_mismatch():
    """Test that dimension mismatch raises an error."""
    points = np.array([[0, 0], [1, 0], [1, 1]])
    wrapper = compute_convex_hull(points)

    wrong_dim = np.array([[0, 0, 0]])
    with pytest.raises(ValueError):
        wrapper.is_inside(wrong_dim)


def test_empty_points():
    """Test that empty points raise an error."""
    with pytest.raises(ValueError):
        compute_convex_hull(np.array([]).reshape(0, 2))


def test_single_point():
    """Test behavior with a single point (degenerate hull)."""
    points = np.array([[0.5, 0.5]])
    # A single point cannot form a hull in the traditional sense for volume,
    # but Delaunay might handle it or raise an error depending on scipy version.
    # We expect an error here because ConvexHull requires at least n+1 points
    # to form a simplex in n-dimensions.
    with pytest.raises(Exception): # scipy.spatial.qhull.QhullError or similar
        compute_convex_hull(points)


def test_wrapper_methods():
    """Test helper methods like get_volume and get_vertices."""
    points = np.array([[0, 0], [1, 0], [0, 1]])
    wrapper = compute_convex_hull(points)

    # Area of triangle with base 1, height 1 is 0.5
    assert np.isclose(wrapper.get_area(), 0.5)

    vertices = wrapper.get_vertices()
    assert len(vertices) == 3
    assert all(v in [0, 1, 2] for v in vertices)


def test_batch_points():
    """Test checking multiple points at once."""
    points = np.array([[0, 0], [2, 0], [2, 2], [0, 2]])
    wrapper = compute_convex_hull(points)

    test_points = np.array([
        [1, 1],   # Inside
        [3, 3],   # Outside
        [0.5, 0.5], # Inside
        [2.5, 1]    # Outside
    ])

    result = wrapper.is_inside(test_points)
    expected = np.array([True, False, True, False])
    assert np.array_equal(result, expected)