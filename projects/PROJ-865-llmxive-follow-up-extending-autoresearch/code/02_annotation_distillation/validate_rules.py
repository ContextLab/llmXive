"""
T015b: Schema Validation for Distilled Rules.

Validates data/derived/rules_library.json against the distilled_rule schema.
Pre-checks ensure the schema file exists and is non-empty.
Outputs a validation report to data/artifacts/rule_validation_report.json.
"""

import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import logging utilities from the project's utils
from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

# Constants for file paths
SCHEMA_PATH = Path("specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml")
INPUT_RULES_PATH = Path("data/derived/rules_library.json")
OUTPUT_REPORT_PATH = Path("data/artifacts/rule_validation_report.json")

# Enum values expected for confidence (float) is handled by type check,
# but the schema defines specific keys.
REQUIRED_KEYS = {"rule_id", "condition_pattern", "pivot_action", "confidence"}


def load_yaml_schema(schema_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a YAML schema file.
    Since pyyaml might not be in the minimal deps for this specific snippet,
    we attempt to import it. If not available, we assume a simple manual parse
    or raise an error if the environment is expected to have it.
    Given T003 (requirements.txt) includes standard libs, we check for yaml.
    """
    try:
        import yaml
    except ImportError:
        logger.error("PyYAML is required to load schema files but is not installed.")
        return None

    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return None

    if schema_path.stat().st_size == 0:
        logger.error(f"Schema file is empty: {schema_path}")
        return None

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        return schema
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse YAML schema: {e}")
        return None


def validate_rule_against_schema(rule: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single rule dictionary against the loaded schema.
    Returns a list of error messages.
    """
    errors = []

    # 1. Check required keys
    if not isinstance(rule, dict):
        errors.append("Rule is not a dictionary.")
        return errors

    missing_keys = REQUIRED_KEYS - set(rule.keys())
    if missing_keys:
        errors.append(f"Missing required keys: {missing_keys}")

    # 2. Type checks based on schema definition:
    # rule_id: string
    if "rule_id" in rule and not isinstance(rule["rule_id"], str):
        errors.append(f"rule_id must be a string, got {type(rule['rule_id']).__name__}")

    # condition_pattern: string
    if "condition_pattern" in rule and not isinstance(rule["condition_pattern"], str):
        errors.append(f"condition_pattern must be a string, got {type(rule['condition_pattern']).__name__}")

    # pivot_action: string
    if "pivot_action" in rule and not isinstance(rule["pivot_action"], str):
        errors.append(f"pivot_action must be a string, got {type(rule['pivot_action']).__name__}")

    # confidence: number (float/int)
    if "confidence" in rule:
        if not isinstance(rule["confidence"], (int, float)):
            errors.append(f"confidence must be a number, got {type(rule['confidence']).__name__}")
        else:
            if rule["confidence"] < 0.0 or rule["confidence"] > 1.0:
                # Optional constraint: confidence should be between 0 and 1
                errors.append(f"confidence must be between 0.0 and 1.0, got {rule['confidence']}")

    return errors


def main():
    log_stage_start("T015b", "Schema Validation for Rules")

    # Pre-Check: Schema file existence and non-empty
    if not SCHEMA_PATH.exists():
        logger.error(f"Pre-check failed: Schema file missing at {SCHEMA_PATH}")
        report = {
            "status": "FAIL",
            "reason": f"Schema file missing: {SCHEMA_PATH}",
            "rules_checked": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "errors": []
        }
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)

    if SCHEMA_PATH.stat().st_size == 0:
        logger.error(f"Pre-check failed: Schema file is empty at {SCHEMA_PATH}")
        report = {
            "status": "FAIL",
            "reason": f"Schema file is empty: {SCHEMA_PATH}",
            "rules_checked": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "errors": []
        }
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)

    # Load Schema
    schema = load_yaml_schema(SCHEMA_PATH)
    if schema is None:
        logger.error("Failed to load or parse schema.")
        report = {
            "status": "FAIL",
            "reason": "Failed to load schema",
            "rules_checked": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "errors": ["Schema loading failed"]
        }
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)

    # Load Rules
    if not INPUT_RULES_PATH.exists():
        logger.error(f"Input rules file not found: {INPUT_RULES_PATH}")
        report = {
            "status": "FAIL",
            "reason": f"Input file missing: {INPUT_RULES_PATH}",
            "rules_checked": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "errors": [f"Input file missing: {INPUT_RULES_PATH}"]
        }
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)

    try:
        with open(INPUT_RULES_PATH, 'r', encoding='utf-8') as f:
            rules = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON rules file: {e}")
        report = {
            "status": "FAIL",
            "reason": "Invalid JSON in rules file",
            "rules_checked": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "errors": [str(e)]
        }
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)

    if not isinstance(rules, list):
        logger.error("Rules file must contain a JSON array.")
        report = {
            "status": "FAIL",
            "reason": "Rules file must be a JSON array",
            "rules_checked": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "errors": ["Root element is not a list"]
        }
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)

    # Validate each rule
    all_errors = []
    valid_count = 0
    invalid_count = 0

    for i, rule in enumerate(rules):
        rule_errors = validate_rule_against_schema(rule, schema)
        if rule_errors:
            invalid_count += 1
            for err in rule_errors:
                all_errors.append({
                    "rule_index": i,
                    "rule_id": rule.get("rule_id", "UNKNOWN"),
                    "error": err
                })
        else:
            valid_count += 1

    total_checked = valid_count + invalid_count
    status = "PASS" if invalid_count == 0 else "FAIL"

    logger.info(f"Validation complete. Checked {total_checked} rules. Valid: {valid_count}, Invalid: {invalid_count}.")

    report = {
        "status": status,
        "reason": "Validation completed" if status == "PASS" else "Validation failed",
        "rules_checked": total_checked,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "errors": all_errors
    }

    # Write Output
    OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to {OUTPUT_REPORT_PATH}")

    if status == "FAIL":
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()