import pytest
import pandas as pd
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

def test_t024_output_schema():
    """
    Contract test: Verify that alpha_diversity_results.csv adheres to the expected schema.
    Schema:
    - sample_id: string
    - pH: float
    - shannon: float
    - simpson: float
    - transformed_shannon: float
    - estimate: float
    - se: float
    - p_value: float
    - model_type: string (LME, FixedEffects, Spearman)
    - nonlinearity_suggestion: string
    """
    # Load the output file if it exists, or skip if not generated yet
    output_path = Path("data/processed/alpha_diversity_results.csv")
    if not output_path.exists():
        pytest.skip("Output file not found. Run T024 first.")
    
    df = pd.read_csv(output_path)
    
    # Check column existence
    expected_cols = [
        'sample_id', 'pH', 'shannon', 'simpson', 'transformed_shannon',
        'estimate', 'se', 'p_value', 'model_type', 'nonlinearity_suggestion'
    ]
    
    for col in expected_cols:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Check data types
    assert pd.api.types.is_float_dtype(df['pH']), "pH must be float"
    assert pd.api.types.is_float_dtype(df['estimate']), "estimate must be float"
    assert pd.api.types.is_float_dtype(df['se']), "se must be float"
    assert pd.api.types.is_float_dtype(df['p_value']), "p_value must be float"
    
    # Check model_type values
    valid_model_types = ['LME', 'FixedEffects', 'Spearman']
    assert df['model_type'].isin(valid_model_types).all(), f"Invalid model_type values found. Expected one of {valid_model_types}"
    
    # Check for nulls in critical fields
    assert not df['estimate'].isna().any(), "estimate cannot be null"
    assert not df['p_value'].isna().any(), "p_value cannot be null"
    assert not df['model_type'].isna().any(), "model_type cannot be null"
    
    # Check p_value range
    assert (df['p_value'] >= 0.0).all() and (df['p_value'] <= 1.0).all(), "p_value must be between 0 and 1"
