"""
Unit tests for cross-validation and model validation logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from src.models.validate import (
    perform_kfold_cross_validation,
    run_validation_pipeline,
    SC003_THRESHOLD
)
from src.models.fit import prepare_features_for_modeling

@pytest.fixture
def sample_data():
    """Create a sample dataset for testing."""
    np.random.seed(42)
    n_samples = 200
    
    # Create synthetic but realistic features
    data = {
        'eco_code': np.random.choice(['B00', 'B10', 'C00', 'D00'], n_samples),
        'avg_move_time_white': np.random.uniform(5.0, 20.0, n_samples),
        'avg_move_time_black': np.random.uniform(5.0, 20.0, n_samples),
        'material_imbalance_move5': np.random.uniform(-2.0, 2.0, n_samples),
        'elo_expected_prob': np.random.uniform(0.1, 0.9, n_samples),
    }
    
    # Create a target that has some correlation with features
    df = pd.DataFrame(data)
    df['outcome_deviation'] = (
        0.3 * (df['avg_move_time_white'] - 12.5) / 7.5 +
        0.2 * (df['avg_move_time_black'] - 12.5) / 7.5 +
        0.1 * df['material_imbalance_move5'] +
        np.random.normal(0, 0.1, n_samples)
    )
    
    return df

class TestCrossValidation:
    def test_perform_kfold_ridge_basic(self, sample_data):
        """Test basic Ridge cross-validation execution."""
        result = perform_kfold_cross_validation(
            sample_data, model_type='ridge', n_folds=3, random_state=42
        )
        
        assert 'model_type' in result
        assert result['model_type'] == 'ridge'
        assert 'mean_r2' in result
        assert 'std_r2' in result
        assert 'r2_scores' in result
        assert len(result['r2_scores']) == 3
        assert result['sc003_passed'] is True
        
        # Check R2 is in reasonable range (can be negative, but usually > -1 for real data)
        assert result['mean_r2'] > -1.0
        assert result['mean_r2'] <= 1.0

    def test_perform_kfold_glm_basic(self, sample_data):
        """Test basic GLM cross-validation execution."""
        result = perform_kfold_cross_validation(
            sample_data, model_type='glm', n_folds=3, random_state=42
        )
        
        assert 'model_type' in result
        assert result['model_type'] == 'glm'
        assert 'mean_r2' in result
        assert 'std_r2' in result
        assert 'r2_scores' in result
        assert len(result['r2_scores']) == 3

    def test_sc003_threshold_enforcement(self, sample_data):
        """Test that SC-003 threshold is properly enforced."""
        # Create data with high variance to potentially trigger SC-003
        # We use a very small dataset with high noise to force instability
        np.random.seed(123)
        unstable_data = pd.DataFrame({
            'eco_code': ['B00'] * 10,
            'avg_move_time_white': np.random.uniform(5, 20, 10),
            'avg_move_time_black': np.random.uniform(5, 20, 10),
            'material_imbalance_move5': np.random.uniform(-2, 2, 10),
            'elo_expected_prob': np.random.uniform(0.1, 0.9, 10),
            'outcome_deviation': np.random.uniform(-1, 1, 10) * 10  # High noise
        })
        
        # This might or might not trigger SC-003 depending on the split
        # but the function should handle it gracefully
        try:
            result = perform_kfold_cross_validation(
                unstable_data, model_type='ridge', n_folds=3, random_state=42
            )
            # If it doesn't raise, SC-003 was passed
            assert result['sc003_passed'] is True
        except RuntimeError as e:
            assert "SC-003" in str(e)

    def test_empty_dataset_raises_error(self):
        """Test that empty dataset raises appropriate error."""
        empty_df = pd.DataFrame(columns=['eco_code', 'outcome_deviation'])
        
        with pytest.raises(ValueError):
            perform_kfold_cross_validation(empty_df, model_type='ridge')

    def test_missing_target_column_raises_error(self, sample_data):
        """Test that missing target column raises error."""
        df = sample_data.drop(columns=['outcome_deviation'])
        
        with pytest.raises(ValueError):
            perform_kfold_cross_validation(df, model_type='ridge')

class TestValidationPipeline:
    def test_run_validation_pipeline(self, sample_data):
        """Test full validation pipeline execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "test_games.parquet"
            output_path = Path(tmpdir) / "test_validation.json"
            
            # Save sample data
            sample_data.to_parquet(data_path)
            
            # Run pipeline
            results = run_validation_pipeline(
                data_path=str(data_path),
                output_path=str(output_path),
                n_folds=3
            )
            
            # Check results structure
            assert 'ridge' in results
            assert 'glm' in results
            
            # Check output file was created
            assert output_path.exists()
            
            # Check JSON content
            with open(output_path, 'r') as f:
                saved_results = json.load(f)
            
            assert 'ridge' in saved_results
            assert 'glm' in saved_results

    def test_missing_data_file_raises_error(self):
        """Test that missing data file raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test.json"
            missing_data = Path(tmpdir) / "missing.parquet"
            
            with pytest.raises(FileNotFoundError):
                run_validation_pipeline(
                    data_path=str(missing_data),
                    output_path=str(output_path)
                )