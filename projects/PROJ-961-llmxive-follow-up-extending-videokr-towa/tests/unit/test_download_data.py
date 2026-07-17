"""
Unit tests for download_data.py
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import the module under test
import code.ingest.download_data as download_data


class TestComputeSha256:
    """Tests for compute_sha256 function."""

    def test_compute_sha256_basic(self):
        """Test basic SHA-256 computation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = Path(f.name)

        try:
            hash_result = download_data.compute_sha256(temp_path)
            assert len(hash_result) == 64  # SHA-256 hex length
            assert all(c in '0123456789abcdef' for c in hash_result)
        finally:
            os.unlink(temp_path)


class TestDownloadFunctions:
    """Tests for download functions (mocked)."""

    @patch('code.ingest.download_data.load_dataset')
    @patch('code.ingest.download_data.ensure_dir')
    def test_download_videokr_sft(self, mock_ensure_dir, mock_load_dataset):
        """Test VideoKR-SFT download logic."""
        # Setup mock dataset
        mock_dataset = MagicMock()
        mock_dataset.__len__ = MagicMock(return_value=100)
        mock_dataset.column_names = ['question', 'answer', 'video_id']
        mock_dataset.to_parquet = MagicMock()

        mock_load_dataset.return_value = mock_dataset

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = download_data.download_videokr_sft(output_dir)

            # Assertions
            assert result.exists()
            mock_load_dataset.assert_called_once()
            mock_dataset.to_parquet.assert_called_once()

    @patch('code.ingest.download_data.load_dataset')
    @patch('code.ingest.download_data.ensure_dir')
    def test_download_knowledge_graph(self, mock_ensure_dir, mock_load_dataset):
        """Test Knowledge Graph download logic."""
        # Setup mock graph dataset
        mock_graph = MagicMock()
        mock_graph.__len__ = MagicMock(return_value=50)
        mock_graph.__iter__ = MagicMock(return_value=iter([{'source': 'A', 'target': 'B'}]))

        mock_load_dataset.return_value = mock_graph

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = download_data.download_knowledge_graph(output_dir)

            # Assertions
            assert result.exists()
            assert result.suffix == '.json'
            mock_load_dataset.assert_called_once()


class TestVerifyChecksums:
    """Tests for checksum verification."""

    def test_verify_checksums_creates_file(self):
        """Test that checksum verification creates the checksums file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            
            # Create a test file
            test_file = output_dir / "test.txt"
            test_file.write_text("test content")

            success, checksums = download_data.verify_checksums(output_dir)

            assert success is True
            assert "test.txt" in checksums
            assert len(checksums["test.txt"]) == 64

            # Check checksum file was created
            checksum_file = output_dir / "checksums.json"
            assert checksum_file.exists()

            with open(checksum_file) as f:
                saved_checksums = json.load(f)
            
            assert "test.txt" in saved_checksums

class TestMain:
    """Tests for main function execution."""

    @patch('code.ingest.download_data.download_videokr_sft')
    @patch('code.ingest.download_data.download_knowledge_graph')
    @patch('code.ingest.download_data.verify_checksums')
    @patch('code.ingest.download_data.get_project_root')
    @patch('code.ingest.download_data.ensure_dir')
    def test_main_success(
        self, 
        mock_ensure_dir, 
        mock_get_root, 
        mock_verify, 
        mock_download_kg, 
        mock_download_sft
    ):
        """Test successful main execution."""
        # Setup mocks
        mock_root = Path("/fake/project")
        mock_get_root.return_value = mock_root
        
        mock_sft_file = MagicMock()
        mock_sft_file.name = "videokr_sft.parquet"
        mock_sft_file.stat.return_value.st_size = 1024
        mock_download_sft.return_value = mock_sft_file

        mock_kg_file = MagicMock()
        mock_kg_file.name = "videokr_kg.json"
        mock_kg_file.stat.return_value.st_size = 512
        mock_download_kg.return_value = mock_kg_file

        mock_verify.return_value = (True, {})

        # Run main
        download_data.main()

        # Verify calls
        mock_get_root.assert_called_once()
        mock_download_sft.assert_called_once()
        mock_download_kg.assert_called_once()
        mock_verify.assert_called_once()