import pytest
import pandas as pd
import numpy as np
from code.data.preprocess import exclude_missing_data, stratified_split, apply_pca

def test_exclude_missing_data():
    data = pd.DataFrame({
        'A': [1, 2, np.nan, 4],
        'B': [5, np.nan, 7, 8],
        'target': [10, 20, 30, 40]
    })
    result, log = exclude_missing_data(data, target_col='target')
    assert len(result) == 2
    assert log['excluded_count'] == 2

def test_stratified_split():
    data = pd.DataFrame({
        'A': [1, 2, 3, 4, 5, 6],
        'target': [0, 0, 1, 1, 2, 2]
    })
    train, val, test = stratified_split(data, target_col='target', split_ratio=[0.5, 0.25, 0.25], seed=42)
    assert len(train) + len(val) + len(test) == 6
    assert len(train) == 3

def test_apply_pca():
    data = pd.DataFrame({
        'A': [1, 2, 3, 4, 5, 6],
        'B': [2, 4, 6, 8, 10, 12],
        'C': [3, 6, 9, 12, 15, 18],
        'target': [10, 20, 30, 40, 50, 60]
    })
    features = data[['A', 'B', 'C']]
    target = data['target']
    transformed, pca = apply_pca(features, target, n_components=2)
    assert transformed.shape[1] == 2
