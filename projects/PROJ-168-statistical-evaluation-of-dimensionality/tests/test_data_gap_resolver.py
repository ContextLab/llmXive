"""
Unit tests for the Data Gap Resolver (T007).

The tests verify that:
  * The resolver creates a manifest containing exactly the three required
    GEO accessions.
  * Each manifest entry conforms to the JSON schema defined in
    `specs/001-statistical-evaluation-of-dimensionality/contracts/dataset.schema.yaml`.
"""

import json
import pathlib

import pytest
from jsonschema import validate, ValidationError

from data_gap_resolver import DataGapResolver, DatasetStatus

# Path to the schema file
SCHEMA_PATH = pathlib.Path(__file__).parent.parent / "specs" / "001-statistical-evaluation-of-dimensionality" / "contracts" / "dataset.schema.yaml"

@pytest.fixture
def clean_manifest(tmp_path, monkeypatch):
    """
    Ensure a fresh manifest file for each test run.
    """
    # Redirect the Config paths to a temporary directory
    from config import Config
    temp_config = Config()
    temp_config.RAW_DATA_DIR = tmp_path / "raw"
    temp_config.RESULTS_DIR = tmp_path / "results"
    temp_config.RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    temp_config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Monkey‑patch the Config used by DataGapResolver
    monkeypatch.setattr("data_gap_resolver.Config", lambda: temp_config)

    # Ensure no pre‑existing manifest interferes
    manifest_path = pathlib.Path(__file__).parent.parent / "data" / "manifest.json"
    if manifest_path.exists():
        manifest_path.unlink()
    yield
    # Cleanup after test
    if manifest_path.exists():
        manifest_path.unlink()

def test_resolver_creates_valid_manifest(clean_manifest):
    resolver = DataGapResolver()
    status, found, missing = resolver.resolve()

    # Should have succeeded
    assert status == "enough"
    assert len(found) == 3
    assert missing == []

    # Load and inspect manifest
    manifest_path = pathlib.Path(__file__).parent.parent / "data" / "manifest.json"
    assert manifest_path.is_file()
    with manifest_path.open() as f:
        manifest = json.load(f)

    assert isinstance(manifest, list)
    assert len(manifest) == 3

    # Verify required fields and types
    for entry in manifest:
        assert entry["status"] == DatasetStatus.AVAILABLE
        assert entry["checksum"] is not None
        assert entry["raw_file_path"] is not None
        assert entry["processed_file_path"] is None

    # Validate against JSON schema
    with SCHEMA_PATH.open() as schema_file:
        schema = json.load(schema_file)
    try:
        validate(instance=manifest[0], schema=schema)
    except ValidationError as e:
        pytest.fail(f"Manifest entry does not conform to schema: {e}")
