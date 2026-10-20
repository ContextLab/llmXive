"""
Unit tests for ``src/data/loader.py``.

The tests use a tiny synthetic CSV fixture that deliberately contains:

* a row with a missing required field,
* a duplicate ``material_id``,
* an outlier (extreme ``band_gap`` and ``hardness``),
* a formula with an unknown element,
* a valid row.

The loader should drop the problematic rows and write only the valid
rows to the output CSV.
"""
import csv
from pathlib import Path

import pandas as pd
import pytest

from src.data.loader import load_and_clean

@pytest.fixture
def tiny_fixture(tmp_path: Path) -> Path:
    """Create a tiny CSV fixture with intentional problems."""
    csv_path = tmp_path / "tiny_materials.csv"
    rows = [
        # Header
        [
            "material_id",
            "formula",
            "band_gap",
            "hardness",
            "crystal_system",
        ],
        # Valid row
        ["m1", "Fe2O3", "2.5", "5.0", "cubic"],
        # Row with missing hardness
        ["m2", "SiO2", "5.0", "", "hexagonal"],
        # Duplicate material_id (same as first)
        ["m1", "Fe2O3", "2.5", "5.0", "cubic"],
        # Outlier row (very large values)
        ["m3", "Al2O3", "100.0", "200.0", "cubic"],
        # Unknown element (X)
        ["m4", "FakeX", "1.0", "2.0", "trigonal"],
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return csv_path

def test_loader_filters_rows(tmp_path: Path, tiny_fixture: Path) -> None:
    """Run the loader on the fixture and verify output."""
    out_path = tmp_path / "cleaned.csv"

    # Execute the loader
    load_and_clean(tiny_fixture, out_path)

    # Load the result
    df = pd.read_csv(out_path)

    # Expected kept rows: only the first valid row (m1)
    assert len(df) == 1
    assert df.iloc[0]["material_id"] == "m1"
    assert df.iloc[0]["formula"] == "Fe2O3"
    assert pytest.approx(df.iloc[0]["band_gap"], rel=1e-6) == 2.5
    assert pytest.approx(df.iloc[0]["hardness"], rel=1e-6) == 5.0
    assert df.iloc[0]["crystal_system"] == "cubic"