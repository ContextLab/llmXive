"""
Unit tests for modeling.
"""
import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modeling import prepare_splits, hyperparameter_search_space

def test_prepare_splits():
    df = pd.DataFrame({
        'weibull_modulus': [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        'primary_anion_cation_group': ['A', 'A', 'B', 'B', 'A', 'B', 'A', 'B', 'A', 'B']
    })
    X, y, stratify, cv = prepare_splits(df)
    assert len(X) == len(df)
    assert len(y) == len(df)

def test_hyperparameter_grid_constraints():
    total = 1
    for values in hyperparameter_search_space.values():
        total *= len(values)
    assert total <= 50
