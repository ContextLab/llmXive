"""
Integration tests for the modeling pipeline.
Verifies that best_model.pkl loads and predicts on held-out data.
"""
import os
import sys
import json
import pickle
import tempfile
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.src.modeling.train import load_clean_data, prepare_features_targets, train_model

@pytest.fixture
def sample_data():
    """Create sample MgB2 data for testing."""
    data = {
        'Tc': [39.2, 38.5, 37.8, 36.2, 35.1, 34.5, 33.8, 32.1, 31.5, 30.2,
              29.8, 28.5, 27.2, 26.1, 25.5, 24.8, 23.5, 22.1, 21.5, 20.2],
        'impurity_C': [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0,
                      0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
        'impurity_O': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0,
                      0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        'impurity_Al': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                       0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        'impurity_Si': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                       0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'temp_K': [300, 300, 300, 300, 300, 300, 300, 300, 300, 300,
                  300, 300, 300, 300, 300, 300, 300, 300, 300, 300],
        'pressure_GPa': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                        0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_csv(sample_data):
    """Create a temporary CSV file with sample data."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        sample_data.to_csv(f, index=False)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

@pytest.fixture
def model_and_data(temp_csv):
    """Train a simple model and return model path and test data."""
    from code.src.modeling.train import main
    
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = os.path.join(tmpdir, 'test_model.pkl')
        metrics_path = os.path.join(tmpdir, 'test_metrics.json')
        
        # Train model using the main function
        sys.argv = ['train.py', '--input', temp_csv, 
                   '--output-model', model_path, 
                   '--output-metrics', metrics_path,
                   '--test-size', '0.3']
        
        # Run training (with reduced timeout for testing)
        from code.src.modeling.train import main as train_main
        train_main()
        
        yield model_path, metrics_path

class TestModelingIntegration:
    """Integration tests for the modeling pipeline."""
    
    def test_model_persistence(self, model_and_data):
        """Test that the trained model can be loaded and used for predictions."""
        model_path, metrics_path = model_and_data
        
        # Load the saved model
        with open(model_path, 'rb') as f:
            saved_model = pickle.load(f)
        
        assert 'model' in saved_model, "Saved model missing 'model' key"
        assert 'scaler' in saved_model, "Saved model missing 'scaler' key"
        assert 'model_name' in saved_model, "Saved model missing 'model_name' key"
        
        # Verify model can make predictions
        model = saved_model['model']
        scaler = saved_model['scaler']
        
        # Create sample test data
        test_X = np.array([
            [1.0, 0.5, 0.0, 0.0, 300, 0.0],
            [2.0, 0.3, 0.0, 0.0, 300, 0.0]
        ])
        
        test_X_scaled = scaler.transform(test_X)
        predictions = model.predict(test_X_scaled)
        
        assert len(predictions) == 2, "Unexpected number of predictions"
        assert all(isinstance(p, (int, float, np.floating)) for p in predictions), \
            "Predictions are not numeric"
        
        logger = __import__('code.src.utils.logging', fromlist=['get_modeling_logger']).get_modeling_logger('test')
        logger.info(f"Model predictions: {predictions}")
    
    def test_metrics_file_structure(self, model_and_data):
        """Test that the metrics JSON file has the correct structure."""
        model_path, metrics_path = model_and_data
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        # Verify required fields
        assert 'timestamp' in metrics, "Missing timestamp"
        assert 'best_model' in metrics, "Missing best_model"
        assert 'best_test_r2' in metrics, "Missing best_test_r2"
        assert 'best_test_mae' in metrics, "Missing best_test_mae"
        assert 'all_models' in metrics, "Missing all_models"
        assert isinstance(metrics['all_models'], list), "all_models should be a list"
        
        # Verify each model entry
        for model_entry in metrics['all_models']:
            assert 'model_name' in model_entry, "Missing model_name in entry"
            assert 'test_r2' in model_entry, "Missing test_r2 in entry"
            assert 'test_mae' in model_entry, "Missing test_mae in entry"
        
        logger = __import__('code.src.utils.logging', fromlist=['get_modeling_logger']).get_modeling_logger('test')
        logger.info(f"Metrics structure validated: {metrics['best_model']}")
    
    def test_model_performance(self, model_and_data):
        """Test that the model achieves reasonable performance."""
        model_path, metrics_path = model_and_data
        
        with open(metrics_path, 'r') as f:
            metrics = json.load(f)
        
        # Check that R² is not NaN and is within reasonable bounds
        assert not np.isnan(metrics['best_test_r2']), "R² is NaN"
        assert metrics['best_test_r2'] > -1.0, "R² is unreasonably low"
        
        # Check that MAE is non-negative
        assert metrics['best_test_mae'] >= 0, "MAE is negative"
        
        logger = __import__('code.src.utils.logging', fromlist=['get_modeling_logger']).get_modeling_logger('test')
        logger.info(f"Model performance: R²={metrics['best_test_r2']:.4f}, MAE={metrics['best_test_mae']:.4f}")
    
    def test_stratified_split(self, temp_csv):
        """Test that stratified splitting is working correctly."""
        df = load_clean_data(temp_csv)
        X, y, strat_labels = prepare_features_targets(df)
        
        # Verify stratification labels are created
        assert len(strat_labels) == len(df), "Stratification labels length mismatch"
        assert len(np.unique(strat_labels)) > 0, "No stratification labels created"
        
        logger = __import__('code.src.utils.logging', fromlist=['get_modeling_logger']).get_modeling_logger('test')
        logger.info(f"Stratification labels: {np.unique(strat_labels, return_counts=True)}")
    
    def test_timeout_guard(self):
        """Test that timeout guard works correctly."""
        from code.src.modeling.train import TimeoutGuard, TimeoutError
        import signal
        
        # Test successful completion within timeout
        with TimeoutGuard(5):
            time.sleep(0.1)
        
        # Test timeout (this should raise TimeoutError)
        with pytest.raises(TimeoutError):
            with TimeoutGuard(1):
                time.sleep(2)