"""
Unit test for the ``assemble_final_dataset`` script.

The test creates minimal synthetic input files (real JSON/CSV structures,
not fabricated metrics) and validates that the script produces a merged CSV
with the expected columns and row count.
"""

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from code.data.assemble_final_dataset import assemble_final_dataset


@pytest.fixture
def temporary_data_dir():
    """Create a temporary directory containing minimal input files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Materials Project mock data
        materials = [
            {"material_id": "mp-1", "formula": "Fe", "property_a": 1.0},
            {"material_id": "mp-2", "formula": "Cu", "property_a": 2.0},
        ]
        materials_path = base / "materials.json"
        with materials_path.open("w", encoding="utf-8") as f:
            json.dump(materials, f)

        # NIST mock data (only one overlapping entry)
        nist = [
            {"material_id": "mp-1", "melting_point": 1538, "latent_heat": 13.8},
            {"material_id": "mp-3", "melting_point": 660, "latent_heat": 13.0},
        ]
        nist_path = base / "nist.json"
        with nist_path.open("w", encoding="utf-8") as f:
            json.dump(nist, f)

        # Features CSV
        features = pd.DataFrame(
            {
                "material_id": ["mp-1", "mp-2", "mp-3"],
                "feat_1": [0.1, 0.2, 0.3],
                "feat_2": [1, 2, 3],
            }
        )
        features_path = base / "features.csv"
        features.to_csv(features_path, index=False)

        yield {
            "materials": materials_path,
            "nist": nist_path,
            "features": features_path,
            "output_dir": base,
        }


def test_assemble_final_dataset_creates_correct_csv(temporary_data_dir):
    out_path = temporary_data_dir["output_dir"] / "final.csv"

    assemble_final_dataset(
        materials_json_path=temporary_data_dir["materials"],
        nist_json_path=temporary_data_dir["nist"],
        features_csv_path=temporary_data_dir["features"],
        output_csv_path=out_path,
    )

    # Verify the file exists
    assert out_path.is_file()

    df = pd.read_csv(out_path)

    # Expected rows: join on material_id -> should have mp-1 and mp-2
    # mp-3 is present only in features and NIST, but not in materials, so it
    # will be dropped because we merge left from materials.
    assert set(df["material_id"]) == {"mp-1", "mp-2"}
    assert df.shape[0] == 2

    # Columns from all sources should be present
    for col in ["formula", "property_a", "melting_point", "latent_heat", "feat_1", "feat_2"]:
        assert col in df.columns

    # Verify that NIST data merged correctly for mp-1
    mp1 = df[df["material_id"] == "mp-1"].iloc[0]
    assert mp1["melting_point"] == 1538
    assert mp1["latent_heat"] == 13.8
    # mp-2 has no NIST entry, should be NaN
    mp2 = df[df["material_id"] == "mp-2"].iloc[0]
    assert pd.isna(mp2["melting_point"])
    assert pd.isna(mp2["latent_heat"])