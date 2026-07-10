"""
Integration tests for data extraction module.

Tests repo cloning and filtering logic.
"""
import pytest
from pathlib import Path
import pandas as pd
import os
import shutil
from datetime import datetime, timedelta

from data_extraction import (
    filter_repos_by_age,
    extract_git_metrics,
    aggregate_file_metrics,
    run_data_extraction
)

@pytest.fixture
def sample_repos():
    """Sample repository data for testing."""
    now = datetime.now()
    old_date = (now - timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%SZ")
    new_date = (now - timedelta(days=100)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return [
        {
            "full_name": "test/old-repo",
            "name": "old-repo",
            "language": "Python",
            "stargazers_count": 1000,
            "created_at": old_date,
            "pushed_at": old_date,
            "html_url": "https://github.com/test/old-repo"
        },
        {
            "full_name": "test/new-repo",
            "name": "new-repo",
            "language": "Python",
            "stargazers_count": 600,
            "created_at": new_date,
            "pushed_at": new_date,
            "html_url": "https://github.com/test/new-repo"
        }
    ]

def test_filter_repos_by_age(sample_repos):
    """Test that repos older than 2 years are kept."""
    filtered = filter_repos_by_age(sample_repos, min_age_years=2)
    
    # Should only keep the old repo
    assert len(filtered) == 1
    assert filtered[0]["full_name"] == "test/old-repo"

def test_aggregate_file_metrics():
    """Test aggregation of file-level metrics."""
    raw_metrics = [
        {
            "repo_id": "test/repo",
            "file_path": "main.py",
            "commit_hash": "abc123",
            "commit_date": datetime.now(),
            "additions": 10,
            "deletions": 5,
            "lines_changed": 15
        },
        {
            "repo_id": "test/repo",
            "file_path": "main.py",
            "commit_hash": "def456",
            "commit_date": datetime.now(),
            "additions": 20,
            "deletions": 10,
            "lines_changed": 30
        },
        {
            "repo_id": "test/repo",
            "file_path": "utils.py",
            "commit_hash": "ghi789",
            "commit_date": datetime.now(),
            "additions": 5,
            "deletions": 2,
            "lines_changed": 7
        }
    ]
    
    aggregated = aggregate_file_metrics(raw_metrics)
    
    assert len(aggregated) == 2
    
    main_py = next((f for f in aggregated if f["file_path"] == "main.py"), None)
    assert main_py is not None
    assert main_py["total_lines_changed"] == 45
    assert main_py["total_additions"] == 30
    assert main_py["total_deletions"] == 15

def test_run_data_extraction_creates_files(tmp_path, monkeypatch):
    """Test that run_data_extraction creates the expected output files."""
    # Mock the GitHub query to return empty list to avoid API calls in tests
    def mock_query(*args, **kwargs):
        return []
    
    monkeypatch.setattr("data_extraction.query_github_repos", mock_query)
    
    # Change working directory to temp
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Create necessary directories
        Path("data/raw").mkdir(parents=True, exist_ok=True)
        Path("data/logs").mkdir(parents=True, exist_ok=True)
        
        result_path = run_data_extraction(max_repos=0)
        
        # Check that metadata file was created (even if empty)
        assert result_path.exists()
        
        # Check that validation log was created
        validation_log = Path("data/logs/tool_validation_log.csv")
        assert validation_log.exists()
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])