import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from utils.logging import get_logger, log_stage_start, log_stage_end

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logger = get_logger(__name__)

RULES_LIBRARY_PATH = Path("data/derived/rules_library.json")
SCHEMA_PATH = Path("specs/001-llmxive-followup/contracts/distilled_rule.schema.yaml")
OUTPUT_PATH = Path("data/artifacts/rule_validation_report.json")

def load_yaml_schema(schema_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load and parse the YAML schema file.
    Returns the schema dictionary or None if the file is missing/empty.
    """
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        return None
    
    try:
        import yaml
        with open(schema_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                logger.error(f"Schema file is empty: {schema_path}")
                return None
            schema = yaml.safe_load(content)
            return schema
    except Exception as e:
        logger.error(f"Failed to load schema {schema_path}: {e}")
        return None

def validate_rule_against_schema(rule: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single rule against the provided JSON schema.
    Returns a list of validation error messages.
    """
    errors = []
    
    # Required fields from the schema definition
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required fields
    for field in required_fields:
        if field not in rule:
            errors.append(f"Missing required field: '{field}'")
    
    # Type checking for existing fields
    for field, value in rule.items():
        if field in properties:
            expected_type = properties[field].get('type')
            enum_values = properties[field].get('enum')
            
            # Handle 'number' type which covers both int and float
            if expected_type == 'number':
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' must be a number (int or float), got {type(value).__name__}")
            elif expected_type == 'string':
                if not isinstance(value, str):
                    errors.append(f"Field '{field}' must be a string, got {type(value).__name__}")
                elif enum_values and value not in enum_values:
                    errors.append(f"Field '{field}' value '{value}' not in allowed enum: {enum_values}")
            elif expected_type == 'boolean':
                if not isinstance(value, bool):
                    errors.append(f"Field '{field}' must be a boolean, got {type(value).__name__}")
            elif expected_type == 'array':
                if not isinstance(value, list):
                    errors.append(f"Field '{field}' must be a list, got {type(value).__name__}")
            elif expected_type == 'object':
                if not isinstance(value, dict):
                    errors.append(f"Field '{field}' must be an object, got {type(value).__name__}")
        # else: Field not in schema properties, could warn but not strictly an error based on schema
    
    return errors

def main():
    log_stage_start("T015b", "Schema Validation")
    
    # Pre-check: Ensure schema exists and is not empty
    schema = load_yaml_schema(SCHEMA_PATH)
    if schema is None:
        logger.critical("Schema validation failed: Schema file missing or empty.")
        report = {
            "status": "FAIL",
            "reason": "Schema file missing or empty",
            "schema_path": str(SCHEMA_PATH),
            "rules_validated": 0,
            "total_errors": 0,
            "errors": []
        }
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        log_stage_end("T015b", "Failed")
        sys.exit(1)
    
    # Check if rules library exists
    if not RULES_LIBRARY_PATH.exists():
        logger.critical(f"Rules library not found: {RULES_LIBRARY_PATH}")
        report = {
            "status": "FAIL",
            "reason": f"Rules library not found at {RULES_LIBRARY_PATH}",
            "schema_path": str(SCHEMA_PATH),
            "rules_validated": 0,
            "total_errors": 0,
            "errors": []
        }
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        log_stage_end("T015b", "Failed")
        sys.exit(1)
    
    # Load rules library
    try:
        with open(RULES_LIBRARY_PATH, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        if not isinstance(rules, list):
            rules = [rules]
    except json.JSONDecodeError as e:
        logger.critical(f"Failed to parse rules library: {e}")
        report = {
            "status": "FAIL",
            "reason": f"Invalid JSON in rules library: {e}",
            "schema_path": str(SCHEMA_PATH),
            "rules_validated": 0,
            "total_errors": 1,
            "errors": [{"rule_index": 0, "error": str(e)}]
        }
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        log_stage_end("T015b", "Failed")
        sys.exit(1)
    
    logger.info(f"Validating {len(rules)} rules against schema...")
    
    all_errors = []
    valid_count = 0
    invalid_count = 0
    
    for idx, rule in enumerate(rules):
        rule_errors = validate_rule_against_schema(rule, schema)
        if rule_errors:
            invalid_count += 1
            for err in rule_errors:
                all_errors.append({
                    "rule_index": idx,
                    "rule_id": rule.get("rule_id", "unknown"),
                    "error": err
                })
        else:
            valid_count += 1
    
    status = "PASS" if invalid_count == 0 else "FAIL"
    logger.info(f"Validation complete. Status: {status}. Valid: {valid_count}, Invalid: {invalid_count}")
    
    report = {
        "status": status,
        "schema_path": str(SCHEMA_PATH),
        "rules_library_path": str(RULES_LIBRARY_PATH),
        "rules_validated": len(rules),
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "total_errors": len(all_errors),
        "errors": all_errors
    }
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {OUTPUT_PATH}")
    
    log_stage_end("T015b", "Completed")
    
    # Exit with error code if validation failed
    if status == "FAIL":
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()