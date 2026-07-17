import os
import sys
import json
import logging
import argparse
import csv
import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from torch.utils.data import DataLoader

# Import from local project structure
from utils.config import get_results_dir, get_data_dir, get_project_root, set_seed, get_seed
from data.loader import MicrostructureDataset, OOMSafeDataLoader
from models.cnn import get_model
from eval.metrics import load_predictions_from_csv

def setup_predictor_logging() -> logging.Logger:
    """Configure logging for the predictor module."""
    logger = logging.getLogger("predictor")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

def enable_dropout(model: torch.nn.Module) -> None:
    """Recursively enable dropout and batch norm training mode."""
    model.train()
    for module in model.modules():
        if isinstance(module, (torch.nn.Dropout, torch.nn.Dropout2d)):
            module.train()

def disable_dropout(model: torch.nn.Module) -> None:
    """Recursively disable dropout and set model to eval mode."""
    model.eval()
    for module in model.modules():
        if isinstance(module, (torch.nn.Dropout, torch.nn.Dropout2d)):
            module.eval()

def run_monte_carlo_dropout(
    model: torch.nn.Module,
    dataloader: DataLoader,
    n_samples: int = 30,
    device: str = "cpu"
) -> Tuple[List[np.ndarray], List[str]]:
    """
    Run Monte Carlo Dropout inference.
    
    Args:
        model: The model with dropout enabled.
        dataloader: DataLoader for the test set.
        n_samples: Number of stochastic forward passes.
        device: Device to run inference on.
        
    Returns:
        Tuple of (list of prediction arrays per sample, list of image_ids)
    """
    all_predictions = [[] for _ in range(n_samples)]
    image_ids = []
    
    # Ensure dropout is enabled
    enable_dropout(model)
    
    with torch.no_grad():
        for batch in dataloader:
            images = batch["image"].to(device)
            ids = batch["image_id"]
            
            # Run multiple forward passes
            for i in range(n_samples):
                outputs = model(images)
                preds = outputs.squeeze().cpu().numpy()
                if isinstance(preds, np.ndarray) and preds.ndim == 0:
                    preds = np.array([preds])
                all_predictions[i].extend(preds)
            
            image_ids.extend(ids)
    
    # Convert to numpy arrays
    prediction_arrays = [np.array(p) for p in all_predictions]
    return prediction_arrays, image_ids

def verify_coverage(
    predictions: List[np.ndarray],
    image_ids: List[str],
    tolerance: float = 0.01
) -> Dict[str, Any]:
    """
    Verify that Monte Carlo Dropout produces valid confidence intervals.
    
    Checks:
    1. All predictions are finite
    2. Variance is non-zero (dropout is actually active)
    3. Coverage is reasonable (not degenerate)
    
    Args:
        predictions: List of prediction arrays from MC samples.
        image_ids: List of image identifiers.
        tolerance: Minimum variance threshold.
        
    Returns:
        Dict with verification status and details.
    """
    if len(predictions) == 0:
        return {"status": "failed", "reason": "No predictions generated"}
    
    # Check variance across samples
    variances = []
    for i in range(len(image_ids)):
        sample_preds = [p[i] for p in predictions]
        var = np.var(sample_preds)
        variances.append(var)
    
    mean_variance = np.mean(variances)
    
    if mean_variance < tolerance:
        return {
            "status": "failed",
            "reason": f"Variance too low ({mean_variance:.6f} < {tolerance}), dropout may be inactive"
        }
    
    # Check for NaN/Inf
    for i, p in enumerate(predictions):
        if not np.all(np.isfinite(p)):
            return {
                "status": "failed",
                "reason": f"Non-finite values found in sample {i}"
            }
    
    return {
        "status": "passed",
        "mean_variance": float(mean_variance),
        "sample_count": len(predictions),
        "image_count": len(image_ids)
    }

def run_confidence_intervals_script(
    model_path: str,
    manifest_path: str,
    output_path: str,
    n_samples: int = 30,
    seed: int = 42
) -> None:
    """
    Main script to generate predictions with confidence intervals.
    
    Args:
        model_path: Path to trained model checkpoint.
        manifest_path: Path to test set manifest.
        output_path: Path to write predictions.csv.
        n_samples: Number of MC dropout samples.
        seed: Random seed for reproducibility.
    """
    logger = setup_predictor_logging()
    logger.info(f"Starting confidence interval calculation with {n_samples} samples")
    
    # Set seed
    set_seed(seed)
    device = "cpu"
    
    # Load model
    logger.info(f"Loading model from {model_path}")
    model = get_model()
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.to(device)
    
    # Load dataset
    logger.info(f"Loading dataset from manifest {manifest_path}")
    dataset = MicrostructureDataset(manifest_path)
    dataloader = OOMSafeDataLoader(dataset, batch_size=8, shuffle=False)
    
    # Run MC Dropout
    logger.info("Running Monte Carlo Dropout inference")
    predictions, image_ids = run_monte_carlo_dropout(model, dataloader, n_samples, device)
    
    # Verify coverage
    logger.info("Verifying coverage")
    verification = verify_coverage(predictions, image_ids)
    if verification["status"] != "passed":
        logger.error(f"Verification failed: {verification['reason']}")
        raise RuntimeError(f"Coverage verification failed: {verification['reason']}")
    
    logger.info("Coverage verification passed")
    
    # Calculate statistics
    logger.info("Calculating confidence intervals")
    mean_preds = np.mean(predictions, axis=0)
    std_preds = np.std(predictions, axis=0)
    
    # 95% CI: mean +/- 1.96 * std
    ci_lower = mean_preds - 1.96 * std_preds
    ci_upper = mean_preds + 1.96 * std_preds
    
    # Load ground truth if available
    ground_truth = {}
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ground_truth[row['image_id']] = float(row['yield_strength_mpa'])
    
    # Write output CSV
    logger.info(f"Writing results to {output_path}")
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'image_id', 
            'prediction', 
            'ci_lower', 
            'ci_upper', 
            'std_dev',
            'ground_truth',
            'error'
        ])
        
        for i, img_id in enumerate(image_ids):
            pred = mean_preds[i]
            lower = ci_lower[i]
            upper = ci_upper[i]
            std = std_preds[i]
            gt = ground_truth.get(img_id, None)
            error = None if gt is None else abs(pred - gt)
            
            writer.writerow([
                img_id,
                f"{pred:.4f}",
                f"{lower:.4f}",
                f"{upper:.4f}",
                f"{std:.4f}",
                gt if gt is not None else "",
                f"{error:.4f}" if error is not None else ""
            ])
    
    logger.info(f"Successfully wrote {len(image_ids)} predictions with confidence intervals")

def main():
    parser = argparse.ArgumentParser(description="Generate predictions with Monte Carlo Dropout confidence intervals")
    parser.add_argument("--model", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--manifest", type=str, required=True, help="Path to test manifest")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path (default: results/predictions.csv)")
    parser.add_argument("--samples", type=int, default=30, help="Number of MC dropout samples")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    if args.output is None:
        results_dir = get_results_dir()
        args.output = os.path.join(results_dir, "predictions.csv")
    
    run_confidence_intervals_script(
        model_path=args.model,
        manifest_path=args.manifest,
        output_path=args.output,
        n_samples=args.samples,
        seed=args.seed
    )

if __name__ == "__main__":
    main()