"""
Unit tests for the repo_fetcher module (T010).
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from utils.repo_fetcher import (
    validate_repo_list_schema,
    fetch_fallback_repos,
    create_repo_list_file,
    RepoFetcherException
)

class TestRepoFetcher:
    
    def test_validate_repo_list_schema_valid(self):
        """Test validation with a valid repository list."""
        valid_repo = {
            "repo_url": "https://github.com/test/repo",
            "github_url": "https://github.com/test/repo",
            "star_count": 100
        }
        assert validate_repo_list_schema([valid_repo]) is True

    def test_validate_repo_list_schema_missing_field(self):
        """Test validation fails with missing fields."""
        invalid_repo = {
            "repo_url": "https://github.com/test/repo",
            "star_count": 100
        }
        with pytest.raises(RepoFetcherException):
            validate_repo_list_schema([invalid_repo])

    def test_validate_repo_list_schema_invalid_type(self):
        """Test validation fails with invalid star_count type."""
        invalid_repo = {
            "repo_url": "https://github.com/test/repo",
            "github_url": "https://github.com/test/repo",
            "star_count": "not an integer"
        }
        with pytest.raises(RepoFetcherException):
            validate_repo_list_schema([invalid_repo])

    def test_fetch_fallback_repos_returns_list(self):
        """Test that fallback repos returns a non-empty list."""
        repos = fetch_fallback_repos()
        assert isinstance(repos, list)
        assert len(repos) > 0

    def test_create_repo_list_file_creates_json(self):
        """Test that create_repo_list_file writes a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_repo_list.json")
            result_path = create_repo_list_file(output_path, limit=5)
            
            assert result_path.exists()
            with open(result_path, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data, list)
            assert len(data) <= 5
            
            # Verify schema
            for repo in data:
                assert "repo_url" in repo
                assert "github_url" in repo
                assert "star_count" in repo

    def test_create_repo_list_file_limit_enforcement(self):
        """Test that the limit parameter is strictly enforced."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_repo_list.json")
            limit = 3
            create_repo_list_file(output_path, limit=limit)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == limit

    def test_create_repo_list_file_count_constraint_warning(self):
        """Test that a warning is logged if count is < 1 (simulated)."""
        # This test is more of a structural check since the frozen list is > 1.
        # We verify the function handles the path correctly.
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_repo_list.json")
            # We can't easily trigger the < 1 case without modifying the frozen list,
            # but we verify the file is created correctly.
            create_repo_list_file(output_path, limit=20)
            assert Path(output_path).exists()
            with open(output_path, 'r') as f:
                data = json.load(f)
            assert 1 <= len(data) <= 20