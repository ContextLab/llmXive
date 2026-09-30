import os
import json
import tempfile
import pytest
from pathlib import Path
import numpy as np
import pandas as pd
import pickle

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from classification.visualize_importance import (
    load_filtered_data_for_importance,
    load_classifier,
    load_shap_values,
    generate_importance_plot,
    generate_beeswarm_plot,
    save_metrics_json,
    run_visualization_pipeline
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with test data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create filtered training data
        X = np.random.rand(100, 10)
        y = np.random.randint(0, 2, 100)
        df = pd.DataFrame(X)
        df['label'] = y
        df.to_csv(tmpdir / "filtered_train.csv", index=False)
        
        # Create dummy classifier
        model = {"type": "dummy", "params": {}}
        with open(tmpdir / "classifier.pkl", 'wb') as f:
            pickle.dump(model, f)
        
        # Create dummy SHAP values
        shap_values = np.random.rand(100, 10)
        feature_names = [f"feature_{i}" for i in range(10)]
        shap_data = {
            "shap_values": shap_values.tolist(),
            "feature_names": feature_names
        }
        with open(tmpdir / "feature_importance.json", 'w') as f:
            json.dump(shap_data, f)
        
        yield tmpdir

def test_load_filtered_data(temp_data_dir):
    """Test loading filtered training data."""
    X, y, feature_names = load_filtered_data_for_importance(str(temp_data_dir))
    
    assert X.shape == (100, 10)
    assert y.shape == (100,)
    assert len(feature_names) == 10
    assert all(f.startswith("feature_") for f in feature_names)

def test_load_classifier(temp_data_dir):
    """Test loading classifier model."""
    model = load_classifier(str(temp_data_dir / "classifier.pkl"))
    assert model["type"] == "dummy"

def test_load_shap_values(temp_data_dir):
    """Test loading SHAP values."""
    shap_values, feature_names = load_shap_values(str(temp_data_dir / "feature_importance.json"))
    
    assert shap_values.shape == (100, 10)
    assert len(feature_names) == 10

def test_generate_importance_plot(temp_data_dir):
    """Test generating importance plot."""
    shap_values, feature_names = load_shap_values(str(temp_data_dir / "feature_importance.json"))
    output_path = temp_data_dir / "test_importance.png"
    
    generate_importance_plot(shap_values, feature_names, str(output_path))
    
    assert output_path.exists()
    assert output_path.stat().st_size > 0

def test_save_metrics_json(temp_data_dir):
    """Test saving metrics to JSON."""
    metrics_data = {
        "test": "value",
        "number": 42
    }
    output_path = temp_data_dir / "test_metrics.json"
    
    save_metrics_json(metrics_data, str(output_path))
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded = json.load(f)
    assert loaded == metrics_data

def test_run_visualization_pipeline(temp_data_dir):
    """Test full visualization pipeline."""
    output_dir = temp_data_dir / "output"
    
    metrics = run_visualization_pipeline(
        data_dir=str(temp_data_dir),
        model_path=str(temp_data_dir / "classifier.pkl"),
        shap_path=str(temp_data_dir / "feature_importance.json"),
        output_dir=str(output_dir)
    )
    
    # Check outputs exist
    assert (output_dir / "feature_importance.png").exists()
    assert (output_dir / "feature_beeswarm.png").exists()
    assert (output_dir / "metrics.json").exists()
    
    # Check metrics content
    with open(output_dir / "metrics.json", 'r') as f:
        loaded_metrics = json.load(f)
    
    assert "num_features" in loaded_metrics
    assert "num_samples" in loaded_metrics
    assert "top_features" in loaded_metrics
    assert "output_files" in loaded_metrics
