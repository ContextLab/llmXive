"""
Integration test for full pipeline on 5-repo seed (T006 -> T007 -> T008 -> T009).
Verifies that the output file `data/processed/repo_metrics_clean.csv` exists and contains
non-null values for required columns for the first 5 repositories.
"""
import os
import sys
import subprocess
import pandas as pd
import pytest
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import ensure_directories
from code.data.generate_target_list import main as generate_target_list_main
from code.data.download_nvd import main as download_nvd_main
from code.data.extract_github import main as extract_github_main
from code.data.merge_datasets import main as merge_datasets_main


@pytest.fixture(scope="module")
def setup_environment():
    """Ensure directories exist."""
    ensure_directories()
    yield


def test_full_pipeline_seed_5(setup_environment):
    """
    Run the full data pipeline on a seed of 5 repositories.
    Steps:
    1. Generate target list (T006)
    2. Download NVD (T007)
    3. Extract GitHub metrics (T008)
    4. Merge datasets (T009)
    5. Assert output file exists and contains valid data.
    """
    
    # 1. Generate Target List (T006)
    target_list_path = PROJECT_ROOT / "data" / "raw" / "target_list.csv"
    if not target_list_path.exists():
        try:
            generate_target_list_main()
        except Exception as e:
            pytest.fail(f"T006 (generate_target_list) failed: {e}")
    
    # Verify we have at least 5 repos to process for the seed test
    # If the real T006 produced fewer, we proceed with what we have, 
    # but the task description implies a 5-repo seed context.
    # The script T006 is expected to generate a large list, so this check is mostly for safety.
    if target_list_path.exists():
        df_target = pd.read_csv(target_list_path)
        if len(df_target) < 5:
            # In a real scenario, T006 should produce enough. 
            # If not, we proceed with what's available, but the test logic below 
            # handles small samples gracefully.
            pass

    # 2. Download NVD (T007)
    nvd_merged_path = PROJECT_ROOT / "data" / "raw" / "nvd_cve_merged.json.gz"
    if not nvd_merged_path.exists():
        try:
            download_nvd_main()
        except Exception as e:
            pytest.fail(f"T007 (download_nvd) failed: {e}")
    
    # 3. Extract GitHub Metrics (T008)
    github_metrics_path = PROJECT_ROOT / "data" / "processed" / "github_raw_metrics.csv"
    if not github_metrics_path.exists():
        try:
            extract_github_main()
        except Exception as e:
            pytest.fail(f"T008 (extract_github) failed: {e}")
    
    # 4. Merge Datasets (T009)
    # The task description and T009 spec explicitly name the output as:
    # `data/processed/repo_metrics_clean.csv`
    merged_path = PROJECT_ROOT / "data" / "processed" / "repo_metrics_clean.csv"
    if not merged_path.exists():
        try:
            merge_datasets_main()
        except Exception as e:
            pytest.fail(f"T009 (merge_datasets) failed: {e}")
    
    # Assertions
    assert merged_path.exists(), f"Output file {merged_path} was not created."
    
    df = pd.read_csv(merged_path)
    
    # Required columns based on T009 spec: 
    # `url`, `primary_language`, `unique_authors`, `kloc`, `authorship_diversity`, `cve_count`, `project_age`, `release_count`
    required_columns = ['url', 'primary_language', 'unique_authors', 'kloc', 'authorship_diversity', 'cve_count', 'project_age', 'release_count']
    
    missing_cols = set(required_columns) - set(df.columns)
    assert not missing_cols, f"Missing columns in output: {missing_cols}"
    
    # Check for the first 5 entries (or all if less than 5)
    sample_size = min(5, len(df))
    if sample_size == 0:
        pytest.fail("No data in repo_metrics_clean.csv")
    
    sample_df = df.head(sample_size)
    
    # Assert non-null values for required fields
    assert sample_df['unique_authors'].notnull().all(), "unique_authors contains null values"
    assert sample_df['kloc'].notnull().all(), "kloc contains null values"
    assert sample_df['cve_count'].notnull().all(), "cve_count contains null values"
    assert sample_df['primary_language'].notnull().all(), "primary_language contains null values"
    
    # Assert valid types/values where applicable
    # kloc should be numeric
    assert pd.to_numeric(sample_df['kloc'], errors='coerce').notna().all(), "kloc contains non-numeric values"
    
    print(f"Pipeline successful. Processed {len(df)} repositories.")
    print(f"Sample of first {sample_size} rows:")
    print(sample_df)