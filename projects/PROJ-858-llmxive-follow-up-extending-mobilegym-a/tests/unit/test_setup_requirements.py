import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_requirements import get_git_commit_hash, create_requirements_txt, write_checksums_file

class TestSetupRequirements:
    def test_create_requirements_txt(self, tmp_path):
        """Test that requirements.txt is created with correct content."""
        commit_hash = "abc123def456"
        req_path = create_requirements_txt(tmp_path, commit_hash)
        
        assert req_path.exists()
        content = req_path.read_text()
        assert f"mobilegym" in content.lower()
        assert commit_hash in content
        assert "git+" in content

    def test_write_checksums_file(self, tmp_path):
        """Test that .checksums.txt is created with correct content."""
        commit_hash = "abc123def456"
        checksum_path = write_checksums_file(tmp_path, commit_hash)
        
        assert checksum_path.exists()
        content = checksum_path.read_text()
        assert f"mobilegym_commit={commit_hash}" in content
        assert "data/raw" in str(checksum_path)

    def test_full_integration(self, tmp_path):
        """Test the full flow of creating requirements and checksums."""
        # Simulate a successful fetch (mocking would be ideal, but we test file creation logic)
        commit_hash = "test_commit_hash_12345"
        
        # Create requirements
        req_path = create_requirements_txt(tmp_path, commit_hash)
        assert req_path.exists()
        
        # Create checksums
        checksum_path = write_checksums_file(tmp_path, commit_hash)
        assert checksum_path.exists()
        
        # Verify consistency
        req_content = req_path.read_text()
        checksum_content = checksum_path.read_text()
        
        assert commit_hash in req_content
        assert commit_hash in checksum_content