"""
Unit tests for preprocessing module.

Tests:
- Interaction feature generation
- Normalization logic
- Data validation
- Pipeline execution
"""
import os
import sys
import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.preprocess import (
    generate_interaction_features,
    normalize_features,
    validate_data_quality,
    run_preprocessing_pipeline,
    load_processed_data
)

class TestInteractionFeatures(unittest.TestCase):
    """Test interaction feature generation."""
    
    def setUp(self):
        """Create sample test data."""
        self.df = pd.DataFrame({
            'rolling_temperature': [400.0, 450.0, 500.0, 550.0],
            'grain_size': [10.5, 12.3, 14.1, 15.8],
            'composition_Mg': [0.5, 0.8, 1.2, 1.5],
            'composition_Si': [0.3, 0.4, 0.6, 0.7],
            'composition_Cu': [0.1, 0.2, 0.3, 0.4]
        })
    
    def test_interaction_feature_generation(self):
        """Test that interaction features are correctly generated."""
        result = generate_interaction_features(self.df.copy())
        
        # Check that interaction columns exist
        expected_interactions = [
            'rolling_temperature_x_composition_Mg',
            'rolling_temperature_x_composition_Si',
            'rolling_temperature_x_composition_Cu'
        ]
        
        for col in expected_interactions:
            self.assertIn(col, result.columns, f"Missing interaction column: {col}")
        
        # Verify calculation for one interaction
        expected_Mg_interaction = self.df['rolling_temperature'] * self.df['composition_Mg']
        actual_Mg_interaction = result['rolling_temperature_x_composition_Mg']
        
        pd.testing.assert_series_equal(
            expected_Mg_interaction.reset_index(drop=True),
            actual_Mg_interaction.reset_index(drop=True),
            check_names=False
        )
    
    def test_interaction_with_missing_elements(self):
        """Test interaction generation when some elements are missing."""
        df_partial = self.df.drop(columns=['composition_Cu'])
        result = generate_interaction_features(df_partial)
        
        # Should only create interactions for available elements
        self.assertIn('rolling_temperature_x_composition_Mg', result.columns)
        self.assertIn('rolling_temperature_x_composition_Si', result.columns)
        self.assertNotIn('rolling_temperature_x_composition_Cu', result.columns)
    
    def test_interaction_preserves_original_data(self):
        """Test that original data is preserved during interaction generation."""
        original_df = self.df.copy()
        result = generate_interaction_features(original_df)
        
        # Original columns should be unchanged
        pd.testing.assert_frame_equal(
            original_df,
            result[original_df.columns]
        )
    
    def test_interaction_with_empty_composition(self):
        """Test interaction generation when no composition columns exist."""
        df_no_comp = self.df.drop(columns=[col for col in self.df.columns if col.startswith('composition_')])
        result = generate_interaction_features(df_no_comp)
        
        # Should return dataframe unchanged (no interactions created)
        self.assertEqual(len(result.columns), len(df_no_comp.columns))
        self.assertFalse(any('_x_' in col for col in result.columns))

class TestNormalization(unittest.TestCase):
    """Test normalization logic."""
    
    def setUp(self):
        """Create sample test data."""
        self.df = pd.DataFrame({
            'rolling_temperature': [400.0, 450.0, 500.0, 550.0],
            'grain_size': [10.5, 12.3, 14.1, 15.8],
            'composition_Mg': [0.5, 0.8, 1.2, 1.5],
            'composition_Si': [0.3, 0.4, 0.6, 0.7],
            'source_study': ['A', 'B', 'C', 'D']
        })
    
    def test_normalization_applied(self):
        """Test that normalization is correctly applied."""
        # First generate interactions
        df_with_interactions = generate_interaction_features(self.df.copy())
        
        # Then normalize
        normalized_df, scaler, feature_groups = normalize_features(df_with_interactions)
        
        # Check that scaler was fitted
        self.assertIsNotNone(scaler)
        
        # Check that feature groups were tracked
        self.assertIn('original', feature_groups)
        self.assertIn('interactions', feature_groups)
        
        # Verify that normalized values have mean ~0 and std ~1
        for col in feature_groups['original'] + feature_groups['interactions']:
            if col in normalized_df.columns:
                col_mean = normalized_df[col].mean()
                col_std = normalized_df[col].std()
                self.assertAlmostEqual(col_mean, 0, delta=0.1, 
                                    msg=f"Column {col} mean should be ~0, got {col_mean}")
                self.assertAlmostEqual(col_std, 1, delta=0.1,
                                    msg=f"Column {col} std should be ~1, got {col_std}")
    
    def test_target_not_normalized(self):
        """Test that target variable is not normalized."""
        df_with_interactions = generate_interaction_features(self.df.copy())
        normalized_df, scaler, _ = normalize_features(df_with_interactions)
        
        # Target should be unchanged
        pd.testing.assert_series_equal(
            self.df['grain_size'],
            normalized_df['grain_size']
        )
    
    def test_categorical_not_normalized(self):
        """Test that categorical columns are not included in normalization."""
        df_with_interactions = generate_interaction_features(self.df.copy())
        normalized_df, scaler, feature_groups = normalize_features(df_with_interactions)
        
        # Categorical column should be unchanged
        pd.testing.assert_series_equal(
            self.df['source_study'],
            normalized_df['source_study']
        )
        
        # Should not be in feature groups
        self.assertNotIn('source_study', feature_groups.get('original', []))
        self.assertNotIn('source_study', feature_groups.get('interactions', []))

class TestDataValidation(unittest.TestCase):
    """Test data validation logic."""
    
    def test_valid_data(self):
        """Test validation on clean data."""
        df = pd.DataFrame({
            'rolling_temperature': [400.0, 450.0, 500.0],
            'grain_size': [10.5, 12.3, 14.1],
            'composition_Mg': [0.5, 0.8, 1.2]
        })
        
        result = validate_data_quality(df)
        
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['issues']), 0)
        self.assertEqual(result['record_count'], 3)
    
    def test_missing_values_detection(self):
        """Test detection of missing values."""
        df = pd.DataFrame({
            'rolling_temperature': [400.0, np.nan, 500.0],
            'grain_size': [10.5, 12.3, 14.1]
        })
        
        result = validate_data_quality(df)
        
        self.assertFalse(result['valid'])
        self.assertTrue(any('rolling_temperature' in issue for issue in result['issues']))
    
    def test_infinite_values_detection(self):
        """Test detection of infinite values."""
        df = pd.DataFrame({
            'rolling_temperature': [400.0, np.inf, 500.0],
            'grain_size': [10.5, 12.3, 14.1]
        })
        
        result = validate_data_quality(df)
        
        self.assertFalse(result['valid'])
        self.assertTrue(any('infinite' in issue for issue in result['issues']))
    
    def test_zero_variance_detection(self):
        """Test detection of zero variance in target."""
        df = pd.DataFrame({
            'rolling_temperature': [400.0, 450.0, 500.0],
            'grain_size': [10.0, 10.0, 10.0]  # Zero variance
        })
        
        result = validate_data_quality(df)
        
        self.assertFalse(result['valid'])
        self.assertTrue(any('zero variance' in issue for issue in result['issues']))

class TestPipeline(unittest.TestCase):
    """Test full preprocessing pipeline."""
    
    def test_pipeline_execution(self):
        """Test end-to-end pipeline execution."""
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.csv')
            output_path = os.path.join(tmpdir, 'output.csv')
            
            # Create sample input data
            df_input = pd.DataFrame({
                'rolling_temperature': [400.0, 450.0, 500.0, 550.0],
                'grain_size': [10.5, 12.3, 14.1, 15.8],
                'composition_Mg': [0.5, 0.8, 1.2, 1.5],
                'composition_Si': [0.3, 0.4, 0.6, 0.7],
                'source_study': ['A', 'B', 'C', 'D']
            })
            df_input.to_csv(input_path, index=False)
            
            # Run pipeline
            result = run_preprocessing_pipeline(input_path, output_path, normalize=True)
            
            # Verify results
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['input_records'], 4)
            self.assertEqual(result['output_records'], 4)
            self.assertTrue(os.path.exists(output_path))
            
            # Verify output contains interaction features
            df_output = pd.read_csv(output_path)
            self.assertTrue(any('_x_' in col for col in df_output.columns))
            
            # Verify scaler file was created
            scaler_path = output_path.replace('.csv', '_scaler.pkl')
            self.assertTrue(os.path.exists(scaler_path))
    
    def test_pipeline_without_normalization(self):
        """Test pipeline with normalization disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.csv')
            output_path = os.path.join(tmpdir, 'output.csv')
            
            # Create sample input data
            df_input = pd.DataFrame({
                'rolling_temperature': [400.0, 450.0, 500.0],
                'grain_size': [10.5, 12.3, 14.1],
                'composition_Mg': [0.5, 0.8, 1.2]
            })
            df_input.to_csv(input_path, index=False)
            
            # Run pipeline without normalization
            result = run_preprocessing_pipeline(input_path, output_path, normalize=False)
            
            # Verify results
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['features_normalized'], 0)
            
            # Verify no scaler file was created
            scaler_path = output_path.replace('.csv', '_scaler.pkl')
            self.assertFalse(os.path.exists(scaler_path))
    
    def test_pipeline_missing_input(self):
        """Test pipeline with missing input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'output.csv')
            
            with self.assertRaises(FileNotFoundError):
                run_preprocessing_pipeline('/nonexistent/path.csv', output_path)

if __name__ == '__main__':
    unittest.main()