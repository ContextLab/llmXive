"""
Unit tests for the CV strategy implementation in code/training/cv_strategy.py.
Verifies:
1. ConfigurationError is raised for datasets < 50 samples.
2. Exactly 5 folds are produced for valid datasets.
3. Solvent-type distribution deviation is <= 5% per fold.
"""

import pytest
import pandas as pd
import numpy as np
from code.training.cv_strategy import get_cv_splitter, ConfigurationError

def test_cv_strategy_raises_error_for_small_dataset():
    """Verify that datasets with < 50 samples raise ConfigurationError."""
    # Dataset with 49 samples
    df = pd.DataFrame({
        "solvent": ["water"] * 25 + ["ethanol"] * 24,
        "target": np.random.rand(49)
    })
    with pytest.raises(ConfigurationError, match="too small"):
        list(get_cv_splitter(df))

def test_cv_strategy_produces_five_folds():
    """Verify that exactly 5 folds are produced for a valid dataset."""
    # Dataset with 100 samples
    df = pd.DataFrame({
        "solvent": ["water"] * 50 + ["ethanol"] * 50,
        "target": np.random.rand(100)
    })
    folds = list(get_cv_splitter(df))
    assert len(folds) == 5

def test_cv_strategy_distribution_constraint():
    """
    Verify that solvent-type distribution deviation is <= 5% per fold.
    We use a balanced dataset to ensure StratifiedKFold can achieve 0% deviation.
    """
    # Create a dataset with 100 samples and 4 solvents (25 each)
    # 100 samples / 5 folds = 20 samples per fold.
    # Each fold should ideally have 5 of each solvent (5/20 = 25%).
    solvents = ["water", "ethanol", "methanol", "acetone"]
    data = []
    for s in solvents:
        data.extend([s] * 25)
    
    df = pd.DataFrame({
        "solvent": data,
        "target": np.random.rand(100)
    })
    
    # Shuffle the dataframe to test the splitter's ability to stratify
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    global_props = df["solvent"].value_counts(normalize=True).to_dict()
    
    folds = list(get_cv_splitter(df))
    
    for i, (train_idx, test_idx) in enumerate(folds):
        fold_df = df.iloc[test_idx]
        fold_props = fold_df["solvent"].value_counts(normalize=True).to_dict()
        
        for solvent in solvents:
            global_p = global_props[solvent]
            fold_p = fold_props.get(solvent, 0.0)
            deviation = abs(fold_p - global_p)
            
            # Assertion: deviation <= 5% (0.05)
            assert deviation <= 0.05, (
                f"Fold {i} solvent {solvent} deviation {deviation:.4f} exceeds 0.05. "
                f"Global: {global_p:.4f}, Fold: {fold_p:.4f}"
            )

def test_cv_strategy_missing_column():
    """Verify ConfigurationError when the solvent column is missing."""
    df = pd.DataFrame({
        "wrong_column": ["water"] * 60,
        "target": np.random.rand(60)
    })
    with pytest.raises(ConfigurationError, match="not found in DataFrame"):
        list(get_cv_splitter(df, solvent_column="solvent"))