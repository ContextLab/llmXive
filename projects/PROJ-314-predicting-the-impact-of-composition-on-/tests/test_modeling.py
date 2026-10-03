"""
Unit tests for modeling pipeline.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from modeling import validate_search_space, prepare_splits

def test_validate_search_space():
    """Test hyperparameter search space validation."""
    valid_space = {
        'n_estimators': [50, 100, 200],
        'max_depth': [None, 10, 20],
        'min_samples_split': [2, 5, 10]
    }
    assert validate_search_space(valid_space) is True

    invalid_space = {
        'n_estimators': [50, 100, 200, 300, 400, 500],
        'max_depth': [None, 10, 20, 30, 40, 50],
        'min_samples_split': [2, 5, 10, 20, 30, 40]
    }
    assert validate_search_space(invalid_space) is False

def test_prepare_splits():
    """Test stratified split preparation."""
    df = pd.DataFrame({
        'feature1': [1, 2, 3, 4, 5, 6],
        'primary_anion_cation_group': ['A', 'A', 'B', 'B', 'A', 'B']
    })
    train_idx, test_idx = prepare_splits(df, n_splits=2)
    assert len(train_idx) + len(test_idx) == len(df)
    assert len(train_idx) > 0
    assert len(test_idx) > 0