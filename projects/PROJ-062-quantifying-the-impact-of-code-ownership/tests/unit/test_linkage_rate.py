"""
Unit tests for T038: Linkage Rate Calculation.
"""
import json
import os
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the function to test
from code.linkage_rate import calculate_linkage_rate, load_issues_for_repo

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        intermediate = tmp_path / "intermediate"
        results = tmp_path / "results"
        intermediate.mkdir()
        results.mkdir()
        yield {
            "base": tmp_path,
            "intermediate": intermediate,
            "results": results
        }

def test_load_issues_for_repo_empty(temp_dirs):
    """Test loading issues when file does not exist."""
    issues = load_issues_for_repo("nonexistent_repo", temp_dirs["intermediate"])
    assert issues == []

def test_load_issues_for_repo_success(temp_dirs):
    """Test loading issues from a valid CSV."""
    repo_name = "test-repo"
    issues_file = temp_dirs["intermediate"] / f"{repo_name}_issues.csv"
    
    # Create a mock CSV
    with open(issues_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['issue_id', 'title', 'linked_path'])
        writer.writerow(['1', 'Bug 1', 'src/main.py'])
        writer.writerow(['2', 'Bug 2', ''])  # Unlinked
        writer.writerow(['3', 'Bug 3', 'src/utils.py'])
    
    issues = load_issues_for_repo(repo_name, temp_dirs["intermediate"])
    assert len(issues) == 3
    assert issues[0]['linked_path'] == 'src/main.py'
    assert issues[1]['linked_path'] == ''

def test_calculate_linkage_rate(temp_dirs):
    """Test the main calculation logic."""
    # Setup mock data for two repos
    repos = ["repo-a", "repo-b"]
    
    # Repo A: 3 issues, 2 linked
    with open(temp_dirs["intermediate"] / "repo-a_issues.csv", 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['issue_id', 'linked_path'])
        w.writerow(['1', 'path1.py'])
        w.writerow(['2', 'path2.py'])
        w.writerow(['3', '']) # Unlinked

    # Repo B: 2 issues, 2 linked
    with open(temp_dirs["intermediate"] / "repo-b_issues.csv", 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['issue_id', 'linked_path'])
        w.writerow(['1', 'path3.py'])
        w.writerow(['2', 'path4.py'])

    result = calculate_linkage_rate(repos, temp_dirs["base"], temp_dirs["intermediate"])

    assert result["total_issues"] == 5
    assert result["linked_issues"] == 4
    assert abs(result["linkage_rate_percentage"] - 80.0) < 0.01

def test_calculate_linkage_rate_no_issues(temp_dirs):
    """Test calculation when no issues exist."""
    repos = ["empty-repo"]
    # No CSV created
    
    result = calculate_linkage_rate(repos, temp_dirs["base"], temp_dirs["intermediate"])
    
    assert result["total_issues"] == 0
    assert result["linked_issues"] == 0
    assert result["linkage_rate_percentage"] == 0.0

def test_calculate_linkage_rate_nan_handling(temp_dirs):
    """Test that 'nan' strings are treated as unlinked."""
    repos = ["repo-nan"]
    
    with open(temp_dirs["intermediate"] / "repo-nan_issues.csv", 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['issue_id', 'linked_path'])
        w.writerow(['1', 'nan'])
        w.writerow(['2', 'valid.py'])

    result = calculate_linkage_rate(repos, temp_dirs["base"], temp_dirs["intermediate"])
    
    # 2 total, 1 linked
    assert result["total_issues"] == 2
    assert result["linked_issues"] == 1
    assert abs(result["linkage_rate_percentage"] - 50.0) < 0.01