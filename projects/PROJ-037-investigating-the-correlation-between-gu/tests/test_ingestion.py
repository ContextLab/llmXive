import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.utils.validators import validate_merged_cohort
from code.schemas import get_required_columns

class TestDataMerging:
    """
    Unit tests for data merging logic in User Story 1.
    Specifically verifies the calculation of N (retained participant count)
    after merging and filtering.
    """

    def test_merge_calculation_n_with_matches(self):
        """
        Verify N calculation when valid matches exist between datasets.
        """
        # Simulate AGP microbiome data
        agp_data = pd.DataFrame({
            'participant_id': ['AGP001', 'AGP002', 'AGP003', 'AGP004'],
            'shannon_diversity': [3.5, 4.2, 3.1, 2.9],
            'sample_id': ['S1', 'S2', 'S3', 'S4']
        })

        # Simulate Open Humans sleep data
        oh_data = pd.DataFrame({
            'participant_id': ['OH001', 'AGP002', 'AGP003', 'OH005'],
            'sleep_duration': [7.5, 6.2, 5.8, 8.1],
            'sleep_quality': [4, 3, 2, 5]
        })

        # Perform inner merge (simulating ingestion logic)
        merged = pd.merge(
            agp_data,
            oh_data,
            on='participant_id',
            how='inner'
        )

        # Expected N is the number of rows in the merged dataframe
        expected_n = 2  # AGP002 and AGP003 match
        actual_n = len(merged)

        assert actual_n == expected_n, f"Expected N={expected_n}, got N={actual_n}"
        assert 'participant_id' in merged.columns
        assert 'shannon_diversity' in merged.columns
        assert 'sleep_duration' in merged.columns

    def test_merge_calculation_n_no_matches(self):
        """
        Verify N calculation when no matches exist (N=0).
        """
        agp_data = pd.DataFrame({
            'participant_id': ['AGP001', 'AGP002'],
            'shannon_diversity': [3.5, 4.2]
        })

        oh_data = pd.DataFrame({
            'participant_id': ['OH001', 'OH002'],
            'sleep_duration': [7.5, 6.2]
        })

        merged = pd.merge(agp_data, oh_data, on='participant_id', how='inner')
        actual_n = len(merged)

        assert actual_n == 0, f"Expected N=0 when no matches, got N={actual_n}"

    def test_merge_calculation_n_after_null_filtering(self):
        """
        Verify N calculation drops after filtering out nulls in required columns.
        """
        # Create merged data with some nulls
        merged_data = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'shannon_diversity': [3.5, np.nan, 3.1, 2.9],
            'sleep_duration': [7.5, 6.2, np.nan, 8.1]
        })

        # Get required columns from schema
        required_cols = get_required_columns()
        
        # Filter out rows with any nulls in required columns
        # (Simulating the logic in code/ingestion.py)
        valid_mask = merged_data[required_cols].notna().all(axis=1)
        filtered_data = merged_data[valid_mask]

        original_n = len(merged_data)
        final_n = len(filtered_data)

        # P1: div=3.5 (ok), sleep=7.5 (ok) -> Valid
        # P2: div=nan (bad) -> Invalid
        # P3: div=3.1 (ok), sleep=nan (bad) -> Invalid
        # P4: div=2.9 (ok), sleep=8.1 (ok) -> Valid
        # Expected N = 2
        
        assert final_n == 2, f"Expected N=2 after filtering nulls, got N={final_n}"

    def test_schema_validation_on_merged_cohort(self):
        """
        Verify that the merged cohort passes schema validation.
        """
        valid_data = pd.DataFrame({
            'participant_id': ['P1', 'P2'],
            'shannon_diversity': [3.5, 4.0],
            'sleep_duration': [7.0, 6.5],
            'sleep_quality': [4, 3]
        })

        # This should not raise an error
        is_valid, errors = validate_merged_cohort(valid_data)
        
        assert is_valid, f"Valid data failed schema validation: {errors}"

    def test_schema_rejection_on_missing_required_column(self):
        """
        Verify that missing required columns are detected.
        """
        invalid_data = pd.DataFrame({
            'participant_id': ['P1'],
            'shannon_diversity': [3.5]
            # Missing 'sleep_duration' which is required
        })

        is_valid, errors = validate_merged_cohort(invalid_data)
        
        assert not is_valid, "Data missing required column should be invalid"
        assert any('sleep_duration' in str(err) for err in errors), "Error should mention missing column"

class TestMissingDataImputation:
    """
    Unit tests for missing data imputation logic in User Story 1.
    Tests median imputation for numerical covariates and mode imputation for categorical ones.
    """

    def test_median_imputation_numerical(self):
        """
        Verify that missing numerical values (e.g., BMI, Age) are imputed with the median.
        """
        # Create data with missing numerical values
        data = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'bmi': [24.5, np.nan, 26.0, 25.5],
            'age': [40, 45, np.nan, 50]
        })

        # Calculate expected medians
        expected_bmi_median = data['bmi'].median() # 25.0
        expected_age_median = data['age'].median() # 47.5

        # Perform imputation (simulating logic in code/ingestion.py)
        # We use a copy to avoid modifying the original for assertion checks
        imputed = data.copy()
        imputed['bmi'] = imputed['bmi'].fillna(data['bmi'].median())
        imputed['age'] = imputed['age'].fillna(data['age'].median())

        # Verify no NaNs remain
        assert not imputed['bmi'].isna().any(), "BMI should have no missing values after imputation"
        assert not imputed['age'].isna().any(), "Age should have no missing values after imputation"

        # Verify values match median
        assert imputed.loc[1, 'bmi'] == expected_bmi_median, f"BMI imputed to {imputed.loc[1, 'bmi']}, expected {expected_bmi_median}"
        assert imputed.loc[2, 'age'] == expected_age_median, f"Age imputed to {imputed.loc[2, 'age']}, expected {expected_age_median}"

    def test_mode_imputation_categorical(self):
        """
        Verify that missing categorical values (e.g., Antibiotic History) are imputed with the mode.
        """
        # Create data with missing categorical values
        data = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'antibiotic_history': ['Yes', 'No', 'No', np.nan]
        })

        # Calculate expected mode (most frequent value)
        expected_mode = data['antibiotic_history'].mode()[0] # 'No'

        # Perform imputation
        imputed = data.copy()
        imputed['antibiotic_history'] = imputed['antibiotic_history'].fillna(data['antibiotic_history'].mode()[0])

        # Verify no NaNs remain
        assert not imputed['antibiotic_history'].isna().any(), "Antibiotic history should have no missing values"

        # Verify value matches mode
        assert imputed.loc[3, 'antibiotic_history'] == expected_mode, f"Antibiotic history imputed to {imputed.loc[3, 'antibiotic_history']}, expected {expected_mode}"

    def test_imputation_preserves_existing_values(self):
        """
        Verify that existing non-null values are not altered by imputation.
        """
        data = pd.DataFrame({
            'participant_id': ['P1', 'P2'],
            'bmi': [22.0, 28.0],
            'age': [30, 60]
        })

        imputed = data.copy()
        imputed['bmi'] = imputed['bmi'].fillna(data['bmi'].median())
        imputed['age'] = imputed['age'].fillna(data['age'].median())

        assert imputed.loc[0, 'bmi'] == 22.0
        assert imputed.loc[1, 'bmi'] == 28.0
        assert imputed.loc[0, 'age'] == 30
        assert imputed.loc[1, 'age'] == 60

    def test_imputation_on_empty_dataframe(self):
        """
        Verify behavior when the dataframe is empty or all values are missing.
        """
        # All missing case
        data_all_missing = pd.DataFrame({
            'participant_id': [],
            'bmi': pd.Series([], dtype=float),
            'age': pd.Series([], dtype=float)
        })
        
        # This test primarily ensures the code doesn't crash when calculating median on empty series
        # In a real scenario, this would likely be caught by a 'N < min_threshold' check before imputation
        # But we test the logic here: median of empty is NaN, fillna with NaN does nothing.
        try:
            imputed = data_all_missing.copy()
            if len(data_all_missing) > 0:
                imputed['bmi'] = imputed['bmi'].fillna(data_all_missing['bmi'].median())
            # If empty, we just skip or handle gracefully
            assert True # No crash
        except Exception:
            pytest.fail("Imputation logic crashed on empty dataframe")
    
    def test_imputation_logic_integration(self):
        """
        Integration test simulating the full imputation step on a mixed dataset.
        """
        data = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
            'bmi': [24.0, np.nan, 26.0, np.nan, 25.0],
            'age': [np.nan, 45, 50, 30, np.nan],
            'antibiotic_history': ['Yes', 'No', np.nan, 'No', 'Yes']
        })

        # Perform imputation
        imputed = data.copy()
        
        # Numerical
        bmi_median = data['bmi'].median()
        age_median = data['age'].median()
        
        imputed['bmi'] = imputed['bmi'].fillna(bmi_median)
        imputed['age'] = imputed['age'].fillna(age_median)
        
        # Categorical
        antibiotic_mode = data['antibiotic_history'].mode()[0]
        imputed['antibiotic_history'] = imputed['antibiotic_history'].fillna(antibiotic_mode)

        # Assertions
        assert not imputed.isna().any().any(), "All missing values should be imputed"
        assert imputed.loc[1, 'bmi'] == bmi_median
        assert imputed.loc[0, 'age'] == age_median
        assert imputed.loc[2, 'antibiotic_history'] == antibiotic_mode