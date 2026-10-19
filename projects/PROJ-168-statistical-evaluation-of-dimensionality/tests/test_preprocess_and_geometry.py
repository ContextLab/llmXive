"""
Unit tests for the ``preprocess_and_geometry`` script.

The tests use a tiny synthetic GEO‑style matrix written to a temporary
directory so that the script can be exercised without downloading the
real GEO files.  The focus is on the *pipeline* logic (file creation,
shape checks, JSON contents) rather than the biological correctness of
the transformations.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from llmxive_toolkit import paths

# Import the module under test
import importlib.util

spec = importlib.util.spec_from_file_location(
    "preprocess_and_geometry",
    Path(__file__).parents[1] / "code" / "preprocess_and_geometry.py",
)
preprocess_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preprocess_mod)


@pytest.fixture
def fake_manifest(tmp_path):
    """
    Create a minimal ``data/manifest.json`` with a single synthetic dataset.
    The raw series‑matrix file contains 5 cells and 10 genes – small enough
    for fast test execution.
    """
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    dataset_id = "FAKE001"
    raw_file = raw_dir / f"{dataset_id}_series_matrix.txt.gz"

    # Construct a tiny GEO‑style matrix:
    #   - 5 cells (columns)
    #   - 10 genes (rows)
    genes = [f"Gene{i}" for i in range(10)]
    cells = [f"Cell{i}" for i in range(5)]
    rng = np.random.default_rng(0)
    counts = rng.integers(low=0, high=100, size=(10, 5))

    df = pd.DataFrame(counts, index=genes, columns=cells)
    # GEO series matrices start with comment lines beginning with "!"
    header_lines = [
        "!Series_matrix_table_begin",
    ]
    with tempfile.NamedTemporaryFile("wt", delete=False) as tmp:
        for line in header_lines:
            tmp.write(line + "\n")
        df.to_csv(tmp, sep="\t")
    # Compress
    import gzip
    with open(tmp.name, "rb") as f_in, gzip.open(raw_file, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    os.unlink(tmp.name)

    manifest = [
        {
            "dataset_id": dataset_id,
            "source_url": "http://example.com/fake",
            "status": "Available",
            "checksum": "deadbeef",
            "raw_file_path": str(raw_file),
            "processed_file_path": None,
        }
    ]
    manifest_path = paths.data("manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return dataset_id


def test_preprocess_creates_expected_files(fake_manifest):
    """Run the main function and verify that all artefacts are written."""
    dataset_id = fake_manifest

    # Run the preprocessing pipeline
    preprocess_mod.main()

    # Expected output paths
    processed_dir = paths.processed()
    matrix_path = processed_dir / f"{dataset_id}_matrix.parquet"
    labels_path = processed_dir / f"{dataset_id}_labels.csv"
    hvg_path = processed_dir / f"{dataset_id}_hvg.txt"
    geom_path = processed_dir / f"{dataset_id}_geometric.json"

    # --------------------------------------------------------------
    # Basic existence checks
    # --------------------------------------------------------------
    assert matrix_path.is_file(), "Processed matrix parquet not created"
    assert labels_path.is_file(), "Labels CSV not created"
    assert hvg_path.is_file(), "HVG count file not created"
    assert geom_path.is_file(), "Geometric JSON not created"

    # --------------------------------------------------------------
    # Shape and content checks
    # --------------------------------------------------------------
    df_matrix = pd.read_parquet(matrix_path)
    assert df_matrix.shape[0] <= Config.SAMPLE_SIZE
    # The synthetic dataset has 10 genes; after HVG selection we expect
    # at most 10 columns.
    assert df_matrix.shape[1] <= 10

    # HVG count must be a positive integer
    n_hvg = int(hvg_path.read_text().strip())
    assert n_hvg > 0

    # Geometric JSON must contain the required keys with proper types
    geom = json.loads(geom_path.read_text())
    assert set(geom.keys()) == {"trustworthiness", "local_continuity"}
    # For a tiny dataset (<500 cells) the spec says values may be null
    assert (geom["trustworthiness"] is None) or (0.0 <= geom["trustworthiness"] <= 1.0)
    assert (geom["local_continuity"] is None) or (0.0 <= geom["local_continuity"] <= 1.0)

    # --------------------------------------------------------------
    # Monitoring CSV must contain a row for this dataset
    # --------------------------------------------------------------
    monitoring_path = paths.results("monitoring.csv")
    assert monitoring_path.is_file()
    monitoring_df = pd.read_csv(monitoring_path)
    assert any(monitoring_df["step"] == f"preprocess_{dataset_id}")

# Clean up temporary files after the test suite runs
def teardown_module(module):
    # Remove generated artefacts to keep the repository tidy
    shutil.rmtree(paths.processed(), ignore_errors=True)
    manifest_path = paths.data("manifest.json")
    if manifest_path.is_file():
        manifest_path.unlink()
    monitoring_path = paths.results("monitoring.csv")
    if monitoring_path.is_file():
        monitoring_path.unlink()