"""
Unit tests for the T023b implementation.

The tests verify that:
  * ``merge_metrics_and_pca_scores`` correctly joins the raw metrics and
    PCA scores on ``subject_id``.
  * The output file ``data/analysis/full_metrics.csv`` is created and
    contains the expected columns.
"""

import os
import shutil
from pathlib import Path

import pandas as pd
import pytest

# Import the functions from the module under test.
from analysis.correlations import (
    merge_metrics_and_pca_scores,
    load_metrics_data,
    run_pca_analysis,
)

# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture(scope="function")
def temporary_analysis_dir(tmp_path):
    """
    Create a temporary ``data/analysis`` directory for the duration of a test
    and ensure the project code sees this path.
    """
    # Resolve the project's root ``data/analysis`` directory.
    project_root = Path(__file__).resolve().parents[2]
    analysis_dir = project_root / "data" / "analysis"

    # Backup any existing files so we do not clobber real results.
    backup_dir = tmp_path / "backup"
    backup_dir.mkdir()
    for file in analysis_dir.iterdir():
        if file.is_file():
            shutil.copy(file, backup_dir / file.name)

    # Ensure the directory exists.
    analysis_dir.mkdir(parents=True, exist_ok=True)

    yield analysis_dir

    # Restore original files after the test finishes.
    for backup_file in backup_dir.iterdir():
        shutil.move(str(backup_file), analysis_dir / backup_file.name)


# ----------------------------------------------------------------------
# Helper to create a minimal synthetic metrics CSV (real CSV format, not
# synthetic *data* for the scientific analysis – this is just for the unit
# test environment).
# ----------------------------------------------------------------------


def create_dummy_metrics_csv(path: Path):
    df = pd.DataFrame(
        {
            "subject_id": [1, 2, 3],
            "modularity": [0.3, 0.35, 0.32],
            "global_efficiency": [0.45, 0.48, 0.46],
            "participation_coef": [0.2, 0.22, 0.21],
            "within_module_degree": [0.5, 0.55, 0.52],
        }
    )
    df.to_csv(path, index=False)


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------


def test_merge_metrics_and_pca_scores_writes_file(temporary_analysis_dir):
    # Arrange: create a dummy raw metrics file.
    metrics_path = temporary_analysis_dir / "metrics.csv"
    create_dummy_metrics_csv(metrics_path)

    # Load the metrics using the production function (ensures path logic works).
    metrics_df = load_metrics_data()

    # Run PCA to generate factor scores.
    _, scores_df = run_pca_analysis(metrics_df)

    # Act: merge and write.
    merged_df = merge_metrics_and_pca_scores(metrics_df, scores_df)

    # Assert: the output file exists.
    output_path = temporary_analysis_dir / "full_metrics.csv"
    assert output_path.is_file(), "full_metrics.csv was not created"

    # Load the file and compare to the returned DataFrame.
    loaded = pd.read_csv(output_path)
    pd.testing.assert_frame_equal(loaded, merged_df)

    # Verify that the merged DataFrame contains both raw metric columns and
    # at least one PCA factor column.
    expected_raw_cols = {"subject_id", "modularity", "global_efficiency", "participation_coef", "within_module_degree"}
    pca_cols = {col for col in merged_df.columns if col.startswith("pca_factor_")}
    assert expected_raw_cols.issubset(set(merged_df.columns))
    assert len(pca_cols) > 0, "PCA factor columns are missing in the merged output"


def test_merge_raises_on_missing_subject_id():
    # Create DataFrames that deliberately lack the required column.
    raw = pd.DataFrame({"modularity": [0.3]})
    scores = pd.DataFrame({"subject_id": [1], "pca_factor_1": [0.1]})

    with pytest.raises(ValueError, match="metrics_df must contain a 'subject_id' column"):
        merge_metrics_and_pca_scores(raw, scores)

    # Now omit it from the scores DataFrame.
    raw = pd.DataFrame({"subject_id": [1], "modularity": [0.3]})
    scores = pd.DataFrame({"pca_factor_1": [0.1]})

    with pytest.raises(ValueError, match="scores_df must contain a 'subject_id' column"):
        merge_metrics_and_pca_scores(raw, scores)