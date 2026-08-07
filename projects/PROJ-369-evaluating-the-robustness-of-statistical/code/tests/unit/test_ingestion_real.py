"""
Unit tests for real data ingestion (T014).
These tests verify that the ingestion functions can handle real URLs and fail loudly on errors.
"""
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data.ingestion import (
    validate_url, 
    download_file, 
    IngestionError, 
    ingest_yahoo_finance,
    load_csv_robust
)

class TestRealDataIngestion:
    """Tests for real data ingestion functionality."""

    def test_validate_url_real(self):
        """Test URL validation with a real URL."""
        url = "https://raw.githubusercontent.com/robertmartin8/USWeatherData/master/NOAA/USW00014895.csv"
        assert validate_url(url, timeout=30) is True

    def test_validate_url_invalid(self):
        """Test URL validation with an invalid URL."""
        url = "https://this-does-not-exist-12345.com/data.csv"
        assert validate_url(url, timeout=5) is False

    def test_download_file_real(self):
        """Test downloading a real file."""
        url = "https://raw.githubusercontent.com/robertmartin8/USWeatherData/master/NOAA/USW00014895.csv"
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = os.path.join(tmpdir, "test.csv")
            result = download_file(url, dest_path)
            assert os.path.exists(result)
            assert os.path.getsize(result) > 0

    def test_download_file_fail_loudly(self):
        """Test that download_file fails loudly on invalid URL."""
        url = "https://this-does-not-exist-12345.com/data.csv"
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = os.path.join(tmpdir, "test.csv")
            with pytest.raises(IngestionError):
                download_file(url, dest_path)

    def test_ingest_yahoo_finance_real(self):
        """Test ingestion of real Yahoo Finance data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = ingest_yahoo_finance("AAPL", tmpdir)
            assert manifest.name == "Yahoo_AAPL"
            assert manifest.status == "downloaded"
            assert manifest.rows is not None
            assert manifest.rows > 0
            assert os.path.exists(manifest.local_path)

    def test_load_csv_robust_real(self):
        """Test loading a real CSV file."""
        url = "https://raw.githubusercontent.com/robertmartin8/USWeatherData/master/NOAA/USW00014895.csv"
        with tempfile.TemporaryDirectory() as tmpdir:
            dest_path = os.path.join(tmpdir, "test.csv")
            download_file(url, dest_path)
            df = load_csv_robust(dest_path)
            assert df is not None
            assert len(df) > 0