"""
Implementation of ArrayBloomFilter using native Python lists.

This module provides a Bloom filter implementation that utilizes standard
Python lists as the underlying bit array. While less memory-efficient than
specialized bitset libraries, it serves as a baseline for performance
comparison and ensures compatibility without external C-extension dependencies
for the bit storage mechanism.
"""

from typing import List, Union, Iterable, Optional, Dict, Tuple
import math
import struct

from .base import BloomFilter, calculate_optimal_parameters
from .hash_utils import get_k_hashes, hash_murmur3_32


class ArrayBloomFilter(BloomFilter):
    """
    A Bloom filter implementation using native Python lists.

    Attributes:
        bits (List[int]): The underlying bit array represented as a list of integers (0 or 1).
        size (int): Total number of bits in the filter.
        k (int): Number of hash functions to use.
        n_elements (int): Count of elements inserted.
    """

    def __init__(
        self,
        n_elements: int,
        fpr: float,
        seed: int = 42,
    ):
        """
        Initialize the ArrayBloomFilter.

        Args:
            n_elements (int): Expected number of elements to insert.
            fpr (float): Target false positive rate (0 < fpr < 1).
            seed (int): Seed for hash functions to ensure reproducibility.
        """
        if not (0 < fpr < 1):
            raise ValueError(f"FPR must be between 0 and 1, got {fpr}")
        if n_elements <= 0:
            raise ValueError(f"n_elements must be positive, got {n_elements}")

        # Calculate optimal m (bits) and k (hash functions)
        self.size, self.k = calculate_optimal_parameters(n_elements, fpr)
        self.n_elements = 0
        self.seed = seed

        # Initialize bit array with 0s
        self.bits: List[int] = [0] * self.size

    def _get_hash_indices(self, item: Union[str, bytes, int]) -> List[int]:
        """
        Compute the k hash indices for a given item.

        Args:
            item: The item to hash.

        Returns:
            List[int]: A list of k indices in the bit array.
        """
        return get_k_hashes(item, self.k, self.seed)

    def insert(self, item: Union[str, bytes, int]) -> None:
        """
        Insert an item into the Bloom filter.

        Args:
            item: The item to insert. Can be a string, bytes, or integer.
        """
        indices = self._get_hash_indices(item)
        for idx in indices:
            self.bits[idx] = 1
        self.n_elements += 1

    def insert_many(self, items: Iterable[Union[str, bytes, int]]) -> None:
        """
        Insert multiple items into the Bloom filter.

        Args:
            items: An iterable of items to insert.
        """
        for item in items:
            self.insert(item)

    def contains(self, item: Union[str, bytes, int]) -> bool:
        """
        Check if an item might be in the Bloom filter.

        Args:
            item: The item to check.

        Returns:
            bool: True if the item might be in the set (possible false positive),
                  False if the item is definitely not in the set.
        """
        indices = self._get_hash_indices(item)
        return all(self.bits[idx] == 1 for idx in indices)

    def contains_many(self, items: Iterable[Union[str, bytes, int]]) -> List[bool]:
        """
        Check multiple items against the Bloom filter.

        Args:
            items: An iterable of items to check.

        Returns:
            List[bool]: A list of booleans indicating potential membership.
        """
        return [self.contains(item) for item in items]

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """
        Get statistics about the current state of the filter.

        Returns:
            Dict[str, Union[int, float]]: Dictionary containing size, k, n_elements,
                                          bits_set, and estimated_fpr.
        """
        bits_set = sum(self.bits)
        # Estimated FPR formula: (1 - e^(-kn/m))^k
        if self.size == 0:
            estimated_fpr = 0.0
        else:
            estimated_fpr = (1 - math.exp(-self.k * self.n_elements / self.size)) ** self.k

        return {
            "size": self.size,
            "k": self.k,
            "n_elements": self.n_elements,
            "bits_set": bits_set,
            "estimated_fpr": estimated_fpr,
            "implementation_type": "array",
        }

    def __len__(self) -> int:
        """Return the total number of bits in the filter."""
        return self.size

    def __repr__(self) -> str:
        return f"ArrayBloomFilter(size={self.size}, k={self.k}, elements={self.n_elements})"