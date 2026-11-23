import pytest
import yaml
from pathlib import Path
from code.aggregate import load_filtered_data, update_metadata

# Load the schema definition (assumed to be in contracts/dataset.schema.yaml)
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")

@pytest.fixture(scope="module")
def valid_metadata():
    # Load the current metadata.yaml for validation
    with open(Path("data/metadata.yaml"), "r") as f:
        return yaml.safe_load(f)

def test_dataset_schema_structure():
    # Ensure the metadata file contains required top‑level keys
    metadata = valid_metadata()
    required_keys = {"project", "data", "models", "analysis", "paths"}
    assert required_keys.issubset(metadata.keys()), "Missing top‑level keys in metadata.yaml"

def test_dataset_schema_with_sample_data():
    # Verify that a minimal valid dataset entry conforms to expectations
    sample = {
        "galaxy_id": "galaxy123",
        "r": [1.0, 2.0, 3.0],
        "v": [100, 150, 200],
        "v_err": [5, 5, 5],
        "inclination": 45,
        "inclination_err": 2.0
    }
    # The actual schema validation logic would be in contract tests;
    # here we just ensure the sample dict can be turned into a DataFrame
    df = pd.DataFrame(sample)
    assert not df.empty
    assert list(df.columns) == ["galaxy_id", "r", "v", "v_err", "inclination", "inclination_err"]