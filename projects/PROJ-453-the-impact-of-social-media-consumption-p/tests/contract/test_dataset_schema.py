import pytest
import yaml
from pathlib import Path

def test_schema_matches_yaml():
    """Validate data schema against contracts/dataset.schema.yaml."""
    schema_path = Path("contracts/dataset.schema.yaml")
    assert schema_path.exists(), "Schema file missing"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_fields = ['switching_index', 'cognitive_flexibility_score', 'age', 'total_screen_time', 'num_platforms', 'switching_frequency']
    schema_fields = schema.get('columns', [])
    
    for field in required_fields:
        assert field in schema_fields, f"Missing required field: {field}"
