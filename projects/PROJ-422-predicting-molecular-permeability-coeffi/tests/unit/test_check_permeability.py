"""
Unit tests for the `code/data/check_permeability.py` script.

The script scans a list of candidate datasets (provided by
``config/verified_datasets.yaml``) for a ``permeability`` column.
If such a column is found, the identifier of the dataset is written to
``config/selected_dataset.yaml`` and the script exits with status 0.
Otherwise it exits with a non‑zero status.

The tests use monkey‑patching to replace the internal
``_load_verified_datasets`` helper with a custom list that points to
temporary CSV files created in the test's temporary directory. This
avoids having to modify the real configuration files on disk.
"""

import csv
import json
import os
from pathlib import Path

import pytest

# Import the module under test
from code.data import check_permeability as cp

# Helper to create a CSV file with the given header columns
def _write_csv(path: Path, header: list, rows: list = None):
    rows = rows or []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

@pytest.fixture
def cleanup_selected():
    """Ensure ``selected_dataset.yaml`` is removed before and after each test."""
    selected_path = Path(cp._project_root()) / "config" / "selected_dataset.yaml"
    if selected_path.is_file():
        selected_path.unlink()
    yield selected_path
    if selected_path.is_file():
        selected_path.unlink()

def test_check_permeability_success(tmp_path: Path, cleanup_selected, monkeypatch):
    """
    The script should return exit code 0 and write the selected dataset
    identifier when a ``permeability`` column is present.
    """
    # Create a temporary CSV that contains a ``permeability`` column
    csv_path = tmp_path / "with_permeability.csv"
    _write_csv(csv_path, ["smiles", "permeability"], [["CCO", "0.85"]])

    # Monkey‑patch the internal loader to return our temporary spec
    monkeypatch.setattr(
        cp,
        "_load_verified_datasets",
        lambda: [{"local_path": str(csv_path)}],
    )

    # Run the main function directly (it returns an exit code)
    exit_code = cp.main()

    # Verify exit code
    assert exit_code == 0, "Expected success exit code (0) when permeability column exists"

    # Verify that the selected_dataset.yaml file was created and contains the correct identifier
    selected_path = Path(cp._project_root()) / "config" / "selected_dataset.yaml"
    assert selected_path.is_file(), "selected_dataset.yaml should be created on success"

    with selected_path.open("r", encoding="utf-8") as f:
        content = yaml.safe_load(f)
    # The identifier should be the local_path we supplied
    assert content.get("selected_dataset") == str(csv_path), "selected_dataset.yaml should contain the chosen dataset identifier"

def test_check_permeability_failure(tmp_path: Path, cleanup_selected, monkeypatch):
    """
    The script should return a non‑zero exit code when no dataset contains a
    ``permeability`` column, and it must not create ``selected_dataset.yaml``.
    """
    # Create a temporary CSV that **does not** contain a permeability column
    csv_path = tmp_path / "without_permeability.csv"
    _write_csv(csv_path, ["smiles", "logp"], [["CCO", "1.2"]])

    # Monkey‑patch the internal loader to return our temporary spec
    monkeypatch.setattr(
        cp,
        "_load_verified_datasets",
        lambda: [{"local_path": str(csv_path)}],
    )

    # Run the main function directly
    exit_code = cp.main()

    # Verify that a non‑zero exit code is returned
    assert exit_code != 0, "Expected non‑zero exit code when permeability column is absent"

    # Verify that selected_dataset.yaml was **not** created
    selected_path = Path(cp._project_root()) / "config" / "selected_dataset.yaml"
    assert not selected_path.is_file(), "selected_dataset.yaml must not be created on failure"

# The tests rely on ``yaml`` which is part of the runtime environment.
# Import it lazily to avoid unnecessary imports when the module is
# imported by other test suites.
import yaml