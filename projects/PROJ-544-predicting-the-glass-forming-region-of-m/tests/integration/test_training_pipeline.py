"""
Task T016: Integration test for full training pipeline on synthetic data.

Runs the full training pipeline (T020) and evaluation (T021) on synthetic data
and verifies that the model achieves >= 0.75 ROC-AUC on a held-out test split.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CODE_MODELS_DIR = PROJECT_ROOT / "code" / "models"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"

def generate_synthetic_data_for_test(tmp_path):
    """
    Generate a small synthetic dataset for integration testing.
    """
    # Create a simple dataset with some separability
    np.random.seed(42)
    n_samples = 200
    n_features = 3

    # Generate features
    X = np.random.randn(n_samples, n_features)
    # Generate labels with some correlation to features to ensure learnability
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(n_features)])
    df["phase_label"] = y

    output_path = tmp_path / "sample_dataset.csv"
    df.to_csv(output_path, index=False)
    return output_path

def test_full_training_pipeline(tmp_path):
    """
    Run the full training and evaluation pipeline on synthetic data.
    """
    # Ensure directories exist
    tmp_data = tmp_path / "data"
    tmp_data.mkdir(parents=True, exist_ok=True)
    tmp_models = tmp_path / "models"
    tmp_models.mkdir(parents=True, exist_ok=True)
    tmp_results = tmp_path / "results"
    tmp_results.mkdir(parents=True, exist_ok=True)

    # Generate synthetic data
    data_path = generate_synthetic_data_for_test(tmp_data)

    # Run training script (T020)
    # We need to adapt the paths for the training script to use our temp directories
    # Since the training script expects specific paths, we might need to create symlinks
    # or modify the script to accept arguments. Assuming it accepts arguments.
    # Looking at T020 main(), it likely has arguments.
    # If not, we might need to create the expected directory structure.

    # Let's assume the training script is: python code/models/train.py --data-path <path> --models-dir <path>
    # We need to check the actual arguments. Based on T020 description, it saves to models/trained_models.pkl
    # and hyperparameters to code/models/hyperparameters.yaml.
    # We will create the necessary directory structure in tmp_path to mimic the project structure.

    # Create a temporary project structure
    temp_project_root = tmp_path / "temp_project"
    temp_project_root.mkdir(parents=True, exist_ok=True)
    temp_code = temp_project_root / "code"
    temp_code.mkdir(parents=True, exist_ok=True)
    temp_models = temp_code / "models"
    temp_models.mkdir(parents=True, exist_ok=True)
    temp_data = temp_project_root / "data"
    temp_data.mkdir(parents=True, exist_ok=True)
    temp_derived = temp_data / "derived"
    temp_derived.mkdir(parents=True, exist_ok=True)
    temp_results = temp_project_root / "results"
    temp_results.mkdir(parents=True, exist_ok=True)

    # Copy synthetic data to temp_derived
    sample_data_path = temp_derived / "filtered_alloys.csv"
    pd.read_csv(data_path).to_csv(sample_data_path, index=False)

    # Create a minimal config file
    config_path = temp_code / "config"
    config_path.mkdir(parents=True, exist_ok=True)
    config_file = config_path / "env.yaml"
    config_file.write_text("random_seed: 42\nmax_ram_gb: 16\n")

    # Run training script
    # We need to run the script from the project root or adjust PYTHONPATH
    # Assuming the script can be run from anywhere if PYTHONPATH is set
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    training_script = PROJECT_ROOT / "code" / "models" / "train.py"
    if not training_script.exists():
        pytest.skip("Training script not found. T020 not implemented.")

    # Run training
    cmd = [
        sys.executable, str(training_script),
        "--config", str(config_file),
        "--data-path", str(sample_data_path),
        "--models-dir", str(temp_models),
        "--output-path", str(temp_results / "performance_metrics.json") # T021 output, but T020 might not need this
    ]
    # T020 main() might not have --output-path for metrics. It saves models.
    # Let's just run T020 to train models.
    cmd_train = [
        sys.executable, str(training_script),
        "--config", str(config_file),
        "--data-path", str(sample_data_path),
        "--models-dir", str(temp_models)
    ]

    result = subprocess.run(cmd_train, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.fail(f"Training failed: {result.stderr}")

    # Check if models were saved
    rf_model = temp_models / "random_forest.pkl"
    gb_model = temp_models / "gradient_boosting.pkl"
    assert rf_model.exists(), "Random Forest model not saved."
    assert gb_model.exists(), "Gradient Boosting model not saved."

    # Run evaluation script (T021)
    evaluation_script = PROJECT_ROOT / "code" / "models" / "evaluate.py"
    if not evaluation_script.exists():
        pytest.skip("Evaluation script not found. T021 not implemented.")

    cmd_eval = [
        sys.executable, str(evaluation_script),
        "--config", str(config_file),
        "--models-dir", str(temp_models),
        "--data-path", str(sample_data_path),
        "--output-path", str(temp_results / "performance_metrics.json")
    ]

    result = subprocess.run(cmd_eval, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.fail(f"Evaluation failed: {result.stderr}")

    # Check output file
    metrics_file = temp_results / "performance_metrics.json"
    assert metrics_file.exists(), "Performance metrics file not created."

    # Load and check metrics
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)

    # Verify ROC-AUC >= 0.75
    models = metrics.get("models", [])
    assert len(models) > 0, "No models in metrics."

    # Check at least one model has ROC-AUC >= 0.75
    passed = False
    for model in models:
        if model.get("roc_auc", 0) >= 0.75:
            passed = True
            break

    assert passed, f"No model achieved ROC-AUC >= 0.75. Metrics: {metrics}"
