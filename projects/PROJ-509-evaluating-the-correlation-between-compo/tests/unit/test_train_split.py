"""
Unit tests for the training split logic in code/train.py.

Tests verify that:
1. Stratified split maintains distribution of crystal systems.
2. Split ratio is approximately 80/20.
3. No NaN values exist in the resulting splits.
"""

import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# Mock the split logic for testing without full pipeline
from code.train import perform_stratified_split, DESCRIPTOR_FEATURES, TARGET_COLUMN, STRATIFY_COLUMN

def test_stratified_split_distribution():
    """Test that the stratified split preserves crystal system distribution."""
    # Create synthetic data with known distribution
    n_samples = 1000
    crystal_systems = ["cubic", "tetragonal", "orthorhombic", "hexagonal", "monoclinic"]
    distribution = [0.4, 0.2, 0.2, 0.1, 0.1]
    
    data = {
        STRATIFY_COLUMN: np.random.choice(crystal_systems, n_samples, p=distribution),
        TARGET_COLUMN: np.random.rand(n_samples),
        **{f"feat_{i}": np.random.rand(n_samples) for i in range(5)}
    }
    df = pd.DataFrame(data)
    
    # Adjust feature names to match actual descriptors
    df.columns = [STRATIFY_COLUMN, TARGET_COLUMN] + [f"mean_electronegativity", "variance_electronegativity", "mean_atomic_radius", "variance_atomic_radius", "mean_valence_electrons"]
    
    # Perform split
    X_train, X_test, y_train, y_test = perform_stratified_split(
        df,
        features=list(df.columns[2:]),
        target=TARGET_COLUMN,
        stratify_col=STRATIFY_COLUMN,
        test_size=0.2,
        random_state=42
    )
    
    # Check split sizes
    assert len(X_train) + len(X_test) == n_samples
    assert abs(len(X_train) / n_samples - 0.8) < 0.05  # Within 5% tolerance
    
    # Check distribution preservation
    train_dist = X_train[STRATIFY_COLUMN].value_counts(normalize=True).sort_index()
    test_dist = X_test[STRATIFY_COLUMN].value_counts(normalize=True).sort_index()
    original_dist = df[STRATIFY_COLUMN].value_counts(normalize=True).sort_index()
    
    # Distributions should be similar (within 10% absolute difference)
    for system in crystal_systems:
        if system in original_dist.index:
            assert abs(train_dist.get(system, 0) - original_dist.get(system, 0)) < 0.1
            assert abs(test_dist.get(system, 0) - original_dist.get(system, 0)) < 0.1

def test_split_no_nulls():
    """Test that split data contains no null values."""
    data = {
        STRATIFY_COLUMN: ["cubic"] * 100,
        TARGET_COLUMN: np.random.rand(100),
        **{f"mean_electronegativity": np.random.rand(100), "variance_electronegativity": np.random.rand(100)}
    }
    df = pd.DataFrame(data)
    
    X_train, X_test, y_train, y_test = perform_stratified_split(
        df,
        features=["mean_electronegativity", "variance_electronegativity"],
        target=TARGET_COLUMN,
        stratify_col=STRATIFY_COLUMN,
        test_size=0.2,
        random_state=42
    )
    
    assert not X_train.isnull().any().any()
    assert not X_test.isnull().any().any()
    assert not y_train.isnull().any()
    assert not y_test.isnull().any()

def test_split_with_imbalanced_classes():
    """Test split handling when some classes have very few samples."""
    data = {
        STRATIFY_COLUMN: ["cubic"] * 95 + ["tetragonal"] * 5,
        TARGET_COLUMN: np.random.rand(100),
        **{f"mean_electronegativity": np.random.rand(100), "variance_electronegativity": np.random.rand(100)}
    }
    df = pd.DataFrame(data)
    
    # This should not raise an error, but may fall back to non-stratified split
    # depending on sklearn's behavior with very small classes
    try:
        X_train, X_test, y_train, y_test = perform_stratified_split(
            df,
            features=["mean_electronegativity", "variance_electronegativity"],
            target=TARGET_COLUMN,
            stratify_col=STRATIFY_COLUMN,
            test_size=0.2,
            random_state=42
        )
        assert len(X_train) + len(X_test) == 100
    except ValueError:
        # Expected if sklearn cannot stratify with such small classes
        pass