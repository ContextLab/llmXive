import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging
import tempfile

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils import MIN_PR_THRESHOLD, save_excluded_repos
from fetch_data import process_pr_data, fetch_prs_and_commits_for_repos

class TestT014ExcludedRepos:
    """Tests for T014: Skipping repos with fewer than MIN_PR_THRESHOLD PRs."""

    def test_min_pr_threshold_constant(self):
        """Verify MIN_PR_THRESHOLD is defined and set to 50."""
        assert MIN_PR_THRESHOLD == 50

    def test_process_pr_data_filters_merged_at(self):
        """Test that PRs without merged_at are excluded."""
        pr = {
            'number': 123,
            'created_at': '2023-01-01T00:00:00Z',
            'merged_at': None,
            'labels': []
        }
        result = process_pr_data('test/repo', pr)
        assert result is None

    def test_save_excluded_repos_creates_file(self):
        """Test that save_excluded_repos writes the file correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'excluded_repos.txt')
            excluded = ['repo1', 'repo2', 'repo3']
            
            save_excluded_repos(excluded, output_path)
            
            assert os.path.exists(output_path)
            with open(output_path, 'r') as f:
                content = f.read()
            
            assert 'repo1' in content
            assert 'repo2' in content
            assert 'repo3' in content

    @patch('fetch_data.fetch_prs_for_repo')
    @patch('fetch_data.fetch_commits_for_pr')
    def test_fetch_prs_excludes_small_repos(self, mock_fetch_commits, mock_fetch_prs):
        """Test that repos with fewer than MIN_PR_THRESHOLD PRs are excluded."""
        # Mock a repo with only 10 PRs (below threshold of 50)
        small_prs = [{'number': i, 'created_at': '2023-01-01', 'merged_at': '2023-01-02', 'labels': []} for i in range(10)]
        mock_fetch_prs.return_value = (small_prs, None)
        mock_fetch_commits.return_value = []
        
        logger = logging.getLogger(__name__)
        repos = [{'name': 'small/repo', 'stars': 1000}]
        
        _, _, excluded_repos = fetch_prs_and_commits_for_repos(repos, logger, max_pages=1)
        
        assert 'small/repo' in excluded_repos

    @patch('fetch_data.fetch_prs_for_repo')
    @patch('fetch_data.fetch_commits_for_pr')
    def test_fetch_prs_includes_large_repos(self, mock_fetch_commits, mock_fetch_prs):
        """Test that repos with >= MIN_PR_THRESHOLD PRs are included."""
        # Mock a repo with 60 PRs (above threshold of 50)
        large_prs = [{'number': i, 'created_at': '2023-01-01', 'merged_at': '2023-01-02', 'labels': []} for i in range(60)]
        mock_fetch_prs.return_value = (large_prs, None)
        mock_fetch_commits.return_value = []
        
        logger = logging.getLogger(__name__)
        repos = [{'name': 'large/repo', 'stars': 1000}]
        
        pr_data, _, excluded_repos = fetch_prs_and_commits_for_repos(repos, logger, max_pages=1)
        
        assert len(pr_data) == 60
        assert 'large/repo' not in excluded_repos