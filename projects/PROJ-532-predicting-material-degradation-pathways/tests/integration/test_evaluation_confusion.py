import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import pickle
import json

# Import the functions to test
from evaluation import generate_confusion_matrix, calculate_macro_f1, perform_permutation_test

@pytest.fixture
def sample_data():
    """Create sample multi-label data for testing."""
    np.random.seed(42)
    n_samples = 100
    n_labels = 3
    
    y_true = np.random.randint(0, 2, size=(n_samples, n_labels))
    y_pred = np.random.randint(0, 2, size=(n_samples, n_labels))
    
    label_names = ["pitting", "sc_c", "uniform_corrosion"]
    
    return y_true, y_pred, label_names

@pytest.fixture
def temp_model_artifact():
    """Create a temporary model artifact for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = Path(tmpdir) / "model.pkl"
        
        # Create a dummy model (using a simple mock)
        class DummyModel:
            def predict(self, X):
                return np.random.randint(0, 2, size=(X.shape[0], 3))
        
        model_artifact = {
            'model': DummyModel(),
            'label_names': ["pitting", "sc_c", "uniform_corrosion"],
            'n_labels': 3
        }
        
        with open(model_path, 'wb') as f:
            pickle.dump(model_artifact, f)
        
        yield model_path

@pytest.fixture
def temp_test_data():
    """Create temporary test data for integration testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "test_data.parquet"
        
        # Create sample dataframe
        df = pd.DataFrame({
            'feature_1': np.random.rand(100),
            'feature_2': np.random.rand(100),
            'feature_3': np.random.rand(100),
            'pitting_label': np.random.randint(0, 2, 100),
            'sc_c_label': np.random.randint(0, 2, 100),
            'uniform_corrosion_label': np.random.randint(0, 2, 100)
        })
        
        df.to_parquet(data_path)
        yield data_path

def test_generate_confusion_matrix_structure(sample_data):
    """Test that confusion matrix generation produces correct structure."""
    y_true, y_pred, label_names = sample_data
    
    result = generate_confusion_matrix(y_true, y_pred, label_names)
    
    # Check top-level keys
    assert "per_label_confusion_matrices" in result
    assert "error_modes" in result
    assert "summary" in result
    
    # Check summary structure
    assert result["summary"]["total_samples"] == len(y_true)
    assert result["summary"]["n_labels"] == len(label_names)
    assert result["summary"]["label_names"] == label_names
    
    # Check per-label structure
    for label in label_names:
        assert label in result["per_label_confusion_matrices"]
        assert label in result["error_modes"]
        
        cm_data = result["per_label_confusion_matrices"][label]
        assert "matrix" in cm_data
        assert "breakdown" in cm_data
        assert len(cm_data["matrix"]) == 2
        assert len(cm_data["matrix"][0]) == 2
        
        error_data = result["error_modes"][label]
        assert "true_negatives" in error_data
        assert "false_positives" in error_data
        assert "false_negatives" in error_data
        assert "true_positives" in error_data
        assert "fp_rate" in error_data
        assert "fn_rate" in error_data

def test_confusion_matrix_values(sample_data):
    """Test that confusion matrix values are calculated correctly."""
    y_true, y_pred, label_names = sample_data
    
    result = generate_confusion_matrix(y_true, y_pred, label_names)
    
    # Verify values are non-negative
    for label in label_names:
        breakdown = result["per_label_confusion_matrices"][label]["breakdown"]
        assert breakdown["TN"] >= 0
        assert breakdown["FP"] >= 0
        assert breakdown["FN"] >= 0
        assert breakdown["TP"] >= 0
        
        # Sum of breakdown should equal total samples
        assert breakdown["TN"] + breakdown["FP"] + breakdown["FN"] + breakdown["TP"] == len(y_true)

def test_error_mode_rates(sample_data):
    """Test that error mode rates are calculated correctly."""
    y_true, y_pred, label_names = sample_data
    
    result = generate_confusion_matrix(y_true, y_pred, label_names)
    
    for label in label_names:
        error_data = result["error_modes"][label]
        
        # FP rate should be between 0 and 1
        assert 0.0 <= error_data["fp_rate"] <= 1.0
        # FN rate should be between 0 and 1
        assert 0.0 <= error_data["fn_rate"] <= 1.0
        
        # Precision and recall should be between 0 and 1
        if error_data["precision"] is not None:
            assert 0.0 <= error_data["precision"] <= 1.0
        if error_data["recall"] is not None:
            assert 0.0 <= error_data["recall"] <= 1.0

def test_macro_f1_calculation():
    """Test macro-F1 calculation with known values."""
    # Create perfect prediction
    y_true = np.array([[1, 0, 1], [0, 1, 0], [1, 1, 0]])
    y_pred = np.array([[1, 0, 1], [0, 1, 0], [1, 1, 0]])
    
    f1 = calculate_macro_f1(y_true, y_pred)
    assert f1 == 1.0
    
    # Create random prediction (should be less than 1.0)
    y_pred_random = np.array([[0, 1, 0], [1, 0, 1], [0, 0, 1]])
    f1_random = calculate_macro_f1(y_true, y_pred_random)
    assert f1_random < 1.0

def test_permutation_test(sample_data):
    """Test permutation test execution."""
    y_true, y_pred, _ = sample_data
    
    p_value = perform_permutation_test(y_true, y_pred, n_permutations=100)
    
    assert 0.0 <= p_value <= 1.0
    # With random data, p-value should not be extremely small
    assert p_value > 0.001

def test_confusion_matrix_file_output(sample_data, tmp_path):
    """Test that confusion matrix can be saved to file."""
    y_true, y_pred, label_names = sample_data
    output_path = tmp_path / "confusion_report.json"
    
    result = generate_confusion_matrix(y_true, y_pred, label_names, output_path)
    
    assert output_path.exists()
    
    # Verify file content
    with open(output_path, 'r') as f:
        saved_result = json.load(f)
    
    assert saved_result["summary"]["total_samples"] == len(y_true)
    assert "error_modes" in saved_result

def test_error_mode_identification():
    """Test that specific error modes (pitting vs SCC) are correctly identified."""
    # Create data with known error patterns
    n_samples = 50
    y_true = np.zeros((n_samples, 2))
    y_pred = np.zeros((n_samples, 2))
    
    # Set up specific errors
    # First 10: True pitting, predicted no pitting (FN)
    y_true[:10, 0] = 1
    y_pred[:10, 0] = 0
    
    # Next 10: No pitting, predicted pitting (FP)
    y_true[10:20, 0] = 0
    y_pred[10:20, 0] = 1
    
    # Rest: Correct predictions
    y_true[20:, 0] = 0
    y_pred[20:, 0] = 0
    
    label_names = ["pitting", "sc_c"]
    
    result = generate_confusion_matrix(y_true, y_pred, label_names)
    
    # Check pitting error modes
    pitting_errors = result["error_modes"]["pitting"]
    assert pitting_errors["false_negatives"] == 10
    assert pitting_errors["false_positives"] == 10
    assert pitting_errors["true_positives"] == 0
    assert pitting_errors["true_negatives"] == 30

def test_integration_evaluation_workflow(temp_model_artifact, temp_test_data, tmp_path):
    """Integration test for the full evaluation workflow."""
    from evaluation import run_evaluation_pipeline
    
    output_dir = tmp_path / "evaluation_output"
    output_dir.mkdir()
    
    # Run the pipeline
    results = run_evaluation_pipeline(
        model_path=temp_model_artifact,
        data_path=temp_test_data,
        output_dir=output_dir
    )
    
    # Verify results structure
    assert "macro_f1" in results
    assert "permutation_test" in results
    assert "confusion_matrix_summary" in results
    assert "error_modes" in results
    
    # Verify files were created
    assert (output_dir / "evaluation_report.json").exists()
    assert (output_dir / "confusion_matrix_report.json").exists()
    
    # Verify report content
    assert results["macro_f1"] >= 0.0
    assert results["macro_f1"] <= 1.0
    assert results["permutation_test"]["p_value"] >= 0.0
    assert results["permutation_test"]["p_value"] <= 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])