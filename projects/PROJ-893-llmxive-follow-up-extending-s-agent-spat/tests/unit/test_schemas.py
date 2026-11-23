"""
Unit tests for schema contract validation.
Ensures that generated data artifacts conform to the defined YAML schemas.
"""
import json
import yaml
import pytest
from pathlib import Path
import jsonschema

# Resolve paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-symbolic-spatial-reasoning" / "contracts"

# Load schemas
@pytest.fixture(scope="module")
def dataset_schema():
    with open(CONTRACTS_DIR / "dataset.schema.yaml", "r") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def solver_output_schema():
    with open(CONTRACTS_DIR / "solver_output.schema.yaml", "r") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def benchmark_result_schema():
    with open(CONTRACTS_DIR / "benchmark_result.schema.yaml", "r") as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def latency_log_schema():
    with open(CONTRACTS_DIR / "latency_log.schema.yaml", "r") as f:
        return yaml.safe_load(f)

def validate_against_schema(data, schema):
    """Helper to validate a dictionary against a schema."""
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, None
    except jsonschema.ValidationError as e:
        return False, str(e.message)

class TestDatasetSchema:
    def test_valid_dataset_record(self, dataset_schema):
        valid_record = {
            "scene_id": "scene_0001",
            "prompt": "How many cubes are to the left of the sphere?",
            "ground_truth": {
                "answer": 3,
                "answer_type": "counting"
            },
            "objects": [
                {
                    "id": "obj_1",
                    "type": "cube",
                    "position": [1.0, 0.0, 0.0]
                },
                {
                    "id": "obj_2",
                    "type": "sphere",
                    "position": [5.0, 0.0, 0.0]
                }
            ],
            "spatial_constraints": [
                {
                    "relation": "left_of",
                    "entities": ["obj_1", "obj_2"]
                }
            ]
        }
        is_valid, error = validate_against_schema(valid_record, dataset_schema)
        assert is_valid, f"Valid record failed validation: {error}"

    def test_invalid_scene_id_format(self, dataset_schema):
        invalid_record = {
            "scene_id": "invalid_id",
            "prompt": "Test",
            "ground_truth": {"answer": 1, "answer_type": "counting"},
            "objects": [],
            "spatial_constraints": []
        }
        is_valid, error = validate_against_schema(invalid_record, dataset_schema)
        assert not is_valid

    def test_missing_required_fields(self, dataset_schema):
        invalid_record = {
            "scene_id": "scene_0001",
            # Missing prompt, ground_truth, objects, spatial_constraints
        }
        is_valid, error = validate_against_schema(invalid_record, dataset_schema)
        assert not is_valid

class TestSolverOutputSchema:
    def test_valid_solved_record(self, solver_output_schema):
        valid_record = {
            "scene_id": "scene_0001",
            "prediction": 3,
            "status": "solved",
            "solver_latency_ms": 125.4,
            "constraint_count": 5,
            "variable_count": 2
        }
        is_valid, error = validate_against_schema(valid_record, solver_output_schema)
        assert is_valid, f"Valid record failed validation: {error}"

    def test_valid_no_solution_record(self, solver_output_schema):
        valid_record = {
            "scene_id": "scene_0002",
            "prediction": None,
            "status": "no_solution",
            "solver_latency_ms": 45.0,
            "constraint_count": 3,
            "variable_count": 1
        }
        is_valid, error = validate_against_schema(valid_record, solver_output_schema)
        assert is_valid

    def test_invalid_status(self, solver_output_schema):
        invalid_record = {
            "scene_id": "scene_0001",
            "prediction": 1,
            "status": "unknown_status",
            "solver_latency_ms": 10.0,
            "constraint_count": 1,
            "variable_count": 1
        }
        is_valid, error = validate_against_schema(invalid_record, solver_output_schema)
        assert not is_valid

class TestBenchmarkResultSchema:
    def test_valid_benchmark_record(self, benchmark_result_schema):
        valid_record = {
            "scene_id": "scene_0001",
            "ground_truth": 3,
            "solver_prediction": 3,
            "vlm_prediction": 4,
            "solver_correct": True,
            "vlm_correct": False,
            "match_type": "solver_only",
            "failure_category": "none",
            "solver_latency_ms": 100.0,
            "vlm_latency_ms": 2500.0
        }
        is_valid, error = validate_against_schema(valid_record, benchmark_result_schema)
        assert is_valid, f"Valid record failed validation: {error}"

    def test_invalid_match_type(self, benchmark_result_schema):
        invalid_record = {
            "scene_id": "scene_0001",
            "ground_truth": 3,
            "solver_prediction": 3,
            "vlm_prediction": 3,
            "solver_correct": True,
            "vlm_correct": True,
            "match_type": "invalid_type",
            "failure_category": "none",
            "solver_latency_ms": 100.0,
            "vlm_latency_ms": 2500.0
        }
        is_valid, error = validate_against_schema(invalid_record, benchmark_result_schema)
        assert not is_valid

class TestLatencyLogSchema:
    def test_valid_latency_record(self, latency_log_schema):
        valid_record = {
            "scene_id": "scene_0001",
            "component": "solving",
            "duration_ms": 150.5,
            "timestamp": "2023-10-27T10:00:00Z"
        }
        is_valid, error = validate_against_schema(valid_record, latency_log_schema)
        assert is_valid, f"Valid record failed validation: {error}"

    def test_invalid_component(self, latency_log_schema):
        invalid_record = {
            "scene_id": "scene_0001",
            "component": "unknown_component",
            "duration_ms": 10.0,
            "timestamp": "2023-10-27T10:00:00Z"
        }
        is_valid, error = validate_against_schema(invalid_record, latency_log_schema)
        assert not is_valid
