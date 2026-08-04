"""
Rule Library Validation Script for llmXive Follow-up.

Validates the generated rules_library.json against the distilled_rule.schema.yaml.
Specifically checks for the presence of an "Unstructured" or "Manual Review" fallback rule
to ensure all failure cases have a prescribed action.

Dependencies:
  - specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml
  - data/derived/rules_library.json
"""

import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

# Paths
SCHEMA_PATH = project_root / "specs" / "001-llmxive-followup" / "contracts" / "distilled_rule.schema.yaml"
RULES_LIBRARY_PATH = project_root / "data" / "derived" / "rules_library.json"
OUTPUT_REPORT_PATH = project_root / "data" / "artifacts" / "rule_validation_report.json"

def load_yaml_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a YAML schema file.
    Note: Uses a simple parser for the expected schema structure to avoid heavy dependencies
    if pyyaml is not strictly available, though it is in requirements.
    """
    import yaml
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    return schema

def validate_rule_against_schema(rule: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validates a single rule object against the provided JSON Schema definition.
    Returns a list of error messages.
    """
    errors = []
    
    # Basic JSON Schema draft-07 validation logic for the specific schema structure
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    for field in required_fields:
        if field not in rule:
            errors.append(f"Missing required field: '{field}'")
    
    for field, value in rule.items():
        if field in properties:
            prop_def = properties[field]
            expected_type = prop_def.get('type')
            
            if expected_type == 'string':
                if not isinstance(value, str):
                    errors.append(f"Field '{field}' must be a string, got {type(value).__name__}")
            elif expected_type == 'number' or expected_type == 'float':
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be a number, got {type(value).__name__}")
            elif expected_type == 'boolean':
                if not isinstance(value, bool):
                    errors.append(f"Field '{field}' must be a boolean, got {type(value).__name__}")
            
            # Check enum if present
            if 'enum' in prop_def:
                if value not in prop_def['enum']:
                    errors.append(f"Field '{field}' value '{value}' not in allowed enum: {prop_def['enum']}")
        else:
            # Optional: warn on unknown fields? For now, just skip.
            pass
    
    return errors

def check_unstructured_fallback(rules: List[Dict[str, Any]]) -> bool:
    """
    Checks if the rule library contains a fallback rule for 'Unstructured' cases
    or a 'Manual Review' action.
    """
    has_unstructured = False
    has_manual_review = False
    
    for rule in rules:
        # Check condition pattern for Unstructured
        condition = rule.get('condition_pattern', '')
        action = rule.get('pivot_action', '')
        
        # Case-insensitive check for "Unstructured" in condition or as a specific feature type
        if 'unstructured' in condition.lower() or 'Unstructured' in condition:
            has_unstructured = True
        
        # Check for Manual Review action
        if 'manual review' in action.lower() or action == 'Manual Review':
            has_manual_review = True
    
    return has_unstructured or has_manual_review

def main():
    log_stage_start("validate_rules")
    
    report = {
        "is_valid": False,
        "errors": [],
        "coverage_status": "unknown",
        "unstructured_fallback_present": False,
        "rule_count": 0,
        "validation_timestamp": None
    }
    
    # Pre-check: Schema existence
    if not SCHEMA_PATH.exists():
        error_msg = f"Schema file missing: {SCHEMA_PATH}"
        logger.error(error_msg)
        report["errors"].append(error_msg)
        report["coverage_status"] = "FAIL"
        # Write report even on failure
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    
    # Load Schema
    try:
        schema = load_yaml_schema(SCHEMA_PATH)
        logger.info(f"Loaded schema from {SCHEMA_PATH}")
    except Exception as e:
        error_msg = f"Failed to load schema: {e}"
        logger.error(error_msg)
        report["errors"].append(error_msg)
        report["coverage_status"] = "FAIL"
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    
    # Check Rules Library existence
    if not RULES_LIBRARY_PATH.exists():
        error_msg = f"Rules library file missing: {RULES_LIBRARY_PATH}"
        logger.error(error_msg)
        report["errors"].append(error_msg)
        report["coverage_status"] = "FAIL"
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    
    # Load Rules
    try:
        with open(RULES_LIBRARY_PATH, 'r', encoding='utf-8') as f:
            rules_library = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in rules library: {e}"
        logger.error(error_msg)
        report["errors"].append(error_msg)
        report["coverage_status"] = "FAIL"
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    
    if not isinstance(rules_library, list):
        error_msg = "Rules library must be a JSON array of rule objects."
        logger.error(error_msg)
        report["errors"].append(error_msg)
        report["coverage_status"] = "FAIL"
        OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    
    report["rule_count"] = len(rules_library)
    
    # Validate each rule
    all_valid = True
    for idx, rule in enumerate(rules_library):
        rule_errors = validate_rule_against_schema(rule, schema)
        if rule_errors:
            all_valid = False
            for err in rule_errors:
                report["errors"].append(f"Rule {idx}: {err}")
    
    if not all_valid:
        report["is_valid"] = False
        logger.warning(f"Validation failed with {len(report['errors'])} errors.")
    else:
        logger.info("All rules passed schema validation.")
    
    # T075 Logic: Check for Unstructured/Manual Review fallback
    fallback_present = check_unstructured_fallback(rules_library)
    report["unstructured_fallback_present"] = fallback_present
    
    if not fallback_present:
        error_msg = "CRITICAL: No 'Unstructured' or 'Manual Review' fallback rule found. All failure cases must have a prescribed action."
        logger.error(error_msg)
        report["errors"].append(error_msg)
        report["is_valid"] = False
        report["coverage_status"] = "FAIL"
    else:
        logger.info("Unstructured/Manual Review fallback rule confirmed.")
    
    # Coverage Check (Rule Coverage per failure type)
    # Count rules by condition pattern category (heuristic based on keywords)
    categories = {
        "Syntactic": 0,
        "Logical": 0,
        "Semantic": 0,
        "Missing": 0,
        "Unstructured": 0
    }
    
    for rule in rules_library:
        cond = rule.get('condition_pattern', '').lower()
        if 'syntax' in cond or 'error' in cond:
            categories["Syntactic"] += 1
        elif 'loop' in cond or 'recursive' in cond:
            categories["Logical"] += 1
        elif 'ambiguity' in cond or 'semantic' in cond:
            categories["Semantic"] += 1
        elif 'missing' in cond or 'context' in cond:
            categories["Missing"] += 1
        elif 'unstructured' in cond:
            categories["Unstructured"] += 1
    
    # Check if coverage is sufficient (at least one rule per category that has data, 
    # but for this check we ensure Unstructured is present if needed)
    # The task specifically mandates Unstructured fallback.
    # We also check if the library is empty.
    if len(rules_library) == 0:
        report["coverage_status"] = "FAIL"
        report["errors"].append("Rule library is empty.")
    elif not fallback_present:
        report["coverage_status"] = "FAIL"
    else:
        # If we have rules and the fallback is present, we consider coverage valid for this task
        # unless the schema validation failed.
        if all_valid:
            report["coverage_status"] = "PASS"
        else:
            report["coverage_status"] = "FAIL"
    
    # Set final validity
    if all_valid and fallback_present and len(rules_library) > 0:
        report["is_valid"] = True
    else:
        report["is_valid"] = False
    
    # Write Report
    OUTPUT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {OUTPUT_REPORT_PATH}")
    
    if not report["is_valid"]:
        logger.error("Validation FAILED. Exiting with code 1.")
        sys.exit(1)
    
    logger.info("Validation PASSED.")
    log_stage_end("validate_rules")
    sys.exit(0)

if __name__ == "__main__":
    main()