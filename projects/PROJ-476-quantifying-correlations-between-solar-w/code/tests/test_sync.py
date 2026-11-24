"""
Test suite for the data synchronisation module (code/data/sync.py).

The tests cover two scenarios:
1. Normal operation using the CI fixture (monthly_sample.csv).  The
   synchronisation pipeline should fall back to this fixture when the
   expected raw files are missing, produce a CSV that conforms to the
   dataset schema and contains no NaNs.
2. Gap handling – a synthetic but *real‑format* raw ACE/NOAA pair is
   created with a short (≤ 6 h) missing interval.  After synchronisation
   the rows belonging to the gap must be present, have
   ``interpolated_flag == True`` and contain interpolated numeric values.
"""

import json
import pathlib
import tempfile

import pandas as pd
import pytest
from jsonschema import validate, ValidationError

from code.data.sync import run_sync
from llmxive_toolkit import paths

# Load the JSON schema that defines the expected columns and types.
SCHEMA_PATH = pathlib.Path("contracts/dataset.schema.yaml")
with open(SCHEMA_PATH, "r") as f:
    DATASET_SCHEMA = json.load(f)


def _validate_csv_schema(csv_path: pathlib.Path) -> None:
    """Validate a CSV file against ``contracts/dataset.schema.yaml``."""
    df = pd.read_csv(csv_path)
    # Convert the DataFrame to a list of JSON‑compatible records.
    records = df.to_dict(orient="records")
    for rec in records:
        # ``jsonschema`` expects the timestamp to be a string; pandas may
        # have already parsed it – ensure correct type.
        if not isinstance(rec["timestamp"], str):
            rec["timestamp"] = str(rec["timestamp"])
        validate(instance=rec, schema=DATASET_SCHEMA)


def test_sync_uses_fixture_and_validates_schema(tmp_path: pathlib.Path):
    """
    Verify that ``run_sync`` falls back to the CI fixture when the raw
    files are absent, writes the output CSV, and that the CSV conforms
    to the dataset schema with no missing values.
    """
    # Ensure the default raw locations do not exist.
    raw_ace = pathlib.Path("data/raw/ace_raw.csv")
    raw_noaa = pathlib.Path("data/raw/noaa_raw.csv")
    if raw_ace.is_file():
        raw_ace.unlink()
    if raw_noaa.is_file():
        raw_noaa.unlink()

    output_path = tmp_path / "synced.csv"
    result_path = run_sync(output_path=output_path)

    # The function should return the exact path we supplied.
    assert result_path == output_path
    assert output_path.is_file()

    # Load the CSV and perform schema validation.
    _validate_csv_schema(output_path)

    # The fixture contains a complete month with no gaps, therefore
    # every ``interpolated_flag`` must be False.
    df = pd.read_csv(output_path)
    assert not df["interpolated_flag"].any()


def _create_raw_csvs_with_gap(tmp_dir: pathlib.Path):
    """
    Helper that writes two minimal raw CSV files (ACE and NOAA) with a
    three‑hour missing interval (≤ 6 h).  The timestamps are UTC and
    hourly.  The missing rows are simply omitted from the files.
    """
    # Base timestamps for a single day.
    base = pd.date_range("2003-10-01 00:00", periods=24, freq="1h", tz="UTC")

    # Create ACE data – drop hours 5,6,7 to simulate a gap.
    ace_df = pd.DataFrame(
        {
            "timestamp": base.delete([5, 6, 7]),
            "N_p": 5.0,
            "T_p": 85000,
            "He2+_ratio": 0.045,
        }
    )
    ace_path = tmp_dir / "ace_raw.csv"
    ace_df.to_csv(ace_path, index=False)

    # Create NOAA data – also drop the same hours.
    noaa_df = pd.DataFrame(
        {
            "timestamp": base.delete([5, 6, 7]),
            "Kp": 2,
            "Dst": -5,
        }
    )
    noaa_path = tmp_dir / "noaa_raw.csv"
    noaa_df.to_csv(noaa_path, index=False)

    return ace_path, noaa_path


def test_sync_interpolates_short_gap(tmp_path: pathlib.Path):
    """
    Ensure that gaps ≤ MAX_GAP_HOURS are kept, flagged, and linearly
    interpolated.  After synchronisation the rows belonging to the gap
    must exist, have ``interpolated_flag == True`` and contain numeric
    values (i.e. NaNs have been filled).
    """
    ace_path, noaa_path = _create_raw_csvs_with_gap(tmp_path)

    output_path = tmp_path / "synced_gap.csv"
    run_sync(ace_path=ace_path, noaa_path=noaa_path, output_path=output_path)

    df = pd.read_csv(output_path)

    # The output must contain the full 24‑hour series.
    assert len(df) == 24

    # Identify rows that were originally missing (hours 5‑7).
    gap_mask = df["timestamp"].str.contains(
        r"2003-10-01 (05|06|07):00:00"
    )
    assert gap_mask.sum() == 3

    # Those rows must be flagged as interpolated.
    assert df.loc[gap_mask, "interpolated_flag"].all()

    # After interpolation there must be no NaNs in the numeric columns.
    numeric_cols = [
        "proton_density",
        "temperature",
        "helium_abundance",
        "Kp",
        "Dst",
    ]
    assert not df[numeric_cols].isna().any().any()

    # Finally, validate the whole file against the schema.
    _validate_csv_schema(output_path)