"""
Implementation of VectorBloomFilter using bytearray for dynamic bit vector storage.

This implementation uses Python's bytearray to simulate a bit vector, providing
a middle-ground between native Python lists (ArrayBloomFilter) and specialized
bitarray libraries (BitsetBloomFilter).
"""
from typing import Union, Iterable, List, Tuple
import math
import struct

from .base import BloomFilter, calculate_optimal_parameters
from .hash_utils import get_k_hashes, hash_murmur3_32


class VectorBloomFilter(BloomFilter):
    """
    Bloom Filter implementation using a bytearray as the underlying bit vector.
    
    This class uses a bytearray to store bits, where each byte represents 8 bits.
    It provides efficient memory usage compared to Python lists while maintaining
    compatibility with the standard BloomFilter interface.
    
    Attributes:
        size (int): Total number of bits in the filter.
        k (int): Number of hash functions to use.
        fpr_target (float): Target false positive rate.
        bit_vector (bytearray): The underlying bit storage.
    """
    
    def __init__(
        self,
        expected_elements: int,
        fpr_target: float = 0.01,
        seed: int = 42
    ):
        """
        Initialize the VectorBloomFilter.
        
        Args:
            expected_elements: The expected number of elements to insert.
            fpr_target: The target false positive rate (0 < fpr < 1).
            seed: Seed for hash functions to ensure reproducibility.
        
        Raises:
            ValueError: If fpr_target is not in (0, 1).
        """
        if not (0 < fpr_target < 1):
            raise ValueError("fpr_target must be between 0 and 1")
        
        # Calculate optimal m (bits) and k (hash functions)
        self.size, self.k = calculate_optimal_parameters(
            expected_elements, fpr_target
        )
        self.fpr_target = fpr_target
        self.expected_elements = expected_elements
        self.seed = seed
        
        # Calculate number of bytes needed
        # ceil(size / 8)
        num_bytes = (self.size + 7) // 8
        self.bit_vector = bytearray(num_bytes)
        
        # Track inserted count for statistics
        self._count = 0
    
    def _get_byte_index(self, bit_index: int) -> int:
        """
        Convert a bit index to a byte index in the bytearray.
        
        Args:
            bit_index: The index of the bit (0 to size-1).
        
        Returns:
            The index of the byte containing this bit.
        """
        return bit_index // 8
    
    def _get_bit_mask(self, bit_index: int) -> int:
        """
        Get the bit mask for a specific bit index within a byte.
        
        Args:
            bit_index: The index of the bit (0 to size-1).
        
        Returns:
            An integer with a single bit set at the appropriate position.
        """
        return 1 << (bit_index % 8)
    
    def _set_bit(self, bit_index: int) -> None:
        """
        Set a bit at the specified index to 1.
        
        Args:
            bit_index: The index of the bit to set.
        """
        byte_idx = self._get_byte_index(bit_index)
        mask = self._get_bit_mask(bit_index)
        self.bit_vector[byte_idx] |= mask
    
    def _get_bit(self, bit_index: int) -> bool:
        """
        Get the value of a bit at the specified index.
        
        Args:
            bit_index: The index of the bit to read.
        
        Returns:
            True if the bit is set, False otherwise.
        """
        byte_idx = self._get_byte_index(bit_index)
        mask = self._get_bit_mask(bit_index)
        return (self.bit_vector[byte_idx] & mask) != 0
    
    def insert(self, item: Union[str, bytes, int, float]) -> None:
        """
        Insert an item into the Bloom filter.
        
        The item is hashed using k different hash functions, and the corresponding
        bits in the bit vector are set to 1.
        
        Args:
            item: The item to insert. Can be a string, bytes, int, or float.
        """
        # Convert item to bytes for hashing
        if isinstance(item, str):
            item_bytes = item.encode('utf-8')
        elif isinstance(item, (int, float)):
            item_bytes = struct.pack('d', float(item))
        elif isinstance(item, bytes):
            item_bytes = item
        else:
            item_bytes = str(item).encode('utf-8')
        
        # Get k hash values
        hash_values = get_k_hashes(item_bytes, self.k, self.seed)
        
        # Set the corresponding bits
        for h in hash_values:
            bit_index = h % self.size
            self._set_bit(bit_index)
        
        self._count += 1
    
    def contains(self, item: Union[str, bytes, int, float]) -> bool:
        """
        Check if an item might be in the Bloom filter.
        
        Args:
            item: The item to check. Can be a string, bytes, int, or float.
        
        Returns:
            True if the item might be in the filter (possible false positive),
            False if the item is definitely not in the filter.
        """
        # Convert item to bytes for hashing
        if isinstance(item, str):
            item_bytes = item.encode('utf-8')
        elif isinstance(item, (int, float)):
            item_bytes = struct.pack('d', float(item))
        elif isinstance(item, bytes):
            item_bytes = item
        else:
            item_bytes = str(item).encode('utf-8')
        
        # Get k hash values
        hash_values = get_k_hashes(item_bytes, self.k, self.seed)
        
        # Check if all corresponding bits are set
        for h in hash_values:
            bit_index = h % self.size
            if not self._get_bit(bit_index):
                return False
        
        return True
    
    def false_positive_rate(self) -> float:
        """
        Calculate the theoretical false positive rate.
        
        Returns:
            The theoretical false positive rate based on the current number of
            inserted elements and the filter parameters.
        """
        n = self._count
        m = self.size
        k = self.k
        
        if n == 0:
            return 0.0
        
        # Theoretical FPR formula: (1 - e^(-kn/m))^k
        # Using the approximation for small probabilities
        return (1 - math.exp(-k * n / m)) ** k
    
    def memory_usage_bytes(self) -> int:
        """
        Calculate the memory usage of the bit vector.
        
        Returns:
            The size of the bit vector in bytes.
        """
        return len(self.bit_vector)
    
    @property
    def count(self) -> int:
        """Return the number of elements inserted."""
        return self._count
    
    @property
    def bits_per_element(self) -> float:
        """Calculate bits per element."""
        if self._count == 0:
            return 0.0
        return self.size / self._count