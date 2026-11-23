import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import tempfile
import os

# Import the functions to test
# We need to mock the imports if they are heavy, but here we test logic
from stats.correlation import flag_cognitive_records, load_instrument_registry, validate_cognitive_instrument

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'participant_id': ['p1', 'p2', 'p3', 'p4'],
        'age': [20, 50, 70, 30],
        'cognitive_score': [28.0, 25.0, np.nan, 29.0],
        'cognitive_instrument': ['MoCA', 'MMSE', 'MoCA', 'InvalidInst']
    })

@pytest.fixture
def valid_registry_path(tmp_path):
    registry_file = tmp_path / "registry.yaml"
    registry_file.write_text("valid_instruments:\n  - MMSE\n  - MoCA\n")
    return str(registry_file)

def test_load_instrument_registry(valid_registry_path):
    instruments = load_instrument_registry(valid_registry_path)
    assert 'MMSE' in instruments
    assert 'MoCA' in instruments
    assert 'InvalidInst' not in instruments

def test_flag_cognitive_records_valid(sample_df, valid_registry_path):
    flagged = flag_cognitive_records(sample_df, valid_registry_path)
    
    # p1: MoCA, score 28 -> Valid
    assert flagged.loc[0, 'cognitive_valid'] == True
    assert flagged.loc[0, 'exclusion_reason'] is None or pd.isna(flagged.loc[0, 'exclusion_reason'])
    
    # p2: MMSE, score 25 -> Valid
    assert flagged.loc[1, 'cognitive_valid'] == True
    
    # p3: MoCA, score NaN -> Missing Score
    assert flagged.loc[2, 'cognitive_valid'] == False
    assert 'Missing' in flagged.loc[2, 'exclusion_reason']
    
    # p4: InvalidInst, score 29 -> Invalid Instrument
    assert flagged.loc[3, 'cognitive_valid'] == False
    assert 'Invalid' in flagged.loc[3, 'exclusion_reason']

def test_flag_cognitive_records_missing_registry(sample_df, tmp_path):
    # Test with non-existent registry
    flagged = flag_cognitive_records(sample_df, str(tmp_path / "nonexistent.yaml"))
    # If registry is empty, no one should be valid based on instrument check
    # But we need to check the logic: if registry is empty, valid_instruments is []
    # So no instrument is in valid list.
    assert flagged['cognitive_valid'].sum() == 0
    
def test_validate_cognitive_instrument():
    valid_list = ['MMSE', 'MoCA']
    assert validate_cognitive_instrument('MMSE', valid_list) == True
    assert validate_cognitive_instrument('Invalid', valid_list) == False
