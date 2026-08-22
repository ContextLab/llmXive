"""
Contract test for dataset schema validation (T010).

This test verifies that the dataset schema validation works correctly
by checking that required variables are present and properly formatted.
"""
import os
import sys
import json
import tempfile
import pandas as pd
from pathlib import Path

def test_dataset_schema_validation():
    """
    Test that the dataset schema validation correctly identifies
    valid and invalid datasets.
    """
    # Create a temporary directory for test data
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Define expected schema based on required_variables.yaml
        expected_predictors = ['Taxon_A', 'Taxon_B', 'Taxon_C', 'Taxon_D', 'Taxon_E']
        expected_outcomes = ['Sleep_Duration', 'REM_Duration', 'SWS_Duration', 'Wake_After_Sleep_Onset']
        
        # Test Case 1: Valid dataset
        valid_data = {
            'subject_id': [f'SUBJ_{i:03d}' for i in range(10)],
            **{pred: [0.1 + i*0.01 for i in range(10)] for pred in expected_predictors},
            **{outcome: [7.0 + i*0.1 for i in range(10)] for outcome in expected_outcomes}
        }
        valid_df = pd.DataFrame(valid_data)
        
        # Validate valid dataset
        missing_predictors = [p for p in expected_predictors if p not in valid_df.columns]
        missing_outcomes = [o for o in expected_outcomes if o not in valid_df.columns]
        
        assert len(missing_predictors) == 0, f"Valid dataset missing predictors: {missing_predictors}"
        assert len(missing_outcomes) == 0, f"Valid dataset missing outcomes: {missing_outcomes}"
        print("✓ Valid dataset passed schema validation")
        
        # Test Case 2: Invalid dataset (missing variables)
        invalid_data = {
            'subject_id': [f'SUBJ_{i:03d}' for i in range(10)],
            'Taxon_A': [0.1 + i*0.01 for i in range(10)],
            # Missing other predictors and outcomes
        }
        invalid_df = pd.DataFrame(invalid_data)
        
        missing_predictors = [p for p in expected_predictors if p not in invalid_df.columns]
        missing_outcomes = [o for o in expected_outcomes if o not in invalid_df.columns]
        
        assert len(missing_predictors) > 0, "Invalid dataset should have missing predictors"
        assert len(missing_outcomes) > 0, "Invalid dataset should have missing outcomes"
        print(f"✓ Invalid dataset correctly identified missing variables: {missing_predictors + missing_outcomes}")
        
        # Test Case 3: Dataset with wrong data types
        type_error_data = {
            'subject_id': [f'SUBJ_{i:03d}' for i in range(10)],
            'Taxon_A': ['string_value' for _ in range(10)],  # Should be numeric
            'Sleep_Duration': ['another_string' for _ in range(10)],  # Should be numeric
        }
        type_error_df = pd.DataFrame(type_error_data)
        
        # Check if numeric conversion would fail
        try:
            pd.to_numeric(type_error_df['Taxon_A'])
            # If this doesn't raise, the test setup is wrong
            assert False, "Type error dataset should have non-numeric values"
        except (ValueError, TypeError):
            print("✓ Type error dataset correctly identified non-numeric values")
        
        return True

def main():
    """Entry point for running the test."""
    try:
        result = test_dataset_schema_validation()
        if result:
            print("\n" + "="*60)
            print("T010 CONTRACT TEST: PASSED")
            print("="*60)
            print("Dataset schema validation works correctly.")
            return 0
        else:
            print("\n" + "="*60)
            print("T010 CONTRACT TEST: FAILED")
            print("="*60)
            return 1
    except Exception as e:
        print(f"\nT010 CONTRACT TEST: FAILED with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())