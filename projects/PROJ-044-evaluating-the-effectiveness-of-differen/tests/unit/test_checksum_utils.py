"""
Unit tests for checksum_utils module.
"""

import os
import tempfile
from pathlib import Path

import pytest

from code.data.checksum_utils import (
    compute_sha256,
    generate_checksum_file,
    verify_checksum,
    batch_verify_checksums,
)


class TestComputeSha256:
    """Tests for compute_sha256 function."""

    def test_compute_sha256_simple(self):
        """Test SHA-256 computation on a simple file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Hello, World!")
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            # Known SHA-256 for "Hello, World!"
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_empty_file(self):
        """Test SHA-256 computation on an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            # Known SHA-256 for empty file
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_compute_sha256_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        with pytest.raises(FileNotFoundError):
            compute_sha256("/nonexistent/path/file.txt")

    def test_compute_sha256_directory(self):
        """Test that ValueError is raised for directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError):
                compute_sha256(tmpdir)

    def test_compute_sha256_binary_file(self):
        """Test SHA-256 computation on a binary file."""
        binary_data = bytes(range(256))
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(binary_data)
            temp_path = f.name

        try:
            checksum = compute_sha256(temp_path)
            assert isinstance(checksum, str)
            assert len(checksum) == 64  # SHA-256 hex string length
        finally:
            os.unlink(temp_path)

class TestGenerateChecksumFile:
    """Tests for generate_checksum_file function."""

    def test_generate_checksum_file_default_output(self):
        """Test checksum file generation with default output path."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            checksum_file = generate_checksum_file(temp_path)
            
            # Check that checksum file was created
            assert os.path.exists(checksum_file)
            assert checksum_file.endswith(".sha256")
            
            # Verify content format
            with open(checksum_file, "r") as f:
                line = f.readline().strip()
                parts = line.split()
                assert len(parts) == 2  # hash and filename
                assert len(parts[0]) == 64  # SHA-256 length
                assert parts[1] == Path(temp_path).name
        finally:
            os.unlink(temp_path)
            if os.path.exists(checksum_file):
                os.unlink(checksum_file)

    def test_generate_checksum_file_custom_output(self):
        """Test checksum file generation with custom output path."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".sha256") as cf:
                custom_path = cf.name
                os.unlink(custom_path)  # Remove so we can create it
            
            checksum_file = generate_checksum_file(temp_path, custom_path)
            
            assert checksum_file == custom_path
            assert os.path.exists(checksum_file)
        finally:
            os.unlink(temp_path)
            if os.path.exists(custom_path):
                os.unlink(custom_path)

    def test_generate_checksum_file_creates_directory(self):
        """Test that generate_checksum_file creates output directory if needed."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = os.path.join(tmpdir, "subdir", "checksum.sha256")
                checksum_file = generate_checksum_file(temp_path, output_path)
                
                assert os.path.exists(checksum_file)
        finally:
            os.unlink(temp_path)

class TestVerifyChecksum:
    """Tests for verify_checksum function."""

    def test_verify_checksum_success(self):
        """Test successful checksum verification."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            checksum_file = generate_checksum_file(temp_path)
            
            try:
                result = verify_checksum(temp_path, checksum_file)
                assert result is True
            finally:
                os.unlink(checksum_file)
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_failure(self):
        """Test checksum verification failure after file modification."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            checksum_file = generate_checksum_file(temp_path)
            
            try:
                # Modify the file
                with open(temp_path, "w") as f:
                    f.write("Modified content")
                
                result = verify_checksum(temp_path, checksum_file)
                assert result is False
            finally:
                os.unlink(checksum_file)
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_file_not_found(self):
        """Test that FileNotFoundError is raised for missing checksum file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            with pytest.raises(FileNotFoundError):
                verify_checksum(temp_path, "/nonexistent/checksum.sha256")
        finally:
            os.unlink(temp_path)

    def test_verify_checksum_default_path(self):
        """Test checksum verification using default checksum file path."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test content")
            temp_path = f.name

        try:
            # Generate checksum file at default location
            generate_checksum_file(temp_path)
            
            try:
                # Verify without specifying checksum file path
                result = verify_checksum(temp_path)
                assert result is True
            finally:
                # Clean up the generated checksum file
                checksum_file = temp_path + ".sha256"
                if os.path.exists(checksum_file):
                    os.unlink(checksum_file)
        finally:
            os.unlink(temp_path)

class TestBatchVerifyChecksums:
    """Tests for batch_verify_checksums function."""

    def test_batch_verify_all_success(self):
        """Test batch verification with all successful verifications."""
        file_paths = []
        
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                f.write(f"Content {i}")
                temp_path = f.name
                file_paths.append(temp_path)
                
                # Generate checksum file
                generate_checksum_file(temp_path)
        
        try:
            results = batch_verify_checksums(file_paths)
            
            assert len(results) == 3
            for path, result in results.items():
                assert result is True
        finally:
            for path in file_paths:
                os.unlink(path)
                checksum_file = path + ".sha256"
                if os.path.exists(checksum_file):
                    os.unlink(checksum_file)

    def test_batch_verify_mixed_results(self):
        """Test batch verification with mixed success/failure results."""
        file_paths = []
        
        # Create a file that will pass
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Good content")
            good_path = f.name
            file_paths.append(good_path)
            generate_checksum_file(good_path)
        
        # Create a file that will fail
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Bad content")
            bad_path = f.name
            file_paths.append(bad_path)
            generate_checksum_file(bad_path)
            
            # Modify the file to break checksum
            with open(bad_path, "w") as f2:
                f2.write("Modified bad content")
        
        try:
            results = batch_verify_checksums(file_paths)
            
            assert len(results) == 2
            assert results[good_path] is True
            assert results[bad_path] is False
        finally:
            for path in file_paths:
                os.unlink(path)
                checksum_file = path + ".sha256"
                if os.path.exists(checksum_file):
                    os.unlink(checksum_file)

    def test_batch_verify_with_missing_file(self):
        """Test batch verification with a missing file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Content")
            temp_path = f.name
            file_paths = [temp_path, "/nonexistent/file.txt"]
            generate_checksum_file(temp_path)
        
        try:
            results = batch_verify_checksums(file_paths)
            
            assert len(results) == 2
            assert results[temp_path] is True
            assert results["/nonexistent/file.txt"] is False
        finally:
            os.unlink(temp_path)
            checksum_file = temp_path + ".sha256"
            if os.path.exists(checksum_file):
                os.unlink(checksum_file)