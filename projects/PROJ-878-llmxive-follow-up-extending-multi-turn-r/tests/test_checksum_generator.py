import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest
from utils.logging_utils import generate_checksum, write_checksum_file, validate_checksum

class TestChecksumUtils:
    """Unit tests for checksum generation and validation utilities."""

    def test_generate_checksum_sha256(self):
        """Test that checksum generation produces a valid SHA-256 hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.jsonl') as f:
            f.write('{"test": "data"}\n')
            temp_path = Path(f.name)
        
        try:
            checksum = generate_checksum(temp_path)
            # SHA-256 produces a 64-character hex string
            assert len(checksum) == 64
            assert all(c in '0123456789abcdef' for c in checksum)
        finally:
            os.unlink(temp_path)

    def test_write_and_validate_checksum(self):
        """Test writing checksum to file and validating it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "test.jsonl"
            checksum_file = tmpdir / "checksums.txt"
            
            # Create test file
            test_file.write_text('{"key": "value"}\n')
            
            # Generate and write checksum
            checksum = generate_checksum(test_file)
            write_checksum_file(checksum_file, test_file.name, checksum)
            
            # Validate checksum
            is_valid = validate_checksum(checksum_file, test_file.name)
            assert is_valid

    def test_checksum_changes_with_content(self):
        """Test that different file contents produce different checksums."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            file1 = tmpdir / "file1.jsonl"
            file2 = tmpdir / "file2.jsonl"
            
            file1.write_text('{"data": "A"}\n')
            file2.write_text('{"data": "B"}\n')
            
            checksum1 = generate_checksum(file1)
            checksum2 = generate_checksum(file2)
            
            assert checksum1 != checksum2

    def test_same_content_same_checksum(self):
        """Test that identical content produces the same checksum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            file1 = tmpdir / "file1.jsonl"
            file2 = tmpdir / "file2.jsonl"
            
            content = '{"consistent": "data"}\n'
            file1.write_text(content)
            file2.write_text(content)
            
            checksum1 = generate_checksum(file1)
            checksum2 = generate_checksum(file2)
            
            assert checksum1 == checksum2

    def test_validate_checksum_invalid(self):
        """Test validation fails when checksum doesn't match file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            test_file = tmpdir / "test.jsonl"
            checksum_file = tmpdir / "checksums.txt"
            
            test_file.write_text('{"original": "data"}\n')
            checksum = generate_checksum(test_file)
            write_checksum_file(checksum_file, test_file.name, checksum)
            
            # Modify file content
            test_file.write_text('{"modified": "data"}\n')
            
            # Validation should fail
            is_valid = validate_checksum(checksum_file, test_file.name)
            assert not is_valid

class TestChecksumGeneratorIntegration:
    """Integration tests for the checksum generation workflow."""

    def test_checksum_generation_workflow(self):
        """Test the complete checksum generation workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            data_dir = tmpdir / "data"
            raw_dir = data_dir / "raw"
            raw_dir.mkdir(parents=True)
            
            # Create a realistic JSONL file
            input_file = raw_dir / "logical_puzzles.jsonl"
            test_data = [
                {"instance_id": "1", "text": "Test puzzle 1", "ground_truth": "path1"},
                {"instance_id": "2", "text": "Test puzzle 2", "ground_truth": "path2"},
            ]
            with open(input_file, 'w') as f:
                for item in test_data:
                    f.write(json.dumps(item) + '\n')
            
            checksum_file = data_dir / "checksums.txt"
            
            # Generate checksum
            checksum = generate_checksum(input_file)
            write_checksum_file(checksum_file, input_file.name, checksum)
            
            # Verify file was created
            assert checksum_file.exists()
            
            # Verify content format
            content = checksum_file.read_text()
            assert input_file.name in content
            assert checksum in content
            
            # Verify validation passes
            assert validate_checksum(checksum_file, input_file.name)