import json
import os
import tempfile
import hashlib
from pathlib import Path
import pytest

from checksums import compute_sha256, record_checksums

class TestComputeSha256:
    def test_compute_sha256_valid_file(self, tmp_path):
        # Create a temporary file with known content
        test_content = b"Hello, World!"
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(test_content)
        
        # Compute hash
        computed_hash = compute_sha256(str(test_file))
        
        # Verify against known hash
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert computed_hash == expected_hash

    def test_compute_sha256_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/file.txt")

    def test_compute_sha256_large_file(self, tmp_path):
        # Create a larger file to test chunking
        test_content = b"x" * (10 * 1024 * 1024) # 10MB
        test_file = tmp_path / "large.txt"
        test_file.write_bytes(test_content)
        
        computed_hash = compute_sha256(str(test_file))
        expected_hash = hashlib.sha256(test_content).hexdigest()
        assert computed_hash == expected_hash

class TestRecordChecksums:
    def test_record_single_file(self, tmp_path):
        test_content = b"Test content for checksum"
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(test_content)
        
        output_file = tmp_path / "checksums.json"
        
        result = record_checksums([str(test_file)], str(output_file))
        
        assert len(result) == 1
        assert "test.txt" in result
        assert result["test.txt"]["sha256"] == hashlib.sha256(test_content).hexdigest()
        assert result["test.txt"]["filename"] == "test.txt"
        
        # Verify file was written
        assert output_file.exists()
        with open(output_file, "r") as f:
            saved_data = json.load(f)
        assert saved_data == result

    def test_record_multiple_files(self, tmp_path):
        files = []
        for i in range(3):
            content = f"Content {i}".encode()
            f = tmp_path / f"file{i}.txt"
            f.write_bytes(content)
            files.append(str(f))
            
        output_file = tmp_path / "checksums.json"
        result = record_checksums(files, str(output_file))
        
        assert len(result) == 3
        for i in range(3):
            fname = f"file{i}.txt"
            assert fname in result
            expected = hashlib.sha256(f"Content {i}".encode()).hexdigest()
            assert result[fname]["sha256"] == expected

    def test_record_missing_file_skipped(self, tmp_path):
        test_content = b"Valid content"
        test_file = tmp_path / "valid.txt"
        test_file.write_bytes(test_content)
        
        output_file = tmp_path / "checksums.json"
        
        # Should not raise, just log warning
        result = record_checksums([str(test_file), "/nonexistent.txt"], str(output_file))
        
        assert len(result) == 1
        assert "valid.txt" in result

    def test_record_overwrite(self, tmp_path):
        # Create initial file
        content1 = b"First content"
        f1 = tmp_path / "file1.txt"
        f1.write_bytes(content1)
        
        output_file = tmp_path / "checksums.json"
        record_checksums([str(f1)], str(output_file))
        
        # Create second file and overwrite
        content2 = b"Second content"
        f2 = tmp_path / "file2.txt"
        f2.write_bytes(content2)
        
        # Overwrite mode
        result = record_checksums([str(f2)], str(output_file), overwrite=True)
        
        assert len(result) == 1
        assert "file2.txt" in result
        assert "file1.txt" not in result

    def test_record_append(self, tmp_path):
        # Create initial file
        content1 = b"First content"
        f1 = tmp_path / "file1.txt"
        f1.write_bytes(content1)
        
        output_file = tmp_path / "checksums.json"
        record_checksums([str(f1)], str(output_file))
        
        # Create second file and append
        content2 = b"Second content"
        f2 = tmp_path / "file2.txt"
        f2.write_bytes(content2)
        
        # Append mode (default)
        result = record_checksums([str(f2)], str(output_file), overwrite=False)
        
        assert len(result) == 2
        assert "file1.txt" in result
        assert "file2.txt" in result