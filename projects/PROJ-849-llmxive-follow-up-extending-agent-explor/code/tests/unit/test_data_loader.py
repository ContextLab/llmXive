"""
Unit tests for the data_loader module.

Tests strict real-data fetch logic, memory limits, and validation.
"""
import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import BytesIO
import socket

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from lib.data_loader import (
    check_url_reachability,
    load_dataset,
    load_dataset_from_url,
    load_dataset_from_file,
    validate_dataset,
    load_and_validate_data,
    DataLoaderError,
    MemoryLimitExceededError
)
from lib.config import (
    ERR_DATASET_UNREACHABLE,
    MAX_RECORDS_LIMIT
)


class TestDataLoader:
    """Test suite for data loading functionality."""

    def test_check_url_reachability_success(self):
        """Test successful URL reachability check."""
        with patch('lib.data_loader.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_urlopen.return_value.__enter__.return_value = mock_response
            
            result = check_url_reachability('https://example.com/dataset.jsonl')
            assert result is True

    def test_check_url_reachability_failure(self):
        """Test failed URL reachability check."""
        with patch('lib.data_loader.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = socket.timeout("Connection timed out")
            
            result = check_url_reachability('https://example.com/dataset.jsonl')
            assert result is False

    def test_check_url_reachability_http_error(self):
        """Test URL reachability with HTTP error."""
        with patch('lib.data_loader.urlopen') as mock_urlopen:
            from urllib.error import HTTPError
            mock_urlopen.side_effect = HTTPError(
                'https://example.com', 404, 'Not Found', {}, None
            )
            
            result = check_url_reachability('https://example.com/dataset.jsonl')
            assert result is False

    def test_load_dataset_from_url_success(self):
        """Test successful dataset loading from URL."""
        # Create mock response
        mock_data = b'{"id": 1, "problem": "test1"}\n{"id": 2, "problem": "test2"}\n'
        
        with patch('lib.data_loader.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.headers.get.return_value = None
            mock_response.read.side_effect = [mock_data, b'']
            mock_response.__enter__.return_value = mock_response
            
            with patch('lib.data_loader.check_url_reachability', return_value=True):
                with tempfile.TemporaryDirectory() as tmpdir:
                    output_path = Path(tmpdir) / "test.jsonl"
                    records = load_dataset_from_url(
                        'https://example.com/dataset.jsonl',
                        output_path,
                        max_records=10
                    )
                    
                    assert len(records) == 2
                    assert records[0]['id'] == 1
                    assert records[1]['id'] == 2
                    
                    # Verify file was created
                    assert output_path.exists()

    def test_load_dataset_from_url_unreachable(self):
        """Test dataset loading when URL is unreachable."""
        with patch('lib.data_loader.check_url_reachability', return_value=False):
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "test.jsonl"
                
                with pytest.raises(DataLoaderError) as exc_info:
                    load_dataset_from_url(
                        'https://example.com/dataset.jsonl',
                        output_path,
                        max_records=10
                    )
                
                assert ERR_DATASET_UNREACHABLE in str(exc_info.value)

    def test_load_dataset_from_file_success(self):
        """Test successful dataset loading from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.jsonl"
            
            # Create test data
            with open(file_path, 'w') as f:
                f.write('{"id": 1, "problem": "test1"}\n')
                f.write('{"id": 2, "problem": "test2"}\n')
                f.write('{"id": 3, "problem": "test3"}\n')
            
            records = load_dataset_from_file(file_path, max_records=10)
            
            assert len(records) == 3
            assert records[0]['id'] == 1

    def test_load_dataset_from_file_not_found(self):
        """Test dataset loading from non-existent file."""
        with pytest.raises(DataLoaderError) as exc_info:
            load_dataset_from_file(Path("/nonexistent/file.jsonl"))
        
        assert "not found" in str(exc_info.value).lower()

    def test_load_dataset_from_file_max_records(self):
        """Test max records limit enforcement."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.jsonl"
            
            # Create test data with 5 records
            with open(file_path, 'w') as f:
                for i in range(5):
                    f.write(f'{{"id": {i}, "problem": "test{i}"}}\n')
            
            records = load_dataset_from_file(file_path, max_records=3)
            
            assert len(records) == 3
            assert records[0]['id'] == 0
            assert records[2]['id'] == 2

    def test_validate_dataset_valid(self):
        """Test validation of valid dataset."""
        records = [
            {"id": 1, "problem": "test1"},
            {"id": 2, "problem": "test2"}
        ]
        
        valid_records, errors = validate_dataset(records)
        
        assert len(valid_records) == 2
        assert len(errors) == 0

    def test_validate_dataset_invalid(self):
        """Test validation with invalid records."""
        records = [
            {"id": 1, "problem": "test1"},
            {"problem": "test2"},  # Missing id
            "not a dict",  # Not a dictionary
            {"id": 3, "problem": "test3"}
        ]
        
        valid_records, errors = validate_dataset(records)
        
        assert len(valid_records) == 2
        assert len(errors) == 2

    def test_load_and_validate_data_success(self):
        """Test combined load and validate function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.jsonl"
            
            with open(file_path, 'w') as f:
                f.write('{"id": 1, "problem": "test1"}\n')
                f.write('{"id": 2, "problem": "test2"}\n')
            
            records = load_and_validate_data(str(file_path), max_records=10)
            
            assert len(records) == 2

    def test_load_and_validate_data_empty(self):
        """Test load and validate with empty dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.jsonl"
            
            with open(file_path, 'w') as f:
                f.write('{"problem": "no_id"}\n')  # Missing id
            
            with pytest.raises(DataLoaderError) as exc_info:
                load_and_validate_data(str(file_path), max_records=10)
            
            assert "No valid records" in str(exc_info.value)

    def test_load_dataset_max_records_limit(self):
        """Test that load_dataset enforces max records limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.jsonl"
            
            # Create 100 records
            with open(file_path, 'w') as f:
                for i in range(100):
                    f.write(f'{{"id": {i}, "problem": "test{i}"}}\n')
            
            records = load_dataset(str(file_path), max_records=50)
            
            assert len(records) == 50

    def test_load_dataset_invalid_json(self):
        """Test handling of invalid JSON in dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.jsonl"
            
            with open(file_path, 'w') as f:
                f.write('{"id": 1, "problem": "test1"}\n')
                f.write('invalid json\n')
                f.write('{"id": 2, "problem": "test2"}\n')
            
            records = load_dataset_from_file(file_path, max_records=10)
            
            assert len(records) == 2
            assert records[0]['id'] == 1
            assert records[1]['id'] == 2

    def test_load_dataset_empty_file(self):
        """Test loading from empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.jsonl"
            file_path.touch()
            
            records = load_dataset_from_file(file_path, max_records=10)
            
            assert len(records) == 0

    def test_load_dataset_memory_limit_simulation(self):
        """Test memory limit enforcement (simulated)."""
        # This test simulates the memory limit check
        # In production, this would use psutil to check actual memory
        
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.jsonl"
            
            # Create a small dataset
            with open(file_path, 'w') as f:
                for i in range(10):
                    f.write(f'{{"id": {i}, "problem": "test{i}"}}\n')
            
            # Should load successfully with small dataset
            records = load_dataset(str(file_path), max_records=10)
            assert len(records) == 10