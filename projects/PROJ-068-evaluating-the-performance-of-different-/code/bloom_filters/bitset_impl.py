"""
Implementation of BloomFilter using the bitarray library for specialized bitset storage.
"""
from typing import Union, Iterable, List, Tuple, Optional
import math
import struct

from .base import BloomFilter, calculate_optimal_parameters
from .hash_utils import get_k_hashes, hash_murmur3_32

try:
    from bitarray import bitarray
except ImportError:
    raise ImportError(
        "The 'bitarray' library is required for BitsetBloomFilter. "
        "Please install it via: pip install bitarray"
    )


class BitsetBloomFilter(BloomFilter):
    """
    A Bloom Filter implementation using the bitarray library for memory-efficient
    bit-level storage.

    Attributes:
        size (int): Total number of bits in the filter.
        num_hashes (int): Number of hash functions (k) used.
        elements_added (int): Count of elements inserted.
        fpr_target (float): Target false positive rate.
        _bit_array (bitarray): The underlying bit storage.
    """

    def __init__(
        self,
        n_elements: int,
        fpr_target: float,
        hash_seed: int = 42
    ):
        """
        Initializes the BitsetBloomFilter with optimal parameters calculated
        based on the expected number of elements and target FPR.

        Args:
            n_elements (int): Expected number of elements to insert (n).
            fpr_target (float): Target false positive rate (p).
            hash_seed (int): Seed for the hash functions.
        """
        # Validate inputs
        if n_elements <= 0:
            raise ValueError("n_elements must be a positive integer.")
        if not (0 < fpr_target < 1):
            raise ValueError("fpr_target must be between 0 and 1.")

        # Calculate optimal m (bits) and k (hashes) using inherited logic
        m, k = calculate_optimal_parameters(n_elements, fpr_target)

        self.size = m
        self.num_hashes = k
        self.elements_added = 0
        self.fpr_target = fpr_target
        self.hash_seed = hash_seed

        # Initialize bitarray with m bits, all set to 0
        self._bit_array = bitarray(m)
        self._bit_array.setall(0)

    def insert(self, item: Union[str, bytes, int, float]) -> None:
        """
        Inserts an item into the Bloom filter.

        Args:
            item: The item to insert. Can be string, bytes, or hashable primitive.
        """
        if item is None:
            raise ValueError("Cannot insert None into the Bloom filter.")

        # Normalize item to bytes for hashing
        if isinstance(item, str):
            item_bytes = item.encode('utf-8')
        elif isinstance(item, (int, float)):
            # Convert numeric types to a consistent byte representation
            item_bytes = struct.pack('d', float(item))
        elif isinstance(item, bytes):
            item_bytes = item
        else:
            # Fallback for other types: use string representation
            item_bytes = str(item).encode('utf-8')

        # Get k hash indices
        indices = get_k_hashes(
            item_bytes,
            self.num_hashes,
            self.hash_seed
        )

        # Set bits at calculated indices
        for idx in indices:
            # Ensure index is within bounds (should be guaranteed by get_k_hashes)
            if 0 <= idx < self.size:
                self._bit_array[idx] = 1

        self.elements_added += 1

    def contains(self, item: Union[str, bytes, int, float]) -> bool:
        """
        Checks if an item is possibly in the Bloom filter.

        Args:
            item: The item to check.

        Returns:
            bool: True if the item might be in the set, False if definitely not.
        """
        if item is None:
            return False

        # Normalize item to bytes for hashing
        if isinstance(item, str):
            item_bytes = item.encode('utf-8')
        elif isinstance(item, (int, float)):
            item_bytes = struct.pack('d', float(item))
        elif isinstance(item, bytes):
            item_bytes = item
        else:
            item_bytes = str(item).encode('utf-8')

        # Get k hash indices
        indices = get_k_hashes(
            item_bytes,
            self.num_hashes,
            self.hash_seed
        )

        # Check if all bits at indices are set
        for idx in indices:
            if not (0 <= idx < self.size):
                return False # Should not happen if logic is correct
            if self._bit_array[idx] == 0:
                return False

        return True

    def false_positive_rate(self) -> float:
        """
        Calculates the theoretical false positive rate based on current state.

        Returns:
            float: The estimated FPR.
        """
        if self.elements_added == 0:
            return 0.0

        # Formula: (1 - e^(-kn/m))^k
        # where k = num_hashes, n = elements_added, m = size
        k = self.num_hashes
        n = self.elements_added
        m = self.size

        if m == 0:
            return 1.0

        exponent = - (k * n) / m
        prob_bit_set = 1.0 - math.exp(exponent)
        fpr = math.pow(prob_bit_set, k)

        return fpr

    def get_memory_usage_bytes(self) -> int:
        """
        Calculates the memory usage of the bitarray in bytes.

        Returns:
            int: Memory usage in bytes.
        """
        # bitarray overhead is minimal, mostly the bits themselves
        # bitarray stores bits, so size in bytes is ceil(size / 8)
        # plus a small object overhead, but for benchmarking we focus on the data size
        return self._bit_array.buffer_info()[1]

    def __len__(self) -> int:
        """Returns the number of elements inserted."""
        return self.elements_added

    def __repr__(self) -> str:
        return (
            f"BitsetBloomFilter(size={self.size}, "
            f"k={self.num_hashes}, "
            f"elements={self.elements_added}, "
            f"fpr_target={self.fpr_target:.4f})"
        )
