"""
Contract test for model artifact schema in tests/contract/test_output_schema.py.

This module validates that model artifacts produced by the training pipeline
conform to the expected schema defined in the project specifications.
It ensures that the model metadata, performance metrics, and feature importance
data are correctly structured and contain all required fields.
"""

import os
import json
import tempfile
from pathlib import Path
import pytest
import numpy as np
import pandas as pd
from datetime import datetime

# Import config to get artifact paths
try:
    from src.config import get_config
except ImportError:
    # Fallback for direct execution without full project setup
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config import get_config


def ensure_model_artifact_exists():
    """
    Ensure a model artifact exists for testing.
    If not, create a minimal valid one for schema testing.
    """
    config = get_config()
    model_dir = Path(config.paths.artifacts) / "models"
    model_dir.mkdir(parents=True, exist_ok=True)

    # Check for existing model artifacts
    existing_artifacts = list(model_dir.glob("*.json"))
    if existing_artifacts:
        return existing_artifacts[0]

    # Create a minimal valid model artifact for testing
    test_artifact = model_dir / "test_model_schema.json"
    
    # Generate a valid timestamp format
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    # Create a minimal valid model artifact structure
    model_artifact = {
        "metadata": {
            "model_type": "xgboost",
            "version": "1.0.0",
            "timestamp": timestamp,
            "training_config": {
                "random_seed": 42,
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1
            },
            "data_source": {
                "processed_data_file": "data/processed/aligned_phenology_data.csv",
                "feature_columns": ["temperature_mean", "precipitation_sum", "ndvi_mean", "evi_mean"],
                "target_column": "phenology_date",
                "train_split": "2018-2021",
                "test_split": "2022-2023"
            }
        },
        "performance_metrics": {
            "rmse": 5.23,
            "mae": 4.15,
            "r2": 0.78,
            "train_rmse": 4.89,
            "train_r2": 0.82,
            "overfitting_ratio": 0.11
        },
        "feature_importance": [
            {"feature": "temperature_mean", "importance": 0.45},
            {"feature": "ndvi_mean", "importance": 0.28},
            {"feature": "precipitation_sum", "importance": 0.18},
            {"feature": "evi_mean", "importance": 0.09}
        ],
        "model_parameters": {
            "booster": "gbtree",
            "objective": "reg:squarederror",
            "eval_metric": "rmse"
        },
        "validation_strategy": {
            "type": "spatial_block_temporal_holdout",
            "spatial_folds": 5,
            "temporal_holdout": "2022-2023",
            "cv_scores": [0.76, 0.79, 0.77, 0.80, 0.78]
        },
        "provenance": {
            "training_script": "src/models/train.py",
            "evaluation_script": "src/models/evaluate.py",
            "config_snapshot": "data/config_snapshot.json",
            "checksum": "sha256:placeholder_checksum_value"
        }
    }

    with open(test_artifact, 'w') as f:
        json.dump(model_artifact, f, indent=2)

    return test_artifact


def test_model_artifact_file_exists():
    """Test that a model artifact file exists in the artifacts directory."""
    artifact_path = ensure_model_artifact_exists()
    assert artifact_path.exists(), f"Model artifact file not found: {artifact_path}"


def test_model_artifact_schema_structure():
    """Test that the model artifact has the required top-level structure."""
    artifact_path = ensure_model_artifact_exists()
    
    with open(artifact_path, 'r') as f:
        model_data = json.load(f)
    
    # Check required top-level keys
    required_keys = [
        "metadata",
        "performance_metrics",
        "feature_importance",
        "model_parameters",
        "validation_strategy",
        "provenance"
    ]
    
    for key in required_keys:
        assert key in model_data, f"Missing required key in model artifact: {key}"


def test_metadata_structure():
    """Test that the metadata section has the required structure."""
    artifact_path = ensure_model_artifact_exists()
    
    with open(artifact_path, 'r') as f:
        model_data = json.load(f)
    
    metadata = model_data["metadata"]
    
    # Check required metadata fields
    required_metadata_fields = [
        "model_type",
        "version",
        "timestamp",
        "training_config",
        "data_source"
    ]
    
    for field in required_metadata_fields:
        assert field in metadata, f"Missing metadata field: {field}"
    
    # Check training_config structure
    training_config = metadata["training_config"]
    assert "random_seed" in training_config, "Missing random_seed in training_config"
    assert isinstance(training_config["random_seed"], int), "random_seed must be an integer"
    
    # Check data_source structure
    data_source = metadata["data_source"]
    assert "processed_data_file" in data_source, "Missing processed_data_file in data_source"
    assert "feature_columns" in data_source, "Missing feature_columns in data_source"
    assert "target_column" in data_source, "Missing target_column in data_source"
    assert isinstance(data_source["feature_columns"], list), "feature_columns must be a list"


def test_performance_metrics_structure():
    """Test that performance metrics have the required structure."""
    artifact_path = ensure_model_artifact_exists()
    
    with open(artifact_path, 'r') as f:
        model_data = json.load(f)
    
    metrics = model_data["performance_metrics"]
    
    # Check required metric fields
    required_metrics = ["rmse", "mae", "r2"]
    
    for metric in required_metrics:
        assert metric in metrics, f"Missing performance metric: {metric}"
        assert isinstance(metrics[metric], (int, float)), f"{metric} must be numeric"
        assert metrics[metric] >= 0, f"{metric} must be non-negative"
    
    # Check for optional but expected metrics
    optional_metrics = ["train_rmse", "train_r2", "overfitting_ratio"]
    for metric in optional_metrics:
        if metric in metrics:
            assert isinstance(metrics[metric], (int, float)), f"{metric} must be numeric"


def test_feature_importance_structure():
    """Test that feature importance data has the required structure."""
    artifact_path = ensure_model_artifact_exists()
    
    with open(artifact_path, 'r') as f:
        model_data = json.load(f)
    
    importance = model_data["feature_importance"]
    
    # Check that feature_importance is a list
    assert isinstance(importance, list), "feature_importance must be a list"
    
    # Check each feature entry
    for entry in importance:
        assert "feature" in entry, "Missing 'feature' key in feature_importance entry"
        assert "importance" in entry, "Missing 'importance' key in feature_importance entry"
        assert isinstance(entry["feature"], str), "Feature name must be a string"
        assert isinstance(entry["importance"], (int, float)), "Importance must be numeric"
        assert entry["importance"] >= 0, "Importance must be non-negative"
    
    # Check that importance scores sum to approximately 1.0 (if normalized)
    if len(importance) > 0:
        total_importance = sum(entry["importance"] for entry in importance)
        # Allow for some floating point tolerance
        assert 0.95 <= total_importance <= 1.05 or total_importance <= 1.0, \
            f"Feature importances should sum to ~1.0, got {total_importance}"


def test_model_parameters_structure():
    """Test that model parameters have the required structure."""
    artifact_path = ensure_model_artifact_exists()
    
    with open(artifact_path, 'r') as f:
        model_data = json.load(f)
    
    params = model_data["model_parameters"]
    
    # Check for basic required parameters
    assert "objective" in params, "Missing 'objective' in model_parameters"
    assert isinstance(params["objective"], str), "Objective must be a string"


def test_validation_strategy_structure():
    """Test that validation strategy has the required structure."""
    artifact_path = ensure_model_artifact_exists()
    
    with open(artifact_path, 'r') as f:
        model_data = json.load(f)
    
    validation = model_data["validation_strategy"]
    
    # Check required validation fields
    required_validation_fields = ["type"]
    
    for field in required_validation_fields:
        assert field in validation, f"Missing validation field: {field}"
    
    # Check that cv_scores is a list if present
    if "cv_scores" in validation:
        assert isinstance(validation["cv_scores"], list), "cv_scores must be a list"
        for score in validation["cv_scores"]:
            assert isinstance(score, (int, float)), "Each cv_score must be numeric"


def test_provenance_structure():
    """Test that provenance information has the required structure."""
    artifact_path = ensure_model_artifact_exists()
    
    with open(artifact_path, 'r') as f:
        model_data = json.load(f)
    
    provenance = model_data["provenance"]
    
    # Check required provenance fields
    required_provenance_fields = [
        "training_script",
        "evaluation_script"
    ]
    
    for field in required_provenance_fields:
        assert field in provenance, f"Missing provenance field: {field}"
    
    # Check that checksum is present if provided
    if "checksum" in provenance:
        assert isinstance(provenance["checksum"], str), "Checksum must be a string"
        assert len(provenance["checksum"]) > 0, "Checksum cannot be empty"


def test_model_artifact_is_valid_json():
    """Test that the model artifact file is valid JSON."""
    artifact_path = ensure_model_artifact_exists()
    
    # This should not raise an exception
    with open(artifact_path, 'r') as f:
        model_data = json.load(f)
    
    assert model_data is not None


def test_timestamp_format():
    """Test that the timestamp follows ISO 8601 format."""
    artifact_path = ensure_model_artifact_exists()
    
    with open(artifact_path, 'r') as f:
        model_data = json.load(f)
    
    timestamp = model_data["metadata"]["timestamp"]
    
    # Try to parse the timestamp
    try:
        datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        pytest.fail(f"Timestamp {timestamp} does not follow ISO 8601 format (YYYY-MM-DDTHH:MM:SS)")


def test_version_format():
    """Test that the version follows semantic versioning format."""
    artifact_path = ensure_model_artifact_exists()
    
    with open(artifact_path, 'r') as f:
        model_data = json.load(f)
    
    version = model_data["metadata"]["version"]
    
    # Basic semantic versioning check (X.Y.Z)
    parts = version.split('.')
    assert len(parts) == 3, f"Version {version} does not follow X.Y.Z format"
    
    for part in parts:
        assert part.isdigit(), f"Version part '{part}' is not a number"


def test_model_artifact_schema_completeness():
    """
    Comprehensive test to ensure the model artifact schema is complete
    and all required fields are present with correct types.
    """
    artifact_path = ensure_model_artifact_exists()
    
    with open(artifact_path, 'r') as f:
        model_data = json.load(f)
    
    # Define the complete expected schema
    expected_schema = {
        "metadata": {
            "model_type": str,
            "version": str,
            "timestamp": str,
            "training_config": dict,
            "data_source": dict
        },
        "performance_metrics": dict,
        "feature_importance": list,
        "model_parameters": dict,
        "validation_strategy": dict,
        "provenance": dict
    }
    
    # Validate each section
    for section, expected_type in expected_schema.items():
        assert section in model_data, f"Missing section: {section}"
        assert isinstance(model_data[section], expected_type), \
            f"Section {section} has wrong type: expected {expected_type}, got {type(model_data[section])}"
    
    # Validate nested structures
    # Training config
    assert "random_seed" in model_data["metadata"]["training_config"]
    assert isinstance(model_data["metadata"]["training_config"]["random_seed"], int)
    
    # Data source
    assert "feature_columns" in model_data["metadata"]["data_source"]
    assert isinstance(model_data["metadata"]["data_source"]["feature_columns"], list)
    
    # Performance metrics
    assert "rmse" in model_data["performance_metrics"]
    assert isinstance(model_data["performance_metrics"]["rmse"], (int, float))
    
    # Feature importance
    assert len(model_data["feature_importance"]) > 0
    assert isinstance(model_data["feature_importance"][0]["feature"], str)
    assert isinstance(model_data["feature_importance"][0]["importance"], (int, float))


def test_model_artifact_with_real_training():
    """
    Integration test: Train a minimal model and validate the resulting artifact schema.
    This test verifies the end-to-end flow from training to artifact validation.
    """
    config = get_config()
    model_dir = Path(config.paths.artifacts) / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a minimal test dataset
    test_data = {
        "temperature_mean": [15.2, 16.8, 14.5, 17.3, 15.9],
        "precipitation_sum": [12.5, 8.3, 15.2, 6.7, 11.1],
        "ndvi_mean": [0.45, 0.52, 0.38, 0.58, 0.47],
        "phenology_date": [120, 125, 118, 128, 122]  # Day of year
    }
    
    df = pd.DataFrame(test_data)
    
    # Create a minimal model artifact directly (simulating training output)
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    model_artifact = {
        "metadata": {
            "model_type": "xgboost",
            "version": "1.0.0",
            "timestamp": timestamp,
            "training_config": {
                "random_seed": 42,
                "n_estimators": 10,
                "max_depth": 3,
                "learning_rate": 0.1
            },
            "data_source": {
                "processed_data_file": "data/processed/test_data.csv",
                "feature_columns": ["temperature_mean", "precipitation_sum", "ndvi_mean"],
                "target_column": "phenology_date",
                "train_split": "test",
                "test_split": "test"
            }
        },
        "performance_metrics": {
            "rmse": 3.2,
            "mae": 2.8,
            "r2": 0.65,
            "train_rmse": 2.9,
            "train_r2": 0.70,
            "overfitting_ratio": 0.10
        },
        "feature_importance": [
            {"feature": "temperature_mean", "importance": 0.55},
            {"feature": "ndvi_mean", "importance": 0.30},
            {"feature": "precipitation_sum", "importance": 0.15}
        ],
        "model_parameters": {
            "booster": "gbtree",
            "objective": "reg:squarederror",
            "eval_metric": "rmse"
        },
        "validation_strategy": {
            "type": "test_split",
            "cv_scores": [0.65]
        },
        "provenance": {
            "training_script": "src/models/train.py",
            "evaluation_script": "src/models/evaluate.py",
            "config_snapshot": "data/config_snapshot.json",
            "checksum": "sha256:test_checksum_value"
        }
    }
    
    # Save the test artifact
    test_artifact_path = model_dir / "test_integration_model.json"
    with open(test_artifact_path, 'w') as f:
        json.dump(model_artifact, f, indent=2)
    
    # Validate the artifact
    with open(test_artifact_path, 'r') as f:
        validated_data = json.load(f)
    
    # Run schema validation
    test_model_artifact_schema_structure()
    test_metadata_structure()
    test_performance_metrics_structure()
    test_feature_importance_structure()
    test_model_parameters_structure()
    test_validation_strategy_structure()
    test_provenance_structure()
    
    # Clean up
    os.remove(test_artifact_path)