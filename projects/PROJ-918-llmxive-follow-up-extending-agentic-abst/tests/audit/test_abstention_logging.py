import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from models.train_meta_critic import log_abstention_events
from xgboost import XGBClassifier

def create_dummy_data():
    """Create a dummy DataFrame for testing."""
    data = {
        'search_count': [1, 2, 3, 4, 5],
        'error_freq': [0.1, 0.2, 0.0, 0.5, 0.3],
        'token_usage': [100, 200, 150, 300, 250],
        'turn_number': [1, 2, 3, 4, 5],
        'embedding_distance': [0.1, 0.5, 0.2, 0.8, 0.4],
        'abstention_label': [0, 1, 0, 1, 1]  # Some should abstain
    }
    return pd.DataFrame(data)

def create_mock_model():
    """Create a mock XGBoost model that predicts abstention for specific conditions."""
    model = XGBClassifier(n_estimators=1, max_depth=1, random_state=42)
    # Fit on dummy data to initialize
    X = np.random.rand(10, 5)
    y = np.random.randint(0, 2, 10)
    model.fit(X, y)
    return model

def test_log_abstention_events_creates_file(tmp_path):
    """Test that log_abstention_events creates the audit log file."""
    df = create_dummy_data()
    model = create_mock_model()
    
    # Mock predictions to ensure some abstentions occur
    # We'll patch the model's predict method for this test
    original_predict = model.predict
    def mock_predict(X):
        # Predict abstention (1) for rows with high error_freq or high turn_number
        result = np.zeros(X.shape[0], dtype=int)
        # Force specific indices to abstain for testing
        result[1] = 1  # Row with error_freq 0.2
        result[3] = 1  # Row with error_freq 0.5
        result[4] = 1  # Row with error_freq 0.3
        return result
    
    model.predict = mock_predict
    
    feature_cols = ['search_count', 'error_freq', 'token_usage', 'turn_number', 'embedding_distance']
    output_path = tmp_path / "audit_log.json"
    
    log_abstention_events(model, df, feature_cols, {}, output_path)
    
    assert output_path.exists(), "Audit log file was not created"
    
    with open(output_path, 'r') as f:
        logs = json.load(f)
    
    assert len(logs) == 3, f"Expected 3 abstention events, got {len(logs)}"
    
    # Check structure of logged events
    for event in logs:
        assert "turn_number" in event
        assert "feature_vector" in event
        assert "prediction_confidence" in event
        assert "decision" in event
        assert event["decision"] == "ABSTAIN"
        assert "turn_number" in event["feature_vector"]

def test_log_abstention_events_content(tmp_path):
    """Test that the logged content matches the feature vector and turn number."""
    df = create_dummy_data()
    model = create_mock_model()
    
    # Force prediction of abstention for the row with turn_number=4
    def mock_predict(X):
        result = np.zeros(X.shape[0], dtype=int)
        result[3] = 1  # Row with turn_number=4
        return result
    
    model.predict = mock_predict
    
    feature_cols = ['search_count', 'error_freq', 'token_usage', 'turn_number', 'embedding_distance']
    output_path = tmp_path / "audit_log.json"
    
    log_abstention_events(model, df, feature_cols, {}, output_path)
    
    with open(output_path, 'r') as f:
        logs = json.load(f)
    
    # Find the event for turn_number=4
    target_event = next((e for e in logs if e["turn_number"] == 4), None)
    
    assert target_event is not None, "Event for turn_number=4 not found"
    assert target_event["feature_vector"]["turn_number"] == 4
    assert target_event["feature_vector"]["error_freq"] == 0.5
    assert target_event["feature_vector"]["search_count"] == 4