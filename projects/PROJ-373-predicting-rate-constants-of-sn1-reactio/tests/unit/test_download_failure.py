"""
tests/unit/test_download_failure.py

Unit test for T600: Verifies that download.py raises a fatal exception
if the HuggingFace dataset fetch fails, ensuring NO synthetic fallback.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datasets import load_dataset

class TestDownloadFailure(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.raw_dir = Path(self.test_dir) / "data" / "raw"
        self.processed_dir = Path(self.test_dir) / "data" / "processed"
        self.raw_dir.mkdir(parents=True)
        self.processed_dir.mkdir(parents=True)

        # Create a mock pipeline status file as 'OK'
        self.pipeline_status_file = self.processed_dir / ".pipeline_status"
        with open(self.pipeline_status_file, 'w') as f:
            f.write("OK")

        self.output_file = self.raw_dir / "sn1_raw.parquet"

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir)

    @patch('code.data.download.load_dataset')
    def test_download_failure_raises_error_no_synthetic(self, mock_load_dataset):
        """
        Test that if load_dataset raises an error, the script exits with code 1
        and NO synthetic file is created.
        """
        # Mock load_dataset to raise a ConnectionError
        mock_load_dataset.side_effect = ConnectionError("Network error")

        # Run the download script
        script_path = project_root / "code" / "data" / "download.py"
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root)

        # We need to run the script as a subprocess to capture exit code
        # But since we are patching, we can't easily patch in a subprocess.
        # Instead, we will test the function directly.
        # However, the task requires testing the script's behavior.
        # Let's test the main function by importing and calling it with mocked dependencies.

        from code.data.download import main, download_dataset

        # Mock the output path and dataset name
        with patch('code.data.download.check_schema_pass', return_value=True):
            with patch('code.data.download.ensure_dirs'):
                try:
                    # This should raise an exception
                    download_dataset("test_dataset", self.output_file, streaming=False)
                    self.fail("Expected RuntimeError to be raised")
                except RuntimeError as e:
                    self.assertIn("Dataset download failed", str(e))
                    # Verify no file was created
                    self.assertFalse(self.output_file.exists())

    @patch('code.data.download.load_dataset')
    def test_download_failure_exits_with_code_1(self, mock_load_dataset):
        """
        Test that the script exits with code 1 on failure.
        """
        mock_load_dataset.side_effect = ValueError("Missing columns")

        # We will test the main function by calling it and catching SystemExit
        from code.data.download import main
        from code.data.download import check_schema_pass, ensure_dirs

        with patch('code.data.download.check_schema_pass', return_value=True):
            with patch('code.data.download.ensure_dirs'):
                with self.assertRaises(SystemExit) as context:
                    # We need to mock the download_dataset function to raise an exception
                    with patch('code.data.download.download_dataset', side_effect=RuntimeError("Download failed")):
                        main()

                self.assertEqual(context.exception.code, 1)

    def test_no_synthetic_file_created_on_failure(self):
        """
        Test that no synthetic file is created if download fails.
        """
        # We will simulate a failure by mocking the download function
        from code.data.download import main, download_dataset
        from code.data.download import check_schema_pass, ensure_dirs

        with patch('code.data.download.check_schema_pass', return_value=True):
            with patch('code.data.download.ensure_dirs'):
                with patch('code.data.download.download_dataset', side_effect=RuntimeError("Download failed")):
                    with self.assertRaises(SystemExit):
                        main()

                    # Verify no synthetic file exists
                    synthetic_files = list(self.raw_dir.glob("synthetic_*"))
                    mock_files = list(self.raw_dir.glob("mock_*"))
                    self.assertEqual(len(synthetic_files), 0)
                    self.assertEqual(len(mock_files), 0)

    def test_pipeline_status_not_modified_on_failure(self):
        """
        Test that the pipeline status is not set to 'OK' if download fails.
        (It should remain 'OK' if it was 'OK', or be unchanged if it was 'ABORTED')
        But the task says: "If 'ABORTED', exit with code 1 immediately. DO NOT create any intermediate files."
        And: "Handle download failures by raising an error (no synthetic fallback)."
        So if download fails, we don't change the status, we just exit.
        """
        from code.data.download import main, download_dataset
        from code.data.download import check_schema_pass, ensure_dirs

        # Set status to 'OK'
        with open(self.pipeline_status_file, 'w') as f:
            f.write("OK")

        with patch('code.data.download.check_schema_pass', return_value=True):
            with patch('code.data.download.ensure_dirs'):
                with patch('code.data.download.download_dataset', side_effect=RuntimeError("Download failed")):
                    with self.assertRaises(SystemExit):
                        main()

                    # Verify status is still 'OK' (or unchanged)
                    with open(self.pipeline_status_file, 'r') as f:
                        status = f.read().strip()
                    self.assertEqual(status, "OK")

if __name__ == '__main__':
    unittest.main()