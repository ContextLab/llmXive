"""
Lossless Compression Module.

Implements wrappers for gzip, bzip2, lzma, and lz4 at specified compression levels.
Ensures bitwise identical reconstruction after decompression.
"""

import gzip
import bz2
import lzma
import lz4.frame
import numpy as np
import json
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

# Constants for compression levels
GZIP_LEVELS = [1, 5, 9]
BZIP2_LEVELS = [1, 5, 9]
LZMA_LEVELS = [0, 5, 9]
LZ4_LEVELS = [1, 5, 9]  # lz4 frame levels

def compress_gzip(data: np.ndarray, level: int = 5) -> bytes:
    """
    Compress numpy array data using gzip.

    Args:
        data: Input numpy array.
        level: Compression level (1-9).

    Returns:
        Compressed bytes.
    """
    if level not in GZIP_LEVELS:
        raise ValueError(f"Gzip level must be in {GZIP_LEVELS}")
    
    # Serialize to bytes
    raw_bytes = data.tobytes()
    return gzip.compress(raw_bytes, compresslevel=level)

def decompress_gzip(compressed_data: bytes, shape: Tuple[int, ...], dtype: np.dtype) -> np.ndarray:
    """
    Decompress gzip data back to numpy array.

    Args:
        compressed_data: Compressed bytes.
        shape: Original array shape.
        dtype: Original array dtype.

    Returns:
        Decompressed numpy array.
    """
    raw_bytes = gzip.decompress(compressed_data)
    return np.frombuffer(raw_bytes, dtype=dtype).reshape(shape)

def compress_bzip2(data: np.ndarray, level: int = 5) -> bytes:
    """
    Compress numpy array data using bzip2.

    Args:
        data: Input numpy array.
        level: Compression level (1-9).

    Returns:
        Compressed bytes.
    """
    if level not in BZIP2_LEVELS:
        raise ValueError(f"Bzip2 level must be in {BZIP2_LEVELS}")
    
    raw_bytes = data.tobytes()
    return bz2.compress(raw_bytes, compresslevel=level)

def decompress_bzip2(compressed_data: bytes, shape: Tuple[int, ...], dtype: np.dtype) -> np.ndarray:
    """
    Decompress bzip2 data back to numpy array.

    Args:
        compressed_data: Compressed bytes.
        shape: Original array shape.
        dtype: Original array dtype.

    Returns:
        Decompressed numpy array.
    """
    raw_bytes = bz2.decompress(compressed_data)
    return np.frombuffer(raw_bytes, dtype=dtype).reshape(shape)

def compress_lzma(data: np.ndarray, level: int = 5) -> bytes:
    """
    Compress numpy array data using lzma.

    Args:
        data: Input numpy array.
        level: Compression level (0-9).

    Returns:
        Compressed bytes.
    """
    if level not in LZMA_LEVELS:
        raise ValueError(f"LZMA level must be in {LZMA_LEVELS}")
    
    raw_bytes = data.tobytes()
    return lzma.compress(raw_bytes, preset=level)

def decompress_lzma(compressed_data: bytes, shape: Tuple[int, ...], dtype: np.dtype) -> np.ndarray:
    """
    Decompress lzma data back to numpy array.

    Args:
        compressed_data: Compressed bytes.
        shape: Original array shape.
        dtype: Original array dtype.

    Returns:
        Decompressed numpy array.
    """
    raw_bytes = lzma.decompress(compressed_data)
    return np.frombuffer(raw_bytes, dtype=dtype).reshape(shape)

def compress_lz4(data: np.ndarray, level: int = 5) -> bytes:
    """
    Compress numpy array data using lz4 frame.

    Args:
        data: Input numpy array.
        level: Compression level (1-9).

    Returns:
        Compressed bytes.
    """
    if level not in LZ4_LEVELS:
        raise ValueError(f"LZ4 level must be in {LZ4_LEVELS}")
    
    raw_bytes = data.tobytes()
    # lz4.frame.compress accepts compress_level
    return lz4.frame.compress(raw_bytes, compress_level=level)

def decompress_lz4(compressed_data: bytes, shape: Tuple[int, ...], dtype: np.dtype) -> np.ndarray:
    """
    Decompress lz4 data back to numpy array.

    Args:
        compressed_data: Compressed bytes.
        shape: Original array shape.
        dtype: Original array dtype.

    Returns:
        Decompressed numpy array.
    """
    raw_bytes = lz4.frame.decompress(compressed_data)
    return np.frombuffer(raw_bytes, dtype=dtype).reshape(shape)

def compress_data(data: np.ndarray, method: str, level: int) -> bytes:
    """
    Generic compressor dispatcher.

    Args:
        data: Input numpy array.
        method: One of 'gzip', 'bzip2', 'lzma', 'lz4'.
        level: Compression level.

    Returns:
        Compressed bytes.
    """
    if method == 'gzip':
        return compress_gzip(data, level)
    elif method == 'bzip2':
        return compress_bzip2(data, level)
    elif method == 'lzma':
        return compress_lzma(data, level)
    elif method == 'lz4':
        return compress_lz4(data, level)
    else:
        raise ValueError(f"Unknown compression method: {method}")

def decompress_data(compressed_data: bytes, method: str, shape: Tuple[int, ...], dtype: np.dtype) -> np.ndarray:
    """
    Generic decompressor dispatcher.

    Args:
        compressed_data: Compressed bytes.
        method: One of 'gzip', 'bzip2', 'lzma', 'lz4'.
        shape: Original array shape.
        dtype: Original array dtype.

    Returns:
        Decompressed numpy array.
    """
    if method == 'gzip':
        return decompress_gzip(compressed_data, shape, dtype)
    elif method == 'bzip2':
        return decompress_bzip2(compressed_data, shape, dtype)
    elif method == 'lzma':
        return decompress_lzma(compressed_data, shape, dtype)
    elif method == 'lz4':
        return decompress_lz4(compressed_data, shape, dtype)
    else:
        raise ValueError(f"Unknown compression method: {method}")

def verify_lossless(original: np.ndarray, reconstructed: np.ndarray) -> bool:
    """
    Verify that decompression is lossless (bitwise identical).

    Args:
        original: Original numpy array.
        reconstructed: Decompressed numpy array.

    Returns:
        True if bitwise identical, False otherwise.
    """
    return np.array_equal(original, reconstructed)

def main():
    """
    Main entry point for testing lossless compression.
    Generates a sample waveform, compresses it at various levels,
    decompresses, and verifies lossless reconstruction.
    """
    import logging
    from src.utils.logging import get_logger
    from src.utils.config import get_project_root, ensure_dir

    logger = get_logger(__name__)
    project_root = get_project_root()
    output_dir = ensure_dir(project_root / "data" / "interim" / "compression_test")

    # Generate sample data (simulating a GW strain segment)
    np.random.seed(42)
    sample_data = np.random.randn(10000).astype(np.float64)
    
    methods = ['gzip', 'bzip2', 'lzma', 'lz4']
    levels = {
        'gzip': [1, 5, 9],
        'bzip2': [1, 5, 9],
        'lzma': [0, 5, 9],
        'lz4': [1, 5, 9]
    }

    results = []

    for method in methods:
        for level in levels[method]:
            try:
                # Compress
                compressed = compress_data(sample_data, method, level)
                
                # Decompress
                reconstructed = decompress_data(
                    compressed, method, sample_data.shape, sample_data.dtype
                )
                
                # Verify
                is_lossless = verify_lossless(sample_data, reconstructed)
                compression_ratio = len(sample_data) * sample_data.itemsize / len(compressed)
                
                results.append({
                    "method": method,
                    "level": level,
                    "is_lossless": is_lossless,
                    "compression_ratio": float(compression_ratio),
                    "original_size": len(sample_data) * sample_data.itemsize,
                    "compressed_size": len(compressed)
                })
                
                logger.info(f"{method} level {level}: Lossless={is_lossless}, Ratio={compression_ratio:.2f}x")
                
            except Exception as e:
                logger.error(f"Failed {method} level {level}: {e}")
                results.append({
                    "method": method,
                    "level": level,
                    "error": str(e)
                })

    # Save results
    output_file = output_dir / "lossless_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")

    # Assert all successful runs were lossless
    failed_checks = [r for r in results if not r.get('is_lossless', False) and 'error' not in r]
    if failed_checks:
        raise AssertionError(f"Lossless verification failed for: {failed_checks}")

if __name__ == "__main__":
    main()