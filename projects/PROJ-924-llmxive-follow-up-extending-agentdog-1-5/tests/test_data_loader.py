"""
Tests for data_loader module.
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from datasets import Dataset

# Import the module under test
from code.data_loader import (
    LoudFailureError,
    verify_checksum,
    validate_data_integrity,
    load_jsonl_file,
    save_jsonl_file,
    fetch_advbench,
    fetch_hf4,
    fetch_taxonomy
)
from code.config import get_path


class TestChecksumVerification:
    """Tests for checksum verification functions."""

    def test_verify_checksum_valid(self, tmp_path):
        """Test that valid checksums are verified correctly."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Calculate actual checksum
        import hashlib
        expected = hashlib.sha256(b"Hello, World!").hexdigest()
        
        result = verify_checksum(str(test_file), expected)
        assert result is True

    def test_verify_checksum_invalid(self, tmp_path):
        """Test that invalid checksums are detected."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        
        result = verify_checksum(str(test_file), "invalid_checksum")
        assert result is False

    def test_verify_checksum_file_not_found(self):
        """Test that missing files return False."""
        result = verify_checksum("/nonexistent/file.txt", "any_checksum")
        assert result is False

    def test_validate_data_integrity_success(self, tmp_path):
        """Test successful data integrity validation."""
        # Create test file and checksums
        test_file = tmp_path / "data.jsonl"
        test_file.write_text('{"text": "test"}\n')
        
        checksums_file = tmp_path / "checksums.json"
        import hashlib
        checksum = hashlib.sha256(b'{"text": "test"}\n').hexdigest()
        checksums_file.write_text(json.dumps({
            "data.jsonl": checksum
        }))
        
        result = validate_data_integrity(str(test_file), str(checksums_file))
        assert result is True

    def test_validate_data_integrity_missing_checksum(self, tmp_path):
        """Test validation fails when checksum is missing."""
        test_file = tmp_path / "data.jsonl"
        test_file.write_text('{"text": "test"}\n')
        
        checksums_file = tmp_path / "checksums.json"
        checksums_file.write_text(json.dumps({
            "other_file.jsonl": "some_checksum"
        }))
        
        with pytest.raises(LoudFailureError):
            validate_data_integrity(str(test_file), str(checksums_file))

    def test_validate_data_integrity_no_checksums_file(self, tmp_path):
        """Test validation fails when checksums file doesn't exist."""
        test_file = tmp_path / "data.jsonl"
        
        with pytest.raises(LoudFailureError):
            validate_data_integrity(str(test_file), "/nonexistent/checksums.json")


class TestJSONLFileOperations:
    """Tests for JSONL file loading and saving."""

    def test_load_jsonl_file(self, tmp_path):
        """Test loading a JSONL file."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"text": "hello"}\n{"text": "world"}\n')
        
        data = load_jsonl_file(str(jsonl_file))
        assert len(data) == 2
        assert data[0]["text"] == "hello"
        assert data[1]["text"] == "world"

    def test_load_jsonl_file_empty_lines(self, tmp_path):
        """Test loading JSONL with empty lines."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"text": "hello"}\n\n{"text": "world"}\n')
        
        data = load_jsonl_file(str(jsonl_file))
        assert len(data) == 2

    def test_load_jsonl_file_invalid_json(self, tmp_path):
        """Test that invalid JSON raises LoudFailureError."""
        jsonl_file = tmp_path / "test.jsonl"
        jsonl_file.write_text('{"text": "hello"}\n{invalid json}\n')
        
        with pytest.raises(LoudFailureError):
            load_jsonl_file(str(jsonl_file))

    def test_save_jsonl_file(self, tmp_path):
        """Test saving a JSONL file."""
        data = [{"text": "hello"}, {"text": "world"}]
        output_file = tmp_path / "output.jsonl"
        
        save_jsonl_file(data, str(output_file))
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "hello" in content
        assert "world" in content


class TestDataFetching:
    """Tests for data fetching functions."""

    @patch('code.data_loader.load_dataset')
    def test_fetch_advbench_success(self, mock_load_dataset):
        """Test successful AdvBench fetch."""
        # Mock the dataset iterator
        mock_dataset = iter([
            {"prompt": "attack1", "label": "attack"},
            {"prompt": "attack2", "label": "attack"}
        ])
        mock_load_dataset.return_value = mock_dataset
        
        results = list(fetch_advbench())
        
        assert len(results) == 2
        assert results[0]["text"] == "attack1"
        assert results[0]["label"] == "attack"
        assert results[0]["source"] == "advbench"

    @patch('code.data_loader.load_dataset')
    def test_fetch_advbench_fallback_label(self, mock_load_dataset):
        """Test that missing label defaults to 'attack'."""
        mock_dataset = iter([
            {"prompt": "attack1"}  # No label field
        ])
        mock_load_dataset.return_value = mock_dataset
        
        results = list(fetch_advbench())
        assert results[0]["label"] == "attack"

    @patch('code.data_loader.load_dataset')
    def test_fetch_advbench_fetch_failure(self, mock_load_dataset):
        """Test that fetch failure raises LoudFailureError."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        with pytest.raises(LoudFailureError) as exc_info:
            list(fetch_advbench())
        
        assert "Failed to fetch AdvBench" in str(exc_info.value)

    @patch('code.data_loader.load_dataset')
    def test_fetch_hf4_success(self, mock_load_dataset):
        """Test successful HF4 fetch."""
        mock_dataset = iter([
            {"text": "benign1", "label": "safe"},
            {"text": "benign2", "label": "safe"}
        ])
        mock_load_dataset.return_value = mock_dataset
        
        results = list(fetch_hf4())
        
        assert len(results) == 2
        assert results[0]["text"] == "benign1"
        assert results[0]["label"] == "safe"
        assert results[0]["source"] == "hf4"

    @patch('code.data_loader.load_dataset')
    def test_fetch_hf4_fallback_label(self, mock_load_dataset):
        """Test that missing label defaults to 'safe'."""
        mock_dataset = iter([
            {"text": "benign1"}  # No label field
        ])
        mock_load_dataset.return_value = mock_dataset
        
        results = list(fetch_hf4())
        assert results[0]["label"] == "safe"

    @patch('code.data_loader.load_dataset')
    def test_fetch_hf4_fetch_failure(self, mock_load_dataset):
        """Test that fetch failure raises LoudFailureError."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        with pytest.raises(LoudFailureError) as exc_info:
            list(fetch_hf4())
        
        assert "Failed to fetch HF4" in str(exc_info.value)

    @patch('code.data_loader.load_dataset')
    def test_fetch_taxonomy_success(self, mock_load_dataset):
        """Test successful taxonomy fetch."""
        mock_dataset = iter([
            {"category": "safe", "description": "Safe content"},
            {"category": "attack", "description": "Attack content"}
        ])
        mock_load_dataset.return_value = mock_dataset
        
        result = fetch_taxonomy()
        
        assert "categories" in result
        assert len(result["categories"]) == 2
        assert result["source"] == "AgentDoG/safety-taxonomy-v1.5"

    @patch('code.data_loader.load_dataset')
    def test_fetch_taxonomy_empty(self, mock_load_dataset):
        """Test that empty taxonomy raises LoudFailureError."""
        mock_dataset = iter([])
        mock_load_dataset.return_value = mock_dataset
        
        with pytest.raises(LoudFailureError) as exc_info:
            fetch_taxonomy()
        
        assert "Taxonomy dataset is empty" in str(exc_info.value)

    @patch('code.data_loader.load_dataset')
    def test_fetch_taxonomy_fetch_failure(self, mock_load_dataset):
        """Test that fetch failure raises LoudFailureError."""
        mock_load_dataset.side_effect = Exception("Network error")
        
        with pytest.raises(LoudFailureError) as exc_info:
            fetch_taxonomy()
        
        assert "Failed to fetch taxonomy" in str(exc_info.value)


class TestStreamingBehavior:
    """Tests to verify streaming behavior (no full load into memory)."""

    @patch('code.data_loader.load_dataset')
    def test_fetch_advbench_returns_generator(self, mock_load_dataset):
        """Test that fetch_advbench returns a generator."""
        mock_dataset = iter([{"prompt": "test"}])
        mock_load_dataset.return_value = mock_dataset
        
        result = fetch_advbench()
        
        # Should be a generator, not a list
        assert hasattr(result, '__iter__')
        assert hasattr(result, '__next__')

    @patch('code.data_loader.load_dataset')
    def test_fetch_hf4_returns_generator(self, mock_load_dataset):
        """Test that fetch_hf4 returns a generator."""
        mock_dataset = iter([{"text": "test"}])
        mock_load_dataset.return_value = mock_dataset
        
        result = fetch_hf4()
        
        # Should be a generator, not a list
        assert hasattr(result, '__iter__')
        assert hasattr(result, '__next__')
