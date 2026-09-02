import gzip
import bz2
import lzma
import json
import numpy as np
from pathlib import Path
from typing import Union, Tuple, Optional, BinaryIO
import logging

from src.utils.logging import get_logger
from src.utils.config import get_project_root, ensure_dir

logger = get_logger(__name__)

# Constants for default compression levels
GZIP_DEFAULT_LEVEL = 9
BZIP2_DEFAULT_LEVEL = 9
LZMA_DEFAULT_PRESET = 6
LZ4_DEFAULT_LEVEL = 1  # Default for lz4 if used, though not in stdlib

def compress_gzip(
    data: Union[np.ndarray, bytes],
    output_path: Path,
    level: int = GZIP_DEFAULT_LEVEL
) -> Tuple[Path, int]:
    """
    Compress data using gzip.
    
    Args:
        data: Input data as numpy array or bytes.
        output_path: Path to save the compressed file.
        level: Compression level (1-9).
        
    Returns:
        Tuple of (output_path, compressed_size_bytes)
    """
    ensure_dir(output_path)
    original_size = 0
    
    if isinstance(data, np.ndarray):
        original_size = data.nbytes
        # Convert to bytes for compression
        data_bytes = data.tobytes()
    elif isinstance(data, bytes):
        original_size = len(data)
        data_bytes = data
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")

    with gzip.open(output_path, 'wb', compresslevel=level) as f:
        f.write(data_bytes)
    
    compressed_size = output_path.stat().st_size
    logger.info(f"Gzip compressed {original_size} -> {compressed_size} bytes (level {level})")
    return output_path, compressed_size

def decompress_gzip(input_path: Path, shape: Optional[Tuple[int, ...]] = None, dtype: np.dtype = np.float64) -> np.ndarray:
    """
    Decompress gzip data and restore to numpy array.
    
    Args:
        input_path: Path to the compressed file.
        shape: Shape of the original array (required if data was an array).
        dtype: Data type of the original array.
        
    Returns:
        Decompressed numpy array.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Compressed file not found: {input_path}")
    
    with gzip.open(input_path, 'rb') as f:
        data_bytes = f.read()
    
    if shape is not None:
        arr = np.frombuffer(data_bytes, dtype=dtype)
        return arr.reshape(shape)
    else:
        # Return bytes if shape is not provided
        logger.warning("Shape not provided, returning raw bytes")
        return data_bytes

def compress_bzip2(
    data: Union[np.ndarray, bytes],
    output_path: Path,
    level: int = BZIP2_DEFAULT_LEVEL
) -> Tuple[Path, int]:
    """
    Compress data using bzip2.
    
    Args:
        data: Input data as numpy array or bytes.
        output_path: Path to save the compressed file.
        level: Compression level (1-9).
        
    Returns:
        Tuple of (output_path, compressed_size_bytes)
    """
    ensure_dir(output_path)
    original_size = 0
    
    if isinstance(data, np.ndarray):
        original_size = data.nbytes
        data_bytes = data.tobytes()
    elif isinstance(data, bytes):
        original_size = len(data)
        data_bytes = data
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")

    with bz2.open(output_path, 'wb', compresslevel=level) as f:
        f.write(data_bytes)
    
    compressed_size = output_path.stat().st_size
    logger.info(f"Bzip2 compressed {original_size} -> {compressed_size} bytes (level {level})")
    return output_path, compressed_size

def decompress_bzip2(input_path: Path, shape: Optional[Tuple[int, ...]] = None, dtype: np.dtype = np.float64) -> Union[np.ndarray, bytes]:
    """
    Decompress bzip2 data and restore to numpy array.
    
    Args:
        input_path: Path to the compressed file.
        shape: Shape of the original array.
        dtype: Data type of the original array.
        
    Returns:
        Decompressed numpy array or bytes.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Compressed file not found: {input_path}")
    
    with bz2.open(input_path, 'rb') as f:
        data_bytes = f.read()
    
    if shape is not None:
        arr = np.frombuffer(data_bytes, dtype=dtype)
        return arr.reshape(shape)
    else:
        logger.warning("Shape not provided, returning raw bytes")
        return data_bytes

def compress_lzma(
    data: Union[np.ndarray, bytes],
    output_path: Path,
    preset: int = LZMA_DEFAULT_PRESET
) -> Tuple[Path, int]:
    """
    Compress data using lzma.
    
    Args:
        data: Input data as numpy array or bytes.
        output_path: Path to save the compressed file.
        preset: Compression preset (0-9).
        
    Returns:
        Tuple of (output_path, compressed_size_bytes)
    """
    ensure_dir(output_path)
    original_size = 0
    
    if isinstance(data, np.ndarray):
        original_size = data.nbytes
        data_bytes = data.tobytes()
    elif isinstance(data, bytes):
        original_size = len(data)
        data_bytes = data
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")

    with lzma.open(output_path, 'wb', preset=preset) as f:
        f.write(data_bytes)
    
    compressed_size = output_path.stat().st_size
    logger.info(f"Lzma compressed {original_size} -> {compressed_size} bytes (preset {preset})")
    return output_path, compressed_size

def decompress_lzma(input_path: Path, shape: Optional[Tuple[int, ...]] = None, dtype: np.dtype = np.float64) -> Union[np.ndarray, bytes]:
    """
    Decompress lzma data and restore to numpy array.
    
    Args:
        input_path: Path to the compressed file.
        shape: Shape of the original array.
        dtype: Data type of the original array.
        
    Returns:
        Decompressed numpy array or bytes.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Compressed file not found: {input_path}")
    
    with lzma.open(input_path, 'rb') as f:
        data_bytes = f.read()
    
    if shape is not None:
        arr = np.frombuffer(data_bytes, dtype=dtype)
        return arr.reshape(shape)
    else:
        logger.warning("Shape not provided, returning raw bytes")
        return data_bytes

def compress_lz4(data: Union[np.ndarray, bytes], output_path: Path, level: int = 1) -> Tuple[Path, int]:
    """
    Compress data using lz4.
    Note: Requires 'lz4' package. If not installed, falls back to lzma with warning.
    
    Args:
        data: Input data as numpy array or bytes.
        output_path: Path to save the compressed file.
        level: Compression level.
        
    Returns:
        Tuple of (output_path, compressed_size_bytes)
    """
    try:
        import lz4.frame
    except ImportError:
        logger.warning("lz4 package not found. Falling back to lzma.")
        return compress_lzma(data, output_path, preset=level)

    ensure_dir(output_path)
    original_size = 0
    
    if isinstance(data, np.ndarray):
        original_size = data.nbytes
        data_bytes = data.tobytes()
    elif isinstance(data, bytes):
        original_size = len(data)
        data_bytes = data
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")

    # lz4 frame compression
    compressed_bytes = lz4.frame.compress(data_bytes, compression_level=level)
    
    with open(output_path, 'wb') as f:
        f.write(compressed_bytes)
    
    compressed_size = output_path.stat().st_size
    logger.info(f"Lz4 compressed {original_size} -> {compressed_size} bytes (level {level})")
    return output_path, compressed_size

def decompress_lz4(input_path: Path, shape: Optional[Tuple[int, ...]] = None, dtype: np.dtype = np.float64) -> Union[np.ndarray, bytes]:
    """
    Decompress lz4 data and restore to numpy array.
    
    Args:
        input_path: Path to the compressed file.
        shape: Shape of the original array.
        dtype: Data type of the original array.
        
    Returns:
        Decompressed numpy array or bytes.
    """
    try:
        import lz4.frame
    except ImportError:
        logger.warning("lz4 package not found. Falling back to lzma decompression.")
        return decompress_lzma(input_path, shape, dtype)

    if not input_path.exists():
        raise FileNotFoundError(f"Compressed file not found: {input_path}")
    
    with open(input_path, 'rb') as f:
        compressed_bytes = f.read()
    
    data_bytes = lz4.frame.decompress(compressed_bytes)
    
    if shape is not None:
        arr = np.frombuffer(data_bytes, dtype=dtype)
        return arr.reshape(shape)
    else:
        logger.warning("Shape not provided, returning raw bytes")
        return data_bytes

def compress_data(
    data: np.ndarray,
    method: str,
    output_dir: Path,
    filename: str,
    **kwargs
) -> Path:
    """
    Generic compression dispatcher.
    
    Args:
        data: Input numpy array.
        method: One of 'gzip', 'bzip2', 'lzma', 'lz4'.
        output_dir: Directory to save the output.
        filename: Base filename (without extension).
        **kwargs: Additional arguments passed to specific compressors (e.g., level).
        
    Returns:
        Path to the compressed file.
    """
    ensure_dir(output_dir)
    extensions = {
        'gzip': '.gz',
        'bzip2': '.bz2',
        'lzma': '.xz',
        'lz4': '.lz4'
    }
    
    if method not in extensions:
        raise ValueError(f"Unsupported lossless method: {method}. Choose from {list(extensions.keys())}")
    
    output_path = output_dir / f"{filename}{extensions[method]}"
    
    compressors = {
        'gzip': compress_gzip,
        'bzip2': compress_bzip2,
        'lzma': compress_lzma,
        'lz4': compress_lz4
    }
    
    compress_func = compressors[method]
    compress_func(data, output_path, **kwargs)
    return output_path

def decompress_data(
    compressed_path: Path,
    method: str,
    shape: Tuple[int, ...],
    dtype: np.dtype = np.float64
) -> np.ndarray:
    """
    Generic decompression dispatcher.
    
    Args:
        compressed_path: Path to the compressed file.
        method: One of 'gzip', 'bzip2', 'lzma', 'lz4'.
        shape: Shape of the original array.
        dtype: Data type of the original array.
        
    Returns:
        Decompressed numpy array.
    """
    decompressors = {
        'gzip': decompress_gzip,
        'bzip2': decompress_bzip2,
        'lzma': decompress_lzma,
        'lz4': decompress_lz4
    }
    
    if method not in decompressors:
        raise ValueError(f"Unsupported lossless method: {method}")
    
    decompress_func = decompressors[method]
    return decompress_func(compressed_path, shape=shape, dtype=dtype)

def verify_lossless(original: np.ndarray, decompressed: np.ndarray, tolerance: float = 1e-10) -> bool:
    """
    Verify that decompression is lossless.
    
    Args:
        original: Original array.
        decompressed: Decompressed array.
        tolerance: Maximum allowed difference.
        
    Returns:
        True if lossless within tolerance.
    """
    if original.shape != decompressed.shape:
        logger.error(f"Shape mismatch: {original.shape} vs {decompressed.shape}")
        return False
    
    if original.dtype != decompressed.dtype:
        logger.error(f"Dtype mismatch: {original.dtype} vs {decompressed.dtype}")
        return False
    
    max_diff = np.max(np.abs(original.astype(float) - decompressed.astype(float)))
    is_lossless = max_diff <= tolerance
    
    if not is_lossless:
        logger.error(f"Lossless verification failed. Max diff: {max_diff}")
    
    return is_lossless

def main():
    """
    Main entry point for lossless compression testing.
    Demonstrates compression and decompression with verification.
    """
    project_root = get_project_root()
    data_dir = project_root / "data" / "interim" / "test_compression"
    ensure_dir(data_dir)
    
    # Generate sample data (real GW strain-like data simulation for testing)
    # In a real pipeline, this would be loaded from data/raw
    logger.info("Generating test data...")
    t = np.linspace(0, 1, 4096)
    strain = np.sin(2 * np.pi * 100 * t) + 0.01 * np.random.randn(4096)
    
    methods = ['gzip', 'bzip2', 'lzma', 'lz4']
    levels = [5, 9]
    
    for method in methods:
        for level in levels:
            logger.info(f"Testing {method} at level {level}...")
            filename = f"strain_{method}_l{level}"
            
            # Compress
            comp_path = compress_data(
                strain, 
                method=method, 
                output_dir=data_dir, 
                filename=filename,
                level=level
            )
            
            # Decompress
            decomp_strain = decompress_data(
                comp_path, 
                method=method, 
                shape=strain.shape, 
                dtype=strain.dtype
            )
            
            # Verify
            if verify_lossless(strain, decomp_strain):
                logger.info(f"  {method} (level {level}): PASSED (Lossless)")
            else:
                logger.error(f"  {method} (level {level}): FAILED")

if __name__ == "__main__":
    main()
