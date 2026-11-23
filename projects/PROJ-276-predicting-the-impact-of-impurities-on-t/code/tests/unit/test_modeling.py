"""
Unit tests for modeling utilities, specifically stratified splitting logic.
Focus: Verify rare impurity binning handles edge cases correctly.
"""
import pytest
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, train_test_split
from code.src.utils.logging import get_modeling_logger

logger = get_modeling_logger()


def bin_rare_impurities(series: pd.Series, threshold: float = 5.0) -> pd.Series:
    """
    Bin rare impurity categories into a single 'RARE' group to ensure
    stratified splitting doesn't fail on classes with too few samples.
    
    Args:
        series: Series of impurity types.
        threshold: Minimum count for a category to be kept as its own class.
        
    Returns:
        Series with rare categories replaced by 'RARE'.
    """
    counts = series.value_counts()
    rare_classes = counts[counts < threshold].index
    
    if len(rare_classes) > 0:
        logger.debug(f"Found {len(rare_classes)} rare impurity classes to bin: {list(rare_classes)}")
        return series.replace(rare_classes, 'RARE')
    
    return series


class TestStratifiedSplitting:
    """Tests for stratified splitting logic with rare impurity binning."""

    def test_rare_binning_aggregates_small_classes(self):
        """Verify that classes below the threshold are aggregated into 'RARE'."""
        data = pd.DataFrame({
            'impurity': ['Al', 'Al', 'Al', 'Si', 'Si', 'C', 'Fe'], 
            'target': [1, 2, 3, 4, 5, 6, 7]
        })
        
        # Threshold 3: 'Al' and 'Si' have 3, 'C' and 'Fe' have 1.
        # Expected: 'C' and 'Fe' become 'RARE'.
        binned = bin_rare_impurities(data['impurity'], threshold=3)
        
        assert binned.value_counts()['RARE'] == 2
        assert binned.value_counts()['Al'] == 3
        assert binned.value_counts()['Si'] == 3
        assert 'C' not in binned.values
        assert 'Fe' not in binned.values

    def test_rare_binning_no_change_if_all_common(self):
        """Verify no binning occurs if all classes meet the threshold."""
        data = pd.DataFrame({
            'impurity': ['Al', 'Al', 'Si', 'Si', 'C', 'C'],
            'target': [1, 2, 3, 4, 5, 6]
        })
        
        binned = bin_rare_impurities(data['impurity'], threshold=2)
        
        # Should remain unchanged
        pd.testing.assert_series_equal(binned, data['impurity'])

    def test_stratified_split_succeeds_after_binning(self):
        """Verify that train_test_split with stratify works after binning rare classes."""
        # Create a dataset where one class has only 1 sample (would fail stratify without binning)
        np.random.seed(42)
        n_samples = 100
        impurities = ['Al'] * 50 + ['Si'] * 49 + ['Fe'] * 1
        targets = np.random.rand(n_samples)
        
        df = pd.DataFrame({
            'impurity': impurities,
            'target': targets
        })
        
        # Without binning, this should raise an error or warning due to min_samples_per_class
        # We expect a ValueError from sklearn if we try to split with the original series
        with pytest.raises(ValueError):
            train_test_split(df, test_size=0.2, stratify=df['impurity'], random_state=42)
        
        # With binning, it should succeed
        binned_impurities = bin_rare_impurities(df['impurity'], threshold=5)
        train, test = train_test_split(
            df, 
            test_size=0.2, 
            stratify=binned_impurities, 
            random_state=42
        )
        
        assert len(train) + len(test) == n_samples
        assert len(train) > 0
        assert len(test) > 0

    def test_binning_preserves_class_distribution_ratio(self):
        """Verify that binning preserves the relative distribution of common classes."""
        data = pd.DataFrame({
            'impurity': ['A'] * 100 + ['B'] * 80 + ['Rare1'] * 5 + ['Rare2'] * 3,
            'target': range(188)
        })
        
        binned = bin_rare_impurities(data['impurity'], threshold=10)
        
        # Check counts
        counts = binned.value_counts()
        assert counts['A'] == 100
        assert counts['B'] == 80
        assert counts['RARE'] == 8  # 5 + 3
        
        # Check that 'Rare1' and 'Rare2' are gone
        assert 'Rare1' not in counts.index
        assert 'Rare2' not in counts.index

    def test_empty_series_handling(self):
        """Verify binning handles empty series gracefully."""
        empty_series = pd.Series([], dtype=str)
        binned = bin_rare_impurities(empty_series, threshold=5)
        assert len(binned) == 0
        assert binned.dtype == object

    def test_single_class_handling(self):
        """Verify handling when there is only one class present."""
        data = pd.DataFrame({
            'impurity': ['Al'] * 10,
            'target': range(10)
        })
        
        binned = bin_rare_impurities(data['impurity'], threshold=5)
        assert (binned == 'Al').all()
        
        # If threshold is higher than count, it should become RARE
        binned_high = bin_rare_impurities(data['impurity'], threshold=15)
        assert (binned_high == 'RARE').all()

class TestModelingUtilities:
    """Additional tests for general modeling utilities if any are added later."""
    
    def test_placeholder(self):
        """Placeholder test to ensure the test file runs."""
        assert True