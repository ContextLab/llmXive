"""
Unit tests for checksum_utils module.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
# Adjust import path based on project structure if running from root
try:
    from code.checksum_utils import calculate_sha256, generate_checksums, validate_checksums
except ImportError:
    # Fallback for running tests from project root
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
    from checksum_utils import calculate_sha256, generate_checksums, validate_checksums


class TestCalculateSha256:
    def test_calculate_sha256_known_file(self):
        """Test calculation against a known file content."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            # "Hello, World!" SHA-256
            expected_hash = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            actual_hash = calculate_sha256(temp_path)
            assert actual_hash == expected_hash
        finally:
            os.unlink(temp_path)

    def test_calculate_sha256_empty_file(self):
        """Test calculation on an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            temp_path = f.name

        try:
            # Empty file SHA-256
            expected_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            actual_hash = calculate_sha256(temp_path)
            assert actual_hash == expected_hash
        finally:
            os.unlink(temp_path)

    def test_calculate_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            calculate_sha256("/nonexistent/path/file.txt")

class TestGenerateChecksums:
    def test_generate_checksums_single_file(self):
        """Test generating checksums for a single file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test content")
            temp_path = f.name

        try:
            checksums = generate_checksums([temp_path])
            assert temp_path in checksums
            assert len(checksums[temp_path]) == 64  # SHA-256 hex length
        finally:
            os.unlink(temp_path)

    def test_generate_checksums_multiple_files(self):
        """Test generating checksums for multiple files."""
        temp_paths = []
        try:
            for i in range(3):
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                    f.write(f"Content {i}")
                    temp_paths.append(f.name)

            checksums = generate_checksums(temp_paths)
            assert len(checksums) == 3
            for path in temp_paths:
                assert path in checksums
                assert len(checksums[path]) == 64
        finally:
            for path in temp_paths:
                os.unlink(path)

    def test_generate_checksums_with_output_file(self):
        """Test generating checksums and saving to a file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Save test")
            temp_path = f.name

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "checksums.json")
            try:
                checksums = generate_checksums([temp_path], output_path)
                
                # Verify file was created
                assert os.path.exists(output_path)
                
                # Verify content
                with open(output_path, 'r') as f:
                    saved_checksums = json.load(f)
                
                assert temp_path in saved_checksums
                assert saved_checksums[temp_path] == checksums[temp_path]
            finally:
                os.unlink(temp_path)

class TestValidateChecksums:
    def test_validate_checksums_success(self):
        """Test successful validation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Validate me")
            temp_path = f.name

        try:
            expected = {temp_path: calculate_sha256(temp_path)}
            valid, calculated, errors = validate_checksums([temp_path], expected_checksums=expected)
            
            assert valid[temp_path] is True
            assert temp_path in calculated
            assert temp_path not in errors
        finally:
            os.unlink(temp_path)

    def test_validate_checksums_failure(self):
        """Test validation failure with mismatched hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Wrong hash")
            temp_path = f.name

        try:
            # Provide a wrong hash
            expected = {temp_path: "a" * 64}
            valid, calculated, errors = validate_checksums([temp_path], expected_checksums=expected)
            
            assert valid[temp_path] is False
            assert temp_path in errors
            assert "Mismatch" in errors[temp_path]
        finally:
            os.unlink(temp_path)

    def test_validate_checksums_from_file(self):
        """Test validation using a checksum file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("From file")
            temp_path = f.name

        with tempfile.TemporaryDirectory() as tmpdir:
            checksum_file = os.path.join(tmpdir, "expected.json")
            try:
                # Create expected checksums file
                expected = {temp_path: calculate_sha256(temp_path)}
                with open(checksum_file, 'w') as f:
                    json.dump(expected, f)

                valid, calculated, errors = validate_checksums(
                    [temp_path], 
                    checksum_file=checksum_file
                )
                
                assert valid[temp_path] is True
            finally:
                os.unlink(temp_path)
                # checksum_file is cleaned up by TemporaryDirectory

    def test_validate_checksums_missing_file(self):
        """Test validation when expected checksum file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                validate_checksums(["/fake/file.txt"], checksum_file=os.path.join(tmpdir, "missing.json"))