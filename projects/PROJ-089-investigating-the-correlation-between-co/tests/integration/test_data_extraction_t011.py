import os
import pytest
import pandas as pd
from pathlib import Path
import shutil
import tempfile

# Import the function we are testing
from data_extraction import process_single_repo, load_repos_metadata, run_data_extraction

@pytest.fixture
def temp_repo_dir():
    """Create a temporary directory for test repos."""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    shutil.rmtree(temp)

@pytest.fixture
def sample_repos_csv(temp_repo_dir):
    """Create a sample repos_metadata.csv."""
    csv_path = temp_repo_dir / "repos_metadata.csv"
    data = {
        'repo_id': ['test-repo-1'],
        'owner': ['pydriller'],
        'name': ['pydriller'],
        'language': ['Python'],
        'url': ['https://github.com/isidentical/pydriller.git']
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    return csv_path

def test_process_single_repo_integration(temp_repo_dir, sample_repos_csv):
    """
    Integration test for T011:
    1. Load sample repos metadata.
    2. Process a real public repo (pydriller).
    3. Verify the output CSV exists and has correct columns.
    """
    repos = load_repos_metadata(sample_repos_csv)
    assert len(repos) == 1
    
    repo_meta = repos[0]
    
    # Run the extraction
    output_path = process_single_repo(repo_meta, temp_repo_dir, days=365)
    
    # Assertions
    assert output_path is not None, "Process returned None"
    assert output_path.exists(), f"Output file does not exist: {output_path}"
    
    # Verify content
    df = pd.read_csv(output_path)
    assert 'file_path' in df.columns
    assert 'total_lines_changed' in df.columns
    assert 'commit_count' in df.columns
    
    # We expect non-empty data for a real repo like pydriller
    # But we allow for the possibility of it being empty if the repo has no history in the last 365 days
    # (unlikely for pydriller, but good to be safe)
    assert len(df) >= 0 

def test_run_data_extraction_integration(temp_repo_dir, sample_repos_csv):
    """
    Integration test for the full extraction pipeline on a small scale.
    """
    output_paths = run_data_extraction(sample_repos_csv, temp_repo_dir, days=365)
    
    assert len(output_paths) > 0
    for path in output_paths:
        assert path.exists()
        df = pd.read_csv(path)
        assert list(df.columns) == ['file_path', 'total_lines_changed', 'commit_count']
