"""
Unit tests for code/utils/data_io.py
"""
import json
import hashlib
import os
import tempfile
from pathlib import Path
from unittest import TestCase

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / 'code'))

from utils.data_io import compute_sha256, write_dataset_metadata, verify_metadata_hash


class TestComputeSha256(TestCase):
    def test_compute_sha256_file(self):
        """Test SHA256 computation on a temporary file."""
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as tmp:
            content = b"Hello, World!"
            tmp.write(content)
            tmp_path = tmp.name

        try:
            expected_hash = hashlib.sha256(content).hexdigest()
            computed_hash = compute_sha256(tmp_path)
            self.assertEqual(computed_hash, expected_hash)
        finally:
            os.unlink(tmp_path)

    def test_compute_sha256_empty_file(self):
        """Test SHA256 computation on an empty file."""
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as tmp:
            tmp_path = tmp.name

        try:
            expected_hash = hashlib.sha256(b"").hexdigest()
            computed_hash = compute_sha256(tmp_path)
            self.assertEqual(computed_hash, expected_hash)
        finally:
            os.unlink(tmp_path)

    def test_compute_sha256_nonexistent_file(self):
        """Test that computing SHA256 on a nonexistent file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            compute_sha256("/nonexistent/path/to/file.txt")


class TestWriteDatasetMetadata(TestCase):
    def test_write_dataset_metadata(self):
        """Test writing dataset metadata to a JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metadata.json"
            data = {
                "seed": 12345,
                "n": 100,
                "p": 1000,
                "rho": 0.5,
                "distribution_type": "normal"
            }

            write_dataset_metadata(output_path, data)

            self.assertTrue(output_path.exists())
            with open(output_path, 'r') as f:
                loaded_data = json.load(f)

            self.assertEqual(loaded_data, data)

    def test_write_dataset_metadata_creates_directory(self):
        """Test that write_dataset_metadata creates the output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "subdir" / "metadata.json"
            data = {"key": "value"}

            write_dataset_metadata(nested_path, data)

            self.assertTrue(nested_path.exists())
            with open(nested_path, 'r') as f:
                loaded_data = json.load(f)
            self.assertEqual(loaded_data, data)


class TestVerifyMetadataHash(TestCase):
    def test_verify_metadata_hash_success(self):
        """Test successful verification when hash matches."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metadata.json"
            data = {
                "seed": 12345,
                "n": 100,
                "p": 1000,
                "rho": 0.5,
                "distribution_type": "normal"
            }

            write_dataset_metadata(output_path, data)
            is_valid = verify_metadata_hash(output_path, data)

            self.assertTrue(is_valid)

    def test_verify_metadata_hash_failure(self):
        """Test verification failure when hash doesn't match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "metadata.json"
            original_data = {
                "seed": 12345,
                "n": 100,
                "p": 1000,
                "rho": 0.5,
                "distribution_type": "normal"
            }

            write_dataset_metadata(output_path, original_data)
            
            # Modify data slightly
            modified_data = original_data.copy()
            modified_data["seed"] = 99999

            is_valid = verify_metadata_hash(output_path, modified_data)

            self.assertFalse(is_valid)