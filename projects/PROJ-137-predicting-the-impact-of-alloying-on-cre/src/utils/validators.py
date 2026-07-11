import yaml
import pandas as pd
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError

_project_root = Path(__file__).resolve().parent.parent.parent

def load_schema(schema_path):
    """Load a JSON/YAML schema."""
    path = _project_root / schema_path
    if not path.exists():
        return None
    with open(path, 'r') as f:
        if schema_path.endswith('.yaml') or schema_path.endswith('.yml'):
            return yaml.safe_load(f)
        else:
            return json.load(f)

def validate_dataset_schema(df, schema_path="contracts/dataset.schema.yaml"):
    """Validate dataframe against a schema."""
    schema = load_schema(schema_path)
    if not schema:
        # If schema missing, skip validation or return True
        return True
    
    # Convert df to dict of lists for jsonschema
    data = df.to_dict(orient='records')
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        raise ValueError(f"Schema validation failed: {e.message}")