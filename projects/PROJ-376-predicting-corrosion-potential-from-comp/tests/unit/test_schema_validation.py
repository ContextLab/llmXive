"""
Unit tests for Schema Contracts (T004).
Verifies that the YAML schemas are valid and enforce expected constraints.
"""
import os
import sys
import yaml
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger

logger = get_logger(__name__)

class TestSchemaContracts:
    """Tests for the schema contract files."""

    @pytest.fixture
    def contracts_dir(self):
        return project_root / "contracts"

    def test_ingest_schema_exists(self, contracts_dir):
        """Test that ingest.schema.yaml exists."""
        path = contracts_dir / "ingest.schema.yaml"
        assert path.exists(), "ingest.schema.yaml must exist"

    def test_dataset_schema_exists(self, contracts_dir):
        """Test that dataset.schema.yaml exists."""
        path = contracts_dir / "dataset.schema.yaml"
        assert path.exists(), "dataset.schema.yaml must exist"

    def test_ingest_schema_is_valid_yaml(self, contracts_dir):
        """Test that ingest.schema.yaml is valid YAML."""
        path = contracts_dir / "ingest.schema.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert "$schema" in schema or "title" in schema, "Schema must have metadata"

    def test_dataset_schema_is_valid_yaml(self, contracts_dir):
        """Test that dataset.schema.yaml is valid YAML."""
        path = contracts_dir / "dataset.schema.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert "properties" in schema, "Schema must define properties"

    def test_dataset_schema_enforces_min_records(self, contracts_dir):
        """Test that dataset schema enforces min 500 records."""
        path = contracts_dir / "dataset.schema.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        # Check metadata minItems
        metadata_props = schema.get("properties", {}).get("metadata", {}).get("properties", {})
        total_records_def = metadata_props.get("total_records", {})
        assert total_records_def.get("minimum") == 500, "total_records must have minimum 500"

        # Check records array minItems
        records_def = schema.get("properties", {}).get("records", {})
        assert records_def.get("minItems") == 500, "records array must have minItems 500"

    def test_ingest_schema_has_required_fields(self, contracts_dir):
        """Test that ingest schema defines required fields."""
        path = contracts_dir / "ingest.schema.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        required_fields = schema.get("required", [])
        assert "record_id" in required_fields, "record_id is required in ingest schema"
        assert "alloy_composition" in required_fields, "alloy_composition is required"
        assert "environment_conditions" in required_fields, "environment_conditions is required"
        assert "corrosion_measurement" in required_fields, "corrosion_measurement is required"

    def test_dataset_schema_has_non_null_constraints(self, contracts_dir):
        """Test that dataset schema implies non-null constraints (via required fields)."""
        path = contracts_dir / "dataset.schema.yaml"
        with open(path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        # Check that 'records' items have required fields
        items_props = schema.get("properties", {}).get("records", {}).get("items", {})
        item_required = items_props.get("required", [])
        
        # Key fields that must be non-null per T009/T014
        critical_fields = ["record_id", "specific_alloy_designation_id", "target_mv", "ph", "temp_c"]
        for field in critical_fields:
            assert field in item_required, f"{field} must be required in dataset schema"