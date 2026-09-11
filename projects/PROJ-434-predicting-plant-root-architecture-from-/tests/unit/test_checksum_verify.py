import os
import sys
import hashlib
import tempfile
from pathlib import Path
import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion.checksum_verify import compute_sha256, verify_checksum

class TestChecksumVerify:
    def test_compute_sha256_known_value(self):
        """Test SHA256 computation against a known string."""
        # "hello" -> 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
        test_content = b"hello"
        expected_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(test_content)
            tmp_path = Path(tmp.name)
        
        try:
            computed = compute_sha256(tmp_path)
            assert computed == expected_hash
        finally:
            os.unlink(tmp_path)

    def test_verify_checksum_success(self):
        """Test successful verification when hash matches."""
        content = b"test data for verification"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
            tmp_csv.write(content)
            csv_path = Path(tmp_csv.name)
        
        try:
            computed_hash = compute_sha256(csv_path)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".sha256") as tmp_sha:
                tmp_sha.write(f"{computed_hash}  {csv_path.name}\n".encode())
                sha_path = Path(tmp_sha.name)
            
            try:
                result = verify_checksum(csv_path, sha_path)
                assert result is True
            finally:
                os.unlink(sha_path)
        finally:
            os.unlink(csv_path)

    def test_verify_checksum_failure(self):
        """Test verification failure when hash does not match."""
        content = b"test data"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
            tmp_csv.write(content)
            csv_path = Path(tmp_csv.name)
        
        try:
            # Write a wrong hash
            wrong_hash = "0" * 64
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".sha256") as tmp_sha:
                tmp_sha.write(f"{wrong_hash}  {csv_path.name}\n".encode())
                sha_path = Path(tmp_sha.name)
            
            try:
                result = verify_checksum(csv_path, sha_path)
                assert result is False
            finally:
                os.unlink(sha_path)
        finally:
            os.unlink(csv_path)

    def test_verify_checksum_missing_csv(self):
        """Test that FileNotFoundError is raised if CSV is missing."""
        fake_path = Path("/nonexistent/file.csv")
        sha_path = Path("/tmp/fake.sha256")
        
        with pytest.raises(FileNotFoundError):
            verify_checksum(fake_path, sha_path)

    def test_verify_checksum_missing_sha(self):
        """Test that FileNotFoundError is raised if SHA file is missing."""
        csv_path = Path("/tmp/fake.csv")
        fake_path = Path("/nonexistent/file.sha256")
        
        with pytest.raises(FileNotFoundError):
            verify_checksum(csv_path, fake_path)