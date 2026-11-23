"""
Unit tests for Bloom Filter implementations, focusing on:
1. Interface consistency (Contract tests)
2. False Positive Rate (FPR) calculation accuracy
"""
import pytest
import math
import random
import sys
import os

# Add parent directory to path for imports if running standalone
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(1, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from bloom_filters.base import BloomFilter, calculate_optimal_parameters
from bloom_filters.array_impl import ArrayBloomFilter
from bloom_filters.vector_impl import VectorBloomFilter
from bloom_filters.bitset_impl import BitsetBloomFilter
from bloom_filters.hash_utils import get_k_hashes, hash_murmur3_32

# Test Configuration Constants
SMALL_N = 1000
SMALL_FPR = 0.01
LARGE_N = 10000
LARGE_FPR = 0.001

# Set a deterministic seed for reproducibility in FPR estimation
RANDOM_SEED = 42


class TestInterfaceConsistency:
    """Contract tests ensuring all implementations share the same interface."""

    @pytest.fixture(autouse=True)
    def setup_filters(self):
        """Create instances of all three Bloom filter implementations."""
        self.n = SMALL_N
        self.fpr = SMALL_FPR
        
        # Calculate optimal m and k
        m, k = calculate_optimal_parameters(self.n, self.fpr)
        
        self.array_filter = ArrayBloomFilter(m, k)
        self.vector_filter = VectorBloomFilter(m, k)
        self.bitset_filter = BitsetBloomFilter(m, k)
        
        self.filters = [
            ("Array", self.array_filter),
            ("Vector", self.vector_filter),
            ("Bitset", self.bitset_filter)
        ]

    def test_has_insert_method(self):
        """Verify all filters have an insert method."""
        for name, f in self.filters:
            assert hasattr(f, 'insert'), f"{name} missing insert method"
            assert callable(getattr(f, 'insert')), f"{name}.insert is not callable"

    def test_has_contains_method(self):
        """Verify all filters have a contains method."""
        for name, f in self.filters:
            assert hasattr(f, 'contains'), f"{name} missing contains method"
            assert callable(getattr(f, 'contains')), f"{name}.contains is not callable"

    def test_has_false_positive_rate_method(self):
        """Verify all filters have a false_positive_rate method."""
        for name, f in self.filters:
            assert hasattr(f, 'false_positive_rate'), f"{name} missing false_positive_rate method"
            assert callable(getattr(f, 'false_positive_rate')), f"{name}.false_positive_rate is not callable"

    def test_insert_consistency(self):
        """Verify all filters insert the same items and return True for membership."""
        test_items = [f"item_{i}" for i in range(100)]
        
        for name, f in self.filters:
            for item in test_items:
                f.insert(item)
        
        for name, f in self.filters:
            for item in test_items:
                assert f.contains(item), f"{name} failed to contain inserted item: {item}"

    def test_consistent_state_across_implementations(self):
        """Verify that identical inputs produce identical membership results."""
        test_items = [f"consistency_test_{i}" for i in range(500)]
        
        # Insert into all
        for name, f in self.filters:
            for item in test_items:
                f.insert(item)
        
        # Check a set of known items and a set of unknown items
        known_items = test_items
        unknown_items = [f"unknown_{i}" for i in range(500)]
        
        results = {}
        for name, f in self.filters:
            results[name] = {
                'known': all(f.contains(item) for item in known_items),
                'unknown': [f.contains(item) for item in unknown_items]
            }
        
        # All implementations must agree on known items
        first_known = results[self.filters[0][0]]['known']
        for name, res in results.items():
            assert res['known'] == first_known, f"Mismatch in known item detection for {name}"
            assert res['known'] is True, f"{name} failed to detect known items"

        # All implementations must agree on unknown items (False Positives)
        # This doesn't guarantee they are the *same* false positives, but the rate should be similar
        # For strict consistency, we check that the count of FP is within a small tolerance
        # However, due to hash collision variations in implementation details, exact bit-level 
        # consistency is hard without identical hash function behavior. 
        # The base class ensures identical hash usage, so FP sets should be identical.
        
        unknown_fps = {name: sum(res['unknown']) for name, res in results.items()}
        first_fp_count = unknown_fps[self.filters[0][0]]
        
        for name, count in unknown_fps.items():
            assert count == first_fp_count, \
                f"False positive count mismatch: {name} ({count}) vs {self.filters[0][0]} ({first_fp_count})"


class TestFalsePositiveRateAccuracy:
    """Unit tests for FPR calculation accuracy."""

    @pytest.fixture(autouse=True)
    def setup(self):
        random.seed(RANDOM_SEED)
        self.n = SMALL_N
        self.fpr_target = SMALL_FPR
        self.m, self.k = calculate_optimal_parameters(self.n, self.fpr_target)
        
        # Generate test data
        self.inserted_items = [f"item_{i}_{random.randint(0, 1000000)}" for i in range(self.n)]
        self.test_items = [f"test_{i}_{random.randint(0, 1000000)}" for i in range(self.n * 10)]
        
        # Ensure no overlap between inserted and test items
        inserted_set = set(self.inserted_items)
        self.test_items = [t for t in self.test_items if t not in inserted_set]
        
        # We need enough test items to get a statistically significant sample
        # If we filtered too many, generate more
        while len(self.test_items) < self.n * 5:
            new_item = f"extra_{random.randint(0, 10000000)}"
            if new_item not in inserted_set:
                self.test_items.append(new_item)

    def _run_fpr_test(self, filter_instance, name):
        """Helper to run FPR test on a specific filter instance."""
        # Insert items
        for item in self.inserted_items:
            filter_instance.insert(item)
        
        # Count false positives
        fp_count = 0
        for item in self.test_items:
            if filter_instance.contains(item):
                fp_count += 1
        
        observed_fpr = fp_count / len(self.test_items)
        
        # Theoretical FPR calculation: (1 - e^(-kn/m))^k
        # Using the formula: P = (1 - exp(-k*n/m))^k
        theoretical_fpr = (1 - math.exp(-self.k * self.n / self.m)) ** self.k
        
        return observed_fpr, theoretical_fpr

    def test_array_filter_fpr_accuracy(self):
        """Test ArrayBloomFilter FPR matches theoretical expectation."""
        bf = ArrayBloomFilter(self.m, self.k)
        observed, theoretical = self._run_fpr_test(bf, "Array")
        
        # Allow a 20% relative error due to statistical variance in sampling
        # For n=1000, sample=10000, standard error is roughly sqrt(p(1-p)/N) ~ 0.001
        # A 20% margin is generous but safe for small n.
        tolerance = max(0.001, theoretical * 0.20) 
        
        assert abs(observed - theoretical) <= tolerance, \
            f"Array FPR: Observed={observed:.6f}, Theoretical={theoretical:.6f}, Diff={abs(observed-theoretical):.6f}"

    def test_vector_filter_fpr_accuracy(self):
        """Test VectorBloomFilter FPR matches theoretical expectation."""
        bf = VectorBloomFilter(self.m, self.k)
        observed, theoretical = self._run_fpr_test(bf, "Vector")
        
        tolerance = max(0.001, theoretical * 0.20)
        
        assert abs(observed - theoretical) <= tolerance, \
            f"Vector FPR: Observed={observed:.6f}, Theoretical={theoretical:.6f}, Diff={abs(observed-theoretical):.6f}"

    def test_bitset_filter_fpr_accuracy(self):
        """Test BitsetBloomFilter FPR matches theoretical expectation."""
        bf = BitsetBloomFilter(self.m, self.k)
        observed, theoretical = self._run_fpr_test(bf, "Bitset")
        
        tolerance = max(0.001, theoretical * 0.20)
        
        assert abs(observed - theoretical) <= tolerance, \
            f"Bitset FPR: Observed={observed:.6f}, Theoretical={theoretical:.6f}, Diff={abs(observed-theoretical):.6f}"

    def test_fpr_consistency_across_implementations(self):
        """Verify all implementations produce similar FPRs on the same data."""
        results = []
        
        for name, impl_class in [("Array", ArrayBloomFilter), ("Vector", VectorBloomFilter), ("Bitset", BitsetBloomFilter)]:
            bf = impl_class(self.m, self.k)
            observed, theoretical = self._run_fpr_test(bf, name)
            results.append((name, observed))
        
        # Check that all observed FPRs are within a tight range of each other
        # Since they use the same hash functions and logic, they should be very close
        fpr_values = [r[1] for r in results]
        max_fpr = max(fpr_values)
        min_fpr = min(fpr_values)
        
        # Allow a small absolute difference (0.0005) for statistical noise
        assert (max_fpr - min_fpr) < 0.0005, \
            f"FPR inconsistency across implementations: {results}"

    def test_fpr_scales_with_parameters(self):
        """Test that FPR decreases as we increase m or decrease k (within optimal range)."""
        # Base case
        n, fpr = 1000, 0.01
        m_base, k_base = calculate_optimal_parameters(n, fpr)
        
        # Larger bit array (should have lower FPR)
        m_large, k_large = calculate_optimal_parameters(n, 0.001)
        
        bf_base = ArrayBloomFilter(m_base, k_base)
        bf_large = ArrayBloomFilter(m_large, k_large)
        
        # Insert same items
        items = [f"item_{i}" for i in range(n)]
        for bf in [bf_base, bf_large]:
            for item in items:
                bf.insert(item)
        
        # Test set
        test_items = [f"test_{i}" for i in range(5000)]
        
        fp_base = sum(1 for item in test_items if bf_base.contains(item))
        fp_large = sum(1 for item in test_items if bf_large.contains(item))
        
        fpr_base = fp_base / len(test_items)
        fpr_large = fp_large / len(test_items)
        
        # The larger filter should have a significantly lower FPR
        # Allow some variance, but it must be lower
        assert fpr_large < fpr_base, \
            f"Larger filter FPR ({fpr_large}) should be lower than base ({fpr_base})"

    def test_zero_false_negatives(self):
        """Verify that Bloom filters never produce false negatives."""
        bf = ArrayBloomFilter(self.m, self.k)
        
        # Insert all items
        for item in self.inserted_items:
            bf.insert(item)
        
        # Check every inserted item is found
        for item in self.inserted_items:
            assert bf.contains(item), f"False negative detected for {item}"

    def test_fpr_theoretical_formula_match(self):
        """Verify the theoretical FPR formula is calculated correctly in the class."""
        # The theoretical FPR is (1 - e^(-kn/m))^k
        # We can verify this by checking the class's false_positive_rate method
        # against the mathematical formula directly.
        
        bf = ArrayBloomFilter(self.m, self.k)
        class_theoretical = bf.false_positive_rate()
        
        manual_theoretical = (1 - math.exp(-self.k * self.n / self.m)) ** self.k
        
        # They should be identical (or very close due to floating point)
        assert math.isclose(class_theoretical, manual_theoretical, rel_tol=1e-9), \
            f"Class theoretical FPR ({class_theoretical}) != Manual ({manual_theoretical})"