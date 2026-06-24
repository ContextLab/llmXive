import pathlib
import yaml

import pytest

# Directory containing the contract schema YAML files.
CONTRACTS_DIR = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    / "specs"
    / "001-evaluate-code-duplication-llm-understanding"
    / "contracts"
)


@pytest.mark.parametrize("schema_path", list(CONTRACTS_DIR.glob("*.schema.yaml")))
def test_schema_is_valid_yaml(schema_path: pathlib.Path):
    """Load each contract schema and verify it is a non‑empty mapping."""
    with schema_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # The schema should be a dictionary (mapping) after loading.
    assert isinstance(data, dict), f"Schema {schema_path.name} should be a mapping"

    # Basic sanity check: the schema must not be empty.
    assert data, f"Schema {schema_path.name} is empty"

    # Optional: ensure a top‑level '$schema' or 'type' key exists.
    if "$schema" not in data and "type" not in data:
        pytest.fail(
            f"Schema {schema_path.name} missing top‑level '$schema' or 'type' key"
        )
