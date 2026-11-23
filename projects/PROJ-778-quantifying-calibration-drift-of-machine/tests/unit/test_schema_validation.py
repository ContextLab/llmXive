"""
Unit tests for schema validation logic in data acquisition.

This module validates that the schema alignment logic correctly rejects
datasets with mismatched columns (>10% mismatch) and accepts those within
the tolerance threshold.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from typing import Set, List, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.config import get_path, ensure_directories


def calculate_schema_mismatch(
    training_features: Set[str],
    test_features: Set[str]
) -> float:
    """
    Calculate the percentage of features in the training set that are missing
    from the test set.
    
    Args:
        training_features: Set of feature names from the training snapshot
        test_features: Set of feature names from the test snapshot
        
    Returns:
        Float representing the percentage of mismatched features (0.0 to 100.0)
    """
    if not training_features:
        return 0.0
    
    missing_features = training_features - test_features
    mismatch_ratio = len(missing_features) / len(training_features)
    return mismatch_ratio * 100.0


def validate_schema_alignment(
    training_features: Set[str],
    test_features: Set[str],
    tolerance_threshold: float = 10.0
) -> Tuple[bool, float, Set[str]]:
    """
    Validate that the schema mismatch between training and test features
    is within the acceptable tolerance threshold.
    
    Args:
        training_features: Set of feature names from the training snapshot
        test_features: Set of feature names from the test snapshot
        tolerance_threshold: Maximum allowed percentage of missing features (default 10.0%)
        
    Returns:
        Tuple of (is_valid, mismatch_percentage, missing_features)
        
    Raises:
        ValueError: If the mismatch exceeds the tolerance threshold
    """
    mismatch_percentage = calculate_schema_mismatch(training_features, test_features)
    missing_features = training_features - test_features
    
    if mismatch_percentage > tolerance_threshold:
        raise ValueError(
            f"Schema mismatch exceeds tolerance threshold ({tolerance_threshold}%). "
            f"Actual mismatch: {mismatch_percentage:.2f}%. "
            f"Missing features: {sorted(missing_features)}"
        )
    
    return True, mismatch_percentage, missing_features


class TestSchemaValidation:
    """Test cases for schema validation logic."""
    
    def test_schema_validation_rejects_mismatched_columns(self):
        """
        Test that a schema mismatch >10% triggers an abort with a clear error message.
        
        This test verifies that when the percentage of missing features in the test
        set exceeds the 10% tolerance threshold, a ValueError is raised with a
        descriptive error message.
        """
        # Define a realistic set of training features (Adult dataset columns)
        training_features = {
            'age', 'workclass', 'education', 'occupation', 'relationship',
            'race', 'sex', 'capital-gain', 'capital-loss', 'hours-per-week',
            'native-country', 'income'
        }
        
        # Create a test set with significant missing features (>10% mismatch)
        # Missing: 'workclass', 'education', 'occupation' (3 out of 12 = 25%)
        test_features = {
            'age', 'relationship', 'race', 'sex', 'capital-gain',
            'capital-loss', 'hours-per-week', 'native-country', 'income'
        }
        
        # Verify the mismatch calculation is correct
        mismatch = calculate_schema_mismatch(training_features, test_features)
        assert mismatch == 25.0, f"Expected 25% mismatch, got {mismatch}%"
        
        # Verify that validation raises an error
        with pytest.raises(ValueError) as exc_info:
            validate_schema_alignment(training_features, test_features, tolerance_threshold=10.0)
        
        # Verify the error message is clear and informative
        error_message = str(exc_info.value)
        assert "Schema mismatch exceeds tolerance threshold" in error_message
        assert "25.00" in error_message  # Shows actual mismatch percentage
        assert "workclass" in error_message  # Lists missing features
        assert "education" in error_message
        assert "occupation" in error_message
        
        print(f"✓ Test passed: Schema validation correctly rejected {mismatch}% mismatch")
        print(f"  Error message: {error_message}")
    
    def test_schema_validation_accepts_within_threshold(self):
        """
        Test that a schema mismatch <=10% is accepted without error.
        """
        training_features = {
            'age', 'workclass', 'education', 'occupation', 'relationship',
            'race', 'sex', 'capital-gain', 'capital-loss', 'hours-per-week',
            'native-country', 'income'
        }
        
        # Missing only 1 feature out of 12 = 8.33% (< 10%)
        test_features = {
            'age', 'workclass', 'education', 'occupation', 'relationship',
            'race', 'sex', 'capital-gain', 'capital-loss', 'hours-per-week',
            'income'
        }
        
        # This should not raise an exception
        is_valid, mismatch, missing = validate_schema_alignment(
            training_features, test_features, tolerance_threshold=10.0
        )
        
        assert is_valid is True
        assert mismatch <= 10.0
        assert len(missing) == 1
        assert 'native-country' in missing
        
        print(f"✓ Test passed: Schema validation accepted {mismatch:.2f}% mismatch")
    
    def test_schema_validation_exact_threshold(self):
        """
        Test that a schema mismatch exactly at the threshold (10%) is accepted.
        """
        # 12 features, missing 1.2 would be 10%, but we need integer features
        # Let's use 10 features, missing 1 = 10%
        training_features = {f'feature_{i}' for i in range(10)}
        test_features = {f'feature_{i}' for i in range(1, 10)}  # Missing feature_0
        
        is_valid, mismatch, missing = validate_schema_alignment(
            training_features, test_features, tolerance_threshold=10.0
        )
        
        assert is_valid is True
        assert mismatch == 10.0
        assert len(missing) == 1
        
        print(f"✓ Test passed: Schema validation accepted exactly 10% mismatch")
    
    def test_schema_validation_empty_training(self):
        """
        Test behavior when training features set is empty.
        """
        training_features = set()
        test_features = {'feature_1', 'feature_2'}
        
        # Should not raise an error (0% mismatch when no training features)
        is_valid, mismatch, missing = validate_schema_alignment(
            training_features, test_features, tolerance_threshold=10.0
        )
        
        assert is_valid is True
        assert mismatch == 0.0
        assert len(missing) == 0
        
        print("✓ Test passed: Empty training features handled correctly")
    
    def test_schema_validation_all_missing(self):
        """
        Test behavior when all training features are missing from test set.
        """
        training_features = {'feature_1', 'feature_2', 'feature_3'}
        test_features = set()
        
        with pytest.raises(ValueError) as exc_info:
            validate_schema_alignment(training_features, test_features, tolerance_threshold=10.0)
        
        error_message = str(exc_info.value)
        assert "100.00" in error_message
        assert "Schema mismatch exceeds tolerance threshold" in error_message
        
        print("✓ Test passed: All missing features correctly rejected with 100% mismatch")


if __name__ == "__main__":
    # Run tests manually if executed directly
    pytest.main([__file__, "-v"])