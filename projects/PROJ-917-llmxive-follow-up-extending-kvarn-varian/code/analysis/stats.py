"""
Statistical analysis utilities for the llmXive KVarN follow-up project.

This module provides functions for:
- Epsilon sensitivity analysis
- Theoretical lower bound computation
- Paired t-tests for simulation results
- Baseline vs. MLP model comparison (T035c)
"""

import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from scipy import stats
import logging

# Import from project utilities
from data_generation.utils import generate_epsilon_sweep_values, safe_log, safe_divide
from model_training.baselines import evaluate_baseline_mse
from model_training.mlp_model import StaticPriorMLP, create_model
import torch

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_training_data(data_path: str = "data/raw/synthetic_attention_matrices.csv") -> Tuple[np.ndarray, np.ndarray]:
    """
    Load the generated dataset containing attention moments and scaling factors.

    Args:
        data_path: Path to the CSV file containing the dataset.

    Returns:
        Tuple of (features, labels) where features are [mean, variance] and labels are scaling factors.
    """
    import pandas as pd

    df = pd.read_csv(data_path)

    # Extract features: mean and variance
    features = df[['mean', 'variance']].values.astype(np.float32)
    # Extract labels: scaling_factor
    labels = df['scaling_factor'].values.astype(np.float32)

    return features, labels


def load_model_weights(model_path: str = "data/models/mlp_weights.pt") -> torch.nn.Module:
    """
    Load the trained MLP model weights.

    Args:
        model_path: Path to the saved model weights.

    Returns:
        The loaded MLP model.
    """
    model = create_model()
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()
    return model


def compare_mlp_vs_baseline(
    mlp_model: torch.nn.Module,
    features: np.ndarray,
    labels: np.ndarray,
    output_path: str = "data/metrics/baseline_comparison.json"
) -> Dict[str, Any]:
    """
    Compare the MLP model against the closed-form baseline.

    Computes MSE for both models and performs a statistical test to determine
    if the MLP significantly outperforms the baseline (FR-009).

    Args:
        mlp_model: The trained StaticPriorMLP model.
        features: Input features (mean, variance).
        labels: Ground truth scaling factors.
        output_path: Path to save the comparison results.

    Returns:
        Dictionary containing comparison metrics and statistical test results.
    """
    import torch
    import numpy as np

    # Ensure model is in eval mode
    mlp_model.eval()

    # Convert inputs to tensors
    X_tensor = torch.from_numpy(features).unsqueeze(0) if features.ndim == 2 else torch.from_numpy(features)
    y_tensor = torch.from_numpy(labels).unsqueeze(0) if labels.ndim == 1 else torch.from_numpy(labels)

    # Get MLP predictions
    with torch.no_grad():
        mlp_preds = mlp_model(X_tensor).squeeze().numpy()

    # Get baseline predictions (s = 1/variance)
    # Extract variance from features (second column)
    variances = features[:, 1]
    baseline_preds = 1.0 / (variances + 1e-8)  # Add epsilon to avoid division by zero

    # Compute MSE for both models
    mlp_mse = np.mean((mlp_preds - labels) ** 2)
    baseline_mse = np.mean((baseline_preds - labels) ** 2)

    # Compute relative improvement
    if baseline_mse > 0:
        relative_improvement = (baseline_mse - mlp_mse) / baseline_mse
    else:
        relative_improvement = 0.0

    # Perform paired t-test on squared errors
    mlp_squared_errors = (mlp_preds - labels) ** 2
    baseline_squared_errors = (baseline_preds - labels) ** 2

    # Paired t-test: test if MLP errors are significantly smaller than baseline errors
    t_stat, p_value = stats.ttest_rel(mlp_squared_errors, baseline_squared_errors, alternative='less')

    # Determine if MLP captures non-trivial relationships (FR-009)
    # Criterion: p-value < 0.05 AND relative improvement > 0
    captures_nontrivial = (p_value < 0.05) and (relative_improvement > 0)

    results = {
        "mlp_mse": float(mlp_mse),
        "baseline_mse": float(baseline_mse),
        "relative_improvement": float(relative_improvement),
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "captures_nontrivial_relationship": captures_nontrivial,
        "sample_size": len(labels),
        "method": "paired_t_test_squared_errors"
    }

    # Save results to file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Baseline comparison results saved to {output_path}")
    logger.info(f"MLP MSE: {mlp_mse:.6f}, Baseline MSE: {baseline_mse:.6f}")
    logger.info(f"Relative improvement: {relative_improvement:.4%}")
    logger.info(f"P-value: {p_value:.6f}, Captures non-trivial: {captures_nontrivial}")

    return results


def main():
    """
    Main entry point for the baseline comparison analysis (T035c).
    """
    logger.info("Starting MLP vs Baseline comparison (T035c)...")

    try:
        # Load data
        logger.info("Loading training data...")
        features, labels = load_training_data()
        logger.info(f"Loaded {len(labels)} samples")

        # Load trained model
        logger.info("Loading trained MLP model...")
        mlp_model = load_model_weights()
        logger.info("Model loaded successfully")

        # Perform comparison
        logger.info("Comparing MLP vs Baseline...")
        results = compare_mlp_vs_baseline(mlp_model, features, labels)

        logger.info("Comparison completed successfully")
        return results

    except Exception as e:
        logger.error(f"Error during comparison: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
