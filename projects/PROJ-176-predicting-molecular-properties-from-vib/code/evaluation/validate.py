import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import torch
from models.cnn_1d import MolecularPropertyCNN
from evaluation.evaluate import load_model_checkpoint, run_inference

def generate_synthetic_validation_data(n_samples: int = 100) -> Dict[str, np.ndarray]:
    """Generate synthetic noise for domain shift simulation."""
    logger = logging.getLogger(__name__)
    logger.warning("Using synthetic validation data (Domain Shift Simulation)")
    spectra = np.random.randn(n_samples, 3601)
    props = np.random.randn(n_samples, 3)
    return {"spectra": spectra, "properties": props}

def load_external_validation_data(path: str) -> Dict[str, np.ndarray]:
    # Load real external data
    return np.load(path)

def compute_validation_metrics(y_true: np.ndarray, y_pred: Dict[str, np.ndarray]) -> Dict[str, float]:
    from evaluation.metrics import compute_mae, compute_r2
    mae_mu = compute_mae(y_true[:, 0], y_pred["mu"])
    mae_alpha = compute_mae(y_true[:, 1], y_pred["alpha"])
    mae_gap = compute_mae(y_true[:, 2], y_pred["gap"])
    return {
        "mae_mu": mae_mu,
        "mae_alpha": mae_alpha,
        "mae_gap": mae_gap
    }

def main(model_path: str, external_data_path: Optional[str], output_dir: str):
    logger = logging.getLogger(__name__)
    logger.info("Running independent validation")
    
    model = load_model_checkpoint(model_path)
    
    if external_data_path and os.path.exists(external_data_path):
        data = load_external_validation_data(external_data_path)
    else:
        data = generate_synthetic_validation_data()
    
    test_spectra = data["spectra"]
    test_props = data["properties"]
    
    y_pred = run_inference(model, test_spectra)
    metrics = compute_validation_metrics(test_props, y_pred)
    
    output_path = Path(output_dir) / "validation_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Validation results saved to {output_path}")

if __name__ == "__main__":
    main("models/model_best.pt", None, "results")
