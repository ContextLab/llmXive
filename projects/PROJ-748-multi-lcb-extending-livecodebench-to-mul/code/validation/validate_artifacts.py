"""
Artifact Validation Script.
Validates that generated JSON artifacts conform to their YAML schemas.
"""
import json
import sys
from pathlib import Path

import yaml
# Note: jsonschema is a standard dependency for schema validation.
# It should be present in requirements.txt.
try:
    import jsonschema
except ImportError:
    print("Error: 'jsonschema' package not found. Please install it via pip.")
    sys.exit(1)

from config import get_contracts_path, get_results_path


def load_schema(schema_path: Path) -> dict:
    """Load a YAML schema file."""
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_artifact(artifact_path: Path, schema: dict) -> bool:
    """Validate a JSON artifact against a schema."""
    if not artifact_path.exists():
        print(f"  [FAIL] Artifact not found: {artifact_path}")
        return False

    try:
        with open(artifact_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"  [FAIL] Invalid JSON in {artifact_path}: {e}")
        return False

    try:
        jsonschema.validate(instance=data, schema=schema)
        print(f"  [PASS] {artifact_path.name} conforms to schema.")
        return True
    except jsonschema.exceptions.ValidationError as e:
        print(f"  [FAIL] {artifact_path.name} validation error: {e.message}")
        print(f"    Path: {list(e.path)}")
        return False


def main():
    contracts_dir = get_contracts_path()
    results_dir = get_results_path()

    schemas = {
        "dataset": contracts_dir / "dataset.schema.yaml",
        "execution_log": contracts_dir / "execution_log.schema.yaml",
        "statistical_results": contracts_dir / "statistical_results.schema.yaml",
    }

    artifacts = {
        "dataset": results_dir / "dataset.json",
        "execution_log": results_dir / "artifacts" / "execution_log.json",
        "statistical_results": results_dir / "artifacts" / "statistical_results.json",
    }

    all_valid = True

    print("Validating artifacts against schemas...")
    print("-" * 40)

    for name, schema_path in schemas.items():
        if not schema_path.exists():
            print(f"[WARN] Schema not found: {schema_path}")
            continue

        schema = load_schema(schema_path)
        artifact_path = artifacts.get(name)

        if not artifact_path:
            print(f"[WARN] No artifact path defined for {name}")
            continue

        if not validate_artifact(artifact_path, schema):
            all_valid = False

    print("-" * 40)
    if all_valid:
        print("All artifacts validated successfully.")
        sys.exit(0)
    else:
        print("Validation failed for one or more artifacts.")
        sys.exit(1)


if __name__ == "__main__":
    main()
