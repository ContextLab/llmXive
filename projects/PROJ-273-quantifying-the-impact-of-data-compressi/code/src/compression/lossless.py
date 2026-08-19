"""
Lossless compression wrappers for gravitational wave strain data.

Implements gzip, LZMA, and bzip2 compression/decompression at varied levels.
Includes verification that decompressed data matches original exactly.
"""
import gzip
import bz2
import lzma
import json
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import logging
import time

from src.utils.logging import get_logger
from src.utils.config import get_path, ensure_dir

logger = get_logger(__name__)

# Compression levels
COMPRESSION_LEVELS = {
    'gzip': [5, 9],
    'lzma': [5, 9],
    'bzip2': [5, 9]
}

def compress_gzip(data: np.ndarray, level: int = 9) -> bytes:
    """
    Compress numpy array data using gzip.
    
    Args:
        data: 1D numpy array of strain values
        level: Compression level (1-9, higher = more compression, slower)
        
    Returns:
        Compressed bytes
    """
    if level < 1 or level > 9:
        raise ValueError(f"Invalid gzip level: {level}. Must be 1-9.")
    
    # Serialize to bytes
    raw_bytes = data.tobytes()
    compressed = gzip.compress(raw_bytes, compresslevel=level)
    return compressed

def decompress_gzip(compressed_data: bytes, shape: Tuple[int, ...], dtype: np.dtype) -> np.ndarray:
    """
    Decompress gzip-compressed data back to numpy array.
    
    Args:
        compressed_data: Compressed bytes
        shape: Original shape of the array
        dtype: Original dtype of the array
        
    Returns:
        Decompressed numpy array
    """
    raw_bytes = gzip.decompress(compressed_data)
    data = np.frombuffer(raw_bytes, dtype=dtype)
    return data.reshape(shape)

def compress_lzma(data: np.ndarray, level: int = 9) -> bytes:
    """
    Compress numpy array data using LZMA.
    
    Args:
        data: 1D numpy array of strain values
        level: Compression level (0-9, higher = more compression, slower)
        
    Returns:
        Compressed bytes
    """
    if level < 0 or level > 9:
        raise ValueError(f"Invalid lzma level: {level}. Must be 0-9.")
    
    raw_bytes = data.tobytes()
    compressed = lzma.compress(raw_bytes, preset=level)
    return compressed

def decompress_lzma(compressed_data: bytes, shape: Tuple[int, ...], dtype: np.dtype) -> np.ndarray:
    """
    Decompress LZMA-compressed data back to numpy array.
    
    Args:
        compressed_data: Compressed bytes
        shape: Original shape of the array
        dtype: Original dtype of the array
        
    Returns:
        Decompressed numpy array
    """
    raw_bytes = lzma.decompress(compressed_data)
    data = np.frombuffer(raw_bytes, dtype=dtype)
    return data.reshape(shape)

def compress_bzip2(data: np.ndarray, level: int = 9) -> bytes:
    """
    Compress numpy array data using bzip2.
    
    Args:
        data: 1D numpy array of strain values
        level: Compression level (1-9, higher = more compression, slower)
        
    Returns:
        Compressed bytes
    """
    if level < 1 or level > 9:
        raise ValueError(f"Invalid bzip2 level: {level}. Must be 1-9.")
    
    raw_bytes = data.tobytes()
    compressed = bz2.compress(raw_bytes, compresslevel=level)
    return compressed

def decompress_bzip2(compressed_data: bytes, shape: Tuple[int, ...], dtype: np.dtype) -> np.ndarray:
    """
    Decompress bzip2-compressed data back to numpy array.
    
    Args:
        compressed_data: Compressed bytes
        shape: Original shape of the array
        dtype: Original dtype of the array
        
    Returns:
        Decompressed numpy array
    """
    raw_bytes = bz2.decompress(compressed_data)
    data = np.frombuffer(raw_bytes, dtype=dtype)
    return data.reshape(shape)

def compress_data(
    data: np.ndarray,
    method: str,
    level: int,
    output_dir: Path,
    event_id: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compress data using specified method and level.
    
    Args:
        data: 1D numpy array of strain values
        method: Compression method ('gzip', 'lzma', 'bzip2')
        level: Compression level
        output_dir: Directory to save compressed data
        event_id: Event identifier for naming
        metadata: Optional metadata to save alongside compressed data
        
    Returns:
        Dictionary with compression results (path, size, ratio, time)
    """
    ensure_dir(output_dir)
    
    start_time = time.time()
    
    if method == 'gzip':
        compressed = compress_gzip(data, level)
        decompress_func = decompress_gzip
    elif method == 'lzma':
        compressed = compress_lzma(data, level)
        decompress_func = decompress_lzma
    elif method == 'bzip2':
        compressed = compress_bzip2(data, level)
        decompress_func = decompress_bzip2
    else:
        raise ValueError(f"Unknown compression method: {method}")
    
    compression_time = time.time() - start_time
    
    # Save compressed data
    output_path = output_dir / f"{event_id}_{method}_level{level}.gz"
    if method == 'lzma':
        output_path = output_dir / f"{event_id}_{method}_level{level}.xz"
    elif method == 'bzip2':
        output_path = output_dir / f"{event_id}_{method}_level{level}.bz2"
    
    with open(output_path, 'wb') as f:
        f.write(compressed)
    
    # Save metadata if provided
    if metadata:
        metadata_path = output_dir / f"{event_id}_{method}_level{level}_meta.json"
        meta_record = {
            'event_id': event_id,
            'method': method,
            'level': level,
            'original_shape': list(data.shape),
            'original_dtype': str(data.dtype),
            'original_size_bytes': data.nbytes,
            'compressed_size_bytes': len(compressed),
            'compression_time_s': compression_time,
            'metadata': metadata
        }
        with open(metadata_path, 'w') as f:
            json.dump(meta_record, f, indent=2)
    
    # Verify lossless
    decompressed = decompress_func(compressed, data.shape, data.dtype)
    if not np.array_equal(data, decompressed):
        raise ValueError(f"Lossless verification failed for {method} level {level}")
    
    # Calculate metrics
    original_size = data.nbytes
    compressed_size = len(compressed)
    compression_ratio = original_size / compressed_size if compressed_size > 0 else float('inf')
    
    logger.info(
        f"Compressed {event_id} with {method} level {level}: "
        f"ratio={compression_ratio:.2f}, time={compression_time:.3f}s"
    )
    
    return {
        'path': str(output_path),
        'original_size_bytes': original_size,
        'compressed_size_bytes': compressed_size,
        'compression_ratio': compression_ratio,
        'compression_time_s': compression_time,
        'method': method,
        'level': level
    }

def decompress_data(
    compressed_path: Path,
    shape: Tuple[int, ...],
    dtype: np.dtype,
    method: Optional[str] = None
) -> np.ndarray:
    """
    Decompress data from file.
    
    Args:
        compressed_path: Path to compressed file
        shape: Expected shape of decompressed array
        dtype: Expected dtype of decompressed array
        method: Compression method (optional, auto-detected from extension)
        
    Returns:
        Decompressed numpy array
    """
    if method is None:
        suffix = compressed_path.suffix.lower()
        if suffix == '.gz':
            method = 'gzip'
        elif suffix == '.xz':
            method = 'lzma'
        elif suffix == '.bz2':
            method = 'bzip2'
        else:
            raise ValueError(f"Cannot auto-detect compression method from extension: {suffix}")
    
    with open(compressed_path, 'rb') as f:
        compressed_data = f.read()
    
    if method == 'gzip':
        return decompress_gzip(compressed_data, shape, dtype)
    elif method == 'lzma':
        return decompress_lzma(compressed_data, shape, dtype)
    elif method == 'bzip2':
        return decompress_bzip2(compressed_data, shape, dtype)
    else:
        raise ValueError(f"Unknown compression method: {method}")

def verify_lossless(
    original: np.ndarray,
    compressed: bytes,
    method: str,
    tolerance: float = 0.0
) -> bool:
    """
    Verify that decompression produces exact original data.
    
    Args:
        original: Original numpy array
        compressed: Compressed bytes
        method: Compression method
        tolerance: Numerical tolerance (0 for exact match)
        
    Returns:
        True if verification passes
    """
    if method == 'gzip':
        decompressed = decompress_gzip(compressed, original.shape, original.dtype)
    elif method == 'lzma':
        decompressed = decompress_lzma(compressed, original.shape, original.dtype)
    elif method == 'bzip2':
        decompressed = decompress_bzip2(compressed, original.shape, original.dtype)
    else:
        raise ValueError(f"Unknown compression method: {method}")
    
    if tolerance == 0:
        return np.array_equal(original, decompressed)
    else:
        return np.allclose(original, decompressed, atol=tolerance)

def main():
    """
    Main entry point for testing compression on sample data.
    This function demonstrates the compression pipeline.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Test lossless compression")
    parser.add_argument("--event-id", type=str, default="test_event", help="Event ID")
    parser.add_argument("--output-dir", type=str, default="data/interim/compressed/lossless", help="Output directory")
    parser.add_argument("--data-file", type=str, default=None, help="Path to input data file (JSON with 'strain' array)")
    parser.add_argument("--method", type=str, choices=['gzip', 'lzma', 'bzip2'], default='gzip', help="Compression method")
    parser.add_argument("--level", type=int, default=9, help="Compression level")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)
    
    # Load or generate test data
    if args.data_file and Path(args.data_file).exists():
        with open(args.data_file, 'r') as f:
            data_dict = json.load(f)
            data = np.array(data_dict['strain'])
        logger.info(f"Loaded data from {args.data_file}: shape={data.shape}")
    else:
        # Generate synthetic test data (real pipeline would use actual GW data)
        np.random.seed(42)
        n_samples = 4096
        data = np.random.randn(n_samples) * 1e-21  # Typical strain amplitude
        logger.info(f"Generated synthetic test data: shape={data.shape}")
    
    # Compress
    metadata = {
        'test_run': True,
        'n_samples': len(data)
    }
    
    result = compress_data(
        data=data,
        method=args.method,
        level=args.level,
        output_dir=output_dir,
        event_id=args.event_id,
        metadata=metadata
    )
    
    logger.info(f"Compression result: {result}")
    
    # Decompress and verify
    compressed_path = Path(result['path'])
    decompressed = decompress_data(
        compressed_path=compressed_path,
        shape=data.shape,
        dtype=data.dtype,
        method=args.method
    )
    
    if np.array_equal(data, decompressed):
        logger.info("Verification PASSED: Decompressed data matches original exactly.")
    else:
        logger.error("Verification FAILED: Decompressed data does not match original.")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    from src.utils.config import set_seed
    from src.utils.logging import setup_logging
    
    setup_logging()
    set_seed(42)
    
    sys.exit(main())
