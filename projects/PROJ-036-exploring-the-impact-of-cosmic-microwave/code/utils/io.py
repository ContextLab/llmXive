"""
I/O utilities with memory-safe streaming and logging integration.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Iterator, Any, Dict, Tuple, List

# Import from sibling modules
try:
    from utils.logging_config import get_logger, check_memory_limit, check_disk_limit, log_resource_snapshot
except ImportError:
    # Fallback if imported directly without package structure
    import logging
    def get_logger():
        return logging.getLogger("cmb_lss_pipeline")
    def check_memory_limit(limit_gb=7.0): return True
    def check_disk_limit(path=None, limit_gb=14.0): return True
    def log_resource_snapshot(prefix=""): pass


def stream_fits_file(
    file_path: Path,
    chunk_size: int = 1024 * 1024,  # 1MB chunks
    memory_limit_gb: float = 7.0,
    disk_limit_gb: float = 14.0
) -> Iterator[bytes]:
    """
    Stream a FITS file in chunks to avoid OOM.
    Checks memory/disk limits before yielding each chunk.

    Args:
        file_path: Path to the FITS file.
        chunk_size: Size of each chunk in bytes.
        memory_limit_gb: Max memory usage in GB.
        disk_limit_gb: Max disk usage in GB.

    Yields:
        Chunks of file data.
    """
    logger = get_logger()
    logger.info(f"Streaming file: {file_path} (chunk_size={chunk_size})")

    if not file_path.exists():
        raise FileNotFoundError(f"FITS file not found: {file_path}")

    # Initial checks
    if not check_memory_limit(memory_limit_gb):
        raise MemoryError(f"Memory limit exceeded before streaming: {file_path}")
    if not check_disk_limit(limit_gb=disk_limit_gb):
        raise OSError(f"Disk limit exceeded before streaming: {file_path}")

    log_resource_snapshot(prefix="Before stream: ")

    with open(file_path, 'rb') as f:
        while True:
            # Check limits periodically
            if not check_memory_limit(memory_limit_gb):
                logger.critical("Memory limit exceeded during stream. Aborting.")
                break
            if not check_disk_limit(limit_gb=disk_limit_gb):
                logger.critical("Disk limit exceeded during stream. Aborting.")
                break

            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk
            log_resource_snapshot(prefix="After chunk: ")


def safe_read_header(file_path: Path, max_bytes: int = 2880 * 10) -> dict:
    """
    Safely read the first N bytes of a FITS file to parse the header.
    Includes logging and resource checks.

    Args:
        file_path: Path to FITS file.
        max_bytes: Maximum bytes to read for header.

    Returns:
        Dictionary of header keywords (basic parsing).
    """
    logger = get_logger()
    logger.info(f"Reading header for: {file_path}")

    if not check_memory_limit():
        raise MemoryError("Memory limit exceeded reading header.")

    header = {}
    try:
        with open(file_path, 'rb') as f:
            raw = f.read(max_bytes)
            # Basic parsing of FITS header (simplified)
            # In a real scenario, use astropy.io.fits or fitsio
            lines = raw.decode('ascii', errors='ignore').split('\n')
            for line in lines:
                if line.startswith('SIMPLE'):
                    header['SIMPLE'] = line.split('=')[1].strip()
                elif line.startswith('BITPIX'):
                    header['BITPIX'] = line.split('=')[1].strip()
                elif line.startswith('NAXIS'):
                    header['NAXIS'] = line.split('=')[1].strip()
                elif line.startswith('NSIDE'):
                    header['NSIDE'] = line.split('=')[1].strip()
    except Exception as e:
        logger.error(f"Error reading header for {file_path}: {e}")
        raise

    log_resource_snapshot(prefix="Header read: ")
    return header


def load_fits_header_with_astropy(file_path: Path) -> Dict[str, Any]:
    """
    Load FITS header using astropy.io.fits for robust parsing.
    This is the primary method for production use.

    Args:
        file_path: Path to FITS file.

    Returns:
        Dictionary of header keywords.
    """
    logger = get_logger()
    logger.info(f"Loading header with astropy for: {file_path}")

    if not check_memory_limit(2.0):  # Conservative limit for header load
        raise MemoryError("Memory limit exceeded reading header with astropy.")

    try:
        from astropy.io import fits
        with fits.open(file_path, memmap=False) as hdul:
            header_dict = dict(hdul[0].header)
            logger.info(f"Successfully loaded header from {file_path}")
            return header_dict
    except ImportError:
        logger.warning("astropy.io.fits not available, falling back to safe_read_header")
        return safe_read_header(file_path)
    except Exception as e:
        logger.error(f"Error loading header with astropy for {file_path}: {e}")
        raise


def load_map_chunked(
    file_path: Path,
    nside: int,
    chunk_pixels: int = 100000
) -> Iterator[Tuple[int, int, List[float]]]:
    """
    Load a HEALPix map in chunks of pixels to avoid OOM.
    Assumes the FITS file contains a single BINTABLE extension with 'PIXEL' and 'TEMPERATURE' columns.

    Args:
        file_path: Path to FITS file.
        nside: HEALPix Nside parameter (for validation).
        chunk_pixels: Number of pixels to load per chunk.

    Yields:
        Tuples of (start_pixel, end_pixel, data_chunk).
    """
    logger = get_logger()
    logger.info(f"Loading map chunked: {file_path}, nside={nside}, chunk_pixels={chunk_pixels}")

    if not check_memory_limit():
        raise MemoryError("Memory limit exceeded before loading map chunks.")

    try:
        from astropy.io import fits
        import numpy as np
    except ImportError as e:
        logger.error(f"Required library missing for chunked loading: {e}")
        raise

    # Validate Nside
    total_pixels = 12 * (nside ** 2)
    logger.info(f"Total pixels for Nside={nside}: {total_pixels}")

    try:
        # Open with memmap=False to avoid loading entire file into memory at once
        # but we will read row by row or in blocks
        with fits.open(file_path, memmap=False) as hdul:
            # Find the primary extension with data
            data_hdu = None
            for hdu in hdul:
                if hasattr(hdu, 'data') and hdu.data is not None:
                    data_hdu = hdu
                    break

            if data_hdu is None:
                raise ValueError("No data found in FITS file.")

            # Check Nside in header
            header_nside = data_hdu.header.get('NSIDE', None)
            if header_nside is not None and int(header_nside) != nside:
                logger.warning(f"Nside mismatch: header={header_nside}, requested={nside}")

            # Determine column names (standard Planck: PIXEL, TEMPERATURE)
            # Or generic: first column is index, second is value
            col_names = [col.name for col in data_hdu.columns]
            if 'PIXEL' in col_names:
                pixel_col = 'PIXEL'
            else:
                pixel_col = col_names[0]

            if 'TEMPERATURE' in col_names:
                temp_col = 'TEMPERATURE'
            else:
                temp_col = col_names[1] if len(col_names) > 1 else col_names[0]

            logger.info(f"Using columns: pixel={pixel_col}, temp={temp_col}")

            # Iterate in chunks
            total_rows = len(data_hdu.data)
            start = 0
            while start < total_rows:
                if not check_memory_limit():
                    logger.critical("Memory limit exceeded during chunked load.")
                    break

                end = min(start + chunk_pixels, total_rows)
                chunk_data = data_hdu.data[start:end]

                pixels = chunk_data[pixel_col]
                temps = chunk_data[temp_col]

                yield start, end, temps.tolist()

                start = end
                log_resource_snapshot(prefix="Map chunk loaded: ")

    except Exception as e:
        logger.error(f"Error in load_map_chunked for {file_path}: {e}")
        raise


def validate_fits_nside(file_path: Path, min_nside: int = 256) -> Tuple[bool, int]:
    """
    Validate that a FITS file has Nside >= min_nside.

    Args:
        file_path: Path to FITS file.
        min_nside: Minimum required Nside.

    Returns:
        Tuple of (is_valid, actual_nside).
    """
    logger = get_logger()
    logger.info(f"Validating Nside for: {file_path} (min={min_nside})")

    try:
        header = load_fits_header_with_astropy(file_path)
        nside = header.get('NSIDE', 0)

        if nside < min_nside:
            logger.error(f"Nside {nside} is less than required {min_nside}")
            return False, nside

        logger.info(f"Nside validation passed: {nside} >= {min_nside}")
        return True, nside

    except Exception as e:
        logger.error(f"Error validating Nside for {file_path}: {e}")
        raise
