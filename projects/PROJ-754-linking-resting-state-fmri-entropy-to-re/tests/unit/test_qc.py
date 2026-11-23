"""
Unit tests for the data quality‑control module (src.data.qc).

The tests create a temporary behavioural dataframe, write it to a parquet
file, invoke ``src.data.qc.main`` via its helper ``validate_and_filter``,
and verify that:

* Subjects with mean FD >= 0.2 mm are excluded.
* Subjects with missing DSRT scores are excluded.
* The resulting ``clean_subjects.parquet`` contains only the valid rows.
* The generated ``subject_qc.csv`` correctly records all exclusions.
"""
import os
import tempfile

import pandas as pd
import pytest

from src.data.qc import validate_and_filter, main
from llmxive_toolkit import paths

@pytest.fixture
def behavioural_df():
    """Create a small behavioural dataframe with a mixture of good/bad rows."""
    data = {
        "subject_id": ["subj01", "subj02", "subj03", "subj04"],
        "age": [25, 30, 22, 28],
        "sex": ["M", "F", "F", "M"],
        # subj01: good motion, has DSRT
        "mean_fd": [0.10, 0.25, 0.15, 0.05],
        # subj02: high motion
        "dsrt_score": [3.5, 4.0, None, 2.8],
    }
    return pd.DataFrame(data)

def test_validate_and_filter(behavioural_df):
    clean_df, exclusions = validate_and_filter(behavioural_df, fd_threshold=0.2)

    # Expected: subj01 and subj04 are valid
    assert set(clean_df["subject_id"]) == {"subj01", "subj04"}
    assert clean_df["status"].eq("valid").all()

    # Expected exclusions: subj02 (high FD) and subj03 (missing DSRT)
    expected_exclusions = {
        ("subj02", "Mean FD >= 0.2 mm"),
        ("subj03", "Missing DSRT score"),
    }
    # Normalise reasons (the function uses the threshold value in the string)
    actual_exclusions = set()
    for sid, reason in exclusions:
        if "Mean FD" in reason:
            actual_exclusions.add((sid, "Mean FD >= 0.2 mm"))
        else:
            actual_exclusions.add((sid, reason))
    assert actual_exclusions == expected_exclusions

def test_cli_writes_files(behavioural_df):
    # Write the input dataframe to a temporary parquet file
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "behavioural.parquet")
        behavioural_df.to_parquet(input_path, index=False)

        # Override the default paths for the CLI run
        output_dir = os.path.join(tmpdir, "data")
        os.makedirs(output_dir, exist_ok=True)

        # Patch the paths module temporarily to redirect to the temp dir
        original_paths_data = paths.data

        def temp_data(*parts):
            return Path(tmpdir, *parts)

        paths.data = temp_data  # type: ignore

        try:
            # Simulate CLI arguments
            import sys
            sys_argv_backup = sys.argv
            sys.argv = [
                "src.data.qc",
                "--input",
                input_path,
                "--fd-threshold",
                "0.2",
                "--output-dir",
                tmpdir,
            ]

            # Execute main (it will write into the temporary directory)
            main()

            # Verify outputs
            clean_path = Path(tmpdir, "derived", "clean_subjects.parquet")
            qc_log_path = Path(tmpdir, "derived", "subject_qc.csv")

            assert clean_path.is_file()
            assert qc_log_path.is_file()

            clean_df = pd.read_parquet(clean_path)
            qc_log_df = pd.read_csv(qc_log_path)

            # Clean dataframe should contain the two valid subjects
            assert set(clean_df["subject_id"]) == {"subj01", "subj04"}
            assert all(clean_df["status"] == "valid")

            # QC log should contain two rows (only the excluded subjects)
            assert qc_log_df.shape[0] == 2
            assert set(qc_log_df["subject_id"]) == {"subj02", "subj03"}
        finally:
            # Restore patched objects
            paths.data = original_paths_data  # type: ignore
            sys.argv = sys_argv_backup