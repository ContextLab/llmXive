import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import torch
from scipy import stats

# Import from sibling modules based on provided API surface
# Note: We assume the model architecture is available via models.cnn_1d
try:
    from models.cnn_1d import MolecularPropertyCNN
except ImportError:
    # Fallback for execution context where path might differ
    from ..models.cnn_1d import MolecularPropertyCNN

from utils.seed_utils import set_seed

# Configuration
MAE_TOLERANCE_FACTOR = 1.2  # Allow up to 20% increase in MAE compared to test set

logger = logging.getLogger(__name__)

def load_model_checkpoint(checkpoint_path: str, device: str = 'cpu') -> Tuple[MolecularPropertyCNN, Dict[str, Any]]:
    """
    Load the model checkpoint and return the model and state dict.
    """
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

    checkpoint = torch.load(checkpoint_path, map_location=device)
    
    # Determine input size from checkpoint or default
    # The checkpoint should ideally store the input size, but we assume a standard or retrieve from metadata
    input_size = checkpoint.get('input_size', 4000) # Default mid-IR grid size if not specified
    
    model = MolecularPropertyCNN(input_size=input_size)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    
    return model, checkpoint

def generate_synthetic_validation_data(n_samples: int = 100, noise_level: float = 0.1) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate synthetic validation data for Domain Shift Simulation (FR-007 fallback).
    This simulates a scenario where the model encounters data with different noise characteristics.
    """
    logger.info(f"Generating synthetic validation data with {n_samples} samples and noise level {noise_level}")
    
    # Simulate spectra: 1D arrays with shape (n_samples, input_length)
    input_length = 4000 # Standard grid size
    spectra = np.random.normal(loc=0.0, scale=1.0, size=(n_samples, input_length)).astype(np.float32)
    
    # Add domain shift noise (e.g., baseline drift or higher frequency noise)
    baseline_drift = np.linspace(0, noise_level * 2, input_length).astype(np.float32)
    spectra += baseline_drift[np.newaxis, :]
    spectra += np.random.normal(loc=0, scale=noise_level, size=spectra.shape).astype(np.float32)
    
    # Simulate properties based on a noisy linear combination of spectrum features
    # This ensures the properties are somewhat correlated but with added noise (domain shift)
    weights = np.random.randn(input_length, 3).astype(np.float32) * 0.01
    true_properties = np.dot(spectra, weights) + np.random.normal(0, 0.1, (n_samples, 3)).astype(np.float32)
    
    return spectra, true_properties, None # No external file path for synthetic

def load_external_validation_data(file_path: str) -> Tuple[np.ndarray, np.ndarray, Optional[str]]:
    """
    Load external validation data from a real file (e.g., experimental or different DFT).
    Expected format: .npz with keys 'spectra', 'properties', 'inchikey' (optional).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"External validation file not found: {file_path}")
    
    logger.info(f"Loading external validation data from {file_path}")
    data = np.load(file_path)
    
    if 'spectra' not in data or 'properties' not in data:
        raise ValueError("External validation file must contain 'spectra' and 'properties' keys.")
    
    spectra = data['spectra']
    properties = data['properties']
    
    return spectra, properties, file_path

def run_inference(model: MolecularPropertyCNN, spectra: np.ndarray, device: str = 'cpu') -> np.ndarray:
    """
    Run model inference on the provided spectra.
    """
    model.eval()
    with torch.no_grad():
        # Convert to tensor
        input_tensor = torch.from_numpy(spectra).float().to(device)
        
        # Ensure correct shape: (batch, 1, length) if the model expects 1D conv input with channels
        # The CNN definition usually expects (batch, channels, length)
        if input_tensor.dim() == 2:
            input_tensor = input_tensor.unsqueeze(1)
        
        output = model(input_tensor)
        
        # Convert back to numpy
        predictions = output.cpu().numpy()
        
    return predictions

def compute_validation_metrics(y_true: np.ndarray, y_pred: np.ndarray, test_metrics: Dict[str, float]) -> Dict[str, Any]:
    """
    Compute validation metrics (MAE, R2) and flag if MAE exceeds tolerance.
    """
    results = {}
    
    # Calculate MAE and R2 for each property (dipole, polarizability, HOMO-LUMO)
    # Assuming y_true and y_pred are (n_samples, 3)
    properties = ['dipole', 'polarizability', 'homo_lumo_gap']
    
    for i, prop in enumerate(properties):
        true_vals = y_true[:, i]
        pred_vals = y_pred[:, i]
        
        # MAE
        mae = np.mean(np.abs(true_vals - pred_vals))
        
        # R2
        ss_res = np.sum((true_vals - pred_vals) ** 2)
        ss_tot = np.sum((true_vals - np.mean(true_vals)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        results[prop] = {
            'mae': float(mae),
            'r2': float(r2)
        }
        
        # Check against test set metrics for tolerance
        if prop in test_metrics:
            test_mae = test_metrics[prop]['mae']
            # Flag if independent MAE exceeds test MAE by more than 20%
            tolerance_threshold = test_mae * MAE_TOLERANCE_FACTOR
            exceeds_tolerance = mae > tolerance_threshold
            
            results[prop]['exceeds_tolerance'] = exceeds_tolerance
            results[prop]['test_mae'] = float(test_mae)
            results[prop]['tolerance_threshold'] = float(tolerance_threshold)
            
            if exceeds_tolerance:
                logger.warning(f"Property '{prop}' MAE ({mae:.4f}) exceeds tolerance ({tolerance_threshold:.4f}). Domain shift detected.")
            else:
                logger.info(f"Property '{prop}' MAE ({mae:.4f}) is within tolerance ({tolerance_threshold:.4f}).")
        else:
            results[prop]['exceeds_tolerance'] = None
            results[prop]['test_mae'] = None
            results[prop]['tolerance_threshold'] = None

    # Overall summary
    avg_mae = np.mean([results[p]['mae'] for p in properties])
    results['summary'] = {
        'avg_mae': float(avg_mae),
        'max_mae_increase_ratio': float(max([results[p]['mae'] / results[p]['test_mae'] if results[p]['test_mae'] and results[p]['test_mae'] > 0 else 0 for p in properties]))
    }
    
    return results

def main(args):
    """
    Main entry point for independent validation.
    """
    # Parse arguments
    checkpoint_path = args.checkpoint
    external_data_path = args.external_data
    output_path = args.output
    test_metrics_path = args.test_metrics
    device = args.device
    seed = args.seed

    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    set_seed(seed)

    # Load test metrics for comparison
    test_metrics = {}
    if os.path.exists(test_metrics_path):
        with open(test_metrics_path, 'r') as f:
            test_metrics = json.load(f)
        logger.info(f"Loaded test metrics from {test_metrics_path}")
    else:
        logger.warning(f"Test metrics file not found at {test_metrics_path}. Tolerance checks will be skipped.")

    # Load model
    model, checkpoint = load_model_checkpoint(checkpoint_path, device)
    logger.info(f"Model loaded from {checkpoint_path}")

    # Load or generate validation data
    if external_data_path and os.path.exists(external_data_path):
        spectra, true_properties, source = load_external_validation_data(external_data_path)
        logger.info(f"Loaded real external validation data from {source}")
    else:
        # Fallback to synthetic data if external data is unavailable (FR-007)
        logger.warning("External validation data not provided or not found. Generating synthetic validation data (Domain Shift Simulation).")
        spectra, true_properties, source = generate_synthetic_validation_data()
        source = "synthetic_domain_shift"

    # Run inference
    predictions = run_inference(model, spectra, device)
    logger.info(f"Inference completed. Predictions shape: {predictions.shape}")

    # Compute metrics
    validation_results = compute_validation_metrics(true_properties, predictions, test_metrics)
    validation_results['source'] = source
    validation_results['timestamp'] = str(np.datetime64('now'))
    validation_results['tolerance_factor'] = MAE_TOLERANCE_FACTOR

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    logger.info(f"Validation results saved to {output_file}")
    
    # Return exit code based on tolerance flag (optional for CI)
    exceeds_any = any(validation_results[p].get('exceeds_tolerance') for p in validation_results if isinstance(validation_results[p], dict) and 'exceeds_tolerance' in validation_results[p])
    if exceeds_any:
        logger.warning("Validation failed: Independent MAE exceeds tolerance for at least one property.")
        return 1
    else:
        logger.info("Validation passed: Independent MAE within tolerance.")
        return 0

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Independent Validation Script")
    parser.add_argument("--checkpoint", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--external-data", type=str, default=None, help="Path to external validation data (.npz)")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSON file")
    parser.add_argument("--test-metrics", type=str, default="results/evaluation_metrics.json", help="Path to test set metrics JSON")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use (cpu/cuda)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    sys.exit(main(args))
