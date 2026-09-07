import pytest
import pandas as pd
import numpy as np
import os
import json
from code.preprocess import (
    clean_data, 
    normalize_and_flag_outliers, 
    log_outlier_removal, 
    extract_features,
    detect_outliers_iqr
)

class TestPreprocess:
    @pytest.fixture
    def sample_data(self):
        """Create a sample dataframe with known outliers."""
        data = {
            'Participant_ID': [1, 1, 1, 2, 2, 2, 3, 3, 3],
            'Condition': ['Rejection', 'Rejection', 'Rejection', 
                          'Control', 'Control', 'Control', 
                          'Rejection', 'Rejection', 'Rejection'],
            'Reaction Time': [200, 210, 5000,  # 5000 is outlier in Rejection
                              200, 210, 220,  # No outlier in Control
                              205, 215, 225],
            'Mood': [3, 4, 2, 5, 5, 4, 3, 4, 3]
        }
        return pd.DataFrame(data)

    def test_clean_data_removes_nan(self, sample_data):
        df = sample_data.copy()
        df.loc[0, 'Reaction Time'] = np.nan
        cleaned = clean_data(df)
        assert len(cleaned) < len(df)
        assert cleaned['Reaction Time'].isna().sum() == 0

    def test_detect_outliers_iqr_per_condition(self, sample_data):
        """Test that outliers are detected per condition group."""
        df = sample_data.copy()
        df_clean = clean_data(df)
        result_df = detect_outliers_iqr(df_clean, group_col='Condition', value_col='Reaction Time')
        
        # Check that is_outlier column exists
        assert 'is_outlier' in result_df.columns
        
        # In Rejection group: 5000 should be outlier (Q1=200, Q3=210? No, let's calc)
        # Rejection values: 200, 210, 5000, 205, 215, 225 -> sorted: 200, 205, 210, 215, 225, 5000
        # Q1 (25%) ~ 205, Q3 (75%) ~ 225. IQR = 20.
        # Upper bound = 225 + 1.5*20 = 255. 5000 > 255 -> True.
        rejection_outliers = result_df[(result_df['Condition'] == 'Rejection') & result_df['is_outlier']]
        assert len(rejection_outliers) >= 1
        
        # Control group: 200, 210, 220. No outliers expected.
        control_outliers = result_df[(result_df['Condition'] == 'Control') & result_df['is_outlier']]
        assert len(control_outliers) == 0

    def test_log_outlier_removal_creates_file(self, sample_data, tmp_path):
        """Test T042: log_outlier_removal writes correct JSON structure."""
        df = sample_data.copy()
        df_clean = clean_data(df)
        df_proc, thresholds = normalize_and_flag_outliers(df_clean)
        
        output_file = tmp_path / "outlier_log.json"
        log_outlier_removal(df_proc, str(output_file), thresholds)
        
        assert os.path.exists(output_file)
        
        with open(output_file, 'r') as f:
            report = json.load(f)
        
        assert 'summary' in report
        assert 'timestamp' in report
        
        # Check schema per task T042
        for entry in report['summary']:
            assert 'condition' in entry
            assert 'flagged_count' in entry
            assert 'iqr_threshold' in entry
            assert isinstance(entry['flagged_count'], int)
            assert isinstance(entry['iqr_threshold'], float)

    def test_extract_features_aggregates(self, sample_data):
        df = sample_data.copy()
        df_clean = clean_data(df)
        features = extract_features(df_clean)
        
        # Should have one row per participant-condition combination
        assert len(features) == 3 # P1-Rec, P2-Con, P3-Rec
        assert 'Reaction Time' in features.columns
        assert features['Reaction Time'].dtype in [np.float64, np.int64]