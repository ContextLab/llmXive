"""
Rule Library Validation Script.

Validates the generated rules_library.json against the distilled_rule.schema.yaml.
Additionally, explicitly checks for the presence of an "Unstructured" or "Manual Review"
fallback rule to ensure no failure case is left without a prescribed action.
"""

import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import logging utilities from the project's utils
from utils.logging import get_logger, log_stage_start, log_stage_end

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RULES_LIBRARY_PATH = PROJECT_ROOT / "data" / "derived" / "rules_library.json"
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-llmxive-followup" / "contracts" / "distilled_rule.schema.yaml"
OUTPUT_PATH = PROJECT_ROOT / "data" / "artifacts" / "rule_validation_report.json"

logger = get_logger(__name__)


def load_yaml_schema(path: Path) -> Dict[str, Any]:
    """
    Load a YAML schema file and return it as a dictionary.
    Since PyYAML is not explicitly listed in the immediate imports of the API surface
    but is standard for schema loading, we attempt to import it.
    If not available, we raise an error as the schema format requires it.
    """
    try:
        import yaml
    except ImportError:
        logger.error("PyYAML is required to load the schema. Please install it.")
        raise

    if not path.exists():
        raise FileNotFoundError(f"Schema file not found at {path}")

    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_rule_against_schema(rule: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single rule object against the JSON schema.
    Returns a list of error messages if validation fails.
    """
    errors = []

    # Check required fields based on the schema definition provided in T006b
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    for field in required_fields:
        if field not in rule:
            errors.append(f"Missing required field: {field}")

    # Type checking for specific fields
    if 'rule_id' in rule and not isinstance(rule['rule_id'], str):
        errors.append("Field 'rule_id' must be a string")
    if 'condition_pattern' in rule and not isinstance(rule['condition_pattern'], str):
        errors.append("Field 'condition_pattern' must be a string")
    if 'pivot_action' in rule and not isinstance(rule['pivot_action'], str):
        errors.append("Field 'pivot_action' must be a string")
    if 'confidence' in rule:
        if not isinstance(rule['confidence'], (int, float)):
            errors.append("Field 'confidence' must be a number")
        elif rule['confidence'] < 0.0 or rule['confidence'] > 1.0:
            errors.append("Field 'confidence' must be between 0.0 and 1.0")

    return errors


def check_unstructured_fallback(rules: List[Dict[str, Any]]) -> bool:
    """
    Check if the rules library contains a fallback rule for 'Unstructured' or 'Manual Review'.
    Returns True if a valid fallback rule exists, False otherwise.
    """
    fallback_keywords = ["Unstructured", "Manual Review", "manual_review", "unstructured"]
    found = False

    for rule in rules:
        pivot_action = rule.get('pivot_action', '')
        # Check if the action is explicitly a fallback type
        if any(kw in pivot_action for kw in fallback_keywords):
            found = True
            logger.info(f"Found fallback rule: {rule.get('rule_id', 'unknown')} with action '{pivot_action}'")
            break

    return found


def main() -> int:
    """
    Main execution function.
    Returns 0 on success, 1 on failure.
    """
    log_stage_start("validate_rules")

    try:
        # 1. Pre-Check: Verify Schema exists
        if not SCHEMA_PATH.exists():
            logger.error(f"Schema file missing: {SCHEMA_PATH}")
            report = {
                "is_valid": False,
                "errors": [f"Schema file missing: {SCHEMA_PATH}"],
                "coverage_status": "FAIL",
                "fallback_present": False,
                "timestamp": "N/A"
            }
            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            return 1

        # 2. Load Schema
        schema = load_yaml_schema(SCHEMA_PATH)
        logger.info(f"Loaded schema from {SCHEMA_PATH}")

        # 3. Pre-Check: Verify Rules Library exists
        if not RULES_LIBRARY_PATH.exists():
            logger.error(f"Rules library file missing: {RULES_LIBRARY_PATH}")
            report = {
                "is_valid": False,
                "errors": [f"Rules library file missing: {RULES_LIBRARY_PATH}"],
                "coverage_status": "FAIL",
                "fallback_present": False,
                "timestamp": "N/A"
            }
            OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            return 1

        # 4. Load Rules Library
        with open(RULES_LIBRARY_PATH, 'r', encoding='utf-8') as f:
            rules_library = json.load(f)

        if not isinstance(rules_library, list):
            logger.error("Rules library must be a JSON array of rule objects.")
            report = {
                "is_valid": False,
                "errors": ["Rules library is not a JSON array"],
                "coverage_status": "FAIL",
                "fallback_present": False,
                "timestamp": "N/A"
            }
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            return 1

        if len(rules_library) == 0:
            logger.warning("Rules library is empty.")
            # Still check for fallback? No, if empty, no fallback exists.
            report = {
                "is_valid": False,
                "errors": ["Rules library is empty"],
                "coverage_status": "FAIL",
                "fallback_present": False,
                "timestamp": "N/A"
            }
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2)
            return 1

        # 5. Validate each rule against schema
        validation_errors = []
        for idx, rule in enumerate(rules_library):
            rule_errors = validate_rule_against_schema(rule, schema)
            if rule_errors:
                validation_errors.extend([f"Rule {idx}: {err}" for err in rule_errors])

        # 6. Check for Unstructured/Manual Review Fallback (Critical Requirement for T075)
        fallback_present = check_unstructured_fallback(rules_library)
        if not fallback_present:
            logger.error("CRITICAL: No 'Unstructured' or 'Manual Review' fallback rule found in the library.")
            logger.error("This validation MUST fail as per T075 requirements.")
            validation_errors.append("CRITICAL: Missing 'Unstructured' or 'Manual Review' fallback rule.")

        # 7. Determine overall validity
        is_valid = len(validation_errors) == 0
        coverage_status = "PASS" if is_valid else "FAIL"

        if is_valid:
            logger.info("Validation PASSED. All rules conform to schema and fallback is present.")
        else:
            logger.error(f"Validation FAILED. Found {len(validation_errors)} error(s).")

        # 8. Generate Report
        report = {
            "is_valid": is_valid,
            "errors": validation_errors,
            "coverage_status": coverage_status,
            "fallback_present": fallback_present,
            "rule_count": len(rules_library),
            "timestamp": "N/A" # Could add datetime if needed, but keeping simple
        }

        # Ensure output directory exists
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Write report to disk
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Validation report written to {OUTPUT_PATH}")

        # Return exit code based on validity
        return 0 if is_valid else 1

    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        # Write a failure report even on exception
        error_report = {
            "is_valid": False,
            "errors": [str(e)],
            "coverage_status": "FAIL",
            "fallback_present": False,
            "timestamp": "N/A"
        }
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(error_report, f, indent=2)
        return 1
    finally:
        log_stage_end("validate_rules")


if __name__ == "__main__":
    sys.exit(main())