"""
Contract test for model output schema.

This test validates that the model artifacts produced by the pipeline
(T027) conform to the required schema defined in the project specifications.

It checks:
1. Presence of required top-level keys in model metadata JSON.
2. Schema of the evaluation metrics dictionary.
3. Structure of the feature importance data.
4. Validity of the model weights file structure (if applicable).

Run with: pytest tests/contract/test_model_output_schema.py -v
"""
import os
import json
import pytest
from pathlib import Path
from typing import Any, Dict, List

# Constants derived from project plan.md and spec.md
REQUIRED_MODEL_KEYS = {
    "model_type",
    "antibiotic_class",
    "feature_set_version",
    "training_config",
    "evaluation_metrics",
    "feature_importance",
    "artifact_hash"
}

REQUIRED_METRIC_KEYS = {
    "auc_roc",
    "precision",
    "recall",
    "f1_score",
    "confusion_matrix"
}

# Expected paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
MODEL_OUTPUT_DIR = PROJECT_ROOT / "data" / "models"


def _find_latest_model_json() -> Path:
    """
    Locate the most recent model metadata JSON file in data/models/.
    
    Raises:
        FileNotFoundError: If no model JSON files are found.
    """
    if not MODEL_OUTPUT_DIR.exists():
        raise FileNotFoundError(f"Model output directory not found: {MODEL_OUTPUT_DIR}")
    
    json_files = list(MODEL_OUTPUT_DIR.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No model JSON files found in {MODEL_OUTPUT_DIR}")
    
    # Return the most recently modified file
    return max(json_files, key=os.path.getmtime)


def test_model_metadata_schema():
    """
    Contract Test: Verify the top-level schema of model metadata JSON.
    
    Ensures that every model output file contains the mandatory keys
    required for downstream validation and reproducibility.
    """
    model_file = _find_latest_model_json()
    
    with open(model_file, 'r') as f:
        metadata = json.load(f)
    
    assert isinstance(metadata, dict), "Model metadata must be a JSON object"
    
    missing_keys = REQUIRED_MODEL_KEYS - set(metadata.keys())
    assert not missing_keys, (
        f"Model metadata missing required keys: {missing_keys}. "
        f"Expected: {REQUIRED_MODEL_KEYS}"
    )


def test_evaluation_metrics_schema():
    """
    Contract Test: Verify the structure of the 'evaluation_metrics' section.
    
    Validates that the metrics dictionary contains all required performance
    indicators and that 'confusion_matrix' is a list of lists (or similar).
    """
    model_file = _find_latest_model_json()
    
    with open(model_file, 'r') as f:
        metadata = json.load(f)
    
    metrics = metadata.get("evaluation_metrics", {})
    assert isinstance(metrics, dict), "evaluation_metrics must be a dictionary"
    
    missing_metrics = REQUIRED_METRIC_KEYS - set(metrics.keys())
    assert not missing_metrics, (
        f"Evaluation metrics missing required keys: {missing_metrics}"
    )
    
    # Validate confusion matrix structure
    cm = metrics.get("confusion_matrix")
    assert isinstance(cm, (list, tuple)), "confusion_matrix must be a list or tuple"
    if len(cm) > 0:
        assert isinstance(cm[0], (list, tuple)), "confusion_matrix rows must be lists"


def test_feature_importance_structure():
    """
    Contract Test: Verify the structure of 'feature_importance'.
    
    Expects a list of dictionaries, where each dictionary represents a feature
    with at least 'feature_name' and 'importance_score'.
    """
    model_file = _find_latest_model_json()
    
    with open(model_file, 'r') as f:
        metadata = json.load(f)
    
    importance_data = metadata.get("feature_importance", [])
    assert isinstance(importance_data, list), "feature_importance must be a list"
    
    if len(importance_data) > 0:
        first_entry = importance_data[0]
        assert isinstance(first_entry, dict), "Each feature importance entry must be a dict"
        assert "feature_name" in first_entry, "Feature entry must have 'feature_name'"
        assert "importance_score" in first_entry, "Feature entry must have 'importance_score'"


def test_model_type_validity():
    """
    Contract Test: Ensure 'model_type' is a recognized string.
    
    Validates that the model type matches one of the expected algorithm names
    defined in the project (e.g., 'LogisticRegression', 'RandomForest').
    """
    model_file = _find_latest_model_json()
    
    with open(model_file, 'r') as f:
        metadata = json.load(f)
    
    model_type = metadata.get("model_type", "")
    valid_types = {"LogisticRegression", "RandomForest", "XGBoost", "SVM"}
    
    # Allow for variations in naming (e.g., "Logistic Regression" vs "LogisticRegression")
    # but enforce that it is not empty and matches a known pattern
    assert model_type is not None and len(model_type) > 0, (
        "model_type cannot be empty or null"
    )
    
    # Normalize for comparison
    normalized_type = model_type.replace(" ", "").replace("_", "")
    valid_normalized = {t.replace(" ", "").replace("_", "") for t in valid_types}
    
    assert normalized_type in valid_normalized, (
        f"Unknown model_type '{model_type}'. Expected one of: {valid_types}"
    )


def test_antibiotic_class_present():
    """
    Contract Test: Verify 'antibiotic_class' is a non-empty string.
    
    Ensures the model is explicitly tagged with the target antibiotic class
    for which it was trained.
    """
    model_file = _find_latest_model_json()
    
    with open(model_file, 'r') as f:
        metadata = json.load(f)
    
    ab_class = metadata.get("antibiotic_class")
    assert ab_class is not None, "antibiotic_class is missing"
    assert isinstance(ab_class, str), "antibiotic_class must be a string"
    assert len(ab_class.strip()) > 0, "antibiotic_class cannot be empty"


def test_artifact_hash_exists():
    """
    Contract Test: Verify 'artifact_hash' is present and valid.
    
    Confirms that the model output includes a hash for reproducibility
    and integrity checking (Constitution Principle V).
    """
    model_file = _find_latest_model_json()
    
    with open(model_file, 'r') as f:
        metadata = json.load(f)
    
    artifact_hash = metadata.get("artifact_hash")
    assert artifact_hash is not None, "artifact_hash is missing"
    assert isinstance(artifact_hash, str), "artifact_hash must be a string"
    assert len(artifact_hash) == 64, (
        f"artifact_hash must be a SHA256 hash (64 chars), got length {len(artifact_hash)}"
    )
    # Verify it's a valid hex string
    try:
        int(artifact_hash, 16)
    except ValueError:
        pytest.fail("artifact_hash is not a valid hexadecimal string")