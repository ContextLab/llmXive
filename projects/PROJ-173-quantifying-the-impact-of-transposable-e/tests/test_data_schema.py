import yaml
from pathlib import Path

def test_dataset_metadata_contains_teaware_flag():
    """Contract test ensuring the mock dataset metadata declares TE‑aware quantification."""
    metadata_file = Path("data/mock/dataset_metadata.yaml")
    assert metadata_file.is_file(), f"Metadata file not found at {metadata_file}"
    with open(metadata_file, "r") as f:
        data = yaml.safe_load(f)
    # The field must exist and be exactly "TEaware"
    assert "quantification_method" in data, "Missing 'quantification_method' in metadata"
    assert data["quantification_method"] == "TEaware", (
        f"Expected quantification_method to be 'TEaware', got {data.get('quantification_method')}"
    )