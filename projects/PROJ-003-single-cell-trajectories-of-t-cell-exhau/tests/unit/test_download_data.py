import unittest
from unittest.mock import patch, MagicMock, Mock
import subprocess
import os
import sys
from pathlib import Path
import tempfile
import json

# Add the code directory to the path for imports
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from download_data import check_sra_toolkit, get_sra_ids_for_gse, download_sra, TARGET_GSE_IDS

class TestCheckSraToolkit(unittest.TestCase):
    @patch('subprocess.run')
    def test_sra_toolkit_installed(self, mock_run):
        # Mock successful runs for both prefetch and fasterq-dump
        mock_run.side_effect = [
            MagicMock(returncode=0), # prefetch
            MagicMock(returncode=0)  # fasterq-dump
        ]
        
        result = check_sra_toolkit()
        self.assertTrue(result)
        self.assertEqual(mock_run.call_count, 2)

    @patch('subprocess.run')
    def test_sra_toolkit_not_found(self, mock_run):
        # Mock FileNotFoundError
        mock_run.side_effect = FileNotFoundError("Command not found")
        
        result = check_sra_toolkit()
        self.assertFalse(result)

    @patch('subprocess.run')
    def test_sra_toolkit_non_zero_exit(self, mock_run):
        # Mock non-zero exit code
        mock_run.side_effect = [
            MagicMock(returncode=1), # prefetch fails
            MagicMock(returncode=0)
        ]
        
        result = check_sra_toolkit()
        self.assertFalse(result)

class TestGetSraIdsForGse(unittest.TestCase):
    @patch('subprocess.run')
    def test_valid_gse_response(self, mock_run):
        # Mock XML response with SRA IDs
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
        <eSearchResult>
            <Count>2</Count>
            <RetMax>2</RetStart>0</RetStart>
            <IdList>
                <Id>SRR123456</Id>
                <Id>SRR789012</Id>
            </IdList>
        </eSearchResult>"""
        
        mock_run.return_value = MagicMock(
            stdout=xml_response,
            stderr="",
            returncode=0
        )
        
        ids = get_sra_ids_for_gse("GSE136103")
        self.assertEqual(len(ids), 2)
        self.assertIn("SRR123456", ids)
        self.assertIn("SRR789012", ids)

    @patch('subprocess.run')
    def test_empty_response(self, mock_run):
        # Mock empty response
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="",
            returncode=0
        )
        
        ids = get_sra_ids_for_gse("GSE999999")
        self.assertEqual(ids, [])

    @patch('subprocess.run')
    def test_timeout_error(self, mock_run):
        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=60)
        
        ids = get_sra_ids_for_gse("GSE136103")
        self.assertEqual(ids, [])

class TestDownloadSra(unittest.TestCase):
    @patch('subprocess.run')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.glob')
    def test_download_success(self, mock_glob, mock_mkdir, mock_run):
        # Setup mocks
        mock_mkdir.return_value = None
        mock_glob.return_value = [Path("mock/SRR123456.fastq")]
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = download_sra("SRR123456", output_dir)
            self.assertTrue(result)
            mock_run.assert_called_once()

    @patch('subprocess.run')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.glob')
    def test_download_failure_no_files(self, mock_glob, mock_mkdir, mock_run):
        # Setup mocks
        mock_mkdir.return_value = None
        mock_glob.return_value = [] # No files found
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr=""
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = download_sra("SRR123456", output_dir)
            self.assertFalse(result)

    @patch('subprocess.run')
    @patch('pathlib.Path.mkdir')
    def test_download_failure_called_process(self, mock_mkdir, mock_run):
        # Setup mocks
        mock_mkdir.return_value = None
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Error")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            result = download_sra("SRR123456", output_dir)
            self.assertFalse(result)

class TestTargetDatasets(unittest.TestCase):
    def test_target_gse_ids(self):
        expected = ["GSE136103", "GSE127465", "GSE111075", "GSE138852"]
        self.assertEqual(TARGET_GSE_IDS, expected)

if __name__ == '__main__':
    unittest.main()
