import pandas as pd
import yaml
import json
import jsonschema
from pathlib import Path

def test_merged_schema():
    """Test that merged_monthly.csv conforms to dataset.schema.yaml."""
    project_root = Path(__file__).parent.parent.parent
    data_path = project_root / "data" / "processed" / "merged_monthly.csv"
    schema_path = project_root / "contracts" / "dataset.schema.yaml"
    
    if not data_path.exists():
        raise FileNotFoundError(f"Test data not found: {data_path}")
    
    df = pd.read_csv(data_path)
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Convert to list of dicts for jsonschema
    records = df.to_dict(orient='records')
    
    # Validate each record
    for record in records:
        jsonschema.validate(record, schema)
    
    assert True, "Schema validation passed for all records"