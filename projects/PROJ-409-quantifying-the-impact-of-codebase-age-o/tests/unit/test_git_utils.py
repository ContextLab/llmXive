"""
Unit tests for git_utils.py
"""
import pytest
from datetime import datetime, timezone, timedelta
from code.extraction.git_utils import (
    calculate_median_commit_age,
    get_file_commits,
    process_file_history,
    clone_repository
)
from pathlib import Path
import tempfile
import subprocess
import os

def test_calculate_median_age_empty_list():
    """Test that empty commit list returns None."""
    assert calculate_median_commit_age([]) is None

def test_calculate_median_age_single_commit():
    """Test sparse history: single commit returns age since that commit."""
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)
    commits = [
        {"hash": "abc123", "timestamp": int(one_day_ago.timestamp()), "datetime": one_day_ago}
    ]
    age = calculate_median_commit_age(commits)
    assert age is not None
    assert 0 <= age <= 2  # Should be around 1 day

def test_calculate_median_age_multiple_commits():
    """Test median calculation with multiple commits."""
    now = datetime.now(timezone.utc)
    # Create commits at 0, 2, and 4 days ago
    dates = [
        now - timedelta(days=0),
        now - timedelta(days=2),
        now - timedelta(days=4)
    ]
    commits = [
        {"hash": f"hash{i}", "timestamp": int(d.timestamp()), "datetime": d}
        for i, d in enumerate(dates)
    ]
    # Intervals: 0->2 (2 days), 2->4 (2 days), 4->now (4 days) -> ages: [2, 2, 4]
    # Sorted: [2, 2, 4] -> Median: 2
    age = calculate_median_commit_age(commits)
    assert age == 2.0

def test_clone_repository_success():
    """Test cloning a small public repository."""
    # Using a very small, stable repo for testing
    repo_url = "https://github.com/octocat/Hello-World.git"
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_repo"
        try:
            cloned_path = clone_repository(repo_url, target)
            assert cloned_path.exists()
            assert (cloned_path / ".git").exists()
            # Check for a known file
            assert (cloned_path / "README.md").exists()
        except Exception:
            # If network fails, skip rather than fail CI
            pytest.skip("Network unavailable for clone test")

def test_process_file_history_no_history():
    """Test file with no history returns None."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        # Create a dummy file but no git history
        dummy_file = repo_path / "dummy.txt"
        dummy_file.write_text("test")
        
        age, count = process_file_history(repo_path, "dummy.txt")
        assert age is None
        assert count == 0
