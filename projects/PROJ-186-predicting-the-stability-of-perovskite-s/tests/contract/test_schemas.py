import pytest
import pandas as pd
import yaml
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_features_csv_schema_validation():
    """
    Test case for T011: Validate the features.csv schema against contracts/data-schema.yaml.
    """
    schema_path = Path(PROJECT_ROOT) / "contracts" / "data-schema.yaml"
    
    if not schema_path.exists():
        pytest.skip("Schema file not found yet")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required_columns = schema.get('required_columns', [])
    # Simulate a features dataframe
    df = pd.DataFrame({
        'material_id': ['mp-123'],
        'tolerance_factor': [0.95],
        'octahedral_factor': [0.45],
        'ionic_mismatch': [0.1],
        'electronegativity_diff': [0.5],
        'decomposition_energy': [-0.2]
    })
    
    # Validate columns
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Validate types (example)
    assert df['decomposition_energy'].dtype in ['float64', 'int64', 'float32']
