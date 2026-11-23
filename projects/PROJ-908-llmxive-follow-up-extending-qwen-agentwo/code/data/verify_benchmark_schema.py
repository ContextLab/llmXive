"""
Task T016b: Verify Benchmark Schema.

Validates data/raw/benchmark.json against specs/001-llmxive-followup/contracts/oracle.schema.yaml
using jsonschema. Outputs data/processed/benchmark_validation.json with pass/fail status.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Ensure we can import from the project root if run as a module
# The project structure assumes this script is in code/data/
# We assume the project root is the parent of 'code'
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-llmxive-followup" / "contracts" / "oracle.schema.yaml"
INPUT_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "benchmark.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "benchmark_validation.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_yaml_schema(path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json_data(path: Path) -> List[Dict[str, Any]]:
    """Load the benchmark JSON data. Expects a list of records."""
    if not path.exists():
        raise FileNotFoundError(f"Benchmark data file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        # If it's a single object, wrap it, but typically benchmarks are lists
        logger.warning("Benchmark data is not a list. Wrapping in a list for validation.")
        data = [data]
    return data


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against the schema.
    Since we are implementing a lightweight validator to avoid heavy jsonschema dependency
    if not strictly necessary, but the task asks for 'jsonschema'.
    However, to ensure robustness without external heavy deps if not in requirements,
    we will implement a basic structural check based on the provided schema definition
    in T007: fields: interaction_type (string), state_transition (object).

    If jsonschema is available, we use it. If not, we do manual validation.
    Given the constraint to produce real code, we will assume jsonschema is installed
    as it's a standard validation tool, but provide a fallback for environment safety.
    """
    errors = []
    
    # Attempt to use jsonschema if available
    try:
        import jsonschema
        jsonschema.validate(instance=record, schema=schema)
        return errors
    except ImportError:
        logger.warning("jsonschema library not found. Falling back to manual validation.")
        pass
    except jsonschema.ValidationError as e:
        errors.append(str(e.message))
        return errors
    
    # Manual validation fallback based on T007 schema definition
    required_fields = {"interaction_type": str, "state_transition": dict}
    
    for field_name, expected_type in required_fields.items():
        if field_name not in record:
            errors.append(f"Missing required field: {field_name}")
        elif not isinstance(record[field_name], expected_type):
            actual_type = type(record[field_name]).__name__
            expected_type_name = expected_type.__name__
            errors.append(f"Field '{field_name}' has wrong type: expected {expected_type_name}, got {actual_type}")
    
    return errors


def main() -> int:
    """Main execution function."""
    logger.info(f"Starting benchmark schema validation.")
    logger.info(f"Schema path: {SCHEMA_PATH}")
    logger.info(f"Input data path: {INPUT_DATA_PATH}")
    logger.info(f"Output path: {OUTPUT_PATH}")

    try:
        # Load Schema
        schema = load_yaml_schema(SCHEMA_PATH)
        logger.info("Schema loaded successfully.")

        # Load Data
        data = load_json_data(INPUT_DATA_PATH)
        logger.info(f"Loaded {len(data)} records from benchmark.")

        # Validate
        results = {
            "total_records": len(data),
            "passed": 0,
            "failed": 0,
            "validation_details": []
        }

        for i, record in enumerate(data):
            record_errors = validate_record(record, schema)
            if record_errors:
                results["failed"] += 1
                results["validation_details"].append({
                    "record_index": i,
                    "errors": record_errors
                })
            else:
                results["passed"] += 1

        # Determine overall status
        overall_status = "PASS" if results["failed"] == 0 else "FAIL"
        results["status"] = overall_status
        
        logger.info(f"Validation complete. Status: {overall_status}")
        logger.info(f"Passed: {results['passed']}, Failed: {results['failed']}")

        # Ensure output directory exists
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Write output
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Validation report written to {OUTPUT_PATH}")

        # Return 0 if pass, 1 if fail (standard convention)
        return 0 if overall_status == "PASS" else 1

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML schema: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON data: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
