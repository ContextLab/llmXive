"""
Contract test for model output schema.
Verifies that trained models and evaluation metrics follow the expected structure.
"""
import pytest
import json
import os
from pathlib import Path

@pytest.mark.skipif(
    not Path("data/models").exists(),
    reason="Models directory not generated yet"
)
def test_model_metrics_schema():
    """
    Contract Test: Verify model evaluation metrics file structure.
    
    Expected keys in metrics JSON:
    - auc_roc
    - precision
    - recall
    - f1_score
    - confusion_matrix
    - antibiotic_class
    - model_type
    """
    metrics_files = list(Path("data/models").glob("metrics_*.json"))
    
    if not metrics_files:
        pytest.skip("No metrics files found")
    
    required_keys = {
        "auc_roc",
        "precision",
        "recall",
        "f1_score",
        "confusion_matrix",
        "antibiotic_class",
        "model_type"
    }
    
    for metrics_file in metrics_files:
        with open(metrics_file, "r") as f:
            metrics = json.load(f)
        
        missing_keys = required_keys - set(metrics.keys())
        assert len(missing_keys) == 0, (
            f"Metrics file {metrics_file.name} missing keys: {missing_keys}. "
            f"Found: {metrics.keys()}"
        )

@pytest.mark.skipif(
    not Path("data/models").exists(),
    reason="Models directory not generated yet"
)
def test_model_artifacts_exist():
    """
    Contract Test: Verify model artifacts (pkl files) exist for trained models.
    """
    model_files = list(Path("data/models").glob("model_*.pkl"))
    
    assert len(model_files) > 0, (
        "No model artifacts (.pkl) found in data/models/. "
        "Ensure train_models.py has been executed."
    )
