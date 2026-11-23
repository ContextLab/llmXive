"""
Unit tests for generate_ingested_cohort.py
"""
import os
import sys
import pytest
from pathlib import Path
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from generate_ingested_cohort import calculate_file_checksum, save_state_entry

class TestCalculateChecksum:
    def test_calculate_file_checksum(self, tmp_path):
        """Test checksum calculation on a known file."""
        test_file = tmp_path / "test.txt"
        test_content = b"Hello, World!"
        test_file.write_bytes(test_content)
        
        checksum = calculate_file_checksum(test_file)
        
        # Expected SHA256 for "Hello, World!"
        expected = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
        assert checksum == expected

    def test_calculate_file_checksum_empty(self, tmp_path):
        """Test checksum calculation on empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_bytes(b"")
        
        checksum = calculate_file_checksum(test_file)
        
        # Expected SHA256 for empty file
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert checksum == expected

class TestSaveStateEntry:
    @patch('generate_ingested_cohort.yaml')
    @patch('generate_ingested_cohort.open')
    def test_save_state_entry_new_file(self, mock_open, mock_yaml, tmp_path):
        """Test saving state entry when state.yaml doesn't exist."""
        # Setup mocks
        mock_yaml.safe_load.return_value = None
        mock_yaml.dump = MagicMock()
        
        test_file = tmp_path / "test.parquet"
        test_file.write_bytes(b"test")
        
        # Mock the project root
        with patch('generate_ingested_cohort.project_root', tmp_path):
            save_state_entry(test_file, "abc123", "Test description")
        
        # Verify yaml.dump was called
        assert mock_yaml.dump.called

    @patch('generate_ingested_cohort.yaml')
    @patch('generate_ingested_cohort.open')
    def test_save_state_entry_existing_file(self, mock_open, mock_yaml, tmp_path):
        """Test saving state entry when state.yaml already exists."""
        # Setup mocks
        existing_state = {"files": {"old_file": {"path": "old.parquet"}}}
        mock_yaml.safe_load.return_value = existing_state
        mock_yaml.dump = MagicMock()
        
        test_file = tmp_path / "test.parquet"
        test_file.write_bytes(b"test")
        
        # Mock the project root
        with patch('generate_ingested_cohort.project_root', tmp_path):
            save_state_entry(test_file, "abc123", "Test description")
        
        # Verify yaml.dump was called
        assert mock_yaml.dump.called