import csv
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from config import ensure_dirs

SCHEMA_PATH = Path("contracts/correlation_result.schema.yaml")
INPUT_CSV_PATH = Path("data/results/correlation_results.csv")
OUTPUT_LOG_PATH = Path("data/results/validation_log.json")

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Loads a YAML schema. Since PyYAML might not be in minimal deps, we assume a simple structure or use yaml if available.
       However, for robustness in this specific task, we will define the expected fields directly based on the schema content
       provided in the artifact, as parsing YAML without dependencies is error-prone.
       We will hardcode the expected fields based on the schema defined in contracts/correlation_result.schema.yaml.
    """
    # Hardcoded expected fields based on the schema provided in the artifact
    return {
        "required_fields": [
            "participant_id", "age", "cognitive_score", "cognitive_instrument",
            "global_efficiency", "local_efficiency", "characteristic_path_length",
            "clustering_coefficient", "modularity",
            "age_correlation_rho", "age_correlation_pvalue", "age_correlation_pvalue_adj",
            "cognition_correlation_rho", "cognition_correlation_pvalue", "cognition_correlation_pvalue_adj",
            "signal_quality_flag", "trace_id"
        ],
        "types": {
            "participant_id": str,
            "age": int,
            "cognitive_score": (int, float, type(None)),
            "cognitive_instrument": str,
            "global_efficiency": (int, float),
            "local_efficiency": (int, float),
            "characteristic_path_length": (int, float),
            "clustering_coefficient": (int, float),
            "modularity": (int, float),
            "age_correlation_rho": (int, float),
            "age_correlation_pvalue": (int, float),
            "age_correlation_pvalue_adj": (int, float),
            "cognition_correlation_rho": (int, float),
            "cognition_correlation_pvalue": (int, float),
            "cognition_correlation_pvalue_adj": (int, float),
            "signal_quality_flag": str,
            "trace_id": str
        },
        "enum_values": {
            "signal_quality_flag": ["Good", "Low Signal Quality"]
        },
        "pattern_values": {
            "trace_id": r'^[a-f0-9]{64}$'
        }
    }

def validate_row(row: Dict[str, str], schema: Dict[str, Any]) -> List[str]:
    """Validates a single row against the schema."""
    errors = []
    required_fields = schema["required_fields"]
    types = schema["types"]
    enum_values = schema["enum_values"]
    pattern_values = schema["pattern_values"]

    # Check required fields
    for field in required_fields:
        if field not in row or row[field] is None or row[field] == "":
            # Allow cognitive_score to be empty if it's null in the dataset
            if field == "cognitive_score":
                continue
            errors.append(f"Missing required field: {field}")

    # Check types and constraints
    for field, value in row.items():
        if field not in types:
            continue

        expected_type = types[field]
        
        # Type checking
        try:
            if expected_type == int:
                int(value)
            elif expected_type == str:
                str(value)
            elif isinstance(expected_type, tuple):
                # Handle mixed types like (int, float, type(None))
                if value is None or value == "":
                    if type(None) in expected_type:
                        continue
                try:
                    float(value)
                except ValueError:
                    errors.append(f"Field {field} is not a valid number: {value}")
        except (ValueError, TypeError) as e:
            errors.append(f"Field {field} has invalid type: {value}")

        # Enum checking
        if field in enum_values:
            if value not in enum_values[field]:
                errors.append(f"Field {field} has invalid value: {value}. Expected one of {enum_values[field]}")

        # Pattern checking
        if field in pattern_values:
            import re
            if not re.match(pattern_values[field], str(value)):
                errors.append(f"Field {field} does not match pattern: {value}")

    return errors

def main():
    ensure_dirs()
    schema = load_schema(SCHEMA_PATH)
    
    if not INPUT_CSV_PATH.exists():
        print(f"Error: Input file not found: {INPUT_CSV_PATH}")
        sys.exit(1)

    validation_results = []
    total_rows = 0
    valid_rows = 0
    error_log = []

    with open(INPUT_CSV_PATH, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            total_rows += 1
            errors = validate_row(row, schema)
            if errors:
                error_log.append({
                    "row_index": i,
                    "participant_id": row.get("participant_id", "Unknown"),
                    "errors": errors
                })
            else:
                valid_rows += 1

    report = {
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "invalid_rows": total_rows - valid_rows,
        "validation_passed": total_rows > 0 and (total_rows == valid_rows),
        "errors": error_log
    }

    with open(OUTPUT_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"Validation complete: {valid_rows}/{total_rows} rows valid.")
    if report["validation_passed"]:
        print("Schema validation PASSED.")
        sys.exit(0)
    else:
        print("Schema validation FAILED.")
        print(f"See {OUTPUT_LOG_PATH} for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
