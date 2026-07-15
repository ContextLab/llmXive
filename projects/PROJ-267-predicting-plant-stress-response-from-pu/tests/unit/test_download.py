"""
Unit tests for code/data_ingestion/download.py (T011)

Tests:
1. Domain validation (allowed vs disallowed).
2. File size validation (mocked response).
3. URL parsing from research.md format.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_ingestion.download import (
    validate_domain,
    parse_research_md_urls,
    download_file,
    ALLOWED_DOMAINS
)
from utils.config import DATA_RAW_PATH

class TestDomainValidation:
    def test_valid_ncbi_domain(self):
        assert validate_domain("https://ncbi.nlm.nih.gov/gds") is True
        assert validate_domain("https://www.ncbi.nlm.nih.gov/gds") is True

    def test_valid_proteomexchange_domain(self):
        assert validate_domain("https://proteomexchange.org") is True
        assert validate_domain("https://www.proteomexchange.org") is True

    def test_valid_ebi_domain(self):
        assert validate_domain("https://ebi.ac.uk") is True
        assert validate_domain("https://www.ebi.ac.uk") is True

    def test_invalid_domain(self):
        assert validate_domain("https://malicious-site.com") is False
        assert validate_domain("https://google.com") is False

class TestUrlParsing:
    def test_parse_urls_from_markdown(self):
        md_content = """
        # Research Data Sources
        
        - [NCBI GEO] (https://ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE12345)
        - [ProteomeXchange] (https://proteomexchange.org/cgi/GetDataset?ID=PXD000001)
        
        Some text with a URL: https://ebi.ac.uk/pride/archive/12345
        """
        
        # Create a temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md_content)
            temp_path = f.name
        
        try:
            urls = parse_research_md_urls(temp_path)
            assert len(urls) == 3
            assert urls[0]['source'] == 'NCBI GEO'
            assert 'ncbi.nlm.nih.gov' in urls[0]['url']
            assert urls[2]['source'] == 'Unknown' # Heuristic might fail on plain text URL
        finally:
            os.unlink(temp_path)

    def test_parse_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# No URLs here")
            temp_path = f.name
        
        try:
            urls = parse_research_md_urls(temp_path)
            assert len(urls) == 0
        finally:
            os.unlink(temp_path)

class TestDownloadFile:
    def test_download_success(self):
        url = "https://ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE12345"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_file.txt"
            
            # Mock response
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b"Hello World " * 100] # > 1KB
            mock_response.headers = {"Content-Length": "1200"}
            mock_response.raise_for_status = MagicMock()
            
            with patch('data_ingestion.download.requests.get', return_value=mock_response):
                result = download_file(url, output_path)
                assert result is True
                assert output_path.exists()
                assert output_path.stat().st_size >= 1024

    def test_download_too_small(self):
        url = "https://ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE12345"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_file.txt"
            
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b"Small"]
            mock_response.headers = {"Content-Length": "5"}
            mock_response.raise_for_status = MagicMock()
            
            with patch('data_ingestion.download.requests.get', return_value=mock_response):
                with pytest.raises(ValueError, match="less than 1KB"):
                    download_file(url, output_path)
                # Verify file was cleaned up
                assert not output_path.exists()

    def test_download_invalid_domain(self):
        url = "https://bad-site.com/data"
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_file.txt"
            
            with pytest.raises(ValueError, match="Domain validation failed"):
                download_file(url, output_path)