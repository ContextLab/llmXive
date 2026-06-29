"""
Integration test for the end‑to‑end data pipeline (T009).

The test verifies that the synthetic pipeline creates a dataset that satisfies
the contractual requirements of User Story 1:
  * ≥10 000 rows
  * ≥5 metric columns
  * a binary ``bug_label`` column
  * a 30 % test split performed at the project level (no project appears in both
    splits) and the proportion is within a reasonable tolerance.
"""
import os
from pathlib import Path

import pandas as pd
import pytest

# Import the pipeline implementation added for this task
from data.pipeline import run_pipeline

# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def pipeline_outputs(tmp_path_factory):
    """
    Run the pipeline once for the entire test module and expose the artefacts.
    The fixture uses a temporary directory to avoid polluting the repository.
    """
    # Switch the working directory to a temporary location so that the
    # ``data/processed`` directory is created inside the temp dir.
    tmp_dir = tmp_path_factory.mktemp("pipeline_test")
    orig_cwd = os.getcwd()
    os.chdir(tmp_dir)

    try:
        outputs = run_pipeline()
        yield outputs
    finally:
        # Return to the original working directory regardless of test outcome
        os.chdir(orig_cwd)

# ---------------------------------------------------------------------------

def test_dataset_shape_and_columns(pipeline_outputs):
    full_df = pipeline_outputs["full"]
    # 1. Row count
    assert len(full_df) >= 10_000, "Dataset must contain at least 10 000 rows"

    # 2. Required metric columns (at least five)
    required_metrics = {
        "loc",
        "cyclomatic_complexity",
        "token_count",
        "nesting_depth",
        "halstead_volume",
    }
    missing = required_metrics - set(full_df.columns)
    assert not missing, f"Missing required metric columns: {missing}"

    # 3. Binary bug label
    assert "bug_label" in full_df.columns, "Missing 'bug_label' column"
    unique_labels = set(full_df["bug_label"].unique())
    assert unique_labels <= {0, 1}, f"'bug_label' must be binary, found {unique_labels}"

# ---------------------------------------------------------------------------

def test_train_test_split_properties(pipeline_outputs):
    train_df = pipeline_outputs["train"]
    test_df = pipeline_outputs["test"]

    # 1. No project appears in both splits
    train_projects = set(train_df["project_id"].unique())
    test_projects = set(test_df["project_id"].unique())
    intersection = train_projects.intersection(test_projects)
    assert not intersection, f"Projects found in both splits: {intersection}"

    # 2. Approximate 30 % test proportion (allow ±5 % tolerance)
    total_rows = len(train_df) + len(test_df)
    test_ratio = len(test_df) / total_rows
    assert 0.25 <= test_ratio <= 0.35, (
        f"Test split proportion {test_ratio:.2%} outside expected 30 % ±5 % range"
    )

# ---------------------------------------------------------------------------

def test_output_files_exist(pipeline_outputs):
    # Verify that the parquet files were written to the expected locations
    paths = pipeline_outputs["paths"]
    for key, file_path in paths.items():
        assert Path(file_path).exists(), f"Expected {key} file at {file_path} to exist"

# ---------------------------------------------------------------------------

# The test suite can be executed with ``pytest -q`` from the repository root.
# No additional fixtures or external services are required.