"""
Unit tests for the OpenNeuro downloader module (code/data/download.py).

Tests cover:
- MD5 checksum calculation on real temporary files.
- Checksum verification logic (match/mismatch).
- Argument validation for download_openneuro_dataset.
- Integration with the real OpenNeuro CLI (if available) or mock verification.
"""

import os
import tempfile
import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
from code.data.download import calculate_md5, verify_checksum, download_openneuro_dataset


class TestCalculateMD5(unittest.TestCase):
    """Tests for the calculate_md5 function."""

    def test_calculate_md5_empty_file(self):
        """MD5 of an empty file should be d41d8cd98f00b204e9800998ecf8427e."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        try:
            result = calculate_md5(tmp_path)
            self.assertEqual(result, "d41d8cd98f00b204e9800998ecf8427e")
        finally:
            os.unlink(tmp_path)

    def test_calculate_md5_known_string(self):
        """MD5 of 'hello' should be 5d41402abc4b2a76b9719d911017c592."""
        content = b"hello"
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            result = calculate_md5(tmp_path)
            self.assertEqual(result, "5d41402abc4b2a76b9719d911017c592")
        finally:
            os.unlink(tmp_path)

    def test_calculate_md5_nonexistent_file(self):
        """Should raise FileNotFoundError for missing paths."""
        with self.assertRaises(FileNotFoundError):
            calculate_md5("/path/that/does/not/exist.txt")


class TestVerifyChecksum(unittest.TestCase):
    """Tests for the verify_checksum function."""

    def test_verify_checksum_match(self):
        """Should return True when file MD5 matches expected."""
        content = b"test_data"
        expected_md5 = hashlib.md5(content).hexdigest()
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            result = verify_checksum(tmp_path, expected_md5)
            self.assertTrue(result)
        finally:
            os.unlink(tmp_path)

    def test_verify_checksum_mismatch(self):
        """Should return False when file MD5 does not match expected."""
        content = b"test_data"
        wrong_md5 = "00000000000000000000000000000000"
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            result = verify_checksum(tmp_path, wrong_md5)
            self.assertFalse(result)
        finally:
            os.unlink(tmp_path)

    def test_verify_checksum_nonexistent_file(self):
        """Should raise FileNotFoundError for missing paths."""
        with self.assertRaises(FileNotFoundError):
            verify_checksum("/nonexistent/file.txt", "some_md5")


class TestDownloadOpenNeuroDataset(unittest.TestCase):
    """Tests for the download_openneuro_dataset function."""

    def test_missing_dataset_id(self):
        """Should raise ValueError if dataset_id is empty."""
        with self.assertRaises(ValueError):
            download_openneuro_dataset(dataset_id="", output_dir="/tmp")

    def test_missing_output_dir(self):
        """Should raise ValueError if output_dir is not a valid path."""
        with self.assertRaises(ValueError):
            download_openneuro_dataset(dataset_id="ds000001", output_dir=None)

    @patch('code.data.download.subprocess.run')
    def test_download_success(self, mock_run):
        """Should call openneuro-cli with correct arguments on success."""
        mock_run.return_value = MagicMock(returncode=0)
        
        dataset_id = "ds000234"
        output_dir = "/tmp/test_output"
        subjects = ["sub-01", "sub-02"]
        
        download_openneuro_dataset(
            dataset_id=dataset_id,
            output_dir=output_dir,
            subjects=subjects
        )
        
        # Verify subprocess.run was called
        self.assertTrue(mock_run.called)
        call_args = mock_run.call_args[0][0]
        
        # Check that the command contains expected parts
        self.assertIn("openneuro", call_args)
        self.assertIn("download", call_args)
        self.assertIn(f"--dataset={dataset_id}", call_args)
        self.assertIn(f"--output={output_dir}", call_args)
        
        # Check that subjects are included if provided
        for sub in subjects:
            self.assertIn(f"--subject={sub}", call_args)

    @patch('code.data.download.subprocess.run')
    def test_download_failure(self, mock_run):
        """Should raise RuntimeError if subprocess returns non-zero exit code."""
        mock_run.return_value = MagicMock(returncode=1, stderr="Error occurred")
        
        with self.assertRaises(RuntimeError):
            download_openneuro_dataset(
                dataset_id="ds000234",
                output_dir="/tmp/test_output"
            )

    @patch('code.data.download.subprocess.run')
    def test_download_with_checksum_verification(self, mock_run):
        """Should verify checksums after download if checksums are provided."""
        mock_run.return_value = MagicMock(returncode=0)
        
        # Mock calculate_md5 to return a specific value for verification
        with patch('code.data.download.calculate_md5') as mock_calc_md5:
            mock_calc_md5.return_value = "verified_md5_hash"
            
            with patch('code.data.download.verify_checksum') as mock_verify:
                mock_verify.return_value = True
                
                dataset_id = "ds000234"
                output_dir = "/tmp/test_output"
                checksums = {
                    "sub-01/anat/sub-01_T1w.nii.gz": "verified_md5_hash"
                }
                
                # This should not raise an exception
                download_openneuro_dataset(
                    dataset_id=dataset_id,
                    output_dir=output_dir,
                    checksums=checksums
                )
                
                # Verify checksum function was called
                self.assertTrue(mock_verify.called)
