import os
import tempfile
import pytest
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

from downloaders import calculate_sha256, generate_checksum_file, verify_checksum

class TestChecksumFunctions:
    def test_calculate_sha256(self):
        """Test SHA-256 calculation on a known file."""
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            temp_path = f.name
        
        try:
            checksum = calculate_sha256(temp_path)
            expected = hashlib.sha256(b"test data").hexdigest()
            assert checksum == expected
        finally:
            os.unlink(temp_path)

    def test_generate_checksum_file(self):
        """Test checksum file generation."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"test data")
            temp_path = f.name
        
        checksum_path = temp_path + ".sha256"
        
        try:
            generate_checksum_file(temp_path, checksum_path)
            
            assert os.path.exists(checksum_path)
            
            with open(checksum_path, 'r') as f:
                content = f.read().strip()
            
            expected_checksum = hashlib.sha256(b"test data").hexdigest()
            assert expected_checksum in content
        finally:
            os.unlink(temp_path)
            if os.path.exists(checksum_path):
                os.unlink(checksum_path)

    def test_verify_checksum_valid(self):
        """Test checksum verification with valid checksum."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"test data")
            temp_path = f.name
        
        checksum_path = temp_path + ".sha256"
        
        try:
            generate_checksum_file(temp_path, checksum_path)
            assert verify_checksum(temp_path, checksum_path) is True
        finally:
            os.unlink(temp_path)
            if os.path.exists(checksum_path):
                os.unlink(checksum_path)

    def test_verify_checksum_invalid(self):
        """Test checksum verification with invalid checksum."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"test data")
            temp_path = f.name
        
        checksum_path = temp_path + ".sha256"
        
        try:
            # Generate valid checksum
            generate_checksum_file(temp_path, checksum_path)
            
            # Corrupt the file
            with open(temp_path, 'wb') as f:
                f.write(b"corrupted data")
            
            assert verify_checksum(temp_path, checksum_path) is False
        finally:
            os.unlink(temp_path)
            if os.path.exists(checksum_path):
                os.unlink(checksum_path)

    def test_verify_checksum_missing_file(self):
        """Test checksum verification with missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = os.path.join(tmpdir, "missing.txt")
            checksum_path = os.path.join(tmpdir, "missing.txt.sha256")
            
            assert verify_checksum(missing_path, checksum_path) is False
