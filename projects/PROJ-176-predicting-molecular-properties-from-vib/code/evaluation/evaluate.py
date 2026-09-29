import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import torch
from models.cnn_1d import MolecularPropertyCNN

def load_preprocessed_data(path: str) -> Dict[str, np.ndarray]:
    data = np.load(path)
    return {
        "spectra": data["spectra"],
        "properties": data["properties"],
        "keys": data["keys"]
    }

def load_model_checkpoint(path: str, device: str = "cpu") -> MolecularPropertyCNN:
    model = MolecularPropertyCNN()
    model.load_state_dict(torch.load(path, map_location=device))
    model.to(device)
    model.eval()
    return model

def load_model_with_dim(path: str, input_dim: int) -> MolecularPropertyCNN:
    model = MolecularPropertyCNN(input_dim=input_dim)
    model.load_state_dict(torch.load(path, map_location="cpu"))
    return model

def run_inference(model: MolecularPropertyCNN, spectra: np.ndarray) -> Dict[str, np.ndarray]:
    model.eval()
    with torch.no_grad():
        x = torch.FloatTensor(spectra).unsqueeze(1)
        preds = model(x)
        return {
            "mu": preds["mu"].numpy().squeeze(),
            "alpha": preds["alpha"].numpy().squeeze(),
            "gap": preds["gap"].numpy().squeeze()
        }

def compute_evaluation_results(y_true: np.ndarray, y_pred: Dict[str, np.ndarray]) -> Dict[str, Any]:
    # y_true shape: (N, 3) -> mu, alpha, gap
    results = {
        "mu": {"mae": 0.0, "r2": 0.0},
        "alpha": {"mae": 0.0, "r2": 0.0},
        "gap": {"mae": 0.0, "r2": 0.0}
    }
    
    from evaluation.metrics import compute_mae, compute_r2
    
    results["mu"]["mae"] = float(compute_mae(y_true[:, 0], y_pred["mu"]))
    results["mu"]["r2"] = float(compute_r2(y_true[:, 0], y_pred["mu"]))
    results["alpha"]["mae"] = float(compute_mae(y_true[:, 1], y_pred["alpha"]))
    results["alpha"]["r2"] = float(compute_r2(y_true[:, 1], y_pred["alpha"]))
    results["gap"]["mae"] = float(compute_mae(y_true[:, 2], y_pred["gap"]))
    results["gap"]["r2"] = float(compute_r2(y_true[:, 2], y_pred["gap"]))
    
    return results

def main(model_path: str, data_path: str, output_dir: str):
    logger = logging.getLogger(__name__)
    logger.info("Running evaluation")
    
    data = load_preprocessed_data(data_path)
    model = load_model_checkpoint(model_path)
    
    # Split for test (assuming last 20%)
    N = len(data["spectra"])
    test_start = int(0.8 * N)
    
    test_spectra = data["spectra"][test_start:]
    test_props = data["properties"][test_start:]
    
    y_pred = run_inference(model, test_spectra)
    
    results = compute_evaluation_results(test_props, y_pred)
    
    output_path = Path(output_dir) / "evaluation_metrics.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Evaluation results saved to {output_path}")

if __name__ == "__main__":
    main("models/model_best.pt", "data/preprocessed/aligned_data.npz", "results")
