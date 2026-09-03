"""
Standalone script to verify T009c: 
1. Load the schema from contracts/experiment_log.schema.yaml
2. Create a sample log entry matching the schema
3. Validate the entry using jsonschema
4. Print success or failure
"""
import os
import sys
import yaml
from jsonschema import validate, ValidationError

# Add project root to path if running from script directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

SCHEMA_PATH = os.path.join(project_root, "contracts", "experiment_log.schema.yaml")

def main():
    print(f"Loading schema from: {SCHEMA_PATH}")
    
    if not os.path.exists(SCHEMA_PATH):
        print(f"ERROR: Schema file not found at {SCHEMA_PATH}")
        return 1

    try:
        with open(SCHEMA_PATH, "r") as f:
            schema = yaml.safe_load(f)
        print("Schema loaded successfully.")
    except Exception as e:
        print(f"ERROR: Failed to parse schema YAML: {e}")
        return 1

    # Construct a sample log entry matching the schema properties
    sample_entry = {
        "task_id": "task_001",
        "skill_id": "skill_42",
        "success": True,
        "latency": 0.45,
        "tokens": 120,
        "retrieval_precision": 0.85,
        "retrieval_diversity": 2.5,
        "pruning_risk_count": 0,
        "library_size": 50,
        "pruning_enabled": True,
        "edge_case": False
    }

    print("Validating sample entry against schema...")
    try:
        validate(instance=sample_entry, schema=schema)
        print("SUCCESS: Sample entry is valid according to contracts/experiment_log.schema.yaml")
        return 0
    except ValidationError as e:
        print(f"FAILURE: Sample entry failed validation: {e.message}")
        return 1

if __name__ == "__main__":
    exit(main())