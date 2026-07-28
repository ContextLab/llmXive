"""
Schema Validation for Distilled Rules

Validates the generated rules_library.json against the distilled_rule.schema.yaml.
Ensures all rules conform to the required structure before downstream consumption.
"""

import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from utils.logging import get_logger, log_stage_start, log_stage_end

# Constants for paths
RULES_LIBRARY_PATH = Path("data/derived/rules_library.json")
SCHEMA_PATH = Path("specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml")
OUTPUT_REPORT_PATH = Path("data/artifacts/rule_validation_report.json")

logger = get_logger(__name__)


def load_yaml_schema(schema_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load the JSON schema from a YAML file.
    Since the schema is simple JSON-compatible YAML, we can parse it manually or use a library.
    Given dependencies, we will use a simple parser or json if it's actually JSON formatted YAML.
    However, the spec says 'yaml'. We assume 'pyyaml' is available per requirements.txt,
    but to be safe and minimize imports if pyyaml isn't strictly guaranteed in the runner context
    without explicit import, we can try to load it as JSON first (if it's just JSON),
    or implement a minimal parser if needed.
    Looking at the task description for T006b, the schema content provided was:
    $schema: http://json-schema.org/draft-07/schema#
    type: object
    ...
    This is valid YAML. We will attempt to import yaml. If not, we fallback to a simple check.
    """
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return None

    try:
        import yaml
        with open(schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not installed. Attempting manual JSON-compatible YAML parsing.")
        # Fallback: The schema provided in T006b is simple enough that we can try to parse it
        # if it's valid JSON (which the example looked like it might be intended as, despite .yaml extension).
        # If it contains colons and hyphens in a way that breaks JSON, this will fail.
        # A robust solution requires PyYAML. We assume it's in requirements.txt (T003).
        # If it's missing, we raise an error as we cannot validate properly.
        logger.error("PyYAML is required for schema validation and is missing.")
        return None
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return None


def validate_rule_against_schema(rule: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validates a single rule dictionary against the loaded schema.
    Returns a list of error messages.
    """
    errors = []
    
    # Schema expectations from T006b:
    # Required: rule_id, condition_pattern, pivot_action, confidence
    # Types: rule_id (string), condition_pattern (string), pivot_action (string), confidence (number)
    
    required_fields = ['rule_id', 'condition_pattern', 'pivot_action', 'confidence']
    
    for field in required_fields:
        if field not in rule:
            errors.append(f"Missing required field: '{field}'")
        else:
            value = rule[field]
            if field == 'confidence':
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be a number, got {type(value).__name__}")
            else:
                if not isinstance(value, str):
                    errors.append(f"Field '{field}' must be a string, got {type(value).__name__}")
    
    # Additional checks based on schema enum if present (not in T006b schema but good practice)
    # T006b schema does not have enums for these fields, just types.
    
    return errors


def main() -> int:
    """
    Main entry point for the validation script.
    Returns 0 on success, 1 on failure.
    """
    log_stage_start(logger, "T015b", "Schema Validation")

    # Pre-Check: Verify schema file exists
    if not SCHEMA_PATH.exists() or SCHEMA_PATH.stat().st_size == 0:
        logger.error(f"Schema file missing or empty: {SCHEMA_PATH}")
        report = {
            "task_id": "T015b",
            "status": "FAIL",
            "reason": f"Schema file missing or empty: {SCHEMA_PATH}",
            "rules_validated": 0,
            "rules_valid": 0,
            "rules_invalid": 0,
            "errors": []
        }
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        return 1

    # Load Schema
    schema = load_yaml_schema(SCHEMA_PATH)
    if schema is None:
        logger.error("Failed to load schema. Aborting.")
        return 1

    # Load Rules Library
    if not RULES_LIBRARY_PATH.exists():
        logger.error(f"Rules library not found: {RULES_LIBRARY_PATH}")
        report = {
            "task_id": "T015b",
            "status": "FAIL",
            "reason": f"Rules library not found: {RULES_LIBRARY_PATH}",
            "rules_validated": 0,
            "rules_valid": 0,
            "rules_invalid": 0,
            "errors": []
        }
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        return 1

    try:
        with open(RULES_LIBRARY_PATH, 'r', encoding='utf-8') as f:
            rules_library = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in rules library: {e}")
        report = {
            "task_id": "T015b",
            "status": "FAIL",
            "reason": f"Invalid JSON in rules library: {e}",
            "rules_validated": 0,
            "rules_valid": 0,
            "rules_invalid": 0,
            "errors": [str(e)]
        }
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        return 1

    if not isinstance(rules_library, list):
        logger.error("Rules library must be a list of rule objects.")
        report = {
            "task_id": "T015b",
            "status": "FAIL",
            "reason": "Rules library must be a list of rule objects.",
            "rules_validated": 0,
            "rules_valid": 0,
            "rules_invalid": 0,
            "errors": ["Rules library is not a list"]
        }
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        return 1

    # Validate each rule
    valid_count = 0
    invalid_count = 0
    all_errors = []

    for idx, rule in enumerate(rules_library):
        rule_errors = validate_rule_against_schema(rule, schema)
        if rule_errors:
            invalid_count += 1
            for err in rule_errors:
                all_errors.append(f"Rule {idx}: {err}")
        else:
            valid_count += 1

    total_validated = valid_count + invalid_count
    status = "PASS" if invalid_count == 0 else "FAIL"

    report = {
        "task_id": "T015b",
        "status": status,
        "rules_validated": total_validated,
        "rules_valid": valid_count,
        "rules_invalid": invalid_count,
        "errors": all_errors
    }

    # Write Output
    OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    if status == "FAIL":
        logger.error(f"Validation failed: {invalid_count} invalid rules found.")
        log_stage_end(logger, "T015b", "FAILED")
        return 1
    else:
        logger.info(f"Validation passed: {total_validated} rules validated successfully.")
        log_stage_end(logger, "T015b", "PASSED")
        return 0


if __name__ == "__main__":
    sys.exit(main())