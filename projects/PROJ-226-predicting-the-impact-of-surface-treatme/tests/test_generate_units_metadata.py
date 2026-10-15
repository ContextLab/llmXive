"""
Test suite for ``code/generate_units_metadata.py``.
It verifies that the script creates the expected JSON files and
raises ``UnitMismatchError`` when a required column is missing.
"""

import json
from pathlib import Path

import pytest

from llmxive_toolkit import paths

# Import the module under test
from code.generate_units_metadata import main, UnitMismatchError

def _setup_minimal_raw_csv(tmp_path: Path) -> Path:
    """Create a minimal CSV with all required columns."""
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    csv_path = raw_dir / "test_source.csv"
    csv_path.write_text(
        "plasma_power_w,exposure_time_s,chemical_concentration_pct,"
        "polymer_surface_energy,substrate_roughness_nm,adhesion_strength_mj_m2,"
        "treatment_type,pair_id\\n"
        "150,30,5,42.5,120,1.8,Oxygen Plasma,PP_Al\\n"
    )
    return csv_path

def test_generate_units_metadata_success(tmp_path):
    """The script should create a <source>_units.json file with correct content."""
    csv_path = _setup_minimal_raw_csv(tmp_path)

    # Run the script
    main()

    json_path = csv_path.with_name("test_source_units.json")
    assert json_path.is_file(), "Unit metadata JSON was not created."

    # Verify JSON content
    with json_path.open() as f:
        data = json.load(f)

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
    assert data == expected_units

def test_missing_required_column_raises(tmp_path):
    """If a required column is missing the script must raise UnitMismatchError."""
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    csv_path = raw_dir / "bad_source.csv"
    # Omit ``exposure_time_s`` deliberately
    csv_path.write_text(
        "plasma_power_w,chemical_concentration_pct,polymer_surface_energy,"
        "substrate_roughness_nm,adhesion_strength_mj_m2,treatment_type,pair_id\\n"
        "150,5,42.5,120,1.8,Oxygen Plasma,PP_Al\\n"
    )

    with pytest.raises(UnitMismatchError) as excinfo:
        main()
    assert "missing required columns" in str(excinfo.value).lower()