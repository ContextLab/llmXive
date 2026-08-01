"""
Confidence Interval Calculator using Monte Carlo Dropout.

This module implements FR-008: Calculate confidence intervals using Monte Carlo Dropout.
It also implements the merged T044 requirement to calculate empirical coverage.
"""

import os
import sys
import json
import logging
import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from tqdm import tqdm

# Import project utilities
# Note: We assume the project root is the parent of 'code'
# The config module provides path helpers that handle project root detection
try:
    from utils.config import get_project_root, get_results_dir, get_data_dir, set_seed, get_seed
    from models.cnn import get_model, MaterialStrengthCNN
except ImportError:
    # Fallback for direct execution if path is not set up correctly
    # This usually happens if running from a different directory
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.config import get_project_root, get_results_dir, get_data_dir, set_seed, get_seed
    from models.cnn import get_model, MaterialStrengthCNN


def setup_predictor_logging() -> logging.Logger:
    """Configure logging for the predictor module."""
    logger = logging.getLogger("predictor")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def enable_dropout(model: nn.Module) -> None:
    """
    Enable dropout layers in the model for Monte Carlo Dropout inference.
    
    This recursively sets all Dropout and Dropout2d layers to training mode.
    """
    for module in model.modules():
        if isinstance(module, (nn.Dropout, nn.Dropout2d, nn.Dropout3d)):
            module.train()


def disable_dropout(model: nn.Module) -> None:
    """
    Disable dropout layers in the model (standard inference mode).
    """
    for module in model.modules():
        if isinstance(module, (nn.Dropout, nn.Dropout2d, nn.Dropout3d)):
            module.eval()


def run_monte_carlo_dropout(
    model: nn.Module,
    dataloader: torch.utils.data.DataLoader,
    device: torch.device,
    num_samples: int = 100,
    dropout_rate: float = 0.2,
    logger: Optional[logging.Logger] = None
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Run Monte Carlo Dropout inference to generate predictions with uncertainty.
    
    Args:
        model: The trained CNN model.
        dataloader: DataLoader for the test set.
        device: Torch device (cpu/cuda).
        num_samples: Number of forward passes (N) per sample.
        dropout_rate: Target dropout rate (used to verify configuration, 
                      though we manually enable dropout).
        logger: Logger instance.
    
    Returns:
        Tuple of (image_ids, mean_predictions, std_predictions)
        - image_ids: List of image identifiers.
        - mean_predictions: Array of shape (N_samples,) containing mean predictions.
        - std_predictions: Array of shape (N_samples,) containing std deviations.
        - ALL predictions: A 3D array of shape (N_samples, N_images, 1) containing 
          all raw predictions for coverage calculation.
    """
    if logger:
        logger.info(f"Starting Monte Carlo Dropout with N={num_samples} samples")
    
    model.eval() # Set to eval mode for batch norm, but we will override dropout manually
    
    all_predictions = [] # List to store predictions for each sample pass
    image_ids = []
    
    # We need to collect predictions for every sample in the dataset
    # to calculate coverage later.
    
    with torch.no_grad():
        for batch_idx, batch in enumerate(tqdm(dataloader, desc="MC Dropout Inference")):
            # Depending on how the dataset is structured, batch might be a dict or tuple
            # Assuming standard structure: (images, labels, metadata) or similar
            # Let's assume the dataloader yields (images, labels, ids)
            if isinstance(batch, dict):
                images = batch['image'].to(device)
                ids = batch.get('id', [f"batch_{batch_idx}_i{i}" for i in range(images.shape[0])])
            else:
                # Fallback for tuple
                images = batch[0].to(device)
                ids = batch[2] if len(batch) > 2 else [f"batch_{batch_idx}_i{i}" for i in range(images.shape[0])]
            
            # Store IDs for this batch
            if isinstance(ids, torch.Tensor):
                ids = ids.cpu().numpy().tolist()
            image_ids.extend(ids)
            
            batch_preds = []
            
            # Run N forward passes with dropout enabled
            for _ in range(num_samples):
                # Enable dropout for this pass
                enable_dropout(model)
                
                # Forward pass
                outputs = model(images)
                
                # Assuming output is a single scalar (strength)
                # If output is logits, we might need sigmoid/softmax, but for regression it's usually direct
                preds = outputs.cpu().numpy()
                batch_preds.append(preds)
                
                # Disable dropout immediately after (though next loop enables it)
                # It's safer to just keep it enabled during the loop and disable after
            
            # Stack predictions: shape (num_samples, batch_size, 1)
            batch_preds = np.stack(batch_preds, axis=0)
            all_predictions.append(batch_preds)
            
            # Reset dropout to eval mode (optional, but good practice)
            disable_dropout(model)
    
    # Concatenate all batches
    all_predictions = np.concatenate(all_predictions, axis=1) # Shape: (num_samples, total_images, 1)
    
    # Calculate mean and std across the sample dimension (axis=0)
    mean_preds = np.mean(all_predictions, axis=0).squeeze() # Shape: (total_images,)
    std_preds = np.std(all_predictions, axis=0).squeeze()   # Shape: (total_images,)
    
    return image_ids, mean_preds, std_preds, all_predictions


def verify_coverage(
    all_predictions: np.ndarray,
    true_values: np.ndarray,
    confidence_level: float = 0.95,
    logger: Optional[logging.Logger] = None
) -> float:
    """
    Calculate empirical coverage of the confidence intervals.
    
    Coverage = Percentage of true values that fall within the [2.5th, 97.5th] percentile interval.
    
    Args:
        all_predictions: 3D array of shape (N_samples, N_images, 1).
        true_values: 1D array of shape (N_images,).
        confidence_level: Target confidence level (e.g., 0.95).
    
    Returns:
        Empirical coverage rate (float between 0 and 1).
    """
    if logger:
        logger.info("Calculating empirical coverage...")
    
    # Calculate percentiles along the sample axis (axis=0)
    lower_percentile = (1 - confidence_level) / 2
    upper_percentile = 1 - lower_percentile
    
    ci_lower = np.percentile(all_predictions, lower_percentile * 100, axis=0).squeeze()
    ci_upper = np.percentile(all_predictions, upper_percentile * 100, axis=0).squeeze()
    
    # Check if true values are within the interval
    # Handle broadcasting if true_values is 1D and ci arrays are 1D
    within_interval = (true_values >= ci_lower) & (true_values <= ci_upper)
    
    coverage = np.mean(within_interval)
    
    if logger:
        logger.info(f"Empirical coverage: {coverage:.4f} ({coverage*100:.2f}%)")
    
    return coverage


def run_confidence_intervals_script(
    model_path: str,
    manifest_path: str,
    output_csv_path: str,
    output_json_path: str,
    num_samples: int = 100,
    dropout_rate: float = 0.2,
    seed: int = 42,
    device: str = "cpu"
) -> None:
    """
    Main orchestration function for running confidence interval analysis.
    
    This function:
    1. Loads the model and sets up Monte Carlo Dropout.
    2. Runs inference on the test set.
    3. Calculates CI (2.5th, 97.5th percentiles).
    4. Appends ci_lower and ci_upper to predictions.
    5. Calculates empirical coverage.
    6. Saves results to CSV and JSON.
    """
    logger = setup_predictor_logging()
    logger.info("Starting Confidence Interval Calculation (T032)")
    
    # Set seed for reproducibility
    set_seed(seed)
    
    # Load model
    logger.info(f"Loading model from {model_path}")
    device = torch.device(device)
    model = get_model() # Assumes get_model returns a configured MaterialStrengthCNN
    
    if os.path.exists(model_path):
        state_dict = torch.load(model_path, map_location=device, weights_only=True)
        # Handle potential key mismatches if state_dict has 'module.' prefix
        if 'module' in list(state_dict.keys())[0]:
            state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}
        model.load_state_dict(state_dict)
    else:
        logger.error(f"Model file not found: {model_path}")
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    model.to(device)
    
    # Load Data
    logger.info(f"Loading manifest from {manifest_path}")
    # We need to reconstruct the dataloader. 
    # Assuming the manifest has columns: image_path, yield_strength, id
    # We'll use the existing loader logic if available, or reconstruct simply.
    
    try:
        from data.loader import MicrostructureDataset, OOMSafeDataLoader
        from utils.config import get_processed_dir
        
        # The manifest should point to the processed test set
        # We need to know which split (train/val/test) is in the manifest
        # For this task, we assume the manifest is for the TEST set as per T032 description
        
        dataset = MicrostructureDataset(manifest_path)
        dataloader = OOMSafeDataLoader(
            dataset, 
            batch_size=32, 
            shuffle=False, 
            num_workers=0, # Set to 0 for safety in this script
            pin_memory=False
        )
    except ImportError as e:
        logger.error(f"Failed to import data loader: {e}")
        raise
    
    # Run MC Dropout
    image_ids, mean_preds, std_preds, all_predictions = run_monte_carlo_dropout(
        model, dataloader, device, num_samples=num_samples, dropout_rate=dropout_rate, logger=logger
    )
    
    # Load true values for coverage calculation
    # We assume the manifest contains the true yield strength
    true_values = []
    with open(manifest_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            true_values.append(float(row['yield_strength']))
    true_values = np.array(true_values)
    
    # Calculate Empirical Coverage
    coverage = verify_coverage(all_predictions, true_values, confidence_level=0.95, logger=logger)
    
    # Calculate Percentile CIs
    lower_percentile = 2.5
    upper_percentile = 97.5
    ci_lower = np.percentile(all_predictions, lower_percentile, axis=0).squeeze()
    ci_upper = np.percentile(all_predictions, upper_percentile, axis=0).squeeze()
    
    # Prepare Output CSV
    output_rows = []
    for i, img_id in enumerate(image_ids):
        output_rows.append({
            'image_id': img_id,
            'mean_prediction': float(mean_preds[i]),
            'std_dev': float(std_preds[i]),
            'ci_lower': float(ci_lower[i]),
            'ci_upper': float(ci_upper[i]),
            'true_value': float(true_values[i])
        })
    
    # Ensure output directory exists
    output_dir = Path(output_csv_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    logger.info(f"Writing predictions to {output_csv_path}")
    with open(output_csv_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['image_id', 'mean_prediction', 'std_dev', 'ci_lower', 'ci_upper', 'true_value']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    
    # Write Coverage Report JSON
    coverage_report = {
        "task": "confidence_intervals",
        "num_samples": num_samples,
        "dropout_rate": dropout_rate,
        "confidence_level": 0.95,
        "lower_percentile": lower_percentile,
        "upper_percentile": upper_percentile,
        "empirical_coverage": float(coverage),
        "total_samples": len(image_ids),
        "status": "success"
    }
    
    logger.info(f"Writing coverage report to {output_json_path}")
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(coverage_report, f, indent=2)
    
    logger.info("Confidence Interval Calculation completed successfully.")


def main():
    """CLI entry point for the confidence interval script."""
    parser = argparse.ArgumentParser(description="Calculate Confidence Intervals via Monte Carlo Dropout")
    parser.add_argument("--model", type=str, required=True, help="Path to the trained model (.pt)")
    parser.add_argument("--manifest", type=str, required=True, help="Path to the test set manifest (CSV)")
    parser.add_argument("--output-csv", type=str, required=True, help="Path for output predictions CSV")
    parser.add_argument("--output-json", type=str, required=True, help="Path for coverage report JSON")
    parser.add_argument("--num-samples", type=int, default=100, help="Number of Monte Carlo samples (N)")
    parser.add_argument("--dropout-rate", type=float, default=0.2, help="Dropout rate to use during inference")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--device", type=str, default="cpu", help="Device to run on (cpu/cuda)")
    
    args = parser.parse_args()
    
    try:
        run_confidence_intervals_script(
            model_path=args.model,
            manifest_path=args.manifest,
            output_csv_path=args.output_csv,
            output_json_path=args.output_json,
            num_samples=args.num_samples,
            dropout_rate=args.dropout_rate,
            seed=args.seed,
            device=args.device
        )
    except Exception as e:
        logging.error(f"Script failed: {e}")
        raise


if __name__ == "__main__":
    main()