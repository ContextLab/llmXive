import json
import os
from pathlib import Path

import pytest

# Import the utilities we just implemented
from code.utils.contract_validation import (
    enforce_contract,
    ContractValidationError,
    _default_contracts_dir,
)

@pytest.fixture
def temp_contract_dir(tmp_path):
    """
    Create a temporary contracts directory with a simple schema.
    """
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir()
    # Simple schema: requires a string field "name" and an integer field "value"
    schema = {
        "type": "object",
        "required": ["name", "value"],
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "integer"},
        },
    }
    schema_path = contracts_dir / "test_schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    return contracts_dir

@pytest.fixture
def temp_artifact(tmp_path):
    """
    Create a temporary JSON artifact that conforms to the test schema.
    """
    artifact = {"name": "example", "value": 42}
    artifact_path = tmp_path / "test_schema.json"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    return artifact_path

def test_enforce_contract_success(temp_contract_dir, temp_artifact, monkeypatch):
    """
    enforce_contract should succeed when the artifact matches the schema.
    """
    # Patch the default contracts directory to point at our temporary location
    monkeypatch.setattr(
        "code.utils.contract_validation._default_contracts_dir", temp_contract_dir
    )
    # Should not raise
    assert enforce_contract(temp_artifact) is True

def test_enforce_contract_failure_missing_field(temp_contract_dir, tmp_path, monkeypatch):
    """
    enforce_contract should raise ContractValidationError when required fields are missing.
    """
    # Patch contracts dir
    monkeypatch.setattr(
        "code.utils.contract_validation._default_contracts_dir", temp_contract_dir
    )
    # Create an invalid artifact (missing 'value')
    invalid_artifact = {"name": "example"}
    invalid_path = tmp_path / "test_schema.json"
    invalid_path.write_text(json.dumps(invalid_artifact), encoding="utf-8")

    with pytest.raises(ContractValidationError) as excinfo:
        enforce_contract(invalid_path)
    # The error details should contain a message about the missing required field
    assert any("Missing required field" in msg for msg in excinfo.value.details)