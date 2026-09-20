import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_checksums_and_dirs import (
    fetch_git_commit_hash,
    update_checksum_file,
    setup_processed_directory
)

class TestSetupChecksumsAndDirs:
    
    def test_update_checksum_file_creates_file(self, tmp_path):
        """Test that update_checksum_file creates the file with correct content."""
        checksum_file = tmp_path / ".checksums.txt"
        test_hash = "abc123def456"
        
        update_checksum_file(test_hash, str(checksum_file))
        
        assert checksum_file.exists()
        content = checksum_file.read_text()
        
        assert "mobilegym_commit_hash=" in content
        assert test_hash in content
        assert "Generated:" in content

    def test_update_checksum_file_overwrites(self, tmp_path):
        """Test that update_checksum_file overwrites existing content."""
        checksum_file = tmp_path / ".checksums.txt"
        checksum_file.write_text("old_content")
        
        test_hash = "new_hash_123"
        update_checksum_file(test_hash, str(checksum_file))
        
        content = checksum_file.read_text()
        assert "old_content" not in content
        assert test_hash in content

    def test_setup_processed_directory_creates_dir(self, tmp_path):
        """Test that setup_processed_directory creates the directory."""
        new_dir = tmp_path / "subdir" / "nested"
        
        setup_processed_directory(str(new_dir))
        
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_setup_processed_directory_uses_existing(self, tmp_path):
        """Test that setup_processed_directory doesn't fail on existing dir."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir(parents=True)
        
        # Should not raise
        setup_processed_directory(str(existing_dir))
        
        assert existing_dir.exists()

    def test_fetch_git_commit_hash_format(self):
        """Test that git commit hash is a valid hex string if available."""
        commit_hash = fetch_git_commit_hash()
        
        # If git is available, it should be a 40-char hex string
        # If not (e.g., in test env without git), it returns "unknown"
        if commit_hash != "unknown":
            assert len(commit_hash) == 40
            assert all(c in '0123456789abcdef' for c in commit_hash)
        else:
            # If git is not available, it should return "unknown"
            assert commit_hash == "unknown"
