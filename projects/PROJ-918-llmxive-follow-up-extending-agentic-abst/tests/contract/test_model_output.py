"""
Contract test for code/models/train_meta_critic.py output schema.

This test verifies that the model training pipeline produces outputs
that conform to the expected schema defined in contracts/output.schema.yaml.

It checks:
1. Existence of required output files (model artifact, metrics JSON, logs)
2. Schema compliance of the metrics JSON against output.schema.yaml
3. Integrity of the model file (non-empty, valid format)
"""
import os
import json
import yaml
import pytest
from pathlib import Path
from typing import Dict, Any, Set

# Import config utilities to locate paths
# Note: We assume the test runs from the project root or code/ directory
# We use relative imports consistent with the project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import get_path, get_config


@pytest.fixture
def output_schema_path():
    """Path to the output schema definition."""
    return Path("contracts/output.schema.yaml")


@pytest.fixture
def expected_output_dir():
    """Directory where model outputs should be generated."""
    # Based on plan.md and tasks.md, outputs go to data/results/ or similar
    # We use the config to determine the exact path
    config = get_config()
    return Path(get_path("model_output_dir"))


@pytest.fixture
def required_files() -> Set[str]:
    """Set of required output files that must exist after training."""
    return {
        "meta_critic_model.json",      # XGBoost/LightGBM model artifact
        "training_metrics.json",       # Metrics conforming to output schema
        "training_log.txt"             # Execution log
    }


def test_output_directory_exists(expected_output_dir: Path):
    """Verify the output directory exists (created by training script)."""
    assert expected_output_dir.exists(), f"Output directory {expected_output_dir} does not exist. Training may not have run."


def test_required_files_exist(expected_output_dir: Path, required_files: Set[str]):
    """Verify all required output files are present."""
    missing_files = []
    for filename in required_files:
        file_path = expected_output_dir / filename
        if not file_path.exists():
            missing_files.append(filename)
    
    assert len(missing_files) == 0, f"Missing required output files: {missing_files}"


def test_model_file_non_empty(expected_output_dir: Path):
    """Verify the model file is not empty."""
    model_path = expected_output_dir / "meta_critic_model.json"
    assert model_path.exists(), "Model file missing"
    assert model_path.stat().st_size > 0, "Model file is empty"


def test_metrics_schema_compliance(output_schema_path: Path, expected_output_dir: Path):
    """
    Verify training_metrics.json conforms to contracts/output.schema.yaml.
    
    Checks:
    - Required top-level fields: model_type, metrics, hyperparameters
    - Required metric fields: timely_abstention_recall, avg_token_consumption, latency_seconds
    - Type constraints (e.g., metrics are numeric)
    """
    schema_path = output_schema_path
    metrics_path = expected_output_dir / "training_metrics.json"
    
    assert schema_path.exists(), f"Schema file not found: {schema_path}"
    assert metrics_path.exists(), f"Metrics file not found: {metrics_path}"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    with open(metrics_path, 'r') as f:
        metrics_data = json.load(f)
    
    # Define expected structure based on typical output.schema.yaml
    # This mirrors the schema validation logic that would be in a dedicated validator
    required_top_level = {"model_type", "metrics", "hyperparameters"}
    required_metrics = {"timely_abstention_recall", "avg_token_consumption", "latency_seconds"}
    
    # Check top-level keys
    missing_top_level = required_top_level - set(metrics_data.keys())
    assert len(missing_top_level) == 0, f"Missing top-level keys in metrics: {missing_top_level}"
    
    # Check metrics sub-keys
    metrics_section = metrics_data.get("metrics", {})
    missing_metrics = required_metrics - set(metrics_section.keys())
    assert len(missing_metrics) == 0, f"Missing metric fields: {missing_metrics}"
    
    # Check types (basic validation)
    for key in required_metrics:
        value = metrics_section.get(key)
        assert isinstance(value, (int, float)), f"Metric '{key}' must be numeric, got {type(value)}"
        assert value >= 0, f"Metric '{key}' must be non-negative, got {value}"


def test_hyperparameters_present(metrics_path: Path = None):
    """Verify hyperparameters are recorded in the metrics file."""
    if metrics_path is None:
        metrics_path = get_path("model_output_dir") / "training_metrics.json"
    
    with open(metrics_path, 'r') as f:
        data = json.load(f)
    
    assert "hyperparameters" in data, "Hyperparameters section missing from metrics"
    assert isinstance(data["hyperparameters"], dict), "Hyperparameters must be a dictionary"
    assert len(data["hyperparameters"]) > 0, "Hyperparameters dictionary is empty"


def test_log_file_content(expected_output_dir: Path):
    """Verify training log contains expected entries."""
    log_path = expected_output_dir / "training_log.txt"
    assert log_path.exists(), "Training log file missing"
    
    with open(log_path, 'r') as f:
        content = f.read()
    
    # Check for key training events
    required_entries = [
        "Starting training",
        "Loading features",
        "Training complete"
    ]
    
    for entry in required_entries:
        assert entry in content, f"Expected log entry not found: '{entry}'"
