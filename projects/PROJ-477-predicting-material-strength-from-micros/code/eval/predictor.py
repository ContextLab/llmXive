"""
Predictor module for Monte Carlo Dropout confidence intervals.

Implements FR-008: Confidence interval calculation using Monte Carlo Dropout.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch
import torch.nn as nn
import pandas as pd
import numpy as np
from torch.utils.data import DataLoader

# Import project utilities
from utils.config import get_results_dir, get_data_dir, set_seed, get_seed
from utils.logging_config import get_logger, log_operation
from data.loader import MicrostructureDataset, OOMSafeDataLoader
from models.cnn import get_model


def setup_predictor_logging() -> logging.Logger:
    """Setup logging for the predictor module."""
    logger = get_logger("predictor")
    logger.setLevel(logging.INFO)
    return logger


@log_operation("enable_dropout")
def enable_dropout(model: nn.Module) -> None:
    """Enable dropout layers in the model for inference."""
    model.train()  # Set model to training mode to enable dropout
    for module in model.modules():
        if isinstance(module, nn.Dropout):
            module.train()  # Ensure dropout is active


@log_operation("disable_dropout")
def disable_dropout(model: nn.Module) -> None:
    """Disable dropout layers in the model (standard evaluation mode)."""
    model.eval()  # Set model to evaluation mode


@log_operation("run_monte_carlo_dropout")
def run_monte_carlo_dropout(
    model: nn.Module,
    dataloader: DataLoader,
    n_samples: int = 100,
    device: str = "cpu",
    logger: Optional[logging.Logger] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Run Monte Carlo Dropout inference.
    
    Args:
        model: The neural network model.
        dataloader: DataLoader for the dataset.
        n_samples: Number of forward passes per sample.
        device: Device to run inference on.
        logger: Optional logger.
        
    Returns:
        Tuple of (predictions_mean, predictions_std, predictions_all)
        where predictions_all has shape (n_samples, n_samples_per_batch)
    """
    if logger:
        logger.info(f"Starting Monte Carlo Dropout with {n_samples} samples")
    
    enable_dropout(model)
    model.to(device)
    
    all_predictions: List[np.ndarray] = []
    all_true_values: List[float] = []
    all_image_ids: List[str] = []
    
    with torch.no_grad():
        for batch_idx, batch in enumerate(dataloader):
            images = batch["image"].to(device)
            labels = batch["label"].cpu().numpy()
            image_ids = batch["image_id"]
            
            batch_predictions_samples: List[np.ndarray] = []
            
            for _ in range(n_samples):
                outputs = model(images)
                preds = outputs.cpu().numpy().flatten()
                batch_predictions_samples.append(preds)
            
            all_predictions.append(np.stack(batch_predictions_samples, axis=0))
            all_true_values.extend(labels)
            all_image_ids.extend(image_ids)
    
    # Concatenate all batch predictions: shape (n_samples, total_samples)
    all_predictions = np.concatenate(all_predictions, axis=1)
    all_true_values = np.array(all_true_values)
    
    # Calculate mean and std across the N samples dimension
    predictions_mean = np.mean(all_predictions, axis=0)
    predictions_std = np.std(all_predictions, axis=0)
    
    disable_dropout(model)
    
    if logger:
        logger.info(f"Completed MC Dropout. Mean shape: {predictions_mean.shape}")
    
    return predictions_mean, predictions_std, all_predictions, all_true_values, all_image_ids


@log_operation("verify_coverage")
def verify_coverage(
    predictions_lower: np.ndarray,
    predictions_upper: np.ndarray,
    true_values: np.ndarray,
    logger: Optional[logging.Logger] = None
) -> float:
    """
    Calculate empirical coverage of the confidence intervals.
    
    Args:
        predictions_lower: Lower bounds of CI.
        predictions_upper: Upper bounds of CI.
        true_values: Ground truth values.
        logger: Optional logger.
        
    Returns:
        Coverage ratio (float between 0 and 1).
    """
    covered = (true_values >= predictions_lower) & (true_values <= predictions_upper)
    coverage = float(np.mean(covered))
    
    if logger:
        logger.info(f"Empirical coverage: {coverage:.4f}")
    
    return coverage


@log_operation("run_confidence_intervals_script")
def run_confidence_intervals_script(
    predictions_path: str,
    output_path: str,
    coverage_output_path: str,
    n_samples: int = 100,
    lower_percentile: float = 2.5,
    upper_percentile: float = 97.5,
    dropout_rate: float = 0.2,
    device: str = "cpu",
    seed: int = 42,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Main function to run Monte Carlo Dropout and generate confidence intervals.
    
    Args:
        predictions_path: Path to the input predictions CSV (from test set).
        output_path: Path to write the output CSV with CI columns.
        coverage_output_path: Path to write the uncertainty calibration JSON.
        n_samples: Number of MC samples.
        lower_percentile: Lower percentile for CI (default 2.5 for 95% CI).
        upper_percentile: Upper percentile for CI (default 97.5 for 95% CI).
        dropout_rate: Dropout rate to use (model must be configured for this).
        device: Device for inference.
        seed: Random seed.
        logger: Logger instance.
    """
    if logger:
        logger.info(f"Starting confidence interval calculation with N={n_samples}")
    
    set_seed(seed)
    
    # Load the input predictions to get image IDs and true values
    # We need to match the image IDs to run inference on the actual images
    if logger:
        logger.info(f"Loading predictions from {predictions_path}")
    
    df = pd.read_csv(predictions_path)
    
    # Expected columns: image_id, true_strength, predicted_strength (or similar)
    # We need image_id to load the actual images for MC Dropout
    if "image_id" not in df.columns:
        raise ValueError(f"Input CSV must contain 'image_id' column. Columns: {df.columns.tolist()}")
    
    if "true_strength" not in df.columns:
        raise ValueError(f"Input CSV must contain 'true_strength' column. Columns: {df.columns.tolist()}")
    
    image_ids = df["image_id"].tolist()
    true_values = df["true_strength"].values
    
    if logger:
        logger.info(f"Found {len(image_ids)} samples in predictions file")
    
    # Load the model
    model = get_model(dropout_rate=dropout_rate)
    
    # Load the dataset for MC Dropout inference
    # We need to construct a dataset that returns images by ID
    # Assuming the test set is in data/processed/test/ or similar
    # We'll use the manifest to map image_id to file path
    
    # For simplicity, we assume the dataset loader can be configured
    # to return specific images. In a real scenario, we'd load the test set.
    # Here, we'll create a minimal dataset from the image_ids if possible.
    
    # NOTE: In the actual pipeline, the test set images and labels are available.
    # We'll assume the MicrostructureDataset can be instantiated with a subset.
    # For now, we'll load the full test set and filter by image_id.
    
    # Load test manifest
    processed_dir = get_data_dir() / "processed"
    test_dir = processed_dir / "test"
    manifest_path = processed_dir / "manifest.csv"
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Test manifest not found at {manifest_path}")
    
    manifest_df = pd.read_csv(manifest_path)
    
    # Filter manifest to only include images in our predictions
    manifest_df = manifest_df[manifest_df["image_id"].isin(image_ids)]
    
    if len(manifest_df) == 0:
        raise ValueError("No matching images found in test manifest for the given image_ids.")
    
    # Create dataset and dataloader
    dataset = MicrostructureDataset(
        manifest_path=manifest_path,
        image_dir=test_dir,
        transform=None  # Preprocessed images
    )
    
    # Filter dataset to only include the image_ids we need
    # We'll create a subset by filtering the manifest
    filtered_manifest_path = processed_dir / "temp_test_manifest.csv"
    manifest_df.to_csv(filtered_manifest_path, index=False)
    
    filtered_dataset = MicrostructureDataset(
        manifest_path=filtered_manifest_path,
        image_dir=test_dir,
        transform=None
    )
    
    dataloader = OOMSafeDataLoader(
        dataset=filtered_dataset,
        batch_size=32,
        shuffle=False,
        num_workers=0,
        pin_memory=False
    )
    
    # Run Monte Carlo Dropout
    predictions_mean, predictions_std, all_predictions_samples, true_values_arr, image_ids_arr = run_monte_carlo_dropout(
        model=model,
        dataloader=dataloader,
        n_samples=n_samples,
        device=device,
        logger=logger
    )
    
    # Calculate confidence intervals using percentile method
    ci_lower = np.percentile(all_predictions_samples, lower_percentile, axis=0)
    ci_upper = np.percentile(all_predictions_samples, upper_percentile, axis=0)
    
    # Verify coverage
    coverage = verify_coverage(ci_lower, ci_upper, true_values_arr, logger)
    
    # Prepare output DataFrame
    output_df = pd.DataFrame({
        "image_id": image_ids_arr,
        "true_strength": true_values_arr,
        "predicted_strength": predictions_mean,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "std": predictions_std
    })
    
    # Write output CSV
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    
    if logger:
        logger.info(f"Wrote {len(output_df)} rows to {output_path}")
    
    # Write uncertainty calibration JSON
    calibration_data = {
        "n_samples": n_samples,
        "lower_percentile": lower_percentile,
        "upper_percentile": upper_percentile,
        "dropout_rate": dropout_rate,
        "empirical_coverage": coverage,
        "total_samples": len(image_ids_arr)
    }
    
    coverage_path_obj = Path(coverage_output_path)
    coverage_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(coverage_output_path, "w") as f:
        json.dump(calibration_data, f, indent=2)
    
    if logger:
        logger.info(f"Wrote calibration data to {coverage_output_path}")
    
    # Cleanup temp manifest
    if filtered_manifest_path.exists():
        filtered_manifest_path.unlink()


def main() -> None:
    """Main entry point for the predictor script."""
    logger = setup_predictor_logging()
    
    parser = argparse.ArgumentParser(description="Run Monte Carlo Dropout for confidence intervals.")
    parser.add_argument("--predictions", type=str, required=True,
                        help="Path to input predictions CSV (e.g., results/predictions.csv)")
    parser.add_argument("--output", type=str, default="results/predictions_ci.csv",
                        help="Path to output CSV with CI columns")
    parser.add_argument("--coverage-output", type=str, default="results/uncertainty_calibration.json",
                        help="Path to output JSON for calibration metrics")
    parser.add_argument("--n-samples", type=int, default=100,
                        help="Number of Monte Carlo samples")
    parser.add_argument("--lower-percentile", type=float, default=2.5,
                        help="Lower percentile for CI")
    parser.add_argument("--upper-percentile", type=float, default=97.5,
                        help="Upper percentile for CI")
    parser.add_argument("--dropout-rate", type=float, default=0.2,
                        help="Dropout rate for MC Dropout")
    parser.add_argument("--device", type=str, default="cpu",
                        help="Device for inference (cpu or cuda)")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed")
    
    args = parser.parse_args()
    
    run_confidence_intervals_script(
        predictions_path=args.predictions,
        output_path=args.output,
        coverage_output_path=args.coverage_output,
        n_samples=args.n_samples,
        lower_percentile=args.lower_percentile,
        upper_percentile=args.upper_percentile,
        dropout_rate=args.dropout_rate,
        device=args.device,
        seed=args.seed,
        logger=logger
    )


if __name__ == "__main__":
    main()