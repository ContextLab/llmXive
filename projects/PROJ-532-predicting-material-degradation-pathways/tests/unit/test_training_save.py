import os
import json
import pickle
import pytest
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

# Ensure code is in path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from training import save_artifacts, load_training_data, run_training_pipeline

@pytest.fixture
def mock_model():
    """Create a mock Random Forest model for testing."""
    model = RandomForestClassifier(n_estimators=2, random_state=42)
    # Fit on dummy data to have feature_names_in_
    X_dummy = np.random.rand(10, 5)
    y_dummy = np.random.randint(0, 2, (10, 3))
    model.fit(X_dummy, y_dummy)
    return model

@pytest.fixture
def mock_mlb():
    """Create a mock MultiLabelBinarizer."""
    mlb = MultiLabelBinarizer()
    y_dummy = [[1, 2], [2, 3], [1, 3]]
    mlb.fit(y_dummy)
    return mlb

@pytest.fixture
def mock_metrics():
    """Create mock metrics."""
    return {
        "macro_f1": 0.85,
        "classification_report": {"class1": {"f1-score": 0.85}},
        "confusion_matrices_per_class": [{"class": "class1", "matrix": [[1, 0], [0, 1]]}],
        "y_pred_shape": [10, 3]
    }

def test_save_artifacts_creates_files(tmp_path, mock_model, mock_mlb, mock_metrics):
    """Test that save_artifacts creates both .pkl and .json files."""
    model_path = tmp_path / "model.pkl"
    report_path = tmp_path / "report.json"

    save_artifacts(
        model=mock_model,
        metrics=mock_metrics,
        mlb=mock_mlb,
        output_model_path=str(model_path),
        output_report_path=str(report_path)
    )

    assert model_path.exists(), "Model artifact .pkl file not created"
    assert report_path.exists(), "Training report .json file not created"

def test_save_artifacts_pickle_content(tmp_path, mock_model, mock_mlb, mock_metrics):
    """Test that the saved .pkl file contains the correct objects."""
    model_path = tmp_path / "model.pkl"
    report_path = tmp_path / "report.json"

    save_artifacts(
        model=mock_model,
        metrics=mock_metrics,
        mlb=mock_mlb,
        output_model_path=str(model_path),
        output_report_path=str(report_path)
    )

    with open(model_path, 'rb') as f:
        data = pickle.load(f)

    assert "model" in data, "Model not saved in artifact"
    assert "mlb" in data, "MLB not saved in artifact"
    assert "metrics" in data, "Metrics not saved in artifact"
    
    # Verify types
    assert isinstance(data["model"], RandomForestClassifier)
    assert isinstance(data["mlb"], MultiLabelBinarizer)
    assert isinstance(data["metrics"], dict)

def test_save_artifacts_json_content(tmp_path, mock_model, mock_mlb, mock_metrics):
    """Test that the saved .json file contains valid JSON and expected keys."""
    model_path = tmp_path / "model.pkl"
    report_path = tmp_path / "report.json"

    save_artifacts(
        model=mock_model,
        metrics=mock_metrics,
        mlb=mock_mlb,
        output_model_path=str(model_path),
        output_report_path=str(report_path)
    )

    with open(report_path, 'r') as f:
        report = json.load(f)

    assert report["artifact_type"] == "ModelArtifact"
    assert report["model_type"] == "RandomForestClassifier"
    assert "metrics" in report
    assert "classes" in report
    assert "feature_names" in report

def test_run_training_pipeline_integration(tmp_path, monkeypatch):
    """Integration test for the full pipeline (mocked data generation)."""
    # Create dummy parquet file
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    train_path = data_dir / "train_set.parquet"
    
    # Create dummy data
    df = pd.DataFrame({
        'Fe': [0.5, 0.6, 0.7],
        'Cr': [0.1, 0.2, 0.3],
        'Ni': [0.2, 0.3, 0.4],
        'labels': [['pitting'], ['sc stress corrosion cracking'], ['uniform corrosion']]
    })
    df.to_parquet(train_path)
    
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    model_path = results_dir / "artifacts" / "model.pkl"
    report_path = results_dir / "metrics" / "training_report.json"
    results_dir / "artifacts" / "metrics".mkdir(parents=True, exist_ok=True)
    
    # Patch paths in the function if needed, or just call with explicit paths
    # Since run_training_pipeline uses defaults, we need to ensure the file exists at the default location
    # or pass the path. We'll pass the path.
    
    metrics = run_training_pipeline(
        train_data_path=str(train_path),
        output_model_path=str(model_path),
        output_report_path=str(report_path),
        random_seed=42
    )
    
    assert metrics is not None
    assert "macro_f1" in metrics
    assert model_path.exists()
    assert report_path.exists()