"""
Tests for data_loader.py error handling and logging logic.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Import the module under test
import sys
sys.path.insert(0, 'code')
from data_loader import calculate_checksum, verify_checksum, load_and_segment, load_local_segmented_data


class TestChecksum:
    """Tests for checksum calculation and verification."""

    def test_calculate_checksum_consistency(self):
        """Test that checksum is consistent across calls."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test data for checksum")
            temp_path = f.name

        try:
            checksum1 = calculate_checksum(temp_path)
            checksum2 = calculate_checksum(temp_path)
            assert checksum1 == checksum2
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_success(self):
        """Test successful checksum verification."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test data")
            temp_path = f.name

        try:
            checksum = calculate_checksum(temp_path)
            assert verify_checksum(temp_path, checksum) is True
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_failure(self):
        """Test checksum verification failure."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test data")
            temp_path = f.name

        try:
            assert verify_checksum(temp_path, "invalid_checksum") is False
        finally:
            os.unlink(temp_path)


class TestLoadAndSegment:
    """Tests for load_and_segment function."""

    def test_download_failure_raises_error(self):
        """Test that download failure raises RuntimeError."""
        with patch('data_loader.requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            with pytest.raises(RuntimeError) as exc_info:
                load_and_segment("http://example.com/data.csv")
            
            assert "Failed to download" in str(exc_info.value)

    def test_checksum_mismatch_raises_error(self):
        """Test that checksum mismatch raises RuntimeError."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("col1,col2\n1,2\n3,4")
            temp_path = f.name

        try:
            with patch('data_loader.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.iter_content = MagicMock(return_value=[open(temp_path, 'rb').read()])
                mock_get.return_value = mock_response
                
                with pytest.raises(RuntimeError) as exc_info:
                    load_and_segment("http://example.com/data.csv", expected_checksum="invalid")
                
                assert "Checksum verification failed" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_empty_dataset_raises_error(self):
        """Test that empty dataset raises ValueError."""
        # Create an empty CSV
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("col1,col2\n")
            temp_path = f.name

        try:
            with patch('data_loader.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.iter_content = MagicMock(return_value=[open(temp_path, 'rb').read()])
                mock_get.return_value = mock_response
                
                with pytest.raises(ValueError) as exc_info:
                    load_and_segment("http://example.com/data.csv")
                
                assert "empty" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_insufficient_segment_logs_skip(self):
        """Test that segments with < 30 rows are logged as skipped."""
        # Create a small CSV (< 30 rows)
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("col1,col2\n")
            for i in range(10):
                f.write(f"{i},{i+1}\n")
            temp_path = f.name

        try:
            # Ensure results directory exists
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            log_path = results_dir / "simulation_logs.json"
            
            # Clear existing logs
            if log_path.exists():
                log_path.unlink()
            
            with patch('data_loader.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.iter_content = MagicMock(return_value=[open(temp_path, 'rb').read()])
                mock_get.return_value = mock_response
                
                segments = load_and_segment("http://example.com/data.csv")
                
                # Should return empty list since all segments are too small
                assert len(segments) == 0
                
                # Check that log was written
                assert log_path.exists()
                with open(log_path, 'r') as f:
                    logs = json.load(f)
                
                assert len(logs) > 0
                assert logs[0]["status"] == "skipped"
                assert logs[0]["reason"] == "insufficient_data"
        finally:
            os.unlink(temp_path)

    def test_missing_values_handled(self):
        """Test that missing values are dropped."""
        # Create CSV with missing values
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("col1,col2,col3\n")
            for i in range(50):
                if i % 5 == 0:
                    f.write(f"{i},,\n")  # Missing value
                else:
                    f.write(f"{i},{i+1},{i+2}\n")
            temp_path = f.name

        try:
            with patch('data_loader.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.iter_content = MagicMock(return_value=[open(temp_path, 'rb').read()])
                mock_get.return_value = mock_response
                
                segments = load_and_segment("http://example.com/data.csv")
                
                # Should have segments after dropping missing values
                assert len(segments) > 0
                for seg in segments:
                    assert len(seg["data"]) >= 30
        finally:
            os.unlink(temp_path)

    def test_valid_data_segmented_correctly(self):
        """Test that valid data is segmented correctly."""
        # Create a larger CSV
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("col1,col2\n")
            for i in range(250):
                f.write(f"{i},{i+1}\n")
            temp_path = f.name

        try:
            with patch('data_loader.requests.get') as mock_get:
                mock_response = MagicMock()
                mock_response.raise_for_status = MagicMock()
                mock_response.iter_content = MagicMock(return_value=[open(temp_path, 'rb').read()])
                mock_get.return_value = mock_response
                
                segments = load_and_segment("http://example.com/data.csv")
                
                # Should have 2 segments of 100 rows each (250 / 100 = 2 full, 1 partial skipped)
                assert len(segments) == 2
                for seg in segments:
                    assert len(seg["data"]) == 100
                    assert seg["size"] == 100
        finally:
            os.unlink(temp_path)


class TestLoadLocalSegmentedData:
    """Tests for load_local_segmented_data function."""

    def test_file_not_found_raises_error(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_local_segmented_data("nonexistent/path/data.csv")

    def test_empty_file_raises_error(self):
        """Test that empty file raises ValueError."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("col1,col2\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                load_local_segmented_data(temp_path)
            
            assert "empty" in str(exc_info.value).lower()
        finally:
            os.unlink(temp_path)

    def test_valid_local_file(self):
        """Test loading valid local file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("col1,col2\n")
            for i in range(200):
                f.write(f"{i},{i+1}\n")
            temp_path = f.name

        try:
            segments = load_local_segmented_data(temp_path)
            
            assert len(segments) == 2
            for seg in segments:
                assert len(seg["data"]) == 100
        finally:
            os.unlink(temp_path)
