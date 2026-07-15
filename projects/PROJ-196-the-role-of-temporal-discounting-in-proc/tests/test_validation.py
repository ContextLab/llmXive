import pytest
import sys
import os
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Mock the config module if needed, or assume it's available
# For testing, we will create a temporary directory structure
import ingestion

def test_validate_core_constructs_missing_column():
    """
    Test that validate_core_constructs raises SystemExit(1) if a core construct is missing.
    """
    # Create a mock dataframe missing 'discount_rate_k'
    df = pd.DataFrame({
        'participant_id': [1, 2, 3],
        'procrastination_score': [1.0, 2.0, 3.0],
        'wm_accuracy': [0.8, 0.9, 0.95]
    })
    
    # We need to patch sys.exit to capture the call
    with pytest.raises(SystemExit) as exc_info:
        ingestion.validate_core_constructs(df)
    
    assert exc_info.value.code == 1

def test_validate_core_constructs_all_present():
    """
    Test that validate_core_constructs returns True if all core constructs are present.
    """
    df = pd.DataFrame({
        'participant_id': [1, 2, 3],
        'discount_rate_k': [0.1, 0.2, 0.3],
        'procrastination_score': [1.0, 2.0, 3.0],
        'wm_accuracy': [0.8, 0.9, 0.95]
    })
    
    result = ingestion.validate_core_constructs(df)
    assert result is True

def test_validate_core_constructs_multiple_missing():
    """
    Test that validate_core_constructs raises SystemExit(1) if multiple core constructs are missing.
    """
    df = pd.DataFrame({
        'participant_id': [1, 2, 3],
        'wm_accuracy': [0.8, 0.9, 0.95]
    })
    
    with pytest.raises(SystemExit) as exc_info:
        ingestion.validate_core_constructs(df)
    
    assert exc_info.value.code == 1