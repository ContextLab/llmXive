import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
import pandas as pd
from code.utils.sra_downloader import (
    _check_sratoolkit,
    get_run_ids_for_accession,
    download_fastq_from_sra,
    fetch_sra_data
)
from code.utils.config import get_raw_path

class TestSRADownloader(unittest.TestCase):

    @patch('code.utils.sra_downloader.subprocess.run')
    def test_check_sratoolkit_true(self, mock_run):
        """Test that _check_sratoolkit returns True when commands are found."""
        mock_run.side_effect = [
            MagicMock(returncode=0), # which prefetch
            MagicMock(returncode=0)  # which fasterq-dump
        ]
        self.assertTrue(_check_sratoolkit())

    @patch('code.utils.sra_downloader.subprocess.run')
    def test_check_sratoolkit_false(self, mock_run):
        """Test that _check_sratoolkit returns False when commands are missing."""
        mock_run.side_effect = [
            MagicMock(returncode=0),
            subprocess.CalledProcessError(1, "cmd")
        ]
        self.assertFalse(_check_sratoolkit())

    @patch('code.utils.sra_downloader.requests.get')
    def test_get_run_ids_for_accession_success(self, mock_get):
        """Test fetching run IDs with mocked requests."""
        # Mock esearch response
        mock_esearch = MagicMock()
        mock_esearch.json.return_value = {"esearchresult": {"idlist": ["12345"]}}
        mock_esearch.raise_for_status = MagicMock()
        
        # Mock efetch response (CSV)
        mock_efetch = MagicMock()
        mock_efetch.text = "Run,Experiment,Title\nSRR123456,ERP000001,Test\nSRR123457,ERP000001,Test2"
        mock_efetch.raise_for_status = MagicMock()
        
        mock_get.side_effect = [mock_esearch, mock_esearch, mock_efetch]

        run_ids = get_run_ids_for_accession("SRP053178")
        self.assertEqual(run_ids, ["SRR123456", "SRR123457"])

    @patch('code.utils.sra_downloader.requests.get')
    def test_get_run_ids_empty(self, mock_get):
        """Test fetching run IDs when no results found."""
        mock_esearch = MagicMock()
        mock_esearch.json.return_value = {"esearchresult": {"idlist": []}}
        mock_get.return_value = mock_esearch
        
        run_ids = get_run_ids_for_accession("INVALID")
        self.assertEqual(run_ids, [])

    @patch('code.utils.sra_downloader._check_sratoolkit')
    def test_download_fastq_no_tool(self, mock_check):
        """Test download fails if sratoolkit is not installed."""
        mock_check.return_value = False
        result = download_fastq_from_sra("SRR123", Path("/tmp"))
        self.assertIsNone(result)

    @patch('code.utils.sra_downloader._check_sratoolkit')
    @patch('code.utils.sra_downloader.subprocess.run')
    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.glob')
    def test_download_fastq_success(self, mock_glob, mock_mkdir, mock_run, mock_check):
        """Test successful download flow."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        mock_glob.return_value = [Path("/tmp/test.fastq")]
        
        result = download_fastq_from_sra("SRR123", Path("/tmp"))
        self.assertEqual(result, Path("/tmp/test.fastq"))

    @patch('code.utils.sra_downloader.get_run_ids_for_accession')
    @patch('code.utils.sra_downloader.download_fastq_from_sra')
    @patch('code.utils.sra_downloader.ensure_directories')
    @patch('code.utils.sra_downloader.get_raw_path')
    def test_fetch_sra_data_integration(self, mock_raw_path, mock_ensure, mock_download, mock_get_ids):
        """Test the full fetch_sra_data orchestration."""
        mock_raw_path.return_value = Path("/data/raw")
        mock_get_ids.return_value = ["SRR1", "SRR2"]
        mock_download.side_effect = [Path("/data/raw/SRR1/test.fastq"), None] # One success, one fail

        run_ids, files = fetch_sra_data("SRP053178")
        
        self.assertEqual(run_ids, ["SRR1", "SRR2"])
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], Path("/data/raw/SRR1/test.fastq"))

    @patch('code.utils.sra_downloader.get_run_ids_for_accession')
    @patch('code.utils.sra_downloader.ensure_directories')
    @patch('code.utils.sra_downloader.get_raw_path')
    def test_fetch_sra_data_no_runs(self, mock_raw_path, mock_ensure, mock_get_ids):
        """Test fetch_sra_data raises error if no runs found."""
        mock_raw_path.return_value = Path("/data/raw")
        mock_get_ids.return_value = []

        with self.assertRaises(RuntimeError) as context:
            fetch_sra_data("SRP053178")
        
        self.assertIn("ERR_NO_DATA", str(context.exception))

if __name__ == '__main__':
    unittest.main()