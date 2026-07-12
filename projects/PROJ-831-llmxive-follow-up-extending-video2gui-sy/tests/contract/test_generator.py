"""
Contract test for benchmark_generator.py.
Verifies that the generated benchmark file matches the benchmark_task.schema.yaml.
"""
import json
import os
import sys
import pytest
from pathlib import Path
import yaml

# Add code/ to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from jsonschema import validate, ValidationError, SchemaError
from config.linting import get_project_root

# Constants
BENCHMARK_FILE = "data/benchmarks/benchmark_500.json"
SCHEMA_FILE = "specs/001-tutorial-bias/benchmark_task.schema.yaml"

def get_full_path(rel_path: str) -> Path:
    """Get absolute path relative to project root."""
    root = get_project_root()
    return root / rel_path

def load_schema() -> dict:
    """Load the JSON Schema from YAML."""
    schema_path = get_full_path(SCHEMA_FILE)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def load_benchmark_data() -> list:
    """Load the generated benchmark data."""
    data_path = get_full_path(BENCHMARK_FILE)
    if not data_path.exists():
        raise FileNotFoundError(f"Benchmark file not found: {data_path}. "
                              "Run code/generators/benchmark_generator.py first.")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Benchmark data must be a list, got {type(data)}")
    
    return data

class TestBenchmarkSchema:
    """Contract tests for benchmark task schema validation."""

    @pytest.fixture(scope="class")
    def schema(self) -> dict:
        """Load schema once for the test class."""
        return load_schema()

    @pytest.fixture(scope="class")
    def benchmark_data(self) -> list:
        """Load benchmark data once for the test class."""
        return load_benchmark_data()

    def test_schema_exists(self, schema: dict):
        """Test that schema was loaded successfully."""
        assert schema is not None
        assert "type" in schema
        assert schema["type"] == "object"

    def test_benchmark_data_loaded(self, benchmark_data: list):
        """Test that benchmark data was loaded and has expected count."""
        assert len(benchmark_data) == 500, f"Expected 500 tasks, got {len(benchmark_data)}"
        assert all(isinstance(task, dict) for task in benchmark_data)

    def test_all_tasks_match_schema(self, schema: dict, benchmark_data: list):
        """Test that every task in the benchmark matches the schema."""
        errors = []
        
        for idx, task in enumerate(benchmark_data):
            try:
                validate(instance=task, schema=schema)
            except ValidationError as e:
                errors.append({
                    "index": idx,
                    "message": e.message,
                    "path": list(e.path),
                    "instance": str(task)[:100]  # Truncate for readability
                })
        
        if errors:
            error_summary = "\n".join([
                f"Task {e['index']}: {e['message']} (path: {e['path']})"
                for e in errors[:5]  # Show first 5 errors
            ])
            pytest.fail(f"Schema validation failed for {len(errors)} tasks.\nFirst 5 errors:\n{error_summary}")

    def test_task_structure_requirements(self, benchmark_data: list):
        """Test that all tasks have required structural elements."""
        required_fields = ["id", "type", "initial_state", "error_injection_point", "recovery_path"]
        
        for idx, task in enumerate(benchmark_data):
            missing = [field for field in required_fields if field not in task]
            if missing:
                pytest.fail(f"Task {idx} missing required fields: {missing}")

    def test_task_type_values(self, benchmark_data: list):
        """Test that task.type has valid values (linear or non-linear)."""
        valid_types = {"linear", "non-linear"}
        
        for idx, task in enumerate(benchmark_data):
            task_type = task.get("type")
            if task_type not in valid_types:
                pytest.fail(f"Task {idx} has invalid type '{task_type}'. "
                          f"Expected one of {valid_types}")

    def test_error_injection_present(self, benchmark_data: list):
        """Test that every task has an error injection point."""
        for idx, task in enumerate(benchmark_data):
            error_point = task.get("error_injection_point")
            if error_point is None:
                pytest.fail(f"Task {idx} has no error_injection_point")
            if not isinstance(error_point, dict):
                pytest.fail(f"Task {idx} error_injection_point is not a dict")

    def test_recovery_path_present(self, benchmark_data: list):
        """Test that every task has a recovery path."""
        for idx, task in enumerate(benchmark_data):
            recovery = task.get("recovery_path")
            if recovery is None:
                pytest.fail(f"Task {idx} has no recovery_path")
            if not isinstance(recovery, list):
                pytest.fail(f"Task {idx} recovery_path is not a list")

    def test_unique_task_ids(self, benchmark_data: list):
        """Test that all task IDs are unique."""
        ids = [task.get("id") for task in benchmark_data]
        if len(ids) != len(set(ids)):
            pytest.fail("Duplicate task IDs found in benchmark")