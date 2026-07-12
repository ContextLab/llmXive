"""
Contract tests to enforce schema validation on all generated data.

This module validates that:
1. Benchmark tasks match benchmark_task.schema.yaml
2. Trajectory logs match trajectory_log.schema.yaml
3. Simulator states match simulator_state.schema.yaml

It uses jsonschema to validate JSON files against the defined schemas.
"""

import json
import os
import sys
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError, SchemaError
import yaml

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / "code"
specs_dir = project_root / "specs"

sys.path.insert(0, str(project_root))

from config.linting import get_project_root

# Schema file paths (relative to project root)
BENCHMARK_SCHEMA_PATH = specs_dir / "001-tutorial-bias-analysis" / "benchmark_task.schema.yaml"
TRAJECTORY_SCHEMA_PATH = specs_dir / "001-tutorial-bias-analysis" / "trajectory_log.schema.yaml"
STATE_SCHEMA_PATH = specs_dir / "001-tutorial-bias-analysis" / "simulator_state.schema.yaml"

# Data directories
DATA_BENCHMARKS = project_root / "data" / "benchmarks"
DATA_RESULTS = project_root / "data" / "results"
DATA_RAW = project_root / "data" / "raw"

def load_schema(schema_path: Path) -> dict:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def load_json_data(file_path: Path) -> list | dict:
    """Load a JSON data file. Handles both list and dict formats."""
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_data_against_schema(data, schema: dict, schema_name: str) -> None:
    """Validate data against a schema. Raises ValidationError if invalid."""
    try:
        # If data is a list, validate each item
        if isinstance(data, list):
            for i, item in enumerate(data):
                validate(instance=item, schema=schema)
        else:
            # Single object validation
            validate(instance=data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Validation failed for {schema_name}: {e.message} at path: {list(e.path)}")

# --- Benchmark Task Schema Tests ---

@pytest.fixture
def benchmark_schema():
    """Load the benchmark task schema."""
    return load_schema(BENCHMARK_SCHEMA_PATH)

@pytest.mark.parametrize("benchmark_file", [
    "benchmark_500.json",
    "benchmark_100.json",
    "linear_trajectories.json",
    "error_recovery_trajectories.json",
    "holdout_set.json"
])
def test_benchmark_task_schema(benchmark_file, benchmark_schema):
    """Validate benchmark task files against benchmark_task.schema.yaml."""
    file_path = DATA_BENCHMARKS / benchmark_file
    if not file_path.exists():
        pytest.skip(f"Data file {benchmark_file} not found. Skipping validation.")

    data = load_json_data(file_path)
    validate_data_against_schema(data, benchmark_schema, "benchmark_task.schema.yaml")

# --- Trajectory Log Schema Tests ---

@pytest.fixture
def trajectory_schema():
    """Load the trajectory log schema."""
    return load_schema(TRAJECTORY_SCHEMA_PATH)

@pytest.mark.parametrize("trajectory_file", [
    "trajectories.json",
    "trajectories_subset.json"
])
def test_trajectory_log_schema(trajectory_file, trajectory_schema):
    """Validate trajectory log files against trajectory_log.schema.yaml."""
    file_path = DATA_RESULTS / trajectory_file
    if not file_path.exists():
        pytest.skip(f"Data file {trajectory_file} not found. Skipping validation.")

    data = load_json_data(file_path)
    validate_data_against_schema(data, trajectory_schema, "trajectory_log.schema.yaml")

# --- Simulator State Schema Tests ---

@pytest.fixture
def state_schema():
    """Load the simulator state schema."""
    return load_schema(STATE_SCHEMA_PATH)

def test_simulator_state_schema(state_schema):
    """Validate simulator state files against simulator_state.schema.yaml."""
    # Look for state files in data/raw or data/results
    possible_paths = [
        DATA_RAW / "simulator_states.json",
        DATA_RESULTS / "simulator_states.json"
    ]

    found = False
    for path in possible_paths:
        if path.exists():
            found = True
            data = load_json_data(path)
            validate_data_against_schema(data, state_schema, "simulator_state.schema.yaml")
            break

    if not found:
        pytest.skip("No simulator state files found. Skipping validation.")

# --- Schema Integrity Tests ---

def test_schemas_exist():
    """Verify that all schema files exist."""
    assert BENCHMARK_SCHEMA_PATH.exists(), f"Benchmark schema missing: {BENCHMARK_SCHEMA_PATH}"
    assert TRAJECTORY_SCHEMA_PATH.exists(), f"Trajectory schema missing: {TRAJECTORY_SCHEMA_PATH}"
    assert STATE_SCHEMA_PATH.exists(), f"State schema missing: {STATE_SCHEMA_PATH}"

def test_schemas_are_valid_jsonschema():
    """Verify that schema files are valid JSON Schema documents."""
    for schema_path in [BENCHMARK_SCHEMA_PATH, TRAJECTORY_SCHEMA_PATH, STATE_SCHEMA_PATH]:
        try:
            schema = load_schema(schema_path)
            # Basic check: schema must have a type or $schema definition
            assert "$schema" in schema or "type" in schema, f"Invalid schema structure in {schema_path}"
        except (yaml.YAMLError, ValueError) as e:
            pytest.fail(f"Schema file {schema_path} is not valid YAML or JSON: {e}")

# --- Integration: Validate all generated data in one run ---

def test_all_generated_data_valid():
    """
    Run validation on all available generated data files.
    This is a convenience test to catch any schema violations across the project.
    """
    errors = []

    # Check benchmark files
    benchmark_files = list(DATA_BENCHMARKS.glob("*.json"))
    if benchmark_files:
        try:
            schema = load_schema(BENCHMARK_SCHEMA_PATH)
            for f in benchmark_files:
                try:
                    data = load_json_data(f)
                    validate_data_against_schema(data, schema, f.name)
                except Exception as e:
                    errors.append(f"{f.name}: {str(e)}")
        except Exception as e:
            errors.append(f"Schema loading failed: {str(e)}")

    # Check trajectory files
    trajectory_files = list(DATA_RESULTS.glob("trajectories*.json"))
    if trajectory_files:
        try:
            schema = load_schema(TRAJECTORY_SCHEMA_PATH)
            for f in trajectory_files:
                try:
                    data = load_json_data(f)
                    validate_data_against_schema(data, schema, f.name)
                except Exception as e:
                    errors.append(f"{f.name}: {str(e)}")
        except Exception as e:
            errors.append(f"Schema loading failed: {str(e)}")

    # Check state files
    state_files = list(DATA_RAW.glob("simulator_states*.json")) + list(DATA_RESULTS.glob("simulator_states*.json"))
    if state_files:
        try:
            schema = load_schema(STATE_SCHEMA_PATH)
            for f in state_files:
                try:
                    data = load_json_data(f)
                    validate_data_against_schema(data, schema, f.name)
                except Exception as e:
                    errors.append(f"{f.name}: {str(e)}")
        except Exception as e:
            errors.append(f"Schema loading failed: {str(e)}")

    if errors:
        pytest.fail("Schema validation errors found:\n" + "\n".join(errors))