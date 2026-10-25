import os
import pytest
from llmxive_toolkit import paths

# Import the module to ensure it can be executed
from code import data_acquisition

@pytest.mark.timeout(300)
def test_data_acquisition_creates_files(tmp_path, monkeypatch):
    """
    Run the data acquisition script and verify that it creates the expected
    parquet files with at least one row each.
    """
    # Ensure the environment does not have a GitHub token to keep the request count low
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    # Run the main function
    data_acquisition.main()

    # Verify per‑repo parquet files exist and contain rows
    for owner, repo in data_acquisition.REPOSITORIES:
        parquet_path = paths.data("raw", f"{owner}_{repo}.parquet")
        assert parquet_path.is_file(), f"{parquet_path} does not exist"
        df = pd.read_parquet(parquet_path)
        assert len(df) > 0, f"{parquet_path} contains no rows"

    # Verify combined commit messages parquet
    commit_path = paths.data("raw", "commit_messages.parquet")
    assert commit_path.is_file(), "commit_messages.parquet does not exist"
    commit_df = pd.read_parquet(commit_path)
    assert len(commit_df) > 0, "commit_messages.parquet contains no rows"
    # Ensure required columns are present
    assert {"pr_id", "commit_message"}.issubset(set(commit_df.columns))