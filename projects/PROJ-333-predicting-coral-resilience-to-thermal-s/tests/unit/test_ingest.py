"""
Unit tests for the ingest module.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import hashlib

# Import the module under test
# Adjust import path based on project structure
from code.ingest import (
    _create_session_with_retries,
    _fetch_sra_run_info,
    _get_fastq_urls,
    _download_file_with_progress,
    _calculate_sha256,
    run_ingestion,
    save_download_log,
    DownloadStatus,
    IngestionError
)
from code.utils.errors import NCBITimeoutError, NCBIConnectionError


class TestCreateSessionWithRetries:
    def test_session_created(self):
        session = _create_session_with_retries()
        assert session is not None
        assert hasattr(session, 'mount')
        
    def test_retries_configured(self):
        session = _create_session_with_retries()
        # Verify adapters are mounted
        assert "https://" in session.adapters
        assert "http://" in session.adapters


class TestGetFastqUrls:
    def test_single_url(self):
        run_info = {"fastq_ftp": "ftp://example.com/file.fastq.gz"}
        urls = _get_fastq_urls(run_info)
        assert urls == ["ftp://example.com/file.fastq.gz"]
        
    def test_multiple_urls(self):
        run_info = {"fastq_ftp": "ftp://example.com/file1.fastq.gz;ftp://example.com/file2.fastq.gz"}
        urls = _get_fastq_urls(run_info)
        assert len(urls) == 2
        
    def test_no_urls(self):
        run_info = {}
        urls = _get_fastq_urls(run_info)
        assert urls == []
        
    def test_mixed_valid_invalid(self):
        run_info = {"fastq_ftp": "ftp://example.com/file1.fastq.gz;http://example.com/file2.fastq.gz"}
        urls = _get_fastq_urls(run_info)
        assert len(urls) == 2  # Both are valid FTP/HTTP URLs


class TestCalculateChecksum:
    def test_valid_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)
            
        try:
            checksum = _calculate_sha256(tmp_path)
            expected = hashlib.sha256(b"test data").hexdigest()
            assert checksum == expected
        finally:
            os.unlink(tmp_path)
            
    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
            
        try:
            checksum = _calculate_sha256(tmp_path)
            expected = hashlib.sha256(b"").hexdigest()
            assert checksum == expected
        finally:
            os.unlink(tmp_path)


class TestDownloadFileWithProgress:
    def test_successful_download(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.fastq.gz"
            url = "https://example.com/test.fastq.gz"
            
            # Mock the session.get response
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b"fake data"]
            mock_response.headers = {"content-length": "9"}
            mock_response.raise_for_status = MagicMock()
            
            with patch('code.ingest.requests.Session') as MockSession:
                mock_session_instance = MagicMock()
                MockSession.return_value = mock_session_instance
                mock_session_instance.get.return_value = mock_response
                
                success, error_msg = _download_file_with_progress(url, output_path, mock_session_instance)
                
                assert success is True
                assert error_msg == ""
                assert output_path.exists()
                
    def test_timeout_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.fastq.gz"
            url = "https://example.com/test.fastq.gz"
            
            with patch('code.ingest.requests.Session') as MockSession:
                mock_session_instance = MagicMock()
                MockSession.return_value = mock_session_instance
                mock_session_instance.get.side_effect = Exception("Timeout")
                
                success, error_msg = _download_file_with_progress(url, output_path, mock_session_instance)
                
                assert success is False
                assert "timeout" in error_msg.lower() or "failed" in error_msg.lower()


class TestSaveDownloadLog:
    def test_save_log(self):
        status_log = [
            DownloadStatus(sample_id="S1", file_path="/path/to/file.fastq.gz", status="success"),
            DownloadStatus(sample_id="S2", file_path=None, status="failed", error_message="Timeout")
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "download_log.json"
            save_download_log(status_log, log_path)
            
            assert log_path.exists()
            with open(log_path, 'r') as f:
                data = json.load(f)
                
            assert len(data) == 2
            assert data[0]["status"] == "success"
            assert data[1]["status"] == "failed"


class TestRunIngestion:
    @patch('code.ingest._fetch_sra_run_info')
    @patch('code.ingest._get_fastq_urls')
    @patch('code.ingest._download_file_with_progress')
    def test_run_ingestion_success(self, mock_download, mock_get_urls, mock_fetch):
        # Mock run info
        mock_fetch.return_value = [
            {"run_id": "SRR123", "fastq_ftp": "ftp://example.com/file.fastq.gz"}
        ]
        mock_get_urls.return_value = ["ftp://example.com/file.fastq.gz"]
        mock_download.return_value = (True, "")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            status_log = run_ingestion(output_dir)
            
            assert len(status_log) > 0
            assert any(s.status == "success" for s in status_log)
            
    @patch('code.ingest._fetch_sra_run_info')
    def test_run_ingestion_no_runs(self, mock_fetch):
        mock_fetch.return_value = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            status_log = run_ingestion(output_dir)
            
            assert len(status_log) == 0
            
    @patch('code.ingest._fetch_sra_run_info')
    def test_run_ingestion_no_urls(self, mock_fetch):
        mock_fetch.return_value = [
            {"run_id": "SRR123", "fastq_ftp": None}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            status_log = run_ingestion(output_dir)
            
            assert len(status_log) == 1
            assert status_log[0].status == "skipped"
            assert "No FASTQ URLs found" in status_log[0].error_message
