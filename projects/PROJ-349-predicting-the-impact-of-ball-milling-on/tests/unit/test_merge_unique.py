"""
Unit test for the merge pipeline ensuring that the resulting dataset contains
unique experiment identifiers.
"""

import pandas as pd
from pathlib import Path

from src.ingest.merge import run_merge_pipeline
from llmxive_toolkit import paths

def test_merged_dataset_has_unique_experiment_id():
    # Load the raw source files that are part of the repository
    nist_path = paths.data("raw", "nist_raw.csv")
    arxiv_path = paths.data("raw", "arxiv_tables.json")
    materials_path = paths.data("raw", "materials_project_raw.parquet")  # may not exist

    # Read NIST data
    nist_df = pd.read_csv(nist_path) if nist_path.is_file() else None

    # Read arXiv data (empty JSON yields empty DataFrame)
    if arxiv_path.is_file():
        try:
            arxiv_df = pd.read_json(arxiv_path, orient="records")
        except ValueError:
            # Empty file -> empty DataFrame
            arxiv_df = pd.DataFrame()
    else:
        arxiv_df = None

    # Materials Project data optional
    materials_df = None
    if materials_path.is_file():
        try:
            materials_df = pd.read_parquet(materials_path)
        except Exception:
            materials_df = None

    # Run the merge pipeline (no output file needed for the test)
    merged_df = run_merge_pipeline(
        materials_project_df=materials_df,
        nist_df=nist_df,
        arxiv_df=arxiv_df,
        output_path=None
    )

    # Ensure the 'experiment_id' column exists
    assert "experiment_id" in merged_df.columns, "Merged dataframe must contain 'experiment_id' column"

    # Verify uniqueness
    exp_ids = merged_df["experiment_id"]
    assert exp_ids.is_unique, "experiment_id values must be unique after merging"