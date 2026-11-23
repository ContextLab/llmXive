"""
BitsetBloomFilter implementation using the bitarray library.

This module provides a memory-efficient Bloom Filter implementation
utilizing the third-party `bitarray` library for compact bit storage.
"""

from typing import Union, Iterable, List, Tuple, Optional
import math
import struct

from .base import BloomFilter, calculate_optimal_parameters
from .hash_utils import get_k_hashes, hash_murmur3_32

# Attempt to import bitarray; fail loudly if missing as per project constraints
try:
    from bitarray import bitarray
except ImportError:
    raise ImportError(
        "The 'bitarray' library is required for BitsetBloomFilter. "
        "Install it via 'pip install bitarray'."
    )


class BitsetBloomFilter(BloomFilter):
    """
    A Bloom Filter implementation using the bitarray library for storage.

    This implementation offers superior memory efficiency compared to
    native Python lists or bytearrays by packing bits tightly (1 bit per flag).

    Attributes:
        m (int): Total number of bits in the filter.
        k (int): Number of hash functions to use.
        n (int): Expected number of elements (for parameter calculation).
        fpr (float): Target false positive rate.
        bit_array (bitarray): The underlying bit storage.
    """

    def __init__(
        self,
        n: int,
        fpr: float,
        name: str = "BitsetBloomFilter"
    ):
        """
        Initialize the BitsetBloomFilter with optimal parameters.

        Args:
            n: Expected number of items to insert.
            fpr: Desired false positive rate (0 < fpr < 1).
            name: Identifier for this instance.
        """
        if not (0 < fpr < 1):
            raise ValueError("fpr must be between 0 and 1")
        if n <= 0:
            raise ValueError("n must be a positive integer")

        # Calculate optimal m and k based on n and fpr
        m, k = calculate_optimal_parameters(n, fpr)

        self.m = m
        self.k = k
        self.n = n
        self.fpr = fpr
        self.name = name
        self.count = 0

        # Initialize bitarray with all bits set to 0
        self.bit_array = bitarray(m)
        self.bit_array.setall(0)

    def insert(self, item: Union[str, bytes, int]) -> None:
        """
        Insert an item into the Bloom Filter.

        Args:
            item: The item to insert. Can be a string, bytes, or integer.
        """
        if item is None:
            raise ValueError("Cannot insert None into Bloom Filter")

        # Convert item to bytes if it isn't already
        if isinstance(item, str):
            item_bytes = item.encode('utf-8')
        elif isinstance(item, int):
            item_bytes = struct.pack('>Q', item)
        elif isinstance(item, bytes):
            item_bytes = item
        else:
            # Fallback for other types, convert to string then bytes
            item_bytes = str(item).encode('utf-8')

        # Get k hash indices
        indices = get_k_hashes(item_bytes, self.k, self.m)

        # Set bits to 1
        for idx in indices:
            self.bit_array[idx] = 1

        self.count += 1

    def insert_many(self, items: Iterable[Union[str, bytes, int]]) -> None:
        """
        Insert multiple items into the Bloom Filter efficiently.

        Args:
            items: An iterable of items to insert.
        """
        for item in items:
            self.insert(item)

    def contains(self, item: Union[str, bytes, int]) -> bool:
        """
        Check if an item might be in the Bloom Filter.

        Args:
            item: The item to check.

        Returns:
            True if the item might be in the set (possible false positive),
            False if the item is definitely not in the set.
        """
        if item is None:
            return False

        # Convert item to bytes
        if isinstance(item, str):
            item_bytes = item.encode('utf-8')
        elif isinstance(item, int):
            item_bytes = struct.pack('>Q', item)
        elif isinstance(item, bytes):
            item_bytes = item
        else:
            item_bytes = str(item).encode('utf-8')

        # Get k hash indices
        indices = get_k_hashes(item_bytes, self.k, self.m)

        # Check if all bits are set
        for idx in indices:
            if not self.bit_array[idx]:
                return False

        return True

    def __contains__(self, item: Union[str, bytes, int]) -> bool:
        """Enable 'item in filter' syntax."""
        return self.contains(item)

    def false_positive_rate(self) -> float:
        """
        Calculate the theoretical false positive rate.

        Returns:
            Theoretical FPR based on current m, k, and count.
        """
        # Formula: (1 - e^(-k * n / m))^k
        # Using current count as n
        if self.count == 0:
            return 0.0

        exponent = -self.k * self.count / self.m
        return (1 - math.exp(exponent)) ** self.k

    def memory_usage_bits(self) -> int:
        """
        Return the memory usage in bits.

        Returns:
            Total bits used (m).
        """
        return self.m

    def memory_usage_bytes(self) -> float:
        """
        Return the memory usage in bytes.

        Returns:
            Memory usage in bytes (rounded up).
        """
        return math.ceil(self.m / 8)

    def get_stats(self) -> dict:
        """
        Return a dictionary of current filter statistics.

        Returns:
            Dict containing m, k, n, fpr, count, and memory usage.
        """
        return {
            "type": self.name,
            "m": self.m,
            "k": self.k,
            "n_expected": self.n,
            "fpr_target": self.fpr,
            "items_inserted": self.count,
            "theoretical_fpr": self.false_positive_rate(),
            "memory_bits": self.memory_usage_bits(),
            "memory_bytes": self.memory_usage_bytes()
        }

    def to_dict(self) -> dict:
        """
        Serialize the filter state to a dictionary.

        Note: The bitarray itself is large, so we store the hex representation
        of the bits rather than the raw object for portability.

        Returns:
            Dict containing configuration and bit state.
        """
        return {
            "m": self.m,
            "k": self.k,
            "n": self.n,
            "fpr": self.fpr,
            "count": self.count,
            "bits_hex": self.bit_array.tobytes().hex()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'BitsetBloomFilter':
        """
        Reconstruct a BitsetBloomFilter from a dictionary.

        Args:
            data: Dictionary containing filter state.

        Returns:
            A new BitsetBloomFilter instance.
        """
        # Create an instance with the stored parameters
        bf = cls.__new__(cls)
        bf.m = data['m']
        bf.k = data['k']
        bf.n = data['n']
        bf.fpr = data['fpr']
        bf.count = data['count']
        bf.name = "BitsetBloomFilter"

        # Reconstruct bitarray from hex string
        bf.bit_array = bitarray()
        bf.bit_array.fromhex(data['bits_hex'])

        return bf

    def __len__(self) -> int:
        """Return the number of items inserted."""
        return self.count

    def __repr__(self) -> str:
        return (
            f"<BitsetBloomFilter(m={self.m}, k={self.k}, "
            f"count={self.count}, fpr={self.fpr:.4f})>"
        )