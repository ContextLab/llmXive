"""Tests for T015 contract validation."""
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft7Validator

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))

from validate_contracts import validate_contract, CONTRACTS


@pytest.mark.parametrize("rel", CONTRACTS)
def test_contract_files_exist(rel):
    assert (Path(__file__).resolve().parents[1] / rel).is_file()


@pytest.mark.parametrize("rel", CONTRACTS)
def test_contract_yaml_parses(rel):
    root = Path(__file__).resolve().parents[1]
    schema = yaml.safe_load((root / rel).read_text(encoding="utf-8"))
    assert isinstance(schema, dict)


@pytest.mark.parametrize("rel", CONTRACTS)
def test_contract_is_valid_json_schema(rel):
    root = Path(__file__).resolve().parents[1]
    schema = yaml.safe_load((root / rel).read_text(encoding="utf-8"))
    Draft7Validator.check_schema(schema)  # raises on invalid schema


def test_validate_contract_reports_success():
    root = Path(__file__).resolve().parents[1]
    result = validate_contract(root / "contracts/dataset.schema.yaml")
    assert result["valid_yaml"] is True
    assert result["valid_json_schema_draft07"] is True


def test_validate_contract_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        validate_contract(Path("contracts/does_not_exist.schema.yaml"))