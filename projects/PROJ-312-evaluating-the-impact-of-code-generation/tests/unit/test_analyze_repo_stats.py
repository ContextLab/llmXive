import pytest
import json
import os
import sys
from pathlib import Path
from statistics import median

# Add the code directory to the path
code_dir = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from analyze_repo_stats import load_repos, calculate_medians

@pytest.fixture
def sample_repos():
    return [
        {"name": "repo1", "stars": 1000, "contributors": 10},
        {"name": "repo2", "stars": 2000, "contributors": 20},
        {"name": "repo3", "stars": 3000, "contributors": 30},
        {"name": "repo4", "stars": 4000, "contributors": 40},
        {"name": "repo5", "stars": 5000, "contributors": 50}
    ]

@pytest.fixture
def sample_repos_missing_contributors():
    return [
        {"name": "repo1", "stars": 1000},
        {"name": "repo2", "stars": 2000},
        {"name": "repo3", "stars": 3000}
    ]

@pytest.fixture
def sample_repos_partial_contributors():
    return [
        {"name": "repo1", "stars": 1000, "contributors": 10},
        {"name": "repo2", "stars": 2000},
        {"name": "repo3", "stars": 3000, "contributors": 30}
    ]

def test_load_repos_success(tmp_path, sample_repos):
    repos_file = tmp_path / "repos.json"
    with open(repos_file, 'w') as f:
        json.dump(sample_repos, f)
    
    result = load_repos(str(repos_file))
    assert len(result) == 5
    assert result[0]["name"] == "repo1"

def test_load_repos_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_repos("/nonexistent/path/repos.json")

def test_calculate_medians_basic(sample_repos):
    result = calculate_medians(sample_repos)
    assert "median_stars" in result
    assert "median_contributors" in result
    assert result["median_stars"] == 3000.0
    assert result["median_contributors"] == 30.0

def test_calculate_medians_empty_list():
    with pytest.raises(ValueError):
        calculate_medians([])

def test_calculate_medians_missing_contributors_all(sample_repos_missing_contributors):
    # Should raise ValueError if no contributors data is found at all
    with pytest.raises(ValueError, match="No 'contributors' field found"):
        calculate_medians(sample_repos_missing_contributors)

def test_calculate_medians_partial_contributors(sample_repos_partial_contributors):
    # Should calculate median from available data
    result = calculate_medians(sample_repos_partial_contributors)
    # Stars: 1000, 2000, 3000 -> median 2000
    assert result["median_stars"] == 2000.0
    # Contributors: 10, 30 -> median 20.0
    assert result["median_contributors"] == 20.0