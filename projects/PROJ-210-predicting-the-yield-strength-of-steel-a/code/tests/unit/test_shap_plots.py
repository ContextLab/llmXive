import pytest
import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestRegressor
from src.models.evaluate import generate_shap_summary_plot, SHAP_PLOTS_DIR

@pytest.fixture
def sample_data():
    """Create sample data for testing SHAP plot generation."""
    np.random.seed(42)
    n_samples = 100
    X = pd.DataFrame({
        'feature_1': np.random.randn(n_samples),
        'feature_2': np.random.randn(n_samples),
        'feature_3': np.random.randn(n_samples),
        'yield_strength': np.random.randn(n_samples) * 10 + 50
    })
    return X

@pytest.fixture
def trained_rf_model(sample_data):
    """Train a simple Random Forest model for testing."""
    X = sample_data.drop(columns=['yield_strength'])
    y = sample_data['yield_strength']
    model = RandomForestRegressor(n_estimators=10, random_state=42)
    model.fit(X, y)
    return model

def test_generate_shap_summary_plot_creates_file(trained_rf_model, sample_data):
    """Test that generate_shap_summary_plot creates a valid PNG file."""
    # Ensure the output directory exists
    os.makedirs(SHAP_PLOTS_DIR, exist_ok=True)
    
    # Generate the plot
    model_name = "test_rf"
    output_path = generate_shap_summary_plot(trained_rf_model, model_name, sample_data)
    
    # Verify the file exists
    assert os.path.exists(output_path), f"Output file {output_path} was not created"
    
    # Verify the filename matches the expected pattern
    expected_filename = f"model_{model_name}_shap_summary.png"
    assert output_path.endswith(expected_filename), f"Filename {output_path} does not match expected pattern"
    
    # Verify the file is not empty
    assert os.path.getsize(output_path) > 0, f"Output file {output_path} is empty"
    
    # Clean up
    os.remove(output_path)
    if not os.listdir(SHAP_PLOTS_DIR):  # Remove directory if empty
        os.rmdir(SHAP_PLOTS_DIR)

def test_generate_shap_summary_plot_with_large_dataset(trained_rf_model, sample_data):
    """Test SHAP plot generation with a larger dataset to ensure sampling works."""
    # Create a larger dataset
    large_data = pd.concat([sample_data] * 10, ignore_index=True)
    
    # Generate the plot
    model_name = "test_rf_large"
    output_path = generate_shap_summary_plot(trained_rf_model, model_name, large_data)
    
    # Verify the file exists
    assert os.path.exists(output_path), f"Output file {output_path} was not created"
    
    # Clean up
    os.remove(output_path)
    if not os.listdir(SHAP_PLOTS_DIR):  # Remove directory if empty
        os.rmdir(SHAP_PLOTS_DIR)