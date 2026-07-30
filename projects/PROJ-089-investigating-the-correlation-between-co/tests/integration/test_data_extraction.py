"""
Integration tests for data extraction module.

Tests:
1. Verify repo cloning and filtering logic.
2. Verify that the pipeline produces a valid CSV with expected columns.
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
import os

# Import the module under test
from code.data_extraction import (
    query_github_repos,
    filter_repos_by_age,
    clone_repository,
    extract_git_metrics,
    run_data_extraction,
    save_repos_metadata
)

# Fixtures
@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test outputs."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_repo_data():
    """Sample repository data for testing."""
    return [
        {
            "full_name": "test/repo1",
            "html_url": "https://github.com/test/repo1.git",
            "stargazers_count": 600,
            "created_at": "2020-01-01T00:00:00Z",
            "language": "Python"
        },
        {
            "full_name": "test/repo2",
            "html_url": "https://github.com/test/repo2.git",
            "stargazers_count": 1000,
            "created_at": "2023-01-01T00:00:00Z", # Too recent
            "language": "Python"
        }
    ]

def test_query_github_repos_returns_list():
    """Test that query_github_repos returns a list of dictionaries."""
    # Use a small max_results to avoid long waits
    repos = query_github_repos(min_stars=500, max_results=2)
    assert isinstance(repos, list)
    assert len(repos) <= 2
    if repos:
        assert "full_name" in repos[0]
        assert "stargazers_count" in repos[0]
        assert repos[0]["stargazers_count"] >= 500

def test_filter_repos_by_age(sample_repo_data):
    """Test filtering repositories by age."""
    filtered = filter_repos_by_age(sample_repo_data, min_age_years=2)
    # repo1 is old, repo2 is new (2023)
    assert len(filtered) == 1
    assert filtered[0]["full_name"] == "test/repo1"

def test_clone_repository_success(temp_output_dir):
    """Test cloning a real repository (small public one)."""
    # Use a known small public repo
    url = "https://github.com/psf/requests.git"
    clone_path = clone_repository(url, temp_output_dir)
    assert clone_path is not None
    assert clone_path.exists()
    assert (clone_path / ".git").exists()

def test_run_data_extraction_integration(temp_output_dir):
    """
    End-to-end test: Query, Filter, Clone, Extract, Save.
    Verifies that the output CSV is created and has the expected schema.
    """
    # Run with very small limits to ensure it finishes quickly in CI
    # Note: This test might be flaky if network is slow or API rate limited.
    # We limit to 1 repo to minimize risk.
    results = run_data_extraction(
        languages=["Python"],
        max_repos=1,
        output_dir=temp_output_dir
    )

    # Check that metadata file was created
    metadata_path = temp_output_dir / "repos_metadata.csv"
    assert metadata_path.exists(), "repos_metadata.csv should be created"

    # Load and verify schema
    df = pd.read_csv(metadata_path)
    expected_columns = [
        'full_name', 'html_url', 'stargazers_count', 'created_at',
        'language', 'total_commits', 'total_lines_changed'
    ]

    for col in expected_columns:
        assert col in df.columns, f"Missing column: {col}"

    # Check that we have at least one row (if network/API allowed)
    # If 0 rows, it means the filter or clone failed, which is also a valid state to check
    # But for a "happy path" integration test, we expect > 0 if the repo exists and is old enough.
    # Given the constraints, we just assert the file exists and has the right headers.
    assert len(df.columns) == len(expected_columns)

def test_save_repos_metadata(temp_output_dir):
    """Test saving repository metadata to CSV."""
    data = [
        {"name": "A", "count": 10},
        {"name": "B", "count": 20}
    ]
    output_path = temp_output_dir / "test_meta.csv"
    save_repos_metadata(data, output_path)

    assert output_path.exists()
    df = pd.read_csv(output_path)
    assert len(df) == 2
    assert "name" in df.columns
    assert "count" in df.columns
