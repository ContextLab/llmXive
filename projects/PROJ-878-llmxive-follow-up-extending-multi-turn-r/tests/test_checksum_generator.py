"""
Tests for checksum generation functionality.

These tests verify that:
1. The checksum generator correctly processes the input file
2. The checksum file is created with the correct format
3. The checksum can be validated against the original file
"""
import os
import sys
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_utils import generate_checksum, write_checksum_file, validate_checksum


class TestChecksumGeneration:
    """Test cases for checksum generation."""

    def test_generate_checksum_valid_file(self, tmp_path):
        """Test that a valid file generates a correct checksum."""
        # Create a temporary file with known content
        test_file = tmp_path / "test.jsonl"
        content = '{"instance_id": "test_001", "text": "test puzzle"}\n'
        test_file.write_text(content)
        
        # Generate checksum
        checksum = generate_checksum(test_file)
        
        # Verify checksum is not None and is a string
        assert checksum is not None
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex length
        
        # Verify checksum matches expected value
        expected_checksum = hashlib.sha256(content.encode()).hexdigest()
        assert checksum == expected_checksum

    def test_generate_checksum_nonexistent_file(self, tmp_path):
        """Test that a nonexistent file returns None."""
        nonexistent_file = tmp_path / "nonexistent.jsonl"
        checksum = generate_checksum(nonexistent_file)
        assert checksum is None

    def test_write_and_validate_checksum(self, tmp_path):
        """Test writing and validating a checksum file."""
        # Create a test file
        test_file = tmp_path / "test.jsonl"
        content = '{"instance_id": "test_001", "text": "test puzzle"}\n'
        test_file.write_text(content)
        
        # Generate checksum
        checksum = generate_checksum(test_file)
        
        # Write checksum file
        checksums_file = tmp_path / "checksums.txt"
        write_checksum_file(checksums_file, "test.jsonl", checksum)
        
        # Verify checksum file exists
        assert checksums_file.exists()
        
        # Validate checksum
        is_valid = validate_checksum(checksums_file, "test.jsonl")
        assert is_valid is True

    def test_validate_checksum_invalid(self, tmp_path):
        """Test validation with incorrect checksum."""
        # Create a test file
        test_file = tmp_path / "test.jsonl"
        content = '{"instance_id": "test_001", "text": "test puzzle"}\n'
        test_file.write_text(content)
        
        # Generate checksum
        checksum = generate_checksum(test_file)
        
        # Write checksum file with wrong filename
        checksums_file = tmp_path / "checksums.txt"
        write_checksum_file(checksums_file, "wrong_name.jsonl", checksum)
        
        # Validate should return False
        is_valid = validate_checksum(checksums_file, "test.jsonl")
        assert is_valid is False

    def test_checksum_consistency(self, tmp_path):
        """Test that checksum is consistent across multiple runs."""
        # Create a test file
        test_file = tmp_path / "test.jsonl"
        content = '{"instance_id": "test_001", "text": "test puzzle"}\n'
        test_file.write_text(content)
        
        # Generate checksum multiple times
        checksum1 = generate_checksum(test_file)
        checksum2 = generate_checksum(test_file)
        checksum3 = generate_checksum(test_file)
        
        # All should be identical
        assert checksum1 == checksum2 == checksum3

    def test_checksum_multiline_file(self, tmp_path):
        """Test checksum generation for multi-line JSONL file."""
        # Create a multi-line test file
        test_file = tmp_path / "test.jsonl"
        content = (
            '{"instance_id": "test_001", "text": "puzzle 1"}\n'
            '{"instance_id": "test_002", "text": "puzzle 2"}\n'
            '{"instance_id": "test_003", "text": "puzzle 3"}\n'
        )
        test_file.write_text(content)
        
        # Generate checksum
        checksum = generate_checksum(test_file)
        
        # Verify checksum is valid
        assert checksum is not None
        assert len(checksum) == 64
        
        # Verify it matches expected
        expected_checksum = hashlib.sha256(content.encode()).hexdigest()
        assert checksum == expected_checksum
