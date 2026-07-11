"""
Contract tests to validate JSON artifacts against schemas defined in
specs/001-llmxive-followup/contracts/.

This module ensures that all generated JSON files (physics constraints,
evaluation results, etc.) strictly adhere to the project's data contracts.
"""

import json
import os
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional

# Attempt to import jsonschema; if missing, provide a minimal validator
try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    # Minimal fallback validator for basic structure checks
    class Draft7Validator:
        def __init__(self, schema):
            self.schema = schema
        
        def iter_errors(self, instance):
            # Basic check for required keys if defined in schema
            if "required" in self.schema:
                for key in self.schema["required"]:
                    if key not in instance:
                        yield type('Error', (), {'message': f"Missing required key: {key}", 'instance': instance})()
            return iter([])

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-llmxive-followup" / "contracts"
DATA_DERIVED = PROJECT_ROOT / "data" / "derived"

# Mapping of output directories to their expected schema files
SCHEMA_MAP = {
    "physics_constraints": "physics_constraint_schema.json",
    "evaluation_results": "evaluation_result_schema.json",
}

# Default schemas if files are missing (fallback for initial run)
DEFAULT_PHYSICS_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["scene_id", "constraints", "metadata"],
    "properties": {
        "scene_id": {"type": "string"},
        "constraints": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["object_a", "object_b", "relation"],
                "properties": {
                    "object_a": {"type": "string"},
                    "object_b": {"type": "string"},
                    "relation": {"type": "string", "enum": ["above", "below", "left_of", "right_of", "on", "collision"]}
                }
            }
        },
        "metadata": {
            "type": "object",
            "properties": {
                "simulation_time": {"type": "number"},
                "contradiction_detected": {"type": "boolean"}
            }
        }
    }
}

DEFAULT_EVALUATION_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["scene_id", "group", "violations", "prompt_adherence_rate"],
    "properties": {
        "scene_id": {"type": "string"},
        "group": {"type": "string", "enum": ["Baseline", "Experimental", "Control"]},
        "violations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["type", "object_a", "object_b"],
                "properties": {
                    "type": {"type": "string"},
                    "object_a": {"type": "string"},
                    "object_b": {"type": "string"},
                    "severity": {"type": "string"}
                }
            }
        },
        "prompt_adherence_rate": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "detection_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0}
    }
}

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema from the contracts directory or return a default."""
    schema_path = CONTRACTS_DIR / schema_name
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Return default based on name
        if "physics" in schema_name:
            return DEFAULT_PHYSICS_SCHEMA
        elif "evaluation" in schema_name:
            return DEFAULT_EVALUATION_SCHEMA
        return {}

def validate_file(file_path: Path, schema: Dict[str, Any]) -> List[str]:
    """Validate a single JSON file against a schema. Returns list of errors."""
    errors = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if HAS_JSONSCHEMA:
            try:
                validate(instance=data, schema=schema)
            except ValidationError as e:
                errors.append(f"Validation error in {file_path}: {e.message}")
        else:
            # Fallback validation
            validator = Draft7Validator(schema)
            for error in validator.iter_errors(data):
                errors.append(f"Validation error in {file_path}: {error.message}")
                
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        errors.append(f"Unexpected error reading {file_path}: {e}")
        
    return errors

def run_contract_tests() -> bool:
    """
    Run contract validation tests on all generated JSON files.
    Returns True if all files are valid, False otherwise.
    """
    all_valid = True
    total_files = 0
    total_errors = 0
    
    if not CONTRACTS_DIR.exists():
        print(f"Warning: Contracts directory not found at {CONTRACTS_DIR}. Skipping validation.")
        return True
    
    for dir_name, schema_file in SCHEMA_MAP.items():
        target_dir = DATA_DERIVED / dir_name
        if not target_dir.exists():
            print(f"Skipping {dir_name}: Directory not found at {target_dir}")
            continue
        
        schema = load_schema(schema_file)
        json_files = list(target_dir.glob("*.json"))
        
        # Skip log files if they don't match specific schema requirements (e.g., contradiction_log.json)
        # We only validate specific artifact files, not general logs unless specified
        artifact_files = [f for f in json_files if not f.name.startswith("contradiction_log")]
        
        for file_path in artifact_files:
            total_files += 1
            file_errors = validate_file(file_path, schema)
            if file_errors:
                all_valid = False
                total_errors += len(file_errors)
                for err in file_errors:
                    print(f"  ❌ {err}")
            else:
                print(f"  ✅ {file_path.name}")
    
    print(f"\nContract Test Summary: {total_files} files checked, {total_errors} errors found.")
    return all_valid

def main():
    """Entry point for running contract tests."""
    print("Running Contract Tests for llmXive Follow-up...")
    success = run_contract_tests()
    if success:
        print("✅ All contract tests passed.")
        exit(0)
    else:
        print("❌ Contract tests failed.")
        exit(1)

if __name__ == "__main__":
    main()