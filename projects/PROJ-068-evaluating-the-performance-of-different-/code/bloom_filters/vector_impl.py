"""
Vector-based Bloom Filter implementation using bytearray.

This module provides the VectorBloomFilter class, which implements the
BloomFilter abstract base class using a bytearray as the underlying
bit vector. This is more memory-efficient than native Python lists
but less efficient than the bitarray library.
"""

from typing import Union, Iterable, List, Tuple, Optional
import math
import struct

from .base import BloomFilter, calculate_optimal_parameters
from .hash_utils import get_k_hashes, hash_murmur3_32


class VectorBloomFilter(BloomFilter):
    """
    A Bloom Filter implementation using a bytearray for the bit vector.

    This implementation uses a bytearray where each byte represents 8 bits.
    It offers better memory efficiency than a list of integers but lacks
    the specialized bit-manipulation speed of the bitarray library.

    Attributes:
        size (int): Total number of bits in the filter.
        k (int): Number of hash functions to use.
        fpr (float): Target false positive rate.
        _vector (bytearray): The underlying bit vector storage.
    """

    def __init__(
        self,
        expected_elements: int,
        false_positive_rate: float,
        seed: int = 42
    ):
        """
        Initialize the VectorBloomFilter.

        Args:
            expected_elements (int): The expected number of elements to insert.
            false_positive_rate (float): The desired false positive rate (0 < fpr < 1).
            seed (int): Seed for the hash functions.
        """
        if not 0 < false_positive_rate < 1:
            raise ValueError("false_positive_rate must be between 0 and 1")

        # Calculate optimal m (bits) and k (hash functions)
        m, k = calculate_optimal_parameters(expected_elements, false_positive_rate)

        self.size = m
        self.k = k
        self.fpr = false_positive_rate
        self.seed = seed

        # Calculate number of bytes needed (ceil(m / 8))
        num_bytes = (m + 7) // 8
        self._vector = bytearray(num_bytes)

    def _set_bit(self, index: int) -> None:
        """Set the bit at the given index to 1."""
        byte_index = index // 8
        bit_index = index % 8
        self._vector[byte_index] |= (1 << bit_index)

    def _get_bit(self, index: int) -> bool:
        """Get the value of the bit at the given index."""
        byte_index = index // 8
        bit_index = index % 8
        return bool(self._vector[byte_index] & (1 << bit_index))

    def insert(self, element: Union[str, bytes, int]) -> None:
        """
        Insert an element into the Bloom filter.

        Args:
            element: The element to insert. Can be a string, bytes, or integer.
        """
        if element is None:
            raise ValueError("Cannot insert None into Bloom filter")

        # Convert element to bytes if it's not already
        if isinstance(element, int):
            # Convert integer to bytes (big-endian)
            # Handle negative numbers by using two's complement representation
            if element < 0:
                # For negative numbers, we need a fixed width.
                # We'll use a reasonable width based on the magnitude.
                byte_length = (element.bit_length() // 8) + 2
                element_bytes = element.to_bytes(byte_length, byteorder='big', signed=True)
            else:
                byte_length = (element.bit_length() // 8) + 1 if element > 0 else 1
                element_bytes = element.to_bytes(byte_length, byteorder='big', signed=False)
        elif isinstance(element, str):
            element_bytes = element.encode('utf-8')
        else:
            element_bytes = element

        # Get k hash indices
        indices = get_k_hashes(element_bytes, self.k, self.seed, self.size)

        for index in indices:
            self._set_bit(index)

    def contains(self, element: Union[str, bytes, int]) -> bool:
        """
        Check if an element is possibly in the Bloom filter.

        Args:
            element: The element to check. Can be a string, bytes, or integer.

        Returns:
            bool: True if the element might be in the set, False if it definitely is not.
        """
        if element is None:
            return False

        # Convert element to bytes if it's not already
        if isinstance(element, int):
            if element < 0:
                byte_length = (element.bit_length() // 8) + 2
                element_bytes = element.to_bytes(byte_length, byteorder='big', signed=True)
            else:
                byte_length = (element.bit_length() // 8) + 1 if element > 0 else 1
                element_bytes = element.to_bytes(byte_length, byteorder='big', signed=False)
        elif isinstance(element, str):
            element_bytes = element.encode('utf-8')
        else:
            element_bytes = element

        # Get k hash indices
        indices = get_k_hashes(element_bytes, self.k, self.seed, self.size)

        for index in indices:
            if not self._get_bit(index):
                return False

        return True

    def false_positive_rate(self) -> float:
        """
        Calculate the theoretical false positive rate.

        Returns:
            float: The theoretical false positive rate.
        """
        # Theoretical FPR: (1 - e^(-k*n/m))^k
        n = self.size  # This is m in the formula, n is expected_elements
        # We need to estimate n based on current bits set, but for theoretical
        # calculation we use the initial parameters
        # Actually, the formula uses n (number of inserted elements)
        # Since we don't track n, we return the target FPR
        # Or we can calculate based on the actual bits set
        # Let's calculate based on actual bits set for a more accurate estimate
        bits_set = sum(bin(b).count('1') for b in self._vector)
        n_estimated = bits_set / self.k if self.k > 0 else 0
        
        if n_estimated == 0:
            return 0.0

        # (1 - exp(-k * n / m))^k
        m = self.size
        k = self.k
        exponent = -k * n_estimated / m
        return (1 - math.exp(exponent)) ** k

    def memory_usage_bytes(self) -> int:
        """
        Calculate the memory usage of the filter in bytes.

        Returns:
            int: Memory usage in bytes.
        """
        return len(self._vector)

    def __len__(self) -> int:
        """Return the size of the filter in bits."""
        return self.size

    def __repr__(self) -> str:
        """Return a string representation of the Bloom filter."""
        return (
            f"VectorBloomFilter(size={self.size}, k={self.k}, "
            f"fpr={self.fpr:.6f}, bytes={self.memory_usage_bytes()})"
        )

    def union(self, other: 'VectorBloomFilter') -> 'VectorBloomFilter':
        """
        Create a new Bloom filter that is the union of this and another.

        Args:
            other: Another VectorBloomFilter with the same size and k.

        Returns:
            VectorBloomFilter: A new filter representing the union.

        Raises:
            ValueError: If the filters have different sizes or k values.
        """
        if self.size != other.size or self.k != other.k:
            raise ValueError("Cannot union Bloom filters with different sizes or k values")

        result = VectorBloomFilter.__new__(VectorBloomFilter)
        result.size = self.size
        result.k = self.k
        result.fpr = self.fpr
        result.seed = self.seed
        result._vector = bytearray(len(self._vector))

        for i in range(len(self._vector)):
            result._vector[i] = self._vector[i] | other._vector[i]

        return result

    def intersection(self, other: 'VectorBloomFilter') -> 'VectorBloomFilter':
        """
        Create a new Bloom filter that is the intersection of this and another.

        Args:
            other: Another VectorBloomFilter with the same size and k.

        Returns:
            VectorBloomFilter: A new filter representing the intersection.

        Raises:
            ValueError: If the filters have different sizes or k values.
        """
        if self.size != other.size or self.k != other.k:
            raise ValueError("Cannot intersect Bloom filters with different sizes or k values")

        result = VectorBloomFilter.__new__(VectorBloomFilter)
        result.size = self.size
        result.k = self.k
        result.fpr = self.fpr
        result.seed = self.seed
        result._vector = bytearray(len(self._vector))

        for i in range(len(self._vector)):
            result._vector[i] = self._vector[i] & other._vector[i]

        return result