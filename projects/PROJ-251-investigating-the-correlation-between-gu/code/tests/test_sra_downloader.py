import os
import unittest
from unittest.mock import patch, MagicMock, mock_open, call
from pathlib import Path
import subprocess

# Import the module to test
from code.utils.sra_downloader import (
    get_sra_run_ids,
    prefetch_sra_run,
    fasterq_dump,
    download_fastq_for_study,
    run_strategy_b,
    DataUnavailableError
)
from code.utils.config import get_raw_path

class TestSRADownloader(unittest.TestCase):

    @patch('code.utils.sra_downloader.subprocess.Popen')
    def test_get_sra_run_ids_success(self, mock_popen):
        """Test successful extraction of Run IDs."""
        # Mock the chain of processes
        mock_p1 = MagicMock()
        mock_p1.communicate.return_value = (b"<eSearchResult><Count>1</Count>...</eSearchResult>", b"")
        mock_p1.returncode = 0

        mock_p2 = MagicMock()
        mock_p2.communicate.return_value = (b"Run\nSRR123456\nSRR789012", b"")
        mock_p2.returncode = 0

        mock_p3 = MagicMock()
        mock_p3.communicate.return_value = (b"SRR123456\nSRR789012\n", b"")
        mock_p3.returncode = 0

        # Setup the sequence of calls
        mock_popen.side_effect = [mock_p1, mock_p2, mock_p3]

        run_ids = get_sra_run_ids("SRP053178")

        self.assertEqual(run_ids, ["SRR123456", "SRR789012"])
        self.assertEqual(mock_popen.call_count, 3)

    @patch('code.utils.sra_downloader.subprocess.Popen')
    def test_get_sra_run_ids_empty_result(self, mock_popen):
        """Test handling of empty search results."""
        mock_p1 = MagicMock()
        mock_p1.communicate.return_value = (b"<eSearchResult><Count>0</Count></eSearchResult>", b"")
        mock_p1.returncode = 0

        mock_popen.side_effect = [mock_p1]

        with self.assertRaises(DataUnavailableError):
            get_sra_run_ids("SRP999999")

    @patch('code.utils.sra_downloader.subprocess.run')
    def test_prefetch_sra_run_success(self, mock_run):
        """Test successful prefetch."""
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock Path.exists to return True
        with patch('code.utils.sra_downloader.Path.exists', return_value=True):
            success, msg = prefetch_sra_run("SRR123", Path("/tmp"))
            self.assertTrue(success)
            self.assertIn("Successfully prefetched", msg)

    @patch('code.utils.sra_downloader.subprocess.run')
    def test_fasterq_dump_success(self, mock_run):
        """Test successful conversion to FASTQ."""
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock glob to find files
        with patch('pathlib.Path.glob', return_value=[Path("/tmp/SRR123_1.fastq")]):
            success, msg = fasterq_dump("SRR123", Path("/tmp/sra"), Path("/tmp/out"))
            self.assertTrue(success)
            self.assertIn("Successfully converted", msg)

    @patch('code.utils.sra_downloader.get_sra_run_ids')
    @patch('code.utils.sra_downloader.prefetch_sra_run')
    @patch('code.utils.sra_downloader.fasterq_dump')
    @patch('code.utils.sra_downloader.get_raw_path')
    def test_run_strategy_b_integration(self, mock_get_raw, mock_fasterq, mock_prefetch, mock_get_ids):
        """Integration test for the full strategy B flow."""
        mock_get_raw.return_value = Path("/tmp/raw")
        mock_get_ids.return_value = ["SRR001"]
        mock_prefetch.return_value = (True, "OK")
        mock_fasterq.return_value = (True, "OK")
        
        # Mock Path.glob to return a file
        with patch('pathlib.Path.glob', return_value=[Path("/tmp/raw/fastq_files/SRR001_1.fastq")]):
            files = run_strategy_b("SRP053178")
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].name, "SRR001_1.fastq")

    @patch('code.utils.sra_downloader.get_sra_run_ids')
    def test_run_strategy_b_no_runs(self, mock_get_ids):
        """Test failure when no runs are found."""
        mock_get_ids.side_effect = DataUnavailableError("No runs found")
        
        with self.assertRaises(DataUnavailableError):
            run_strategy_b("SRP999")

if __name__ == '__main__':
    unittest.main()