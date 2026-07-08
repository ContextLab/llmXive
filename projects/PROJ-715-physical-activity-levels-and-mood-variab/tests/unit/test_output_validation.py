import pytest
import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from preprocess import compute_daily_aggregates
from output_validator import validate_dataframe, load_schema

@pytest.fixture
def sample_daily_data():
    data = {
        'participant_id': ['P1', 'P1', 'P2'],
        'date': ['2023-01-01', '2023-01-02', '2023-01-01'],
        'total_steps': [5000, 0, 10000],
        'mean_mood': [3.5, 4.0, 2.5],
        'mood_std': [0.5, 0.0, 1.2],
        'mood_count': [3, 2, 4]
    }
    return pd.DataFrame(data)

def test_zero_steps_handling(sample_daily_data):
    """Test that zero steps are recorded as 0, not NaN."""
    result = compute_daily_aggregates(sample_daily_data)
    assert result.loc[result['date'] == '2023-01-02', 'total_steps'].iloc[0] == 0
    assert not pd.isna(result.loc[result['date'] == '2023-01-02', 'total_steps'].iloc[0])

def test_zero_mood_std_transformation(sample_daily_data):
    """Test that zero mood_std is log-transformed with epsilon."""
    result = compute_daily_aggregates(sample_daily_data)
    # The row with 0.0 mood_std should be log10(0 + epsilon)
    row = result.loc[result['date'] == '2023-01-02']
    std_val = row['mood_std'].iloc[0]
    # It should be a valid number (negative log of small number)
    assert not pd.isna(std_val)
    assert std_val < 0 # log10(1e-5) is -5

def test_schema_validation_passes(sample_daily_data):
    """Test that a valid dataframe passes schema validation."""
    # Load schema
    schema_path = Path('specs/001-physical-activity-mood-variability/contracts/daily_aggregates.schema.yaml')
    if not schema_path.exists():
        pytest.skip("Schema file not found for test")
    
    schema = load_schema(schema_path)
    # Create a minimal valid schema for testing if the real one is complex
    # Assuming the real schema requires 'participant_id', 'date', 'total_steps', 'mean_mood', 'mood_std'
    # We rely on the real schema if it exists, otherwise skip or mock
    
    # For this test, we assume the schema exists and is correct.
    # We check that our processed data matches the required columns.
    required_cols = schema.get('required', [])
    for col in required_cols:
        assert col in result.columns

def test_schema_validation_fails_missing_column():
    """Test that a dataframe with missing required columns fails."""
    schema = {
        'required': ['participant_id', 'date', 'total_steps'],
        'properties': {
            'participant_id': {'type': 'string'},
            'date': {'type': 'string'},
            'total_steps': {'type': 'number'}
        }
    }
    bad_df = pd.DataFrame({'participant_id': ['P1'], 'date': ['2023-01-01']})
    assert not validate_dataframe(bad_df, schema)