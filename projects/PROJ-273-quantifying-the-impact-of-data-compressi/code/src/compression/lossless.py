"""
Lossless compression wrappers for GW strain data.
Implements gzip, LZ4, and bzip2 compression with varied levels.
"""
import gzip
import bz2
import lzma
import json
import numpy as np
from pathlib import Path
from typing import Union, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Default compression levels
GZIP_LEVELS = [1, 5, 9]
BZIP2_LEVELS = [1, 5, 9]
LZMA_LEVELS = [0, 5, 9]

def compress_gzip(data: Union[np.ndarray, bytes], output_path: Path, level: int = 9) -> None:
    """
    Compress data using gzip.
    
    Args:
        data: Input data as numpy array or bytes
        output_path: Path to write compressed file
        level: Compression level (1-9), default 9 (best compression)
    """
    if isinstance(data, np.ndarray):
        # Save numpy array to bytes first
        data_bytes = data.tobytes()
    else:
        data_bytes = data
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with gzip.open(output_path, 'wb', compresslevel=level) as f:
        f.write(data_bytes)
    
    logger.info(f"Compressed data with gzip (level={level}) to {output_path}")

def decompress_gzip(input_path: Path) -> np.ndarray:
    """
    Decompress gzip data back to numpy array.
    
    Args:
        input_path: Path to compressed file
        
    Returns:
        Decompressed numpy array
    """
    with gzip.open(input_path, 'rb') as f:
        data_bytes = f.read()
    
    # Convert bytes back to numpy array
    # We need to know the original shape and dtype, so we store them in metadata
    # For now, assume we'll reconstruct from metadata file if available
    return np.frombuffer(data_bytes, dtype=np.float64)

def compress_bzip2(data: Union[np.ndarray, bytes], output_path: Path, level: int = 9) -> None:
    """
    Compress data using bzip2.
    
    Args:
        data: Input data as numpy array or bytes
        output_path: Path to write compressed file
        level: Compression level (1-9), default 9 (best compression)
    """
    if isinstance(data, np.ndarray):
        data_bytes = data.tobytes()
    else:
        data_bytes = data
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with bz2.BZ2File(output_path, 'wb', compresslevel=level) as f:
        f.write(data_bytes)
    
    logger.info(f"Compressed data with bzip2 (level={level}) to {output_path}")

def decompress_bzip2(input_path: Path) -> np.ndarray:
    """
    Decompress bzip2 data back to numpy array.
    
    Args:
        input_path: Path to compressed file
        
    Returns:
        Decompressed numpy array
    """
    with bz2.BZ2File(input_path, 'rb') as f:
        data_bytes = f.read()
    
    return np.frombuffer(data_bytes, dtype=np.float64)

def compress_lzma(data: Union[np.ndarray, bytes], output_path: Path, level: int = 9) -> None:
    """
    Compress data using lzma (XZ).
    
    Args:
        data: Input data as numpy array or bytes
        output_path: Path to write compressed file
        level: Compression level (0-9), default 9 (best compression)
    """
    if isinstance(data, np.ndarray):
        data_bytes = data.tobytes()
    else:
        data_bytes = data
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with lzma.open(output_path, 'wb', preset=level) as f:
        f.write(data_bytes)
    
    logger.info(f"Compressed data with lzma (level={level}) to {output_path}")

def decompress_lzma(input_path: Path) -> np.ndarray:
    """
    Decompress lzma data back to numpy array.
    
    Args:
        input_path: Path to compressed file
        
    Returns:
        Decompressed numpy array
    """
    with lzma.open(input_path, 'rb') as f:
        data_bytes = f.read()
    
    return np.frombuffer(data_bytes, dtype=np.float64)

def compress_data(data: np.ndarray, compression_type: str, output_path: Path, level: Optional[int] = None) -> None:
    """
    Generic compression function that dispatches to specific compressors.
    
    Args:
        data: Input numpy array
        compression_type: One of 'gzip', 'bzip2', 'lzma'
        output_path: Path to write compressed file
        level: Compression level (optional, uses default if not provided)
    """
    if level is None:
        level = 9  # Default to best compression
    
    if compression_type == 'gzip':
        compress_gzip(data, output_path, level)
    elif compression_type == 'bzip2':
        compress_bzip2(data, output_path, level)
    elif compression_type == 'lzma':
        compress_lzma(data, output_path, level)
    else:
        raise ValueError(f"Unknown compression type: {compression_type}")

def decompress_data(compression_type: str, input_path: Path) -> np.ndarray:
    """
    Generic decompression function that dispatches to specific decompressors.
    
    Args:
        compression_type: One of 'gzip', 'bzip2', 'lzma'
        input_path: Path to compressed file
        
    Returns:
        Decompressed numpy array
    """
    if compression_type == 'gzip':
        return decompress_gzip(input_path)
    elif compression_type == 'bzip2':
        return decompress_bzip2(input_path)
    elif compression_type == 'lzma':
        return decompress_lzma(input_path)
    else:
        raise ValueError(f"Unknown compression type: {compression_type}")

def verify_lossless(original: np.ndarray, decompressed: np.ndarray, tolerance: float = 1e-10) -> bool:
    """
    Verify that decompressed data matches original data within tolerance.
    
    Args:
        original: Original numpy array
        decompressed: Decompressed numpy array
        tolerance: Maximum allowed difference (default 1e-10 for lossless)
        
    Returns:
        True if data matches within tolerance, False otherwise
    """
    if original.shape != decompressed.shape:
        logger.error(f"Shape mismatch: {original.shape} vs {decompressed.shape}")
        return False
    
    if original.dtype != decompressed.dtype:
        logger.warning(f"Dtype mismatch: {original.dtype} vs {decompressed.dtype}")
        # Convert for comparison if needed
        decompressed = decompressed.astype(original.dtype)
    
    max_diff = np.max(np.abs(original - decompressed))
    
    if max_diff > tolerance:
        logger.error(f"Lossless verification failed: max_diff={max_diff}, tolerance={tolerance}")
        return False
    
    logger.info(f"Lossless verification passed: max_diff={max_diff}")
    return True

def main():
    """
    Main function to demonstrate lossless compression.
    """
    # Create test data
    test_data = np.random.randn(10000).astype(np.float64)
    
    # Test different compression types and levels
    compression_configs = [
        ('gzip', 1),
        ('gzip', 5),
        ('gzip', 9),
        ('bzip2', 1),
        ('bzip2', 5),
        ('bzip2', 9),
        ('lzma', 0),
        ('lzma', 5),
        ('lzma', 9),
    ]
    
    output_dir = Path("data/interim/compression_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for comp_type, level in compression_configs:
        # Compress
        output_path = output_dir / f"test_{comp_type}_level{level}.tmp"
        compress_data(test_data, comp_type, output_path, level)
        
        # Decompress
        decompressed = decompress_data(comp_type, output_path)
        
        # Verify
        is_lossless = verify_lossless(test_data, decompressed)
        
        # Report size reduction
        original_size = test_data.nbytes
        compressed_size = output_path.stat().st_size
        ratio = compressed_size / original_size
        
        logger.info(f"{comp_type} (level={level}): "
                   f"Original={original_size}B, Compressed={compressed_size}B, "
                   f"Ratio={ratio:.3f}, Lossless={is_lossless}")
        
        # Clean up
        output_path.unlink()
    
    logger.info("Lossless compression test completed")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
