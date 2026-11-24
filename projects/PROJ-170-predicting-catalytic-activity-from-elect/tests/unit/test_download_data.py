import json
from pathlib import Path

from code.download_data import (
    PARQUET_FILE,
    MP_DESCRIPTORS_FILE,
    REQUIRED_COLUMNS_FILE,
    CHECKSUM_FILE,
    compute_file_hash,
    load_expected_checksums,
)

def test_files_exist():
    # Ensure the three core output files were created
    assert PARQUET_FILE.exists()
    assert MP_DESCRIPTORS_FILE.exists()
    assert REQUIRED_COLUMNS_FILE.exists()

def test_checksums_recorded():
    # Load the checksum registry and verify entries for each file
    checksums = load_expected_checksums()
    for path in (PARQUET_FILE, MP_DESCRIPTORS_FILE, REQUIRED_COLUMNS_FILE):
        assert path.name in checksums
        # Verify that the recorded hash matches the actual file hash
        assert checksums[path.name] == compute_file_hash(path)

def test_required_columns_schema():
    with open(REQUIRED_COLUMNS_FILE, "r") as f:
        cols = json.load(f)
    expected = [
        "catalyst_id",
        "composition",
        "surface_facet",
        "synthesis_condition",
        "d_band_center",
        "p_band_center",
        "bader_charges",
        "activation_barrier",
        "reaction_energy",
        "experimental_tof",
        "temperature",
        "pressure",
    ]
    assert cols == expected