"""
Test suite for the preprocessing and geometry computation script.

This test ensures that for each dataset marked as "Available" in the
manifest, the required output files are created and contain the expected
structure and keys.
"""

import json
from pathlib import Path

import pytest

from data_gap_resolver import DataGapResolver
from preprocess_and_geometry import main as preprocess_main
from llmxive_toolkit import paths


@pytest.fixture(scope="module")
def resolved_manifest():
    """
    Resolve the raw datasets using the DataGapResolver and return the
    manifest entries. This fixture runs once per test session.
    """
    resolver = DataGapResolver()
    status, _, _ = resolver.resolve()
    assert status == "enough", "Data gap resolution did not find enough datasets"
    manifest_path = paths.data("manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_preprocess_and_geometry_outputs(resolved_manifest):
    """
    Run the preprocessing pipeline and verify that for each available
    dataset the expected files are produced and contain the required
    fields.
    """
    # Execute the preprocessing script (wrapped with ResourceMonitor)
    preprocess_main()

    for entry in resolved_manifest:
        if entry.get("status") != "Available":
            continue

        dataset_id = entry["dataset_id"]

        # 1. Labels CSV
        labels_path = paths.processed(f"{dataset_id}_labels.csv")
        assert labels_path.is_file(), f"Labels file missing: {labels_path}"
        # Basic sanity check – at least two columns (cell_id, label)
        with open(labels_path, "r", encoding="utf-8") as f:
            header = f.readline().strip().split(",")
            assert "cell_id" in header and "label" in header, \
                f"Labels CSV header incorrect in {labels_path}"

        # 2. HVG count text file
        hvg_path = paths.processed(f"{dataset_id}_hvg.txt")
        assert hvg_path.is_file(), f"HVG count file missing: {hvg_path}"
        hvg_count = int(hvg_path.read_text().strip())
        assert hvg_count > 0, f"HVG count non‑positive for {dataset_id}"

        # 3. Processed matrix Parquet
        matrix_path = paths.processed(f"{dataset_id}_matrix.parquet")
        assert matrix_path.is_file(), f"Processed matrix missing: {matrix_path}"
        # Verify that the file can be read with pandas
        import pandas as pd
        df = pd.read_parquet(matrix_path)
        assert not df.empty, f"Processed matrix is empty for {dataset_id}"
        assert df.shape[0] == df.index.nunique(), \
            "Row identifiers in matrix are not unique"

        # 4. Geometry JSON
        geom_path = paths.processed(f"{dataset_id}_geometric.json")
        assert geom_path.is_file(), f"Geometry JSON missing: {geom_path}"
        with open(geom_path, "r", encoding="utf-8") as f:
            geom = json.load(f)

        # Required keys
        required_keys = {"intrinsic_dimensionality", "local_density", "params"}
        assert required_keys.issubset(geom.keys()), \
            f"Geometry JSON missing keys for {dataset_id}"

        # Parameter verification
        params = geom["params"]
        assert params.get("k") == 15, "k parameter mismatch in geometry JSON"
        assert params.get("seed") == 42, "seed parameter mismatch in geometry JSON"
        # pair_count should be the lesser of 10000 or number of cells
        pair_count = params.get("pair_count")
        assert isinstance(pair_count, int) and pair_count > 0, \
            "pair_count invalid in geometry JSON"

        # Intrinsic dimensionality and local density should be finite floats
        assert isinstance(geom["intrinsic_dimensionality"], float), \
            "intrinsic_dimensionality is not a float"
        assert isinstance(geom["local_density"], float), \
            "local_density is not a float"
        assert not any(map(lambda x: not (x == x),  # NaN check
                           [geom["intrinsic_dimensionality"], geom["local_density"]]
                           )), "Geometry values contain NaN"