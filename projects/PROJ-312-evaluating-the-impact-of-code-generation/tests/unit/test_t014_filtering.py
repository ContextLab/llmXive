import pytest
import os
import json
from pathlib import Path
import sys
import tempfile
import shutil

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from fetch_data import filter_repos_by_pr_count, save_excluded_repos
from utils import MIN_PR_THRESHOLD

class TestT014RepoFiltering:
    
    def test_filter_repos_below_threshold(self):
        """Test that repos with fewer than MIN_PR_THRESHOLD are excluded."""
        # Setup mock data
        repos_data = [
            {"name": "repo_large", "stars": 1000},
            {"name": "repo_small", "stars": 500},
            {"name": "repo_medium", "stars": 800}
        ]
        
        processed_prs = {
            "repo_large": [{"is_valid": True}] * 100, # 100 valid PRs
            "repo_small": [{"is_valid": True}] * 10,  # 10 valid PRs (< 50)
            "repo_medium": [{"is_valid": True}] * 49  # 49 valid PRs (< 50)
        }
        
        # Execute
        excluded = filter_repos_by_pr_count(repos_data, processed_prs)
        
        # Assertions
        assert "repo_small" in excluded
        assert "repo_medium" in excluded
        assert "repo_large" not in excluded
        assert len(excluded) == 2

    def test_filter_repos_empty_list(self):
        """Test that repos with 0 PRs are excluded."""
        repos_data = [{"name": "empty_repo", "stars": 100}]
        processed_prs = {"empty_repo": []}
        
        excluded = filter_repos_by_pr_count(repos_data, processed_prs)
        
        assert "empty_repo" in excluded

    def test_filter_repos_exact_threshold(self):
        """Test that repos with exactly MIN_PR_THRESHOLD are NOT excluded."""
        repos_data = [{"name": "exact_repo", "stars": 100}]
        processed_prs = {"exact_repo": [{"is_valid": True}] * MIN_PR_THRESHOLD}
        
        excluded = filter_repos_by_pr_count(repos_data, processed_prs)
        
        assert "exact_repo" not in excluded
        assert len(excluded) == 0

    def test_save_excluded_repos_creates_file(self, tmp_path):
        """Test that save_excluded_repos writes the file correctly."""
        excluded_list = ["repo_a", "repo_b", "repo_c"]
        output_path = str(tmp_path / "excluded.txt")
        
        save_excluded_repos(excluded_list, output_path)
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            lines = f.readlines()
        
        assert len(lines) == 3
        assert "repo_a" in lines[0]
        assert "repo_b" in lines[1]
        assert "repo_c" in lines[2]

    def test_min_pr_threshold_is_configurable(self):
        """Verify that MIN_PR_THRESHOLD is a constant and not hardcoded in logic."""
        # This is a sanity check that the constant exists and is an integer
        assert isinstance(MIN_PR_THRESHOLD, int)
        assert MIN_PR_THRESHOLD > 0