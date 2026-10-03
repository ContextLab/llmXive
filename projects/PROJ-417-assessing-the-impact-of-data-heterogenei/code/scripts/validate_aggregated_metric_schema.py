"""
Script to validate the aggregated_metric.schema.yaml and verify it against a dummy record.
This satisfies the verification requirement for T004c.
"""
import os
import json
import sys
import yaml
from pathlib import Path

# Add project root to path to allow imports if needed, though this script is standalone logic
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def main():
    schema_path = project_root / "specs" / "001-assess-heterogeneity-impact" / "contracts" / "aggregated_metric.schema.yaml"
    output_dir = project_root / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "schema_aggregated_metric_validation.json"

    logger = None
    try:
        from utils.logging import get_logger
        logger = get_logger(__name__)
    except ImportError:
        logger = None

    def log(msg):
        if logger:
            logger.info(msg)
        else:
            print(msg)

    log(f"Validating schema at: {schema_path}")
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    # Load Schema
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    log("Schema loaded successfully.")
    log(f"Schema keys: {list(schema.keys())}")
    log(f"Required fields: {schema.get('required', [])}")

    # Dummy Record per Task Specification
    dummy_record = {
        "tau2_level": 0.1,
        "coverage_rate": 0.94,
        "mean_bias": 0.02,
        "p_value_binomial": 0.35,
        "p_value_normality_test": 0.12,
        "test_type_bias_comparison": "Kruskal-Wallis"
    }

    # Validate using jsonschema
    try:
        import jsonschema
        jsonschema.validate(instance=dummy_record, schema=schema)
        log("Dummy record validation: PASSED")
        validation_status = "PASSED"
        error_message = None
    except ImportError:
        # Fallback manual validation if jsonschema not installed (though it should be per requirements)
        log("jsonschema library not found. Performing basic manual validation.")
        required_keys = schema.get('required', [])
        missing_keys = [k for k in required_keys if k not in dummy_record]
        if missing_keys:
            raise ValueError(f"Missing required keys in dummy record: {missing_keys}")
        
        props = schema.get('properties', {})
        for key, value in dummy_record.items():
            if key in props:
                expected_type = props[key].get('type')
                if expected_type == 'number' and not isinstance(value, (int, float)):
                    raise TypeError(f"Key '{key}' expected number, got {type(value)}")
                elif expected_type == 'string' and not isinstance(value, str):
                    raise TypeError(f"Key '{key}' expected string, got {type(value)}")
                elif expected_type == 'integer' and not isinstance(value, int):
                    raise TypeError(f"Key '{key}' expected integer, got {type(value)}")
        
        log("Manual validation: PASSED")
        validation_status = "PASSED"
        error_message = None
    except jsonschema.ValidationError as e:
        log(f"Dummy record validation: FAILED - {e.message}")
        validation_status = "FAILED"
        error_message = str(e.message)
        raise

    # Write Output
    result = {
        "schema_file": str(schema_path),
        "validation_status": validation_status,
        "dummy_record": dummy_record,
        "error": error_message
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    log(f"Validation result written to: {output_path}")
    print(f"SUCCESS: Schema {schema_path.name} is valid and verified against a dummy record.")

if __name__ == "__main__":
    main()
