import pandas as pd
import json
import jsonschema
import yaml
import os

def test_correlation_schema():
    """Validate correlation results against the output schema."""
    output_path = 'data/processed/correlation_results.csv'
    schema_path = 'contracts/output.schema.yaml'
    
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Output file not found: {output_path}")
    
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    df = pd.read_csv(output_path)
    
    # Load schema
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Convert DataFrame to list of dicts
    records = df.to_dict(orient='records')
    
    # Validate each record
    for i, record in enumerate(records):
        try:
            jsonschema.validate(record, schema)
        except jsonschema.ValidationError as e:
            raise AssertionError(f"Record {i} failed validation: {e.message}")
    
    print("Correlation schema validation passed.")

if __name__ == "__main__":
    test_correlation_schema()