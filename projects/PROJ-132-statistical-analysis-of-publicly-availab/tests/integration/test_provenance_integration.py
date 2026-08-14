import pytest
import json
import polars as pl
from pathlib import Path
import tempfile
import shutil

from src.data.preprocess import run_preprocessing_pipeline


@pytest.fixture
def temp_integration_dir():
    """Create a temporary directory for integration test data."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


def test_provenance_mapping_in_full_pipeline(temp_integration_dir):
    """
    Integration test: Run full preprocessing pipeline and verify
    that provenance mapping is generated correctly.
    """
    # Create sample eBird data
    ebird_data = pl.DataFrame(
        {
            "species": ["SpeciesA", "SpeciesB", "SpeciesA", "SpeciesC"],
            "lat": [0.1, 0.6, 0.2, 1.1],
            "lon": [0.1, 0.6, 0.3, 1.2],
            "date": ["2023-03-01", "2023-03-02", "2023-03-01", "2023-03-03"],
            "count": [5, 3, 7, 2],
            "checklist_id": ["CHK001", "CHK002", "CHK003", "CHK004"],
        }
    )

    input_path = Path(temp_integration_dir) / "ebird_sample.parquet"
    output_path = Path(temp_integration_dir) / "preprocessed_data.parquet"
    migratory_list_path = Path(temp_integration_dir) / "migratory_list.json"

    # Create migratory species list
    with open(migratory_list_path, "w", encoding="utf-8") as f:
        json.dump({"species": ["SpeciesA", "SpeciesB", "SpeciesC"]}, f)

    # Save input data
    ebird_data.write_parquet(str(input_path))

    # Run preprocessing pipeline
    run_preprocessing_pipeline(
        input_path=str(input_path),
        output_path=str(output_path),
        migratory_list_path=str(migratory_list_path),
        min_obs=1,
    )

    # Verify preprocessed data exists
    assert output_path.exists(), "Preprocessed data file was not created"

    # Verify provenance mapping exists
    provenance_path = Path(temp_integration_dir) / "row_mapping.json"
    assert provenance_path.exists(), "Provenance mapping file was not created"

    # Load and validate provenance
    with open(provenance_path, "r", encoding="utf-8") as f:
        provenance = json.load(f)

    assert isinstance(provenance, list), "Provenance mapping should be a list"
    assert len(provenance) > 0, "Provenance mapping should not be empty"

    # Verify schema
    required_keys = {"processed_row_id", "original_checklist_id", "species", "grid_cell"}
    for record in provenance:
        assert set(record.keys()) == required_keys, f"Record missing keys: {record.keys()}"

    # Verify that checklist_ids in provenance match those in input data
    input_checklist_ids = set(ebird_data["checklist_id"].to_list())
    provenance_checklist_ids = {record["original_checklist_id"] for record in provenance}
    assert input_checklist_ids == provenance_checklist_ids, "Checklist IDs mismatch between input and provenance"