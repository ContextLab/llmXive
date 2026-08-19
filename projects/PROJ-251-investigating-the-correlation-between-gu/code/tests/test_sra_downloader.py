"""
Placeholder for SRA Downloader Tests.
"""
import os
import unittest
from unittest.mock import patch, MagicMock, mock_open, call
from pathlib import Path
import subprocess
from code.utils.sra_downloader import DataUnavailableError, get_sra_run_ids, prefetch_sra_run, fasterq_dump, download_fastq_for_study, run_strategy_b

class TestSRADownloader(unittest.TestCase):
    def test_get_sra_run_ids(self):
        pass

if __name__ == "__main__":
    unittest.main()
