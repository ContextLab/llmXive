import os
import sys
import pytest
import yaml
from pathlib import Path

# Add code directory to path for imports if needed, though this test mostly uses standard libs
CODE_DIR = Path(__file__).parent.parent.parent / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from config import get_specs_dir

SCHEMAS = [
    "stimulus.schema.yaml",
    "rating.schema.yaml",
    "analysis_ready.schema.yaml",
    "lmm_summary.schema.yaml",
    "analysis_result.schema.yaml"
]

@pytest.fixture
def contracts_dir():
    return get_specs_dir() / "001-the-impact-of-text-message-tone-on-perce" / "contracts"

@pytest.mark.parametrize("schema_file", SCHEMAS)
def test_schema_file_exists(contracts_dir, schema_file):
    """Verify that all required schema files exist in the contracts directory."""
    schema_path = contracts_dir / schema_file
    assert schema_path.exists(), f"Schema file {schema_file} is missing from {contracts_dir}"

@pytest.mark.parametrize("schema_file", SCHEMAS)
def test_schema_file_is_valid_yaml(contracts_dir, schema_file):
    """Verify that all schema files are valid YAML and can be loaded."""
    schema_path = contracts_dir / schema_file
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), f"Schema {schema_file} must be a YAML dictionary"
        assert "$schema" in schema, f"Schema {schema_file} must define a $schema"
        assert "properties" in schema, f"Schema {schema_file} must define properties"
    except yaml.YAMLError as e:
        pytest.fail(f"Schema {schema_file} is not valid YAML: {e}")

def test_all_schemas_defined(contracts_dir):
    """Ensure all expected schemas are present."""
    existing_files = [f.name for f in contracts_dir.glob("*.yaml")]
    missing = set(SCHEMAS) - set(existing_files)
    assert not missing, f"Missing schema files: {missing}"
