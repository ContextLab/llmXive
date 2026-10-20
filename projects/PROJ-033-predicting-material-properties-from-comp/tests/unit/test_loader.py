"""
Unit tests for ``src/data/loader.py``.

The fixture deliberately contains:

* a row with a missing required field,
* a duplicate ``material_id``,
* a genuine 1.5 x IQR outlier (extreme ``band_gap`` and ``hardness``),
* a formula with an unknown element,
* several valid rows (including a zero‑band‑gap metal, which must be
  RETAINED).

The loader must drop the problematic rows, keep the valid ones, log the
outlier drop count, warn on unknown elements, and stay within the 6 GB
RAM limit (FR‑001).
"""
import csv
import json
from pathlib import Path

import pandas as pd
import pytest

from src.data.loader import (
    RAM_LIMIT_BYTES,
    iqr_filter,
    is_known_formula,
    load_and_clean,
)

VALID_ROWS = [
    # (material_id, formula, band_gap, hardness, crystal_system)
    ("m01", "Fe2O3", 2.0, 6.0, "hexagonal"),
    ("m02", "SiO2", 5.0, 8.0, "hexagonal"),
    ("m03", "Al2O3", 4.5, 12.0, "trigonal"),
    ("m04", "TiO2", 3.0, 9.0, "tetragonal"),
    ("m05", "ZnO", 3.2, 5.0, "hexagonal"),
    ("m06", "NiO", 2.5, 7.0, "cubic"),
    ("m07", "SnO2", 3.5, 6.5, "tetragonal"),
    ("m08", "CuO", 1.2, 5.5, "cubic"),
    # zero‑band‑gap metal – must be retained
    ("m09", "Si", 0.0, 0.0, "cubic"),
]


@pytest.fixture
def tiny_fixture(tmp_path: Path) -> Path:
    """Create a tiny CSV fixture with intentional problems."""
    csv_path = tmp_path / "tiny_materials.csv"
    rows = [
        ["material_id", "formula", "band_gap", "hardness", "crystal_system"]
    ]
    rows.extend([list(r) for r in VALID_ROWS])
    # Row with missing hardness
    rows.append(["m10", "SiC", "2.5", "", "cubic"])
    # Duplicate material_id (same as first valid row)
    rows.append(["m01", "Fe2O3", "2.0", "6.0", "hexagonal"])
    # Outlier row (extreme band_gap and hardness)
    rows.append(["m11", "MgO", "100.0", "200.0", "cubic"])
    # Unknown element (X)
    rows.append(["m12", "FakeX", "1.0", "2.0", "trigonal"])
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return csv_path


def test_loader_filters_rows(tmp_path: Path, tiny_fixture: Path) -> None:
    """Run the loader and verify only the valid rows survive."""
    out_path = tmp_path / "cleaned.csv"
    report_path = tmp_path / "report.json"
    load_and_clean(tiny_fixture, out_path, report_path)

    df = pd.read_csv(out_path)
    kept_ids = set(df["material_id"])

    # All valid rows (incl. the zero‑band‑gap metal m09) are kept
    for row in VALID_ROWS:
        assert row[0] in kept_ids, f"{row[0]} should have been kept"
    # Problem rows are dropped
    for bad in ("m10", "m11", "m12"):
        assert bad not in kept_ids, f"{bad} should have been dropped"
    # No duplicate ids in output
    assert df["material_id"].is_unique
    assert len(df) == len(VALID_ROWS)


def test_zero_band_gap_metals_retained(tmp_path, tiny_fixture):
    out_path = tmp_path / "cleaned.csv"
    load_and_clean(tiny_fixture, out_path)
    df = pd.read_csv(out_path)
    metal = df[df["material_id"] == "m09"]
    assert len(metal) == 1
    assert metal.iloc[0]["band_gap"] == 0.0


def test_outlier_removal_logged(tmp_path, tiny_fixture, caplog):
    """The 1.5 x IQR drop count must be logged."""
    import logging

    out_path = tmp_path / "cleaned.csv"
    with caplog.at_level(logging.INFO, logger="src.data.loader"):
        load_and_clean(tiny_fixture, out_path)
    assert any(
        "Outlier removal" in rec.message and "dropped 1" in rec.message
        for rec in caplog.records
    ), caplog.text


def test_unknown_element_warning(tmp_path, tiny_fixture, caplog):
    """Unknown elements must trigger a warning log."""
    import logging

    out_path = tmp_path / "cleaned.csv"
    with caplog.at_level(logging.WARNING, logger="src.data.loader"):
        load_and_clean(tiny_fixture, out_path)
    assert any(
        rec.levelno == logging.WARNING
        and "Unknown element" in rec.getMessage()
        for rec in caplog.records
    ), caplog.text


def test_ram_limit_assertion(tmp_path, tiny_fixture):
    """Peak RAM recorded in the report must respect the 6 GB limit."""
    out_path = tmp_path / "cleaned.csv"
    report_path = tmp_path / "report.json"
    summary = load_and_clean(tiny_fixture, out_path, report_path)
    assert summary["peak_ram_bytes"] <= RAM_LIMIT_BYTES
    assert summary["ram_within_limit"] is True
    with open(report_path) as f:
        on_disk = json.load(f)
    assert on_disk["peak_ram_bytes"] <= RAM_LIMIT_BYTES
    assert on_disk["rows_read"] == 13
    assert on_disk["rows_kept"] == len(VALID_ROWS)


def test_missing_required_column_raises(tmp_path):
    """A dataset without the hardness column must fail loudly."""
    bad = tmp_path / "bad.csv"
    bad.write_text(
        "material_id,formula,band_gap,crystal_system\n"
        "m1,Fe2O3,1.5,cubic\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="hardness"):
        load_and_clean(bad, tmp_path / "out.csv")


def test_missing_input_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_and_clean(tmp_path / "nope.csv", tmp_path / "out.csv")


def test_iqr_filter_unit():
    df = pd.DataFrame({"band_gap": [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]})
    mask = iqr_filter(df, "band_gap")
    assert mask.iloc[:5].all()
    assert not mask.iloc[5]


def test_is_known_formula():
    assert is_known_formula("Fe2O3") is True
    assert is_known_formula("Si") is True
    assert is_known_formula("FakeX") is False