import pytest
import pandas as pd
import numpy as np
from code.ingestion import filter_missing_data, cap_outliers, impute_covariates

class TestFilterMissingData:
    def test_filter_missing_data_removes_nulls(self):
        """Test that filter_missing_data removes rows with null values in required columns."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'shannon': [3.5, np.nan, 3.8, 4.1],
            'sleep_duration': [7.0, 6.5, np.nan, 8.0],
            'age': [25, 30, 35, 40]
        })
        
        required_cols = ['participant_id', 'shannon', 'sleep_duration']
        filtered_df = filter_missing_data(df, required_cols)
        
        assert len(filtered_df) == 2
        assert 'P1' in filtered_df['participant_id'].values
        assert 'P4' in filtered_df['participant_id'].values
        assert 'P2' not in filtered_df['participant_id'].values
        assert 'P3' not in filtered_df['participant_id'].values

    def test_filter_missing_data_all_valid(self):
        """Test that filter_missing_data returns all rows if no nulls."""
        df = pd.DataFrame({
            'participant_id': ['P1', 'P2', 'P3'],
            'shannon': [3.5, 4.1, 3.8],
            'sleep_duration': [7.0, 6.5, 8.0],
            'age': [25, 30, 35]
        })
        
        required_cols = ['participant_id', 'shannon', 'sleep_duration']
        filtered_df = filter_missing_data(df, required_cols)
        
        assert len(filtered_df) == 3

class TestCapOutliers:
    def test_cap_outliers_below_threshold(self):
        """Test that cap_outliers caps values below the 1st percentile."""
        # Create data with an extreme outlier below 1st percentile
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] + [-100]  # -100 is extreme outlier
        df = pd.DataFrame({'sleep_duration': values})
        
        capped_df = cap_outliers(df, 'sleep_duration', lower_percentile=1, upper_percentile=99)
        
        # The outlier should be capped to the 1st percentile value
        min_capped = capped_df['sleep_duration'].min()
        assert min_capped > -100  # Should be capped

    def test_cap_outliers_above_threshold(self):
        """Test that cap_outliers caps values above the 99th percentile."""
        # Create data with an extreme outlier above 99th percentile
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10] + [1000]  # 1000 is extreme outlier
        df = pd.DataFrame({'sleep_duration': values})
        
        capped_df = cap_outliers(df, 'sleep_duration', lower_percentile=1, upper_percentile=99)
        
        # The outlier should be capped to the 99th percentile value
        max_capped = capped_df['sleep_duration'].max()
        assert max_capped < 1000  # Should be capped

    def test_cap_outliers_no_outliers(self):
        """Test that cap_outliers doesn't modify data without outliers."""
        df = pd.DataFrame({
            'sleep_duration': [6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0]
        })
        
        original_values = df['sleep_duration'].copy()
        capped_df = cap_outliers(df, 'sleep_duration', lower_percentile=1, upper_percentile=99)
        
        pd.testing.assert_series_equal(capped_df['sleep_duration'], original_values)

class TestImputeCovariates:
    def test_impute_median_for_numerical(self):
        """Test that impute_covariates uses median for numerical columns."""
        df = pd.DataFrame({
            'age': [25, np.nan, 35, 40, np.nan],
            'bmi': [22.0, 25.5, np.nan, 28.0, 30.0]
        })
        
        # Specify imputation strategy
        imputation_strategies = {
            'age': 'median',
            'bmi': 'median'
        }
        
        imputed_df = impute_covariates(df, imputation_strategies)
        
        # Check that no NaN values remain in specified columns
        assert not imputed_df['age'].isna().any()
        assert not imputed_df['bmi'].isna().any()
        
        # Verify median imputation
        median_age = df['age'].median()
        assert imputed_df.loc[1, 'age'] == median_age

    def test_impute_mode_for_categorical(self):
        """Test that impute_covariates uses mode for categorical columns."""
        df = pd.DataFrame({
            'antibiotic_use': ['No', 'Yes', 'No', np.nan, 'No', 'Yes']
        })
        
        imputation_strategies = {
            'antibiotic_use': 'mode'
        }
        
        imputed_df = impute_covariates(df, imputation_strategies)
        
        # Check that no NaN values remain
        assert not imputed_df['antibiotic_use'].isna().any()
        
        # Verify mode imputation (most common value is 'No')
        mode_val = df['antibiotic_use'].mode()[0]
        assert imputed_df.loc[3, 'antibiotic_use'] == mode_val

    def test_impute_mixed_strategies(self):
        """Test imputation with mixed strategies for different columns."""
        df = pd.DataFrame({
            'age': [25, np.nan, 35, 40],
            'bmi': [22.0, 25.5, np.nan, 28.0],
            'antibiotic_use': ['No', 'Yes', 'No', np.nan]
        })
        
        imputation_strategies = {
            'age': 'median',
            'bmi': 'median',
            'antibiotic_use': 'mode'
        }
        
        imputed_df = impute_covariates(df, imputation_strategies)
        
        # Check that no NaN values remain in any imputed column
        assert not imputed_df['age'].isna().any()
        assert not imputed_df['bmi'].isna().any()
        assert not imputed_df['antibiotic_use'].isna().any()