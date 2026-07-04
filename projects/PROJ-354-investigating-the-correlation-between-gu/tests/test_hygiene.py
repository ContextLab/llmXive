"""
Unit tests for data hygiene utilities in code/utils/hygiene.py
"""

import json
import tempfile
from pathlib import Path
from unittest import TestCase

import pandas as pd
import numpy as np

from code.utils.hygiene import (
    compute_file_checksum,
    compute_directory_checksum,
    mask_pii_value,
    mask_dataframe_pii,
    validate_data_integrity,
    generate_data_manifest,
)


class TestFileChecksum(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = Path(self.temp_dir.name) / "test.txt"
        self.test_content = b"Hello, World! This is test content."
        self.test_file.write_bytes(self.test_content)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_sha256_checksum(self):
        checksum = compute_file_checksum(self.test_file, 'sha256')
        self.assertEqual(len(checksum), 64)  # SHA256 produces 64 hex chars
        self.assertIsInstance(checksum, str)
    
    def test_md5_checksum(self):
        checksum = compute_file_checksum(self.test_file, 'md5')
        self.assertEqual(len(checksum), 32)  # MD5 produces 32 hex chars
    
    def test_nonexistent_file(self):
        with self.assertRaises(FileNotFoundError):
            compute_file_checksum("nonexistent.txt")
    
    def test_deterministic(self):
        checksum1 = compute_file_checksum(self.test_file)
        checksum2 = compute_file_checksum(self.test_file)
        self.assertEqual(checksum1, checksum2)


class TestDirectoryChecksum(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        
        # Create nested structure
        (self.data_dir / "subdir").mkdir()
        (self.data_dir / "file1.txt").write_text("content1")
        (self.data_dir / "subdir" / "file2.txt").write_text("content2")
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_directory_checksum(self):
        checksums = compute_directory_checksum(self.data_dir)
        self.assertIn("file1.txt", checksums)
        self.assertIn("subdir/file2.txt", checksums)
        self.assertEqual(len(checksums), 2)
    
    def test_non_directory(self):
        with self.assertRaises(NotADirectoryError):
            compute_directory_checksum(self.data_dir / "file1.txt")


class TestPIIMasking(TestCase):
    def test_mask_email(self):
        value = "user@example.com"
        masked = mask_pii_value(value, field_name="email")
        self.assertIn("@", masked)
        self.assertNotEqual(value, masked)
    
    def test_mask_phone(self):
        value = "123-456-7890"
        masked = mask_pii_value(value, field_name="phone")
        self.assertNotEqual(value, masked)
    
    def test_mask_ssn(self):
        value = "123-45-6789"
        masked = mask_pii_value(value, field_name="ssn")
        self.assertNotEqual(value, masked)
    
    def test_mask_ip(self):
        value = "192.168.1.1"
        masked = mask_pii_value(value, field_name="ip")
        self.assertNotEqual(value, masked)
    
    def test_no_pii(self):
        value = "12345"
        masked = mask_pii_value(value)
        self.assertEqual(value, masked)
    
    def test_none_value(self):
        self.assertIsNone(mask_pii_value(None))
        self.assertTrue(pd.isna(mask_pii_value(np.nan)))
    
    def test_generic_email_detection(self):
        value = "Contact: user@example.com for info"
        masked = mask_pii_value(value)
        self.assertNotEqual(value, masked)
        self.assertIn("@", masked)

class TestDataframePIIMasking(TestCase):
    def setUp(self):
        self.df = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'email': ['alice@test.com', 'bob@test.com', 'charlie@test.com'],
            'age': [25, 30, 35],
            'ssn': ['123-45-6789', '234-56-7890', '345-67-8901'],
            'score': [85, 90, 95]
        })
    
    def test_mask_auto_detect(self):
        masked_df = mask_dataframe_pii(self.df)
        self.assertNotEqual(masked_df['email'].iloc[0], self.df['email'].iloc[0])
        self.assertNotEqual(masked_df['ssn'].iloc[0], self.df['ssn'].iloc[0])
        self.assertEqual(masked_df['age'].iloc[0], self.df['age'].iloc[0])
        self.assertEqual(masked_df['score'].iloc[0], self.df['score'].iloc[0])
    
    def test_mask_explicit_columns(self):
        masked_df = mask_dataframe_pii(self.df, pii_columns=['email'])
        self.assertNotEqual(masked_df['email'].iloc[0], self.df['email'].iloc[0])
        self.assertEqual(masked_df['ssn'].iloc[0], self.df['ssn'].iloc[0])

class TestDataIntegrityValidation(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        
        self.file1 = self.data_dir / "file1.txt"
        self.file2 = self.data_dir / "file2.txt"
        
        self.file1.write_text("content1")
        self.file2.write_text("content2")
        
        self.expected_checksums = {
            "file1.txt": compute_file_checksum(self.file1),
            "file2.txt": compute_file_checksum(self.file2),
        }
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_valid_checksums(self):
        results = validate_data_integrity(self.expected_checksums, self.data_dir)
        self.assertTrue(all(results.values()))
    
    def test_invalid_checksum(self):
        invalid_checksums = self.expected_checksums.copy()
        invalid_checksums["file1.txt"] = "invalid_checksum"
        
        results = validate_data_integrity(invalid_checksums, self.data_dir)
        self.assertFalse(results["file1.txt"])
        self.assertTrue(results["file2.txt"])
    
    def test_missing_file(self):
        results = validate_data_integrity(self.expected_checksums, self.data_dir)
        self.assertTrue(results["file1.txt"])
        self.assertTrue(results["file2.txt"])

class TestDataManifest(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        
        self.file1 = self.data_dir / "file1.txt"
        self.file1.write_text("content1")
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_generate_manifest(self):
        manifest = generate_data_manifest(self.data_dir)
        self.assertIn('checksums', manifest)
        self.assertIn('file1.txt', manifest['checksums'])
        self.assertEqual(manifest['file_count'], 1)
    
    def test_write_manifest(self):
        manifest_path = Path(self.temp_dir.name) / "manifest.json"
        manifest = generate_data_manifest(self.data_dir, manifest_path)
        
        self.assertTrue(manifest_path.exists())
        with open(manifest_path) as f:
            loaded_manifest = json.load(f)
        
        self.assertEqual(manifest, loaded_manifest)