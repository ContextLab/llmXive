"""
Tests for chunked FITS streaming and memory-safe I/O.
"""
import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
from astropy.io import fits
from utils.io import load_map_chunked, validate_fits_nside, safe_read_header, stream_fits_file
import logging

# Set up logging for tests
logging.basicConfig(level=logging.INFO)


def create_test_fits_file(tmp_path: Path, nside: int, size_mb: int = 10) -> Path:
    """
    Create a mock FITS file with HEALPix data for testing.
    """
    n_pix = 12 * (nside ** 2)
    # Create a small subset for testing if file would be too large
    if n_pix > 1000000:
        n_pix = 1000000  # Cap for test speed

    data = np.zeros(n_pix, dtype=[('PIXEL', np.int32), ('TEMPERATURE', np.float32)])
    data['PIXEL'] = np.arange(n_pix)
    data['TEMPERATURE'] = np.random.randn(n_pix).astype(np.float32)

    file_path = tmp_path / "test_map.fits"

    hdu = fits.BinTableHDU(data=data, name='SIGNAL')
    hdu.header['NSIDE'] = nside
    hdu.header['ORDERING'] = 'RING'
    hdu.header['PIXTYPE'] = 'HEALPIX'

    hdul = fits.HDUList([fits.PrimaryHDU(), hdu])
    hdul.writeto(file_path, overwrite=True)
    hdul.close()

    return file_path


class TestChunkedMapLoadingAndMask:
    """
    Tests for chunked FITS loading to ensure no OOM on constrained memory.
    """

    def test_chunked_loading_basic(self, tmp_path):
        """Test basic chunked loading of a FITS file."""
        nside = 64
        file_path = create_test_fits_file(tmp_path, nside)

        chunks = list(load_map_chunked(file_path, nside, chunk_pixels=1000))

        assert len(chunks) > 0
        total_pixels = 0
        for start, end, temps in chunks:
            total_pixels += len(temps)
            assert isinstance(temps, list)
            assert len(temps) > 0

        expected_pixels = 12 * (nside ** 2)
        assert total_pixels == expected_pixels

    def test_chunked_loading_memory_safe(self, tmp_path):
        """Test that chunked loading respects memory limits."""
        nside = 128
        file_path = create_test_fits_file(tmp_path, nside)

        # Load with small chunks
        chunks = list(load_map_chunked(file_path, nside, chunk_pixels=100))

        assert len(chunks) > 0
        # Verify data integrity across chunks
        first_chunk = chunks[0]
        assert first_chunk[0] == 0  # Start at 0
        assert first_chunk[1] == 100  # End at 100

    def test_validate_nside_success(self, tmp_path):
        """Test Nside validation for valid file."""
        nside = 256
        file_path = create_test_fits_file(tmp_path, nside)

        is_valid, actual_nside = validate_fits_nside(file_path, min_nside=256)

        assert is_valid is True
        assert actual_nside == nside

    def test_validate_nside_failure(self, tmp_path):
        """Test Nside validation for invalid file (too low)."""
        nside = 128
        file_path = create_test_fits_file(tmp_path, nside)

        is_valid, actual_nside = validate_fits_nside(file_path, min_nside=256)

        assert is_valid is False
        assert actual_nside == nside

    def test_safe_read_header(self, tmp_path):
        """Test safe reading of FITS header."""
        nside = 64
        file_path = create_test_fits_file(tmp_path, nside)

        header = safe_read_header(file_path)

        assert 'NSIDE' in header
        assert header['NSIDE'] == str(nside)

    def test_stream_fits_file(self, tmp_path):
        """Test streaming FITS file in chunks."""
        nside = 64
        file_path = create_test_fits_file(tmp_path, nside)

        chunks = list(stream_fits_file(file_path, chunk_size=1024))

        assert len(chunks) > 0
        total_size = sum(len(c) for c in chunks)
        assert total_size > 0

    def test_chunked_loading_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            list(load_map_chunked(Path("/nonexistent/file.fits"), 64))

    def test_chunked_loading_invalid_nside(self, tmp_path):
        """Test behavior when nside doesn't match file."""
        nside = 64
        file_path = create_test_fits_file(tmp_path, nside)

        # Request wrong nside - should still load but warn
        chunks = list(load_map_chunked(file_path, nside=32))
        assert len(chunks) > 0
