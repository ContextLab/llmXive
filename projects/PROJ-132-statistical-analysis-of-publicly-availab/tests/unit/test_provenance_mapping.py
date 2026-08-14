import pytest
import json
import hashlib
from pathlib import Path
import polars as pl
import tempfile
import shutil

from src.data.preprocess import generate_provenance


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def test_generate_provenance_creates_correct_schema(temp_data_dir):
    """Test that generate_provenance creates a JSON file with the correct schema."""
    # Create sample DataFrame
    df = pl.DataFrame(
        {
            "checklist_id": ["CHK001", "CHK002", "CHK003"],
            "species": ["SpeciesA", "SpeciesB", "SpeciesA"],
            "grid_cell": ["lat_0.0_lon_0.0", "lat_0.5_lon_0.5", "lat_0.0_lon_0.5"],
        }
    )

    output_path = Path(temp_data_dir) / "row_mapping.json"
    generate_provenance(df, str(output_path))

    # Verify file exists
    assert output_path.exists(), "Provenance mapping file was not created"

    # Load and validate JSON
    with open(output_path, "r", encoding="utf-8") as f:
        provenance = json.load(f)

    assert isinstance(provenance, list), "Provenance mapping should be a list"
    assert len(provenance) == 3, f"Expected 3 rows, got {len(provenance)}"

    # Check schema
    required_keys = {"processed_row_id", "original_checklist_id", "species", "grid_cell"}
    for record in provenance:
        assert set(record.keys()) == required_keys, f"Record missing keys: {record.keys()}"

    # Verify processed_row_id is a SHA256 hash of checklist_id + index
    for idx, record in enumerate(provenance):
        expected_hash_input = f"{record['original_checklist_id']}{idx}".encode("utf-8")
        expected_hash = hashlib.sha256(expected_hash_input).hexdigest()
        assert record["processed_row_id"] == expected_hash, f"Hash mismatch for row {idx}"


def test_generate_provenance_empty_dataframe(temp_data_dir):
    """Test that generate_provenance handles empty DataFrame."""
    df = pl.DataFrame(
        {
            "checklist_id": [],
            "species": [],
            "grid_cell": [],
        }
    )

    output_path = Path(temp_data_dir) / "row_mapping.json"
    generate_provenance(df, str(output_path))

    with open(output_path, "r", encoding="utf-8") as f:
        provenance = json.load(f)

    assert provenance == [], "Empty DataFrame should produce empty provenance list"


def test_generate_provenance_unique_hashes(temp_data_dir):
    """Test that each processed_row_id is unique."""
    df = pl.DataFrame(
        {
            "checklist_id": ["CHK001", "CHK002", "CHK003", "CHK001"],
            "species": ["SpeciesA", "SpeciesB", "SpeciesA", "SpeciesC"],
            "grid_cell": ["lat_0.0_lon_0.0", "lat_0.5_lon_0.5", "lat_0.0_lon_0.5", "lat_1.0_lon_1.0"],
        }
    )

    output_path = Path(temp_data_dir) / "row_mapping.json"
    generate_provenance(df, str(output_path))

    with open(output_path, "r", encoding="utf-8") as f:
        provenance = json.load(f)

    hashes = [record["processed_row_id"] for record in provenance]
    assert len(hashes) == len(set(hashes)), "All processed_row_ids should be unique"
