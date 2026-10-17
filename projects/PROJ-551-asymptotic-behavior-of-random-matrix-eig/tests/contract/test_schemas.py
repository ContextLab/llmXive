import json
import pathlib
import pytest
import yaml
import jsonschema
from jsonschema import Draft7Validator, RefResolver

# Paths to the schema files
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SIM_SCHEMA_PATH = CONTRACTS_DIR / "simulation_run.schema.yaml"
EIG_SCHEMA_PATH = CONTRACTS_DIR / "eigenvalue_result.schema.yaml"
AGG_SCHEMA_PATH = CONTRACTS_DIR / "aggregated_threshold.schema.yaml"

def load_schema(path: pathlib.Path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

SIM_SCHEMA = load_schema(SIM_SCHEMA_PATH)
EIG_SCHEMA = load_schema(EIG_SCHEMA_PATH)
AGG_SCHEMA = load_schema(AGG_SCHEMA_PATH)

def test_schema_files_exist():
    """All three contract schema files must be present."""
    assert SIM_SCHEMA_PATH.is_file()
    assert EIG_SCHEMA_PATH.is_file()
    assert AGG_SCHEMA_PATH.is_file()

def test_processed_json_files():
    """Validate every JSON file in data/processed/ against the appropriate schema."""
    processed_dir = PROJECT_ROOT / "data" / "processed"
    assert processed_dir.is_dir(), f"Processed data directory missing: {processed_dir}"

    # Resolver that can resolve relative $ref references among the contract files
    resolver = RefResolver(base_uri=f"file://{CONTRACTS_DIR}/", referrer=SIM_SCHEMA)

    for file_path in processed_dir.iterdir():
        if file_path.suffix.lower() != ".json":
            continue  # Skip non‑JSON files

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Choose schema based on content
        if isinstance(data, dict) and "eigenvalues" in data:
            # Full SimulationRun record
            validator = Draft7Validator(SIM_SCHEMA, resolver=resolver)
            validator.validate(data)
        elif isinstance(data, dict) and {"run_id", "eigenvalue_index", "value",
                                        "is_outlier", "theoretical_bbp", "deviation"}.issubset(data.keys()):
            # Stand‑alone EigenvalueResult object
            validator = Draft7Validator(EIG_SCHEMA)
            validator.validate(data)
        else:
            # For other JSON structures (e.g., aggregated threshold info) we skip validation
            # but ensure the file is not empty.
            assert data, f"JSON file {file_path} is empty or malformed."

def test_processed_csv_files():
    """If CSV files exist, ensure they contain the required columns for aggregated thresholds."""
    processed_dir = PROJECT_ROOT / "data" / "processed"
    required_cols = {
        "N", "k", "pattern_type", "total_runs", "outlier_count",
        "outlier_probability", "mean_deviation", "std_deviation",
        "theta_c_estimate", "theta_c_confidence"
    }
    for file_path in processed_dir.iterdir():
        if file_path.suffix.lower() != ".csv":
            continue
        # Simple column header check
        with open(file_path, "r", encoding="utf-8") as f:
            header = f.readline().strip()
        cols = {col.strip() for col in header.split(",")}
        missing = required_cols - cols
        assert not missing, f"CSV {file_path.name} is missing columns: {missing}"

# The test suite will pass if no assertion is raised.