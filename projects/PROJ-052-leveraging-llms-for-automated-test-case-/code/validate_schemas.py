"""
Schema validation module for llmXive pipeline artifacts.

Validates all output artifacts against the JSON schemas defined in contracts/
before analysis proceeds. Ensures data integrity and format compliance.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    # Fallback for environments where jsonschema might not be installed yet
    # In a real run, this should be caught and reported as a missing dependency
    print("ERROR: jsonschema library not installed. Please run: pip install jsonschema")
    sys.exit(1)

from config import get_data_dir, get_output_dir


# Mapping of artifact filenames to their corresponding schema filenames
ARTIFACT_SCHEMA_MAP = {
    "defects4j_v1.0.parquet": "dataset.schema.yaml",  # Parquet is binary, schema validation usually happens on the CSV/JSON export or metadata
    "changed_lines.json": "dataset.schema.yaml",       # Changed lines are part of dataset structure
    "coverage_metrics.csv": "coverage.schema.yaml",    # CSV structure validation
    "analysis_results.json": "analysis_result.schema.yaml",
    "generated_test_*.json": "generated_test.schema.yaml", # Wildcard for generated test metadata
}

# Specific paths relative to project root
CONTRACTS_DIR = "contracts"


def load_schema(schema_filename: str) -> Dict[str, Any]:
    """
    Load a JSON schema from the contracts directory.
    Note: The schemas are defined as YAML in the project, but jsonschema expects JSON.
    We assume the YAML schemas have been converted to JSON or we parse them.
    For this implementation, we assume the presence of .json versions or we parse YAML.
    Since the task references YAML schemas, we need a YAML parser or JSON equivalents.
    To avoid extra dependencies if not needed, we check for .json first, then .yaml.
    """
    schema_path_yaml = Path(CONTRACTS_DIR) / schema_filename
    schema_path_json = Path(CONTRACTS_DIR) / schema_filename.replace(".yaml", ".json")

    if schema_path_json.exists():
        with open(schema_path_json, "r", encoding="utf-8") as f:
            return json.load(f)
    elif schema_path_yaml.exists():
        # Try to load YAML if jsonschema is not available or if we need to parse YAML
        # We'll use a simple check: if pyyaml is available, use it.
        try:
            import yaml
            with open(schema_path_yaml, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except ImportError:
            raise RuntimeError(
                f"Schema file {schema_filename} is YAML but 'pyyaml' is not installed. "
                "Install it via 'pip install pyyaml' or provide a JSON version."
            )
    else:
        raise FileNotFoundError(f"Schema file not found: {schema_path_yaml} or {schema_path_json}")


def validate_artifact(artifact_path: Path, schema_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a single artifact against its schema.

    Args:
        artifact_path: Path to the artifact file.
        schema_name: Name of the schema file in contracts/.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not artifact_path.exists():
        return False, f"Artifact not found: {artifact_path}"

    try:
        schema = load_schema(schema_name)
    except Exception as e:
        return False, f"Failed to load schema {schema_name}: {str(e)}"

    # Handle specific file types
    if artifact_path.suffix == ".json":
        try:
            with open(artifact_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            validate(instance=data, schema=schema)
            return True, None
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in {artifact_path}: {str(e)}"
        except ValidationError as e:
            return False, f"Validation error in {artifact_path}: {e.message}"

    elif artifact_path.suffix == ".csv":
        # CSV validation is tricky with JSON Schema.
        # We assume the schema defines the expected columns and types if it were JSON.
        # For CSV, we do a basic header check if the schema has 'properties' or 'required'.
        # A more robust approach would require a CSV-specific validator or converting CSV to dict first.
        # Here we implement a basic check based on schema 'required' fields if they map to headers.
        if "required" in schema:
            try:
                import pandas as pd
                df = pd.read_csv(artifact_path)
                missing_cols = set(schema["required"]) - set(df.columns)
                if missing_cols:
                    return False, f"Missing required columns in {artifact_path}: {missing_cols}"
                # Additional type checks could be added here if schema has 'properties'
                return True, None
            except Exception as e:
                return False, f"Error reading CSV {artifact_path}: {str(e)}"
        else:
            # If no required fields in schema, assume valid for now
            return True, None

    elif artifact_path.suffix == ".parquet":
        # Parquet validation is binary. We check existence and maybe row count if schema specifies.
        # For now, we assume existence is the primary check unless schema has specific metadata.
        # A full validation would require reading the parquet and checking columns/types against schema.
        try:
            import pandas as pd
            df = pd.read_parquet(artifact_path)
            # Basic check: ensure it's not empty if schema implies data
            if schema.get("minItems", 0) > 0 and len(df) == 0:
                return False, f"Parquet file {artifact_path} is empty but schema requires data."
            return True, None
        except Exception as e:
            return False, f"Error reading Parquet {artifact_path}: {str(e)}"

    else:
        return False, f"Unsupported file type for validation: {artifact_path.suffix}"


def validate_all_artifacts() -> bool:
    """
    Validate all known output artifacts against their schemas.

    Returns:
        True if all artifacts are valid, False otherwise.
    """
    data_dir = get_data_dir()
    all_valid = True
    errors = []

    # Define artifacts to check based on the pipeline flow
    # We check for existence first, then validate
    artifacts_to_check = [
        ("data/changed_lines.json", "dataset.schema.yaml"),
        ("data/coverage_metrics.csv", "coverage.schema.yaml"),
        ("data/analysis_results.json", "analysis_result.schema.yaml"),
    ]

    # Check for generated test metadata if it exists
    generated_test_dir = Path(data_dir) / "generated_tests"
    if generated_test_dir.exists():
        for json_file in generated_test_dir.glob("*.json"):
            artifacts_to_check.append((str(json_file.relative_to(Path.cwd())), "generated_test.schema.yaml"))

    for artifact_rel_path, schema_name in artifacts_to_check:
        artifact_path = Path.cwd() / artifact_rel_path
        is_valid, error_msg = validate_artifact(artifact_path, schema_name)

        if is_valid:
            print(f"[OK] {artifact_rel_path} validated against {schema_name}")
        else:
            print(f"[FAIL] {artifact_rel_path}: {error_msg}")
            errors.append((artifact_rel_path, error_msg))
            all_valid = False

    if not all_valid:
        print("\nSchema validation failed. Please fix the errors above.")
        print("Analysis cannot proceed until all artifacts are valid.")
    else:
        print("\nAll artifacts validated successfully.")

    return all_valid


def main():
    """Entry point for schema validation."""
    print("Starting schema validation for llmXive artifacts...")
    success = validate_all_artifacts()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
