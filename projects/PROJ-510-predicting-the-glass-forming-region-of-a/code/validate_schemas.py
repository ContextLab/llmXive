import yaml
import json
import jsonschema
import os
import sys

def validate_schemas():
    """
    Validate all JSON artifacts against their defined schemas in contracts/.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    contracts_dir = os.path.join(project_root, "contracts")
    data_dir = os.path.join(project_root, "data")
    
    schemas = {
        "dataset.schema.yaml": os.path.join(data_dir, "processed", "processed_alloys.csv"), # CSV, manual check
        "model_output.schema.yaml": os.path.join(data_dir, "models", "model_metrics_final.json")
    }

    # Validate Model Metrics JSON
    metrics_path = schemas["model_output.schema.yaml"]
    schema_path = os.path.join(contracts_dir, "model_output.schema.yaml")

    if not os.path.exists(metrics_path):
        print(f"Warning: Metrics file not found at {metrics_path}. Skipping validation.")
        return

    if not os.path.exists(schema_path):
        print(f"Error: Schema file not found at {schema_path}")
        sys.exit(1)

    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    with open(metrics_path, 'r') as f:
        data = json.load(f)

    try:
        jsonschema.validate(data, schema)
        print(f"Validation passed for {metrics_path}")
    except jsonschema.exceptions.ValidationError as e:
        print(f"Validation FAILED for {metrics_path}: {e.message}")
        sys.exit(1)

    # Validate CSV structure manually (simple check)
    csv_path = schemas["dataset.schema.yaml"]
    if os.path.exists(csv_path):
        import pandas as pd
        df = pd.read_csv(csv_path)
        required_cols = ['composition', 'critical_cooling_rate', 'mixing_enthalpy', 'atomic_size_mismatch', 'electronegativity_variance']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            print(f"Validation FAILED for {csv_path}: Missing columns {missing}")
            sys.exit(1)
        print(f"Validation passed for {csv_path} (structure check)")
    else:
        print(f"Warning: CSV file not found at {csv_path}. Skipping validation.")

    print("All schema validations completed successfully.")

if __name__ == "__main__":
    validate_schemas()
