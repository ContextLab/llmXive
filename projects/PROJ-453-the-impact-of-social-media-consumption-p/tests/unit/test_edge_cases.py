import pytest
import pandas as pd
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from code_02_engineer import handle_missing_outcomes, engineer_switching_index

def test_empty_dataframe_handling():
    """Test handling of empty dataframe."""
    df = pd.DataFrame()
    # Should not raise, just return empty
    result = engineer_switching_index(df)
    assert len(result) == 0

def test_missing_value_exclusion():
    """Test that missing outcomes are excluded."""
    df = pd.DataFrame({
        'cognitive_flexibility_score': [10.0, None, 20.0],
        'num_platforms': [5, 5, 5],
        'switching_frequency': [2.0, 2.0, 2.0]
    })
    result = handle_missing_outcomes(df)
    assert len(result) == 2
    assert not result['cognitive_flexibility_score'].isna().any()
