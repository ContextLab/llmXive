import pytest
from code_01_ingest import validate_data_types_and_constraints
import pandas as pd

def test_missing_variable_raises_error():
    """Test that missing variable raises error."""
    df = pd.DataFrame({'a': [1, 2, 3]})
    schema = {'columns': ['a', 'b']}
    
    with pytest.raises(ValueError) as exc_info:
        validate_data_types_and_constraints(df, schema)
    
    assert "Missing required columns" in str(exc_info.value)
