"""
Lossless compression wrappers for GW strain data.

Implements wrappers for gzip, bzip2, lzma, and lz4.
Supports various compression levels including 5 and 9.
"""
import gzip
import bz2
import lzma
import json
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import struct
import lz4.frame

from src.utils.logging import get_logger
from src.utils.config import get_project_root, ensure_dir

logger = get_logger(__name__)

# Default compression levels
GZIP_DEFAULT = 6
BZIP2_DEFAULT = 9
LZMA_DEFAULT = 6
LZ4_DEFAULT = 4

# Supported levels for each method
GZIP_LEVELS = [1, 5, 9]
BZIP2_LEVELS = [1, 5, 9]
LZMA_LEVELS = [0, 5, 9]
LZ4_LEVELS = [1, 5, 9]

def _save_metadata(compressed_path: Path, original_shape: Tuple[int], original_dtype: str, method: str, level: int):
    """Save metadata for decompression."""
    meta_path = compressed_path.with_suffix('.meta.json')
    metadata = {
        'original_shape': list(original_shape),
        'original_dtype': original_dtype,
        'compression_method': method,
        'compression_level': level
    }
    with open(meta_path, 'w') as f:
        json.dump(metadata, f)
    logger.debug(f"Saved metadata to {meta_path}")

def _load_metadata(compressed_path: Path) -> Dict[str, Any]:
    """Load metadata for decompression."""
    meta_path = compressed_path.with_suffix('.meta.json')
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")
    with open(meta_path, 'r') as f:
        return json.load(f)

def compress_gzip(data: np.ndarray, level: int = GZIP_DEFAULT, output_path: Optional[Path] = None) -> Path:
    """
    Compress numpy array using gzip.
    
    Args:
        data: 1D or 2D numpy array of strain data
        level: Compression level (1-9, default 6)
        output_path: Optional output path. If None, uses default naming.
        
    Returns:
        Path to compressed file
    """
    if level not in GZIP_LEVELS:
        logger.warning(f"Level {level} not in standard set {GZIP_LEVELS}, proceeding anyway")
    
    if output_path is None:
        output_path = get_project_root() / "data" / "interim" / "compressed" / "lossless" / "gzip" / f"level_{level}.gz"
    
    ensure_dir(output_path.parent)
    
    # Flatten and save as binary
    flat_data = data.flatten()
    
    with gzip.open(output_path, 'wb', compresslevel=level) as f:
        # Write shape and dtype info first
        f.write(struct.pack('I', data.ndim))
        f.write(struct.pack('Q', data.size))
        for dim in data.shape:
            f.write(struct.pack('Q', dim))
        f.write(data.dtype.str.encode('ascii'))
        f.write(flat_data.tobytes())
    
    logger.info(f"Compressed data to {output_path} using gzip level {level}")
    return output_path

def decompress_gzip(compressed_path: Path) -> np.ndarray:
    """
    Decompress gzip-compressed numpy array.
    
    Args:
        compressed_path: Path to compressed file
        
    Returns:
        Decompressed numpy array
    """
    with gzip.open(compressed_path, 'rb') as f:
        # Read shape and dtype info
        ndim = struct.unpack('I', f.read(4))[0]
        size = struct.unpack('Q', f.read(8))[0]
        shape = tuple(struct.unpack('Q', f.read(8)) for _ in range(ndim))
        dtype_str = f.readline().strip().decode('ascii')
        
        # Read data
        raw_data = f.read()
        data = np.frombuffer(raw_data, dtype=dtype_str)
        data = data.reshape(shape)
    
    logger.debug(f"Decompressed data from {compressed_path}")
    return data

def compress_bzip2(data: np.ndarray, level: int = BZIP2_DEFAULT, output_path: Optional[Path] = None) -> Path:
    """
    Compress numpy array using bzip2.
    
    Args:
        data: 1D or 2D numpy array of strain data
        level: Compression level (1-9, default 9)
        output_path: Optional output path. If None, uses default naming.
        
    Returns:
        Path to compressed file
    """
    if level not in BZIP2_LEVELS:
        logger.warning(f"Level {level} not in standard set {BZIP2_LEVELS}, proceeding anyway")
    
    if output_path is None:
        output_path = get_project_root() / "data" / "interim" / "compressed" / "lossless" / "bzip2" / f"level_{level}.bz2"
    
    ensure_dir(output_path.parent)
    
    flat_data = data.flatten()
    
    with bz2.open(output_path, 'wb', compresslevel=level) as f:
        f.write(struct.pack('I', data.ndim))
        f.write(struct.pack('Q', data.size))
        for dim in data.shape:
            f.write(struct.pack('Q', dim))
        f.write(data.dtype.str.encode('ascii'))
        f.write(flat_data.tobytes())
    
    logger.info(f"Compressed data to {output_path} using bzip2 level {level}")
    return output_path

def decompress_bzip2(compressed_path: Path) -> np.ndarray:
    """
    Decompress bzip2-compressed numpy array.
    
    Args:
        compressed_path: Path to compressed file
        
    Returns:
        Decompressed numpy array
    """
    with bz2.open(compressed_path, 'rb') as f:
        ndim = struct.unpack('I', f.read(4))[0]
        size = struct.unpack('Q', f.read(8))[0]
        shape = tuple(struct.unpack('Q', f.read(8)) for _ in range(ndim))
        dtype_str = f.readline().strip().decode('ascii')
        
        raw_data = f.read()
        data = np.frombuffer(raw_data, dtype=dtype_str)
        data = data.reshape(shape)
    
    logger.debug(f"Decompressed data from {compressed_path}")
    return data

def compress_lzma(data: np.ndarray, level: int = LZMA_DEFAULT, output_path: Optional[Path] = None) -> Path:
    """
    Compress numpy array using lzma.
    
    Args:
        data: 1D or 2D numpy array of strain data
        level: Compression level (0-9, default 6)
        output_path: Optional output path. If None, uses default naming.
        
    Returns:
        Path to compressed file
    """
    if level not in LZMA_LEVELS:
        logger.warning(f"Level {level} not in standard set {LZMA_LEVELS}, proceeding anyway")
    
    if output_path is None:
        output_path = get_project_root() / "data" / "interim" / "compressed" / "lossless" / "lzma" / f"level_{level}.xz"
    
    ensure_dir(output_path.parent)
    
    flat_data = data.flatten()
    
    with lzma.open(output_path, 'wb', preset=level) as f:
        f.write(struct.pack('I', data.ndim))
        f.write(struct.pack('Q', data.size))
        for dim in data.shape:
            f.write(struct.pack('Q', dim))
        f.write(data.dtype.str.encode('ascii'))
        f.write(flat_data.tobytes())
    
    logger.info(f"Compressed data to {output_path} using lzma level {level}")
    return output_path

def decompress_lzma(compressed_path: Path) -> np.ndarray:
    """
    Decompress lzma-compressed numpy array.
    
    Args:
        compressed_path: Path to compressed file
        
    Returns:
        Decompressed numpy array
    """
    with lzma.open(compressed_path, 'rb') as f:
        ndim = struct.unpack('I', f.read(4))[0]
        size = struct.unpack('Q', f.read(8))[0]
        shape = tuple(struct.unpack('Q', f.read(8)) for _ in range(ndim))
        dtype_str = f.readline().strip().decode('ascii')
        
        raw_data = f.read()
        data = np.frombuffer(raw_data, dtype=dtype_str)
        data = data.reshape(shape)
    
    logger.debug(f"Decompressed data from {compressed_path}")
    return data

def compress_lz4(data: np.ndarray, level: int = LZ4_DEFAULT, output_path: Optional[Path] = None) -> Path:
    """
    Compress numpy array using lz4.
    
    Args:
        data: 1D or 2D numpy array of strain data
        level: Compression level (1-9, default 4)
        output_path: Optional output path. If None, uses default naming.
        
    Returns:
        Path to compressed file
    """
    if level not in LZ4_LEVELS:
        logger.warning(f"Level {level} not in standard set {LZ4_LEVELS}, proceeding anyway")
    
    if output_path is None:
        output_path = get_project_root() / "data" / "interim" / "compressed" / "lossless" / "lz4" / f"level_{level}.lz4"
    
    ensure_dir(output_path.parent)
    
    flat_data = data.flatten()
    
    # lz4.frame.compress accepts level as integer
    compressed_bytes = lz4.frame.compress(
        struct.pack('I', data.ndim) + 
        struct.pack('Q', data.size) + 
        b''.join(struct.pack('Q', dim) for dim in data.shape) + 
        data.dtype.str.encode('ascii') + b'\n' +
        flat_data.tobytes(),
        compression_level=level
    )
    
    with open(output_path, 'wb') as f:
        f.write(compressed_bytes)
    
    logger.info(f"Compressed data to {output_path} using lz4 level {level}")
    return output_path

def decompress_lz4(compressed_path: Path) -> np.ndarray:
    """
    Decompress lz4-compressed numpy array.
    
    Args:
        compressed_path: Path to compressed file
        
    Returns:
        Decompressed numpy array
    """
    with open(compressed_path, 'rb') as f:
        compressed_bytes = f.read()
    
    decompressed_bytes = lz4.frame.decompress(compressed_bytes)
    
    # Parse header
    ndim = struct.unpack('I', decompressed_bytes[:4])[0]
    size = struct.unpack('Q', decompressed_bytes[4:12])[0]
    offset = 12
    shape = []
    for _ in range(ndim):
        shape.append(struct.unpack('Q', decompressed_bytes[offset:offset+8])[0])
        offset += 8
    
    dtype_str = decompressed_bytes[offset:offset+10].decode('ascii').strip('\x00')
    offset += len(dtype_str) + 1
    
    data = np.frombuffer(decompressed_bytes[offset:], dtype=dtype_str)
    data = data.reshape(shape)
    
    logger.debug(f"Decompressed data from {compressed_path}")
    return data

def compress_data(data: np.ndarray, method: str, level: int, output_path: Optional[Path] = None) -> Path:
    """
    Generic compression dispatcher.
    
    Args:
        data: Numpy array to compress
        method: One of 'gzip', 'bzip2', 'lzma', 'lz4'
        level: Compression level
        output_path: Optional output path
        
    Returns:
        Path to compressed file
    """
    method_map = {
        'gzip': (compress_gzip, GZIP_LEVELS),
        'bzip2': (compress_bzip2, BZIP2_LEVELS),
        'lzma': (compress_lzma, LZMA_LEVELS),
        'lz4': (compress_lz4, LZ4_LEVELS)
    }
    
    if method not in method_map:
        raise ValueError(f"Unknown compression method: {method}. Supported: {list(method_map.keys())}")
    
    compressor, valid_levels = method_map[method]
    if level not in valid_levels:
        logger.warning(f"Level {level} not in standard set {valid_levels} for {method}")
    
    return compressor(data, level=level, output_path=output_path)

def decompress_data(compressed_path: Path, method: str) -> np.ndarray:
    """
    Generic decompression dispatcher.
    
    Args:
        compressed_path: Path to compressed file
        method: One of 'gzip', 'bzip2', 'lzma', 'lz4'
        
    Returns:
        Decompressed numpy array
    """
    method_map = {
        'gzip': decompress_gzip,
        'bzip2': decompress_bzip2,
        'lzma': decompress_lzma,
        'lz4': decompress_lz4
    }
    
    if method not in method_map:
        raise ValueError(f"Unknown compression method: {method}. Supported: {list(method_map.keys())}")
    
    return method_map[method](compressed_path)

def verify_lossless(original: np.ndarray, decompressed: np.ndarray, tolerance: float = 1e-10) -> bool:
    """
    Verify that decompression is lossless.
    
    Args:
        original: Original numpy array
        decompressed: Decompressed numpy array
        tolerance: Floating point tolerance for comparison
        
    Returns:
        True if arrays are equal within tolerance
    """
    if original.shape != decompressed.shape:
        logger.error(f"Shape mismatch: {original.shape} vs {decompressed.shape}")
        return False
    
    if original.dtype != decompressed.dtype:
        logger.error(f"Dtype mismatch: {original.dtype} vs {decompressed.dtype}")
        return False
    
    max_diff = np.max(np.abs(original - decompressed))
    is_lossless = max_diff <= tolerance
    
    if not is_lossless:
        logger.error(f"Lossless verification failed. Max diff: {max_diff}")
    else:
        logger.debug("Lossless verification passed")
        
    return is_lossless

def main():
    """
    Run a simple test of all compression methods.
    """
    logger.info("Running lossless compression test...")
    
    # Create test data
    np.random.seed(42)
    test_data = np.random.randn(10000).astype(np.float64)
    
    methods = ['gzip', 'bzip2', 'lzma', 'lz4']
    levels = [1, 5, 9]
    
    for method in methods:
        for level in levels:
            try:
                # Compress
                comp_path = compress_data(test_data, method, level)
                
                # Decompress
                dec_data = decompress_data(comp_path, method)
                
                # Verify
                is_ok = verify_lossless(test_data, dec_data)
                
                # Calculate compression ratio
                orig_size = test_data.nbytes
                comp_size = comp_path.stat().st_size
                ratio = orig_size / comp_size
                
                status = "PASS" if is_ok else "FAIL"
                logger.info(f"{method} level {level}: {status}, Ratio: {ratio:.2f}x")
                
                # Cleanup
                comp_path.unlink()
                meta_path = comp_path.with_suffix('.meta.json')
                if meta_path.exists():
                    meta_path.unlink()
                    
            except Exception as e:
                logger.error(f"{method} level {level} failed: {e}")
    
    logger.info("Lossless compression test complete.")

if __name__ == "__main__":
    main()