"""
Unit tests for the Bloom Filter consistency validation logic.
"""
import pytest
import os
import sys
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bloom_filters.base import BloomFilter, calculate_optimal_parameters
from bloom_filters.array_impl import ArrayBloomFilter
from bloom_filters.vector_impl import VectorBloomFilter
from bloom_filters.bitset_impl import BitsetBloomFilter
from bloom_filters.consistency_validator import run_consistency_check, generate_test_data


class TestConsistencyValidation:
    """Tests for the consistency validation module."""

    def test_generate_test_data(self):
        """Test that test data generation is deterministic."""
        data1 = generate_test_data(100, seed=42)
        data2 = generate_test_data(100, seed=42)
        data3 = generate_test_data(100, seed=123)

        assert data1 == data2
        assert data1 != data3
        assert len(data1) == 100

    def test_array_vs_vector_consistency(self):
        """Test that ArrayBloomFilter and VectorBloomFilter produce identical results."""
        size = 1000
        fpr = 0.01
        test_data = generate_test_data(size * 2)

        bf_array = ArrayBloomFilter(size, fpr)
        bf_vector = VectorBloomFilter(size, fpr)

        # Insert data
        for item in test_data[:size]:
            bf_array.insert(item)
            bf_vector.insert(item)

        # Check consistency
        result = bf_array.validate_consistency(bf_vector, test_data[size:])

        assert result["mismatches"] == 0
        assert result["match_rate"] == 1.0

    def test_array_vs_bitset_consistency(self):
        """Test that ArrayBloomFilter and BitsetBloomFilter produce identical results."""
        size = 1000
        fpr = 0.01
        test_data = generate_test_data(size * 2)

        bf_array = ArrayBloomFilter(size, fpr)
        bf_bitset = BitsetBloomFilter(size, fpr)

        # Insert data
        for item in test_data[:size]:
            bf_array.insert(item)
            bf_bitset.insert(item)

        # Check consistency
        result = bf_array.validate_consistency(bf_bitset, test_data[size:])

        assert result["mismatches"] == 0
        assert result["match_rate"] == 1.0

    def test_vector_vs_bitset_consistency(self):
        """Test that VectorBloomFilter and BitsetBloomFilter produce identical results."""
        size = 1000
        fpr = 0.01
        test_data = generate_test_data(size * 2)

        bf_vector = VectorBloomFilter(size, fpr)
        bf_bitset = BitsetBloomFilter(size, fpr)

        # Insert data
        for item in test_data[:size]:
            bf_vector.insert(item)
            bf_bitset.insert(item)

        # Check consistency
        result = bf_vector.validate_consistency(bf_bitset, test_data[size:])

        assert result["mismatches"] == 0
        assert result["match_rate"] == 1.0

    def test_run_consistency_check_full(self):
        """Test the full consistency check runner."""
        size = 500
        fpr = 0.01

        result = run_consistency_check(size, fpr)

        assert result["size"] == size
        assert result["fpr"] == fpr
        assert result["passed"] is True
        assert result["mismatches"] == 0 if "mismatches" in result else True

        # Check that all comparisons passed
        for comp_name, comp_result in result["comparisons"].items():
            assert comp_result["mismatches"] == 0

    def test_consistency_with_duplicates(self):
        """Test consistency when inserting duplicate items."""
        size = 500
        fpr = 0.01
        test_data = generate_test_data(size)

        # Create data with duplicates
        data_with_dups = test_data[:size//2] + test_data[:size//2]

        bf_array = ArrayBloomFilter(size, fpr)
        bf_vector = VectorBloomFilter(size, fpr)

        for item in data_with_dups:
            bf_array.insert(item)
            bf_vector.insert(item)

        # Check consistency
        result = bf_array.validate_consistency(bf_vector, test_data)

        assert result["mismatches"] == 0

    def test_empty_test_set(self):
        """Test consistency check with an empty query set."""
        size = 100
        fpr = 0.01

        bf_array = ArrayBloomFilter(size, fpr)
        bf_vector = VectorBloomFilter(size, fpr)

        # Insert some data
        for i in range(size):
            bf_array.insert(f"item_{i}")
            bf_vector.insert(f"item_{i}")

        # Check consistency with empty query set
        result = bf_array.validate_consistency(bf_vector, [])

        assert result["total_queries"] == 0
        assert result["match_rate"] == 1.0
        assert result["mismatches"] == 0

    def test_different_fpr_values(self):
        """Test consistency across different FPR values."""
        for fpr in [0.001, 0.01, 0.1]:
            size = 500
            result = run_consistency_check(size, fpr)

            assert result["passed"] is True
            assert result["fpr"] == fpr