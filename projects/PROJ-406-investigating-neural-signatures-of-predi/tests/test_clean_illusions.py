"""
Tests for the ``src.ingest.clean_illusions`` module.

The test suite verifies that:
  1. The cleaning script runs without error.
  2. The expected CSV files are created.
  3. Each CSV contains at least one row.
  4. No required columns contain missing values.
"""

import pathlib

import pandas as pd
import pytest

from llmxive_toolkit import paths

# Import the module to ensure that any import‑time side‑effects (e.g.,
# seeding) are exercised.
import src.ingest.clean_illusions  # noqa: F401

@pytest.fixture(scope="session")
def run_clean_script():
    """Execute the cleaning script once for the whole test session."""
    import subprocess

    result = subprocess.run(
        ["python", "-m", "src.ingest.clean_illusions"],
        capture_output=True,
        text=True,
        check=False,
    )
    # Propagate stdout/stderr to aid debugging if the script fails.
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0, "Cleaning script failed to execute"

# Expected schema definitions – these match the contract files in
# ``contracts/``.  They are duplicated here to keep the test self‑contained.
MULLER_REQUIRED = [
    "subject_id",
    "trial_id",
    "stimulus_length",
    "response_length",
    "stimulus_parameters",
]

PONZO_REQUIRED = [
    "subject_id",
    "trial_id",
    "arrow_angle",
    "depth_cue",
    "perceived_length",
]

@pytest.mark.usefixtures("run_clean_script")
def test_clean_muller_lyer_exists_and_valid():
    csv_path = paths.data("clean", "clean_muller_lyer.csv")
    assert csv_path.is_file(), f"Missing cleaned file: {csv_path}"
    df = pd.read_csv(csv_path)

    # At least one row should be present.
    assert len(df) > 0, "Cleaned Müller‑Lyer CSV is empty"

    # Required columns must exist.
    missing = [c for c in MULLER_REQUIRED if c not in df.columns]
    assert not missing, f"Missing required columns in Müller‑Lyer CSV: {missing}"

    # No NaNs in required columns.
    assert not df[MULLER_REQUIRED].isnull().any().any(), "NaNs found in required columns of Müller‑Lyer CSV"

@pytest.mark.usefixtures("run_clean_script")
def test_clean_ponzo_exists_and_valid():
    csv_path = paths.data("clean", "clean_ponzo.csv")
    assert csv_path.is_file(), f"Missing cleaned file: {csv_path}"
    df = pd.read_csv(csv_path)

    # At least one row should be present.
    assert len(df) > 0, "Cleaned Ponzo CSV is empty"

    # Required columns must exist.
    missing = [c for c in PONZO_REQUIRED if c not in df.columns]
    assert not missing, f"Missing required columns in Ponzo CSV: {missing}"

    # No NaNs in required columns.
    assert not df[PONZO_REQUIRED].isnull().any().any(), "NaNs found in required columns of Ponzo CSV"