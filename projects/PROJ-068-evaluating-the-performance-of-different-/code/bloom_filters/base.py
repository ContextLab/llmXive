from abc import ABC, abstractmethod
from typing import List, Union, Dict, Tuple, Iterable, Optional
import math
from collections import defaultdict

# Configuration constants
FPR_TARGETS = {
    "low": 1e-3,
    "medium": 1e-2,
    "high": 1e-1
}

class BloomFilter(ABC):
    """Abstract base class for all Bloom filter implementations."""

    def __init__(self, num_elements: int, false_positive_rate: float):
        """
        Initialize the Bloom filter.

        Args:
            num_elements: Expected number of elements to insert.
            false_positive_rate: Target false positive rate (e.g., 0.01 for 1%).
        """
        self.num_elements = num_elements
        self.false_positive_rate = false_positive_rate
        self.m, self.k = calculate_optimal_parameters(num_elements, false_positive_rate)
        self.bit_array = self._initialize_bit_array()
        self.inserted_count = 0

    @abstractmethod
    def _initialize_bit_array(self) -> Union[List[int], bytearray, List[bool]]:
        """Initialize the underlying bit storage."""
        pass

    @abstractmethod
    def insert(self, item: Union[str, bytes, int]) -> None:
        """Insert an item into the filter."""
        pass

    @abstractmethod
    def contains(self, item: Union[str, bytes, int]) -> bool:
        """Check if an item might be in the filter."""
        pass

    @abstractmethod
    def get_memory_usage_bits(self) -> int:
        """Return the memory usage in bits."""
        pass

    def false_positive_rate(self) -> float:
        """Return the theoretical false positive rate."""
        return self.false_positive_rate

    def __len__(self) -> int:
        """Return the number of inserted elements."""
        return self.inserted_count

    def validate_consistency(self, other: 'BloomFilter', test_set: List[Union[str, bytes, int]]) -> Dict[str, int]:
        """
        Validate that this implementation produces identical results to another
        implementation for a given set of test queries.

        Args:
            other: Another BloomFilter instance to compare against.
            test_set: List of items to query both filters with.

        Returns:
            A dictionary with counts of matches and mismatches.
        """
        mismatches = 0
        total_queries = len(test_set)

        for item in test_set:
            self_result = self.contains(item)
            other_result = other.contains(item)

            if self_result != other_result:
                mismatches += 1

        return {
            "total_queries": total_queries,
            "mismatches": mismatches,
            "match_rate": (total_queries - mismatches) / total_queries if total_queries > 0 else 1.0
        }


def calculate_optimal_parameters(n: int, p: float) -> Tuple[int, int]:
    """
    Calculate optimal m (number of bits) and k (number of hash functions)
    for a Bloom filter given n expected elements and p desired false positive rate.

    Formula:
      m = - (n * ln(p)) / (ln(2)^2)
      k = (m / n) * ln(2)

    Args:
        n: Expected number of elements.
        p: Desired false positive rate.

    Returns:
        Tuple of (m, k) as integers.
    """
    if n <= 0:
        raise ValueError("Number of elements must be positive")
    if p <= 0 or p >= 1:
        raise ValueError("False positive rate must be between 0 and 1 (exclusive)")

    m = - (n * math.log(p)) / (math.log(2) ** 2)
    k = (m / n) * math.log(2)

    return int(math.ceil(m)), int(math.ceil(k))


def get_config_for_sizes(sizes: List[int], fpr_targets: Optional[Dict[str, float]] = None) -> List[Dict]:
    """
    Generate configuration dictionaries for a list of dataset sizes.

    Args:
        sizes: List of dataset sizes (number of elements).
        fpr_targets: Dictionary mapping FPR names to values. Defaults to FPR_TARGETS.

    Returns:
        List of config dicts with keys: 'size', 'fpr_target', 'm', 'k'
    """
    if fpr_targets is None:
        fpr_targets = FPR_TARGETS

    configs = []
    for size in sizes:
        for name, fpr in fpr_targets.items():
            m, k = calculate_optimal_parameters(size, fpr)
            configs.append({
                "size": size,
                "fpr_target": fpr,
                "fpr_name": name,
                "m": m,
                "k": k
            })
    return configs


def get_fpr_configs_for_sizes(sizes: List[int]) -> List[Dict]:
    """
    Convenience wrapper to get configurations for standard FPR targets.

    Args:
        sizes: List of dataset sizes.

    Returns:
        List of config dicts for all standard FPR targets.
    """
    return get_config_for_sizes(sizes, FPR_TARGETS)
