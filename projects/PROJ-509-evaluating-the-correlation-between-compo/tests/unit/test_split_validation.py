"""
Unit tests for stratified split logic and Total Variation Distance (TVD) calculation.
This module validates the integrity of data splits used in model training (User Story 2).
"""

import pytest
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional

# Helper function to calculate Total Variation Distance
def calculate_tvd(dist1: pd.Series, dist2: pd.Series) -> float:
    """
    Calculates the Total Variation Distance between two categorical distributions.
    
    TVD = 0.5 * sum(|p_i - q_i|)
    
    Args:
        dist1: A pandas Series representing the first distribution (counts or probabilities).
        dist2: A pandas Series representing the second distribution (counts or probabilities).
        
    Returns:
        float: The TVD value between 0.0 and 1.0.
    """
    # Normalize to probabilities
    total1 = dist1.sum()
    total2 = dist2.sum()
    
    if total1 == 0 or total2 == 0:
        return 1.0 # Max distance if one is empty
    
    probs1 = dist1 / total1
    probs2 = dist2 / total2
    
    # Ensure both series have the same index (categories) for alignment
    all_categories = probs1.index.union(probs2.index)
    probs1 = probs1.reindex(all_categories, fill_value=0.0)
    probs2 = probs2.reindex(all_categories, fill_value=0.0)
    
    tvd = 0.5 * np.abs(probs1 - probs2).sum()
    return float(tvd)


def calculate_stratified_split_distributions(
    df: pd.DataFrame, 
    stratify_col: str, 
    train_size: float = 0.8, 
    random_state: int = 42
) -> Tuple[pd.Series, pd.Series]:
    """
    Simulates a stratified split and returns the distribution of the stratification column
    for both train and validation sets.
    
    Args:
        df: The input DataFrame.
        stratify_col: The column name to stratify by.
        train_size: The proportion of the dataset to include in the train split.
        random_state: The random seed for reproducibility.
        
    Returns:
        Tuple of (train_distribution, val_distribution) as pandas Series of counts.
    """
    # Simple stratified sampling implementation
    np.random.seed(random_state)
    
    train_indices = []
    val_indices = []
    
    groups = df.groupby(stratify_col)
    
    for name, group in groups:
        indices = group.index.tolist()
        n_train = int(len(indices) * train_size)
        
        # Shuffle indices
        shuffled = indices.copy()
        np.random.shuffle(shuffled)
        
        train_indices.extend(shuffled[:n_train])
        val_indices.extend(shuffled[n_train:])
    
    train_df = df.loc[train_indices]
    val_df = df.loc[val_indices]
    
    return train_df[stratify_col].value_counts(), val_df[stratify_col].value_counts()


class TestStratifiedSplitValidation:
    """Tests for the stratified split logic and TVD calculation."""

    def test_tvd_identical_distributions(self):
        """TVD should be 0.0 for identical distributions."""
        s1 = pd.Series([10, 20, 30], index=['A', 'B', 'C'])
        s2 = pd.Series([10, 20, 30], index=['A', 'B', 'C'])
        
        tvd = calculate_tvd(s1, s2)
        assert tvd == 0.0, f"Expected TVD 0.0, got {tvd}"

    def test_tvd_disjoint_distributions(self):
        """TVD should be 1.0 for completely disjoint distributions."""
        s1 = pd.Series([10], index=['A'])
        s2 = pd.Series([10], index=['B'])
        
        tvd = calculate_tvd(s1, s2)
        # 0.5 * (|1.0 - 0.0| + |0.0 - 1.0|) = 0.5 * 2 = 1.0
        assert tvd == 1.0, f"Expected TVD 1.0, got {tvd}"

    def test_tvd_partial_overlap(self):
        """TVD should be between 0 and 1 for partial overlap."""
        s1 = pd.Series([10, 10], index=['A', 'B'])
        s2 = pd.Series([5, 15], index=['A', 'B'])
        
        # p = [0.5, 0.5], q = [0.25, 0.75]
        # |0.5 - 0.25| + |0.5 - 0.75| = 0.25 + 0.25 = 0.5
        # TVD = 0.5 * 0.5 = 0.25
        tvd = calculate_tvd(s1, s2)
        assert abs(tvd - 0.25) < 1e-6, f"Expected TVD 0.25, got {tvd}"

    def test_stratified_split_preserves_distribution(self):
        """Stratified split should result in very low TVD between train and val sets."""
        # Create a synthetic dataset with known distribution
        data = {
            'crystal_system': ['Cubic'] * 800 + ['Hexagonal'] * 100 + ['Orthorhombic'] * 100,
            'value': range(1000)
        }
        df = pd.DataFrame(data)
        
        train_dist, val_dist = calculate_stratified_split_distributions(
            df, 
            stratify_col='crystal_system', 
            train_size=0.8, 
            random_state=42
        )
        
        tvd = calculate_tvd(train_dist, val_dist)
        
        # With perfect stratification, TVD should be very close to 0
        # Allow small float errors or edge cases in small groups
        assert tvd <= 0.05, f"Stratified split TVD ({tvd}) exceeds threshold 0.05"

    def test_stratified_split_handles_imbalanced_data(self):
        """Stratified split should handle highly imbalanced classes."""
        # 990 A, 10 B
        data = {
            'crystal_system': ['A'] * 990 + ['B'] * 10,
            'value': range(1000)
        }
        df = pd.DataFrame(data)
        
        train_dist, val_dist = calculate_stratified_split_distributions(
            df, 
            stratify_col='crystal_system', 
            train_size=0.8, 
            random_state=123
        )
        
        tvd = calculate_tvd(train_dist, val_dist)
        
        # Should still maintain the ratio, resulting in low TVD
        assert tvd <= 0.05, f"Stratified split TVD ({tvd}) exceeds threshold 0.05 for imbalanced data"

    def test_tvd_with_missing_categories(self):
        """TVD calculation should handle cases where one distribution lacks a category."""
        s1 = pd.Series([10, 5], index=['A', 'B'])
        s2 = pd.Series([10], index=['A']) # Missing 'B'
        
        tvd = calculate_tvd(s1, s2)
        
        # p = [0.66, 0.33], q = [1.0, 0.0]
        # |0.66 - 1.0| + |0.33 - 0.0| = 0.33 + 0.33 = 0.66
        # TVD = 0.5 * 0.66 = 0.33
        assert 0.3 <= tvd <= 0.4, f"Expected TVD around 0.33, got {tvd}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])