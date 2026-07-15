from abc import ABC, abstractmethod
from typing import List, Union, Dict, Tuple, Iterable, Optional
import math
from collections import defaultdict

# Constants for FPR targets (Constitution Principle VI)
FPR_TARGETS: Tuple[float, float, float] = (0.01, 0.05, 0.10)

def calculate_optimal_parameters(n: int, p: float) -> Tuple[int, int]:
    """
    Calculate optimal m (number of bits) and k (number of hash functions)
    for a given expected number of elements n and target false positive rate p.

    Formulae:
      m = -(n * ln(p)) / (ln(2)^2)
      k = (m / n) * ln(2)

    Args:
        n: Expected number of elements to insert
        p: Target false positive rate

    Returns:
        Tuple of (m, k)
    """
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 < p < 1:
        raise ValueError("p must be between 0 and 1")

    m = - (n * math.log(p)) / (math.log(2) ** 2)
    m = int(math.ceil(m))
    k = (m / n) * math.log(2)
    k = int(round(k))
    if k == 0:
        k = 1
    return m, k

def get_config_for_sizes(sizes: List[int], fpr: float = 0.01) -> Dict[int, Dict[str, int]]:
    """
    Generate configuration parameters for a list of dataset sizes.

    Args:
        sizes: List of expected element counts
        fpr: Target false positive rate (default 0.01)

    Returns:
        Dictionary mapping size -> {'m': bits, 'k': hash_functions}
    """
    return {n: {'m': calculate_optimal_parameters(n, fpr)[0],
                'k': calculate_optimal_parameters(n, fpr)[1]}
            for n in sizes}

class BloomFilter(ABC):
    """
    Abstract Base Class for Bloom Filter implementations.
    All concrete implementations must provide insert and contains methods.
    """

    def __init__(self, m: int, k: int, fpr_target: float):
        """
        Initialize the Bloom Filter.

        Args:
            m: Number of bits in the filter
            k: Number of hash functions to use
            fpr_target: Theoretical target false positive rate
        """
        self.m = m
        self.k = k
        self.fpr_target = fpr_target
        self._inserted_count = 0

    @abstractmethod
    def insert(self, item: Union[str, bytes, int]) -> None:
        """Insert an item into the filter."""
        pass

    @abstractmethod
    def contains(self, item: Union[str, bytes, int]) -> bool:
        """Check if an item is possibly in the filter."""
        pass

    @abstractmethod
    def get_memory_bits(self) -> int:
        """Return the total number of bits used by this implementation."""
        pass

    def get_memory_bytes(self) -> int:
        """Return the total number of bytes used by this implementation."""
        return math.ceil(self.get_memory_bits() / 8)

    def _validate_consistency(self, items: List[Union[str, bytes, int]],
                              other_filters: List['BloomFilter'],
                              query_items: Optional[List[Union[str, bytes, int]]] = None) -> Dict[str, bool]:
        """
        Validate that this filter produces identical membership results
        as the provided other filters for a given set of items.

        Args:
            items: List of items to insert into all filters
            other_filters: List of other BloomFilter instances to compare against
            query_items: Optional list of items to query (defaults to 'items')

        Returns:
            Dictionary with keys 'all_match' (bool) and 'details' (str)
        """
        if not items:
            return {'all_match': True, 'details': 'No items to validate.'}

        if query_items is None:
            query_items = items

        # Insert items into all filters
        for other in other_filters:
            for item in items:
                other.insert(item)

        # Perform queries
        mismatches = []
        for item in query_items:
            self_result = self.contains(item)
            for i, other in enumerate(other_filters):
                other_result = other.contains(item)
                if self_result != other_result:
                    mismatches.append({
                        'item': item,
                        'self_result': self_result,
                        'other_idx': i,
                        'other_result': other_result
                    })

        if mismatches:
            details = f"Found {len(mismatches)} mismatches. First: {mismatches[0]}"
            return {'all_match': False, 'details': details}
        else:
            return {'all_match': True, 'details': 'All implementations returned identical results.'}

    @classmethod
    def validate_all_implementations(cls,
                                     implementations: List['BloomFilter'],
                                     items: List[Union[str, bytes, int]],
                                     query_items: Optional[List[Union[str, bytes, int]]] = None) -> bool:
        """
        Static helper to validate consistency across a list of BloomFilter instances.
        Ensures all implementations produce the same membership results for the same inputs.

        Args:
            implementations: List of BloomFilter instances to compare
            items: Items to insert
            query_items: Items to query (defaults to items)

        Returns:
            True if all implementations are consistent, False otherwise.
        """
        if len(implementations) < 2:
            return True

        # Use the first implementation as the reference
        reference = implementations[0]
        others = implementations[1:]

        result = reference._validate_consistency(items, others, query_items)
        if not result['all_match']:
            raise AssertionError(f"Implementation consistency check failed: {result['details']}")
        return True