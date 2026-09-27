"""
Unit tests for generated JSON/YAML schemas.
Verifies that the schemas are valid YAML and contain required fields
as per the data-model.md and task requirements.
"""
import yaml
import json
import jsonschema
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).parent.parent.parent
CONTRACTS_DIR = BASE_DIR / "contracts"

def load_schema(filename: str) -> dict:
    """Load a YAML schema from the contracts directory."""
    path = CONTRACTS_DIR / filename
    assert path.exists(), f"Schema file not found: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema: dict, required_fields: list, title: str):
    """Generic validator for schema structure."""
    assert "$schema" in schema, f"{title}: Missing $schema"
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#", \
        f"{title}: Wrong schema version"
    assert "required" in schema, f"{title}: Missing required fields"
    for field in required_fields:
        assert field in schema["required"], f"{title}: Missing required field '{field}'"
        assert "properties" in schema, f"{title}: Missing properties"
        assert field in schema["properties"], f"{title}: Property '{field}' not defined"

class TestGraphSchema:
    def test_graph_schema_exists_and_valid_yaml(self):
        """Test T006a: Verify graph.schema.yaml is valid YAML."""
        schema = load_schema("graph.schema.yaml")
        assert isinstance(schema, dict)

    def test_graph_schema_draft_7(self):
        """Test T006a: Verify JSON Schema Draft 7 compliance."""
        schema = load_schema("graph.schema.yaml")
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"

    def test_graph_schema_required_fields(self):
        """Test T006a: Verify required fields from data-model.md."""
        schema = load_schema("graph.schema.yaml")
        required = ["id", "beta", "node_count", "clustering_coeff", "edge_list", "labels", "seed"]
        validate_schema_structure(schema, required, "GraphSchema")

    def test_graph_schema_beta_constraints(self):
        """Test T006a: Verify beta constraints (0.0 to 1.0)."""
        schema = load_schema("graph.schema.yaml")
        beta_prop = schema["properties"]["beta"]
        assert beta_prop["minimum"] == 0.0
        assert beta_prop["maximum"] == 1.0

    def test_graph_schema_node_count_const(self):
        """Test T006a: Verify node_count is fixed at 110."""
        schema = load_schema("graph.schema.yaml")
        nc_prop = schema["properties"]["node_count"]
        assert nc_prop.get("const") == 110

class TestTrainingRunSchema:
    def test_training_run_schema_exists_and_valid_yaml(self):
        """Test T007: Verify training_run.schema.yaml is valid YAML."""
        schema = load_schema("training_run.schema.yaml")
        assert isinstance(schema, dict)

    def test_training_run_schema_draft_7(self):
        """Test T007: Verify JSON Schema Draft 7 compliance."""
        schema = load_schema("training_run.schema.yaml")
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"

    def test_training_run_schema_required_fields(self):
        """Test T007: Verify required fields including trajectory."""
        schema = load_schema("training_run.schema.yaml")
        required = ["id", "graph_id", "loss_type", "epochs_trained", "convergence_status", "steps_to_convergence", "trajectory"]
        validate_schema_structure(schema, required, "TrainingRunSchema")

    def test_training_run_schema_trajectory_structure(self):
        """Test T007: Verify trajectory field contains per-epoch loss/accuracy."""
        schema = load_schema("training_run.schema.yaml")
        traj_prop = schema["properties"]["trajectory"]
        assert traj_prop["type"] == "array"
        
        items = traj_prop["items"]
        assert "required" in items
        assert "loss" in items["required"]
        assert "accuracy" in items["required"]
        assert "epoch" in items["required"]

    def test_training_run_schema_convergence_status_enum(self):
        """Test T007: Verify convergence_status enum values."""
        schema = load_schema("training_run.schema.yaml")
        cs_prop = schema["properties"]["convergence_status"]
        assert "enum" in cs_prop
        assert "converged" in cs_prop["enum"]
        assert "censored" in cs_prop["enum"]

    def test_training_run_schema_json_validation(self):
        """Test T007: Validate a sample JSON instance against the schema."""
        schema = load_schema("training_run.schema.yaml")
        
        # Valid instance
        valid_instance = {
            "id": "run_12345678",
            "graph_id": "graph_001",
            "loss_type": "CrossEntropy",
            "epochs_trained": 10,
            "convergence_status": "converged",
            "steps_to_convergence": 5,
            "trajectory": [
                {"epoch": 1, "loss": 1.2, "accuracy": 0.5},
                {"epoch": 5, "loss": 0.1, "accuracy": 0.95}
            ]
        }
        
        jsonschema.validate(instance=valid_instance, schema=schema)

        # Invalid instance (missing trajectory)
        invalid_instance = {
            "id": "run_12345678",
            "graph_id": "graph_001",
            "loss_type": "CrossEntropy",
            "epochs_trained": 10,
            "convergence_status": "converged",
            "steps_to_convergence": 5
        }
        
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=invalid_instance, schema=schema)