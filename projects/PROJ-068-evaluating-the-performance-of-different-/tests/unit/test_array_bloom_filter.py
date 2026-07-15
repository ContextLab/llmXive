"""
Unit tests for ArrayBloomFilter implementation.
"""

import pytest
from code.bloom_filters.array_impl import ArrayBloomFilter
from code.bloom_filters.base import calculate_optimal_parameters


class TestArrayBloomFilter:
    """Tests for the ArrayBloomFilter class."""

    def test_initialization(self):
        """Test that the filter initializes with correct parameters."""
        n = 1000
        fpr = 0.01
        bf = ArrayBloomFilter(n, fpr)

        assert bf.n_elements == 0
        assert bf.fpr_target == fpr
        assert bf.m > 0
        assert bf.k > 0
        assert len(bf.bit_array) == bf.m
        assert all(x == 0 for x in bf.bit_array)

    def test_insert_and_contains(self):
        """Test that inserted items are found."""
        bf = ArrayBloomFilter(100, 0.01)

        items = ["apple", "banana", "cherry", 123, b"bytes"]
        for item in items:
            bf.insert(item)
            assert bf.contains(item) is True

        assert bf.n_elements == len(items)

    def test_non_inserted_item_false_positive(self):
        """Test that non-inserted items are usually not found (allowing for FPR)."""
        bf = ArrayBloomFilter(100, 0.01)
        bf.insert("unique_item_12345")

        # Check a definitely non-existent item
        # With FPR 0.01, it's statistically unlikely to collide immediately
        # but not impossible. We check for a few distinct items to ensure
        # the filter isn't returning True for everything.
        non_items = ["definitely_not_here", "another_random_string"]
        found_count = 0
        for item in non_items:
            if bf.contains(item):
                found_count += 1

        # If all non-items are found, something is wrong (filter is all 1s)
        # With 0.01 FPR, we expect very few hits.
        # This is a sanity check, not a strict statistical test.
        assert found_count < len(non_items), "Filter seems to be returning True for all items."

    def test_theoretical_fpr_calculation(self):
        """Test that theoretical FPR is calculated and is reasonable."""
        n = 1000
        fpr_target = 0.01
        bf = ArrayBloomFilter(n, fpr_target)

        # Before insertion, FPR should be 0
        assert bf.false_positive_rate() == 0.0

        # Insert items
        for i in range(n):
            bf.insert(f"item_{i}")

        # After insertion, FPR should be close to target
        actual_fpr = bf.false_positive_rate()
        assert actual_fpr > 0
        # Allow some variance, but it should be in the ballpark of the target
        assert actual_fpr < 0.1  # Should be much lower than 10%

    def test_optimal_parameters_consistency(self):
        """Test that calculated m and k match the base class calculation."""
        n = 10000
        fpr = 0.05
        bf = ArrayBloomFilter(n, fpr)

        expected_m, expected_k = calculate_optimal_parameters(n, fpr)

        assert bf.m == expected_m
        assert bf.k == expected_k

    def test_memory_usage(self):
        """Test that memory usage is reported."""
        bf = ArrayBloomFilter(1000, 0.01)
        mem = bf.get_memory_usage_bytes()
        assert mem == bf.m  # Returns bits as per implementation

    def test_str_representation(self):
        """Test string representation."""
        bf = ArrayBloomFilter(100, 0.01)
        s = str(bf)
        assert "ArrayBloomFilter" in s
        assert "n=0" in s

    def test_insert_none_raises(self):
        """Test that inserting None raises an error."""
        bf = ArrayBloomFilter(100, 0.01)
        with pytest.raises(ValueError):
            bf.insert(None)

    def test_contains_none_returns_false(self):
        """Test that checking None returns False."""
        bf = ArrayBloomFilter(100, 0.01)
        assert bf.contains(None) is False

    def test_invalid_fpr_raises(self):
        """Test that invalid FPR raises an error."""
        with pytest.raises(ValueError):
            ArrayBloomFilter(100, 1.5)
        with pytest.raises(ValueError):
            ArrayBloomFilter(100, -0.1)
        with pytest.raises(ValueError):
            ArrayBloomFilter(100, 0)

    def test_invalid_n_elements_raises(self):
        """Test that invalid n_elements raises an error."""
        with pytest.raises(ValueError):
            ArrayBloomFilter(0, 0.01)
        with pytest.raises(ValueError):
            ArrayBloomFilter(-10, 0.01)