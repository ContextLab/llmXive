"""
Evaluation module for the molecular properties prediction model.
Loads model checkpoints, runs inference, and computes evaluation metrics.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

# Import from local modules
from models.cnn_1d import MolecularPropertyCNN
from evaluation.metrics import (
    compute_mae,
    compute_r2,
    compute_metrics_per_property,
    compute_all_statistics
)
from utils.logging_utils import setup_logging, get_logger
from utils.seed_utils import set_seed

# Configure paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PREPROCESSED_DIR = DATA_DIR / "preprocessed"
MODEL_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
LOGS_DIR = PROJECT_ROOT / "logs"

def load_preprocessed_data(
    data_path: Optional[Path] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, int]]:
    """
    Load preprocessed data from the .npz file.

    Args:
        data_path: Path to the preprocessed .npz file. If None, uses default path.

    Returns:
        Tuple of (X_train, y_train, X_test, y_test, property_indices).
    """
    if data_path is None:
        data_path = PREPROCESSED_DIR / "aligned_data.npz"

    if not data_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {data_path}")

    logger = get_logger()
    logger.info(f"Loading preprocessed data from {data_path}")

    data = np.load(data_path)
    X = data["X"]
    y = data["y"]
    property_indices = data["property_indices"].item() if "property_indices" in data else {}

    # Split into train/test (80/20)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    logger.info(f"Loaded {len(X)} samples, split into {len(X_train)} train and {len(X_test)} test")

    return X_train, y_train, X_test, y_test, property_indices

def load_model_checkpoint(
    checkpoint_path: Optional[Path] = None,
    device: str = "cpu"
) -> torch.nn.Module:
    """
    Load a model checkpoint.

    Args:
        checkpoint_path: Path to the checkpoint file. If None, uses default path.
        device: Device to load the model onto.

    Returns:
        Loaded model.
    """
    if checkpoint_path is None:
        checkpoint_path = MODEL_DIR / "model_best.pt"

    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found at {checkpoint_path}")

    logger = get_logger()
    logger.info(f"Loading model checkpoint from {checkpoint_path}")

    # Load the checkpoint
    checkpoint = torch.load(checkpoint_path, map_location=device)

    # Get model configuration from checkpoint
    model_config = checkpoint.get("model_config", {})
    input_dim = model_config.get("input_dim", 3601)  # 4000 - 400 + 1
    num_targets = model_config.get("num_targets", 3)

    # Create and load model
    model = MolecularPropertyCNN(input_dim=input_dim, num_targets=num_targets)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    logger.info("Model loaded successfully")
    return model

def load_model_with_dim(
    checkpoint_path: Path,
    input_dim: int,
    num_targets: int = 3,
    device: str = "cpu"
) -> MolecularPropertyCNN:
    """
    Load a model with specific dimensions.

    Args:
        checkpoint_path: Path to the checkpoint file.
        input_dim: Input dimension for the model.
        num_targets: Number of target properties.
        device: Device to load the model onto.

    Returns:
        Loaded model.
    """
    logger = get_logger()
    logger.info(f"Creating model with input_dim={input_dim}, num_targets={num_targets}")

    model = MolecularPropertyCNN(input_dim=input_dim, num_targets=num_targets)

    if checkpoint_path.exists():
        checkpoint = torch.load(checkpoint_path, map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        logger.info(f"Loaded weights from {checkpoint_path}")
    else:
        logger.warning(f"Checkpoint not found at {checkpoint_path}, using random weights")

    model.to(device)
    model.eval()
    return model

def run_inference(
    model: torch.nn.Module,
    X_test: np.ndarray,
    batch_size: int = 32,
    device: str = "cpu"
) -> np.ndarray:
    """
    Run inference on test data.

    Args:
        model: Trained model.
        X_test: Test input data.
        batch_size: Batch size for inference.
        device: Device to run inference on.

    Returns:
        Model predictions.
    """
    logger = get_logger()
    logger.info(f"Running inference on {len(X_test)} test samples")

    # Convert to tensors
    X_tensor = torch.FloatTensor(X_test).to(device)
    dataset = TensorDataset(X_tensor)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

    predictions = []
    model.eval()

    with torch.no_grad():
        for batch in dataloader:
            x_batch = batch[0]
            y_pred = model(x_batch)
            predictions.append(y_pred.cpu().numpy())

    predictions = np.vstack(predictions)
    logger.info(f"Inference complete, predictions shape: {predictions.shape}")

    return predictions

def compute_evaluation_results(
    y_test: np.ndarray,
    predictions: np.ndarray,
    property_names: List[str],
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Compute and save evaluation results.

    Args:
        y_test: True test labels.
        predictions: Model predictions.
        property_names: Names of the properties.
        output_path: Path to save the results JSON. If None, uses default path.

    Returns:
        Dictionary of evaluation results.
    """
    logger = get_logger()
    logger.info("Computing evaluation metrics")

    results = {
        "metrics": {},
        "statistics": {},
        "summary": {}
    }

    # Compute metrics for each property
    for i, prop_name in enumerate(property_names):
        y_true = y_test[:, i]
        y_pred = predictions[:, i]

        mae = compute_mae(y_true, y_pred)
        r2 = compute_r2(y_true, y_pred)

        results["metrics"][prop_name] = {
            "mae": float(mae),
            "r2": float(r2)
        }

        logger.info(f"{prop_name}: MAE={mae:.4f}, R²={r2:.4f}")

    # Compute statistical tests
    stats_results = compute_all_statistics(y_test, predictions, property_names)
    results["statistics"] = stats_results

    # Summary
    avg_mae = np.mean([results["metrics"][p]["mae"] for p in property_names])
    avg_r2 = np.mean([results["metrics"][p]["r2"] for p in property_names])

    results["summary"] = {
        "avg_mae": float(avg_mae),
        "avg_r2": float(avg_r2),
        "num_samples": len(y_test),
        "num_properties": len(property_names)
    }

    # Save results
    if output_path is None:
        output_path = RESULTS_DIR / "evaluation_metrics.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Evaluation results saved to {output_path}")

    return results

def main():
    """
    Main entry point for the evaluation script.
    """
    # Set up logging
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(LOGS_DIR)
    logger.info("Starting evaluation")

    # Set seed for reproducibility
    set_seed(42)

    try:
        # Load data
        X_train, y_train, X_test, y_test, property_indices = load_preprocessed_data()

        # Create property names list
        property_names = ["dipole", "polarizability", "homo_lumo_gap"]

        # Load model
        model = load_model_checkpoint()

        # Run inference
        predictions = run_inference(model, X_test)

        # Compute and save results
        results = compute_evaluation_results(y_test, predictions, property_names)

        logger.info("Evaluation completed successfully")
        logger.info(f"Results summary: {results['summary']}")

    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
