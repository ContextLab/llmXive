"""
Deterministic MurmurHash3 wrapper for Bloom Filter implementations.

This module provides a consistent interface to MurmurHash3 (x86_32 variant)
ensuring identical outputs across all three Bloom Filter variants (Array,
Vector, Bitset). It uses the `murmurhash3` library which was added to
requirements.txt in T002.
"""

import struct
from typing import List, Tuple

try:
    from murmurhash3 import murmurhash3
except ImportError:
    raise ImportError(
        "The 'murmurhash3' package is required but not installed. "
        "Please run: pip install murmurhash3"
    )


def _get_seed() -> int:
    """
    Returns a fixed seed for deterministic hashing.
    Using a fixed seed ensures that the same input always produces the same output.
    """
    return 0xC0FFEE00  # Arbitrary fixed seed


def hash_murmur3_32(data: bytes, seed: int = None) -> int:
    """
    Computes the MurmurHash3 (x86_32) hash of the input data.

    Args:
        data: The input data as bytes.
        seed: An optional seed. If None, a fixed seed is used for determinism.

    Returns:
        A 32-bit unsigned integer hash value.
    """
    if seed is None:
        seed = _get_seed()

    # murmurhash3.murmurhash3 returns a signed 32-bit integer in some versions
    # or unsigned in others. We ensure we treat it as unsigned 32-bit.
    raw_hash = murmurhash3(data, seed)
    return raw_hash & 0xFFFFFFFF


def get_k_hashes(data: bytes, k: int, seed: int = None) -> List[int]:
    """
    Generates k distinct hash values for a given data item.

    This implementation uses the double hashing technique:
    h(i) = (h1 + i * h2) mod m
    where h1 is the base hash and h2 is a secondary hash derived from h1 + a salt.
    This avoids computing k separate full hash functions, which is efficient.

    Args:
        data: The input data as bytes.
        k: The number of hash values needed.
        seed: The base seed. If None, a fixed seed is used.

    Returns:
        A list of k integers (hash values).
    """
    if seed is None:
        seed = _get_seed()

    # Compute h1
    h1 = hash_murmur3_32(data, seed)

    # Compute h2 using a slightly modified seed to ensure independence
    # We use seed + 1 as the salt for h2
    h2 = hash_murmur3_32(data, seed + 1)

    hashes = []
    for i in range(k):
        # Double hashing formula: h(i) = (h1 + i * h2) mod 2^32
        # We use 2^32 as the modulus for 32-bit integers
        combined = (h1 + i * h2) & 0xFFFFFFFF
        hashes.append(combined)

    return hashes


def get_hash_indices(data: bytes, k: int, m: int, seed: int = None) -> List[int]:
    """
    Generates k distinct indices in the range [0, m) for a given data item.

    This is a convenience wrapper around get_k_hashes that maps the hash
    values to valid bit array indices.

    Args:
        data: The input data as bytes.
        k: The number of hash values needed.
        m: The size of the bit array (number of bits).
        seed: The base seed. If None, a fixed seed is used.

    Returns:
        A list of k integer indices in the range [0, m).
    """
    raw_hashes = get_k_hashes(data, k, seed)
    return [h % m for h in raw_hashes]