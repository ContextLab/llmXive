import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from train import evaluate_models, TrainingResult, prepare_features_targets, load_processed_data
from seed import set_seed, get_seed

@pytest.fixture
def mock_data_csv(tmp_path):
    """Create a mock CSV file for testing."""
    data = {
        'pulse_duration': [10.0, 20.0, 30.0, 40.0, 50.0],
        'power': [100.0, 200.0, 300.0, 400.0, 500.0],
        'scanning_speed': [50.0, 60.0, 70.0, 80.0, 90.0],
        'wear_coefficient': [0.1, 0.2, 0.3, 0.4, 0.5]
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "test_data.csv"
    df.to_csv(csv_path, index=False)
    return str(csv_path)

@pytest.fixture
def mock_output_dir(tmp_path):
    """Create a temporary directory for output."""
    out_dir = tmp_path / "reports"
    out_dir.mkdir()
    return str(out_dir)

def test_prepare_features_targets(mock_data_csv):
    """Test that features and targets are correctly separated."""
    df = pd.read_csv(mock_data_csv)
    X, y, feature_names = prepare_features_targets(df, target_col='wear_coefficient')
    
    assert X.shape[0] == 5
    assert y.shape[0] == 5
    assert 'wear_coefficient' not in feature_names
    assert len(feature_names) == 3
    assert set(feature_names) == {'pulse_duration', 'power', 'scanning_speed'}

def test_evaluate_models_integration(mock_data_csv, mock_output_dir):
    """Test the full evaluate_models pipeline."""
    set_seed(42)
    output_file = os.path.join(mock_output_dir, "model_performance.json")
    
    # Run evaluation
    result = evaluate_models(
        input_path=mock_data_csv,
        output_path=output_file
    )
    
    # Verify output file exists
    assert Path(output_file).exists()
    
    # Verify result structure
    assert "best_model" in result
    assert "models_evaluated" in result
    assert result["best_model"]["name"] in ["LinearRegression", "RandomForest", "GradientBoosting"]
    assert isinstance(result["best_model"]["r2"], float)
    assert isinstance(result["best_model"]["mae"], float)
    assert isinstance(result["best_model"]["rmse"], float)
    
    # Verify JSON content
    with open(output_file, 'r') as f:
        json_data = json.load(f)
    
    assert json_data["selection_criteria"] == "highest_r2"
    assert len(json_data["models_evaluated"]) == 3

def test_evaluate_models_missing_input(tmp_path):
    """Test that evaluate_models fails gracefully on missing input."""
    set_seed(42)
    output_file = str(tmp_path / "reports/model_performance.json")
    
    with pytest.raises(FileNotFoundError):
        evaluate_models(
            input_path="nonexistent/path.csv",
            output_path=output_file
        )

def test_best_model_selection():
    """Test that the model with the highest R2 is selected."""
    # Create dummy results
    res1 = TrainingResult(model_name="ModelA", r2=0.5, mae=0.1, rmse=0.2)
    res2 = TrainingResult(model_name="ModelB", r2=0.8, mae=0.1, rmse=0.2)
    res3 = TrainingResult(model_name="ModelC", r2=0.3, mae=0.1, rmse=0.2)
    
    results = [res1, res2, res3]
    best = max(results, key=lambda x: x.r2)
    
    assert best.model_name == "ModelB"
    assert best.r2 == 0.8
