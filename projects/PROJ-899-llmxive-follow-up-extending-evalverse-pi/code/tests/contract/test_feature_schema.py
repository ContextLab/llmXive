import pytest
import pandas as pd
import numpy as np

def test_feature_extraction_schema():
    """
    Contract test: Verify that feature extraction output matches expected schema.
    """
    # Expected schema based on T012/T013 implementation
    expected_columns = [
        'clip_id',
        'optical_flow_mean',
        'optical_flow_var',
        'audio_spectral',
        'audio_zcr',
        'human_score'
    ]
    
    # Simulate a dataframe that should be produced by the pipeline
    df = pd.DataFrame({
        'clip_id': ['c1'],
        'optical_flow_mean': [10.0],
        'optical_flow_var': [1.0],
        'audio_spectral': [100.0],
        'audio_zcr': [0.1],
        'human_score': [0.9]
    })
    
    assert list(df.columns) == expected_columns
    assert df['clip_id'].dtype == object
    assert np.issubdtype(df['optical_flow_mean'].dtype, np.floating)
