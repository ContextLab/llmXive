"""
Verification script for T009c: Validates that a sample experiment log entry
conforms to the contracts/experiment_log.schema.yaml schema.
"""
import os
import sys
import yaml
from jsonschema import validate, ValidationError

# Add parent directory to path if running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    schema_path = os.path.join("contracts", "experiment_log.schema.yaml")
    
    if not os.path.exists(schema_path):
        print(f"ERROR: Schema file not found at {schema_path}")
        return False

    # Load the schema
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    # Define a valid sample log entry matching the schema properties
    sample_entry = {
        "task_id": "T001_SAMPLE",
        "skill_id": "SKILL_ADD_01",
        "success": True,
        "latency": 0.45,
        "tokens": 120,
        "retrieval_precision": 0.8,
        "retrieval_diversity": 2.5,
        "pruning_risk_count": 0,
        "library_size": 50,
        "pruning_enabled": True,
        "edge_case": False
    }

    try:
        validate(instance=sample_entry, schema=schema)
        print("SUCCESS: Sample entry validates correctly against experiment_log.schema.yaml")
        return True
    except ValidationError as e:
        print(f"FAILED: Validation error - {e.message}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
