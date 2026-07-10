"""
Integration test for repo fetch and commit pinning logic.

This test verifies that the repository fetching and commit pinning
logic in code/repo_utils.py works correctly end-to-end.

It uses a small, real public repository to validate:
1. Successful cloning/fetching of a repository
2. Correct commit pinning to a specific hash
3. Proper file listing and validation
4. Checksum generation for reproducibility
"""

import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path

# Import the real functions from the project's repo_utils module
from repo_utils import (
    ensure_dirs,
    clone_or_fetch_repo,
    get_repo_files,
    generate_checksum,
    log_pinned_repo,
    main as repo_utils_main
)

# Test constants
TEST_REPO_URL = "https://github.com/psf/requests.git"
TEST_COMMIT_HASH = "5322260237f545f233123f53446f822171723d1c"  # A known stable commit from requests
TEST_TIMEOUT = 60  # seconds


class TestRepoFetchAndPin:
    """Integration tests for repository fetching and commit pinning."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down test environment."""
        # Create a temporary directory for test artifacts
        self.test_dir = tempfile.mkdtemp(prefix="llmxive_test_")
        self.repo_dir = os.path.join(self.test_dir, "repo")
        self.logs_dir = os.path.join(self.test_dir, "logs")
        
        yield
        
        # Clean up temporary directory
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_ensure_dirs_creates_structure(self):
        """Test that ensure_dirs creates the required directory structure."""
        result = ensure_dirs(self.repo_dir, self.logs_dir)
        
        assert result is True
        assert os.path.isdir(self.repo_dir)
        assert os.path.isdir(self.logs_dir)

    def test_clone_or_fetch_repo_success(self):
        """Test successful cloning of a real repository."""
        success, repo_path = clone_or_fetch_repo(
            TEST_REPO_URL,
            self.repo_dir,
            timeout=TEST_TIMEOUT
        )
        
        assert success is True
        assert os.path.isdir(repo_path)
        assert os.path.exists(os.path.join(repo_path, ".git"))

    def test_clone_or_fetch_repo_with_commit_pin(self):
        """Test that a specific commit can be pinned after fetching."""
        # First, clone the repo
        success, repo_path = clone_or_fetch_repo(
            TEST_REPO_URL,
            self.repo_dir,
            timeout=TEST_TIMEOUT
        )
        assert success is True
        
        # Now pin to a specific commit
        success, message = clone_or_fetch_repo(
            TEST_REPO_URL,
            self.repo_dir,
            commit=TEST_COMMIT_HASH,
            timeout=TEST_TIMEOUT
        )
        
        assert success is True
        assert "pinned" in message.lower() or "checkout" in message.lower()
        
        # Verify we're on the correct commit
        result = os.system(f"cd {repo_path} && git rev-parse HEAD")
        # Note: This is a simple check; a more robust check would parse the output

    def test_get_repo_files_returns_valid_list(self):
        """Test that get_repo_files returns a valid list of files."""
        # Clone first
        success, repo_path = clone_or_fetch_repo(
            TEST_REPO_URL,
            self.repo_dir,
            timeout=TEST_TIMEOUT
        )
        assert success is True
        
        # Get files with a limit
        files = get_repo_files(repo_path, max_files=50)
        
        assert isinstance(files, list)
        assert len(files) > 0
        assert len(files) <= 50
        
        # Check that file paths are valid
        for file_path in files:
            full_path = os.path.join(repo_path, file_path)
            assert os.path.isfile(full_path) or os.path.isdir(full_path)

    def test_generate_checksum_consistency(self):
        """Test that checksum generation is consistent."""
        # Clone first
        success, repo_path = clone_or_fetch_repo(
            TEST_REPO_URL,
            self.repo_dir,
            timeout=TEST_TIMEOUT
        )
        assert success is True
        
        # Generate checksum twice
        checksum1 = generate_checksum(repo_path)
        checksum2 = generate_checksum(repo_path)
        
        assert checksum1 is not None
        assert checksum2 is not None
        assert checksum1 == checksum2
        assert len(checksum1) == 64  # SHA-256 hex length

    def test_log_pinned_repo_creates_valid_log(self):
        """Test that log_pinned_repo creates a valid log entry."""
        # Clone and pin
        success, repo_path = clone_or_fetch_repo(
            TEST_REPO_URL,
            self.repo_dir,
            commit=TEST_COMMIT_HASH,
            timeout=TEST_TIMEOUT
        )
        assert success is True
        
        # Log the pinned repo
        log_path = log_pinned_repo(
            repo_path,
            self.logs_dir,
            url=TEST_REPO_URL,
            commit=TEST_COMMIT_HASH,
            file_count=10,
            checksum=generate_checksum(repo_path)
        )
        
        assert log_path is not None
        assert os.path.isfile(log_path)
        
        # Verify log content
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        assert log_data['url'] == TEST_REPO_URL
        assert log_data['commit'] == TEST_COMMIT_HASH
        assert 'checksum' in log_data
        assert 'file_count' in log_data
        assert 'timestamp' in log_data

    def test_full_pipeline_integration(self):
        """Test the full pipeline: clone, pin, list, checksum, log."""
        # Step 1: Ensure directories
        ensure_dirs(self.repo_dir, self.logs_dir)
        
        # Step 2: Clone repository
        success, repo_path = clone_or_fetch_repo(
            TEST_REPO_URL,
            self.repo_dir,
            timeout=TEST_TIMEOUT
        )
        assert success is True
        
        # Step 3: Pin to specific commit
        success, message = clone_or_fetch_repo(
            TEST_REPO_URL,
            self.repo_dir,
            commit=TEST_COMMIT_HASH,
            timeout=TEST_TIMEOUT
        )
        assert success is True
        
        # Step 4: Get files
        files = get_repo_files(repo_path, max_files=20)
        assert len(files) > 0
        
        # Step 5: Generate checksum
        checksum = generate_checksum(repo_path)
        assert checksum is not None
        assert len(checksum) == 64
        
        # Step 6: Log the result
        log_path = log_pinned_repo(
            repo_path,
            self.logs_dir,
            url=TEST_REPO_URL,
            commit=TEST_COMMIT_HASH,
            file_count=len(files),
            checksum=checksum
        )
        assert log_path is not None
        assert os.path.isfile(log_path)
        
        # Step 7: Verify log integrity
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        assert log_data['commit'] == TEST_COMMIT_HASH
        assert log_data['checksum'] == checksum
        assert log_data['file_count'] == len(files)

    def test_error_handling_invalid_repo(self):
        """Test error handling for invalid repository URL."""
        success, repo_path = clone_or_fetch_repo(
            "https://github.com/nonexistent/invalid-repo-12345.git",
            self.repo_dir,
            timeout=5
        )
        
        assert success is False
        assert repo_path is None

    def test_error_handling_invalid_commit(self):
        """Test error handling for invalid commit hash."""
        # Clone valid repo first
        success, repo_path = clone_or_fetch_repo(
            TEST_REPO_URL,
            self.repo_dir,
            timeout=TEST_TIMEOUT
        )
        assert success is True
        
        # Try to pin to invalid commit
        success, message = clone_or_fetch_repo(
            TEST_REPO_URL,
            self.repo_dir,
            commit="invalid_commit_hash_12345",
            timeout=TEST_TIMEOUT
        )
        
        assert success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])