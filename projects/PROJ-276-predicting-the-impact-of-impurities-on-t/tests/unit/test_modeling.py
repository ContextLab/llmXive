import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, train_test_split
from code.src.utils.logging import get_modeling_logger
from code.src.modeling.train import build_hyperparameter_grid

# Logger instance for the test module
logger = get_modeling_logger(__name__)


def bin_rare_impurities(df: pd.DataFrame, column: str, threshold: int = 5) -> pd.DataFrame:
    """
    Utility function to bin rare impurities into an 'Other' category.
    Used in stratified splitting to ensure sufficient sample sizes per class.
    """
    value_counts = df[column].value_counts()
    rare_categories = value_counts[value_counts < threshold].index.tolist()
    if not rare_categories:
        return df
    
    df_copy = df.copy()
    df_copy[column] = df_copy[column].apply(lambda x: 'Other' if x in rare_categories else x)
    return df_copy


class TestStratifiedSplitting:
    """
    Unit tests for stratified splitting logic and rare impurity binning.
    """

    def test_bin_rare_impurities_groups_low_frequency(self):
        """Verify that impurities with count < threshold are grouped into 'Other'."""
        data = {
            'impurity_type': ['Al', 'Al', 'Al', 'Si', 'Si', 'C', 'Fe'],
            'value': [1, 2, 3, 4, 5, 6, 7]
        }
        df = pd.DataFrame(data)
        
        # Threshold 3 means 'C' and 'Fe' (count 1) should become 'Other'
        result = bin_rare_impurities(df, 'impurity_type', threshold=3)
        
        assert result['impurity_type'].tolist() == ['Al', 'Al', 'Al', 'Si', 'Si', 'Other', 'Other']
        logger.info("Rare impurity binning test passed.")

    def test_stratified_split_preserves_distribution(self):
        """Verify that train_test_split with stratify preserves class proportions."""
        # Create a dataset with known distribution
        classes = ['Al'] * 80 + ['Si'] * 20
        values = list(range(100))
        df = pd.DataFrame({'impurity_type': classes, 'value': values})
        
        train, test = train_test_split(
            df, 
            test_size=0.2, 
            stratify=df['impurity_type'],
            random_state=42
        )
        
        # Check proportions
        train_ratio = train['impurity_type'].value_counts(normalize=True)['Al']
        test_ratio = test['impurity_type'].value_counts(normalize=True)['Al']
        original_ratio = df['impurity_type'].value_counts(normalize=True)['Al']
        
        assert abs(train_ratio - original_ratio) < 0.05
        assert abs(test_ratio - original_ratio) < 0.05
        logger.info("Stratified split distribution test passed.")


class TestModelingUtilities:
    """
    Unit tests for modeling utilities, specifically hyperparameter grid limits.
    """

    def test_hyperparameter_grid_size_limit(self):
        """
        Verify that the hyperparameter grid for any model does not exceed
        10 combinations. This enforces the constraint to prevent excessive
        runtime and ensure compliance with the 30-minute execution limit.
        """
        # Get the grid for a standard model (e.g., Random Forest)
        grid = build_hyperparameter_grid('RandomForest')
        
        # Calculate total combinations
        total_combinations = 1
        for key in grid:
            if isinstance(grid[key], list):
                total_combinations *= len(grid[key])
            else:
                total_combinations *= 1  # Single value
        
        logger.info(f"Generated {total_combinations} hyperparameter combinations for RandomForest.")
        
        assert total_combinations <= 10, (
            f"Hyperparameter grid size ({total_combinations}) exceeds the limit of 10. "
            "This violates the runtime constraints defined in the project plan."
        )

    def test_hyperparameter_grid_size_limit_xgboost(self):
        """
        Verify that the hyperparameter grid for XGBoost does not exceed 10 combinations.
        """
        grid = build_hyperparameter_grid('XGBoost')
        
        total_combinations = 1
        for key in grid:
            if isinstance(grid[key], list):
                total_combinations *= len(grid[key])
            else:
                total_combinations *= 1
        
        logger.info(f"Generated {total_combinations} hyperparameter combinations for XGBoost.")
        
        assert total_combinations <= 10, (
            f"Hyperparameter grid size ({total_combinations}) exceeds the limit of 10."
        )

    def test_hyperparameter_grid_size_limit_linear(self):
        """
        Verify that the hyperparameter grid for Linear/Ridge Regression does not exceed 10 combinations.
        """
        grid = build_hyperparameter_grid('Ridge')
        
        total_combinations = 1
        for key in grid:
            if isinstance(grid[key], list):
                total_combinations *= len(grid[key])
            else:
                total_combinations *= 1
        
        logger.info(f"Generated {total_combinations} hyperparameter combinations for Ridge.")
        
        assert total_combinations <= 10, (
            f"Hyperparameter grid size ({total_combinations}) exceeds the limit of 10."
        )