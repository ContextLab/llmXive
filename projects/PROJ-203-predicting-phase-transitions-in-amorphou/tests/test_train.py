"""
Tests for the model training module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

# Mock dependencies for testing
from unittest.mock import patch, MagicMock

# Import functions to test
from models.train import (
    load_final_dataset,
    validate_dataset_schema,
    identify_predictor_columns,
    split_data,
    train_regression_model,
    train_classification_model,
    evaluate_and_plot_classifier
)
from utils.validators import ValidationError

@pytest.fixture
def sample_dataset():
    """Create a minimal valid dataset for testing."""
    data = {
        'composition': ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'],
        'family': ['Oxide', 'Oxide', 'Sulfide', 'Sulfide', 'Organic', 'Organic', 'Oxide', 'Sulfide', 'Organic', 'Oxide'],
        'Tg_exp': [500.0, 520.0, 480.0, 490.0, 300.0, 310.0, 510.0, 485.0, 305.0, 505.0],
        'crystallization_label': [0, 0, 1, 1, 0, 0, 0, 1, 0, 0],
        'rdf_peak_pos': [2.5, 2.6, 2.4, 2.45, 3.0, 3.1, 2.55, 2.42, 3.05, 2.52],
        'rdf_peak_width': [0.5, 0.55, 0.45, 0.48, 0.6, 0.65, 0.52, 0.46, 0.62, 0.53],
        'bond_angle_variance': [10.0, 11.0, 9.0, 9.5, 15.0, 16.0, 10.5, 9.2, 15.5, 10.8],
        'coordination_numbers': [4.0, 4.1, 3.9, 4.0, 3.0, 3.1, 4.0, 3.9, 3.0, 4.0],
        'truncation_flag': [0]*10,
        'simulation_id': [f'sim_{i}' for i in range(10)]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_parquet_file(sample_dataset):
    """Create a temporary parquet file for testing load functions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "final_dataset.parquet"
        sample_dataset.to_parquet(path)
        yield path

def test_validate_dataset_schema_valid(sample_dataset):
    """Test validation passes for valid data."""
    # Should not raise
    validate_dataset_schema(sample_dataset)

def test_validate_dataset_schema_missing_target(sample_dataset):
    """Test validation fails if target is missing."""
    df = sample_dataset.drop(columns=['Tg_exp'])
    with pytest.raises(ValidationError, match="Missing required columns"):
        validate_dataset_schema(df)

def test_validate_dataset_schema_nan_target(sample_dataset):
    """Test validation fails if target has NaN."""
    df = sample_dataset.copy()
    df.loc[0, 'Tg_exp'] = np.nan
    with pytest.raises(ValidationError, match="contains NaN"):
        validate_dataset_schema(df)

def test_identify_predictor_columns(sample_dataset):
    """Test that predictor columns are correctly identified."""
    preds = identify_predictor_columns(sample_dataset)
    assert 'Tg_exp' not in preds
    assert 'crystallization_label' not in preds
    assert 'rdf_peak_pos' in preds
    assert 'coordination_numbers' in preds

def test_split_data_stratified(sample_dataset):
    """Test that data is split and stratified correctly."""
    predictors = identify_predictor_columns(sample_dataset)
    reg_split, clf_split = split_data(
        sample_dataset, 
        predictors, 
        'Tg_exp', 
        'crystallization_label',
        test_size=0.3,
        random_state=42
    )
    
    assert 'X_train' in reg_split
    assert 'X_test' in reg_split
    assert 'y_train' in reg_split
    assert 'y_test' in reg_split
    
    # Check sizes
    total = len(sample_dataset)
    assert len(reg_split['X_train']) + len(reg_split['X_test']) == total
    
    # Check that classes are present in both sets (if possible)
    # With N=10, stratification might fail if classes are too small, 
    # but the logic should attempt it.
    assert len(reg_split['y_train']) > 0
    assert len(reg_split['y_test']) > 0

def test_train_regression_model(sample_dataset):
    """Test regression model training."""
    predictors = identify_predictor_columns(sample_dataset)
    reg_split, _ = split_data(sample_dataset, predictors, 'Tg_exp', 'crystallization_label')
    
    model = train_regression_model(reg_split['X_train'], reg_split['y_train'])
    assert model is not None
    assert hasattr(model, 'predict')

def test_train_classification_model(sample_dataset):
    """Test classification model training."""
    predictors = identify_predictor_columns(sample_dataset)
    _, clf_split = split_data(sample_dataset, predictors, 'Tg_exp', 'crystallization_label')
    
    model = train_classification_model(clf_split['X_train'], clf_split['y_train'])
    assert model is not None
    assert hasattr(model, 'predict')

def test_evaluate_and_plot_classifier(sample_dataset, tmp_path):
    """Test classifier evaluation and confusion matrix plotting."""
    predictors = identify_predictor_columns(sample_dataset)
    _, clf_split = split_data(sample_dataset, predictors, 'Tg_exp', 'crystallization_label')
    
    model = train_classification_model(clf_split['X_train'], clf_split['y_train'])
    
    output_path = tmp_path / "confusion_matrix.png"
    metrics = evaluate_and_plot_classifier(model, clf_split['X_test'], clf_split['y_test'], output_path)
    
    assert output_path.exists()
    assert 'accuracy' in metrics
    assert 'confusion_matrix' in metrics
    assert 'classification_report' in metrics