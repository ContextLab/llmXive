"""
Test suite for ``code/generate_units_metadata.py``.

The test creates a temporary CSV file containing the exact required
columns, invokes the ``main`` function, and checks that the corresponding
``*_units.json`` file is written with the expected unit mapping.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

# Import the module under test
from generate_units_metadata import main, UnitMismatchError
from llmxive_toolkit import paths


@pytest.fixture
def temp_raw_csv(tmp_path: Path):
    """Create a temporary raw CSV file with the required schema."""
    raw_dir = paths.data("raw")
    # Ensure the test works even if the directory already exists
    raw_dir.mkdir(parents=True, exist_ok=True)

    csv_path = raw_dir / "temp_test_source.csv"
    data = {
        "plasma_power_w": [100, 150],
        "exposure_time_s": [20, 30],
        "chemical_concentration_pct": [5, 10],
        "polymer_surface_energy": [40.0, 42.5],
        "substrate_roughness_nm": [120, 95],
        "adhesion_strength_mj_m2": [1.8, 2.3],
        "treatment_type": ["Oxygen Plasma", "Nitrogen Plasma"],
        "pair_id": ["PP_Al", "PE_Cu"],
    }
    pd.DataFrame(data).to_csv(csv_path, index=False)
    yield csv_path
    # Cleanup after test
    if csv_path.exists():
        csv_path.unlink()
    json_path = raw_dir / "temp_test_source_units.json"
    if json_path.exists():
        json_path.unlink()


def test_generate_units_metadata_success(temp_raw_csv: Path):
    """The script should create a JSON unit‑metadata file for a valid CSV."""
    # Ensure no leftover JSON from previous runs
    json_path = temp_raw_csv.with_name("temp_test_source_units.json")
    if json_path.exists():
        json_path.unlink()

    # Run the main workflow
    try:
        main()
    except UnitMismatchError as e:
        pytest.fail(f"Unexpected UnitMismatchError raised: {e}")

    # Verify that the JSON file was created
    assert json_path.is_file(), "Unit metadata JSON file was not created."

    # Load and validate the content
    with json_path.open("r", encoding="utf-8") as f:
        units = json.load(f)

    expected_units = {
        "plasma_power_w": "W",
        "exposure_time_s": "s",
        "chemical_concentration_pct": "%",
        "polymer_surface_energy": "mJ/m^2",
        "substrate_roughness_nm": "nm",
        "adhesion_strength_mj_m2": "MJ/m^2",
        "treatment_type": "category",
        "pair_id": "category",
    }

    assert units == expected_units, "Unit mapping does not match expected values."