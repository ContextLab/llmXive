import os
import sys
import pytest
import pandas as pd
import hashlib
from pathlib import Path
import tempfile

from analysis.write_dataset import calculate_file_checksum, write_processed_dataset

class TestWriteDataset:
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data = pd.DataFrame({
            "sample_id": ["S1", "S2", "S3"],
            "heteroplasmy_burden": [0.1, 0.2, 0.3],
            "age": [20, 30, 40],
            "sex": ["M", "F", "M"],
            "haplogroup": ["H1", "J1", "T1"]
        })
        self.output_path = Path(self.temp_dir) / "test_dataset.csv"
        self.checksum_path = Path(self.temp_dir) / "test_dataset.csv.md5"

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.output_path.exists():
            self.output_path.unlink()
        if self.checksum_path.exists():
            self.checksum_path.unlink()
        os.rmdir(self.temp_dir)

    def test_write_processed_dataset_creates_files(self):
        """Test that write_processed_dataset creates the CSV and checksum files."""
        write_processed_dataset(self.test_data, self.output_path, self.checksum_path)
        
        assert self.output_path.exists(), "Output CSV file was not created."
        assert self.checksum_path.exists(), "Checksum file was not created."

    def test_write_processed_dataset_content(self):
        """Test that the written CSV contains the correct data."""
        write_processed_dataset(self.test_data, self.output_path, self.checksum_path)
        
        loaded_df = pd.read_csv(self.output_path)
        pd.testing.assert_frame_equal(self.test_data, loaded_df)

    def test_calculate_file_checksum(self):
        """Test that calculate_file_checksum returns the correct hash."""
        # Create a known file
        test_content = b"Hello, World!"
        test_file = Path(self.temp_dir) / "known_content.txt"
        test_file.write_bytes(test_content)
        
        expected_hash = hashlib.md5(test_content).hexdigest()
        calculated_hash = calculate_file_checksum(test_file)
        
        assert calculated_hash == expected_hash, "Checksum calculation is incorrect."

    def test_checksum_file_content(self):
        """Test that the checksum file contains the correct hash and filename."""
        write_processed_dataset(self.test_data, self.output_path, self.checksum_path)
        
        with open(self.checksum_path, "r") as f:
            line = f.readline().strip()
        
        parts = line.split("  ")
        assert len(parts) == 2, "Checksum file format is incorrect."
        
        stored_hash, stored_filename = parts
        calculated_hash = calculate_file_checksum(self.output_path)
        
        assert stored_hash == calculated_hash, "Stored hash does not match calculated hash."
        assert stored_filename == self.output_path.name, "Stored filename does not match."