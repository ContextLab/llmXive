"""
Evaluation script for User Story 3.
Loads the best model checkpoint and the preprocessed test set,
runs inference, computes metrics (MAE, R²), performs statistical tests,
and saves results to results/evaluation_metrics.json.
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

# Project imports matching the API surface
from models.cnn_1d import MolecularPropertyCNN
from evaluation.metrics import (
    compute_mae,
    compute_r2,
    compute_all_statistics,
    compute_metrics_per_property,
)
from utils.seed_utils import set_seed
from utils.update_state import update_artifact_state

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
TARGET_PROPERTIES = ["dipole", "polarizability", "homo_lumo_gap"]
DEVICE = "cpu"  # Enforce CPU-only as per constraints

def load_preprocessed_data(data_path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load the preprocessed .npz file containing spectra and properties.
    Returns: (spectra, properties, inchikeys, metadata)
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found at {data_path}")
    
    logger.info(f"Loading preprocessed data from {data_path}")
    data = np.load(data_path, allow_pickle=True)
    
    # Expecting keys based on T014d implementation:
    # 'spectra': (N, L), 'properties': (N, 3), 'inchikeys': (N,), 'metadata': dict or object
    spectra = data["spectra"]
    properties = data["properties"]
    inchikeys = data["inchikeys"] if "inchikeys" in data else None
    
    # Split into train/val/test if not already done, or assume the file contains all
    # For this task, we assume the preprocessed file contains the full dataset.
    # The trainer (T026) likely saved a specific split or we need to split here.
    # However, T023 (Integration) usually handles the split and saves the model.
    # To be robust, we assume the preprocessed file has 'train_indices', 'val_indices', 'test_indices'
    # if they exist, otherwise we assume the file provided to this script is the TEST set
    # or we need to load the specific test split generated during training.
    
    # Re-reading T023: "load preprocessed .npz, split data, train, and save best checkpoint".
    # T026 Trainer handles the split.
    # For evaluation, we need the TEST set.
    # Option A: The preprocessed file has a 'test' key.
    # Option B: We load the full file and re-split (requires seed consistency).
    # Option C: The trainer saved a 'test_indices.npy' or similar.
    
    # Let's assume the standard pipeline saves indices in the .npz or we re-split deterministically.
    # Given T026 uses a fixed seed, we can re-split if indices aren't stored.
    # But to be safe and avoid re-splitting errors, let's check for stored indices.
    
    if "test_indices" in data:
        test_idx = data["test_indices"]
        spectra = spectra[test_idx]
        properties = properties[test_idx]
        if inchikeys is not None:
            inchikeys = inchikeys[test_idx]
        logger.info(f"Using stored test split: {len(test_idx)} samples")
    else:
        # Fallback: deterministic split if not stored (using seed from T006)
        logger.warning("No stored test indices found. Re-splitting data deterministically.")
        set_seed(42)
        n = len(spectra)
        indices = np.arange(n)
        np.random.shuffle(indices)
        split_ratio = 0.2
        test_size = int(n * split_ratio)
        test_idx = indices[:test_size]
        spectra = spectra[test_idx]
        properties = properties[test_idx]
        if inchikeys is not None:
            inchikeys = inchikeys[test_idx]
        logger.info(f"Re-split test set: {len(test_idx)} samples")

    return spectra, properties, inchikeys, data.get("metadata", {})

def load_model_checkpoint(checkpoint_path: Path, device: str = DEVICE) -> MolecularPropertyCNN:
    """
    Load the model architecture and weights from the checkpoint.
    """
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found at {checkpoint_path}")
    
    logger.info(f"Loading model from {checkpoint_path}")
    
    # We need to reconstruct the model architecture.
    # T025 defines the model. We assume standard hyperparameters if not saved in checkpoint.
    # Or the checkpoint dict should contain 'model_state_dict' and potentially config.
    
    # Default architecture parameters from T025:
    # 3 convolutional blocks, kernel sizes (9, 64, ...), 3 heads.
    # Let's assume input_dim is inferred from data or fixed.
    # T014b interpolates to a fixed grid. Let's assume a standard size or read from data.
    
    # For now, we assume the checkpoint was saved with the model class.
    # If not, we need to instantiate manually.
    # T025: MolecularPropertyCNN.
    
    # Attempt to load config from checkpoint if available
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    
    # If config is saved, use it. Otherwise, assume defaults.
    # Assuming input_dim is derived from the first key in state_dict or data.
    # We will pass the input_dim from the data later, but here we need to instantiate.
    # Let's assume a default input size of 1000 (typical for interpolated IR) if not found.
    # Better: We can infer input_dim from the first layer in state_dict if we inspect it,
    # but simpler is to pass it from the data loading step.
    
    # To make this robust, we'll instantiate the model with a placeholder input_dim
    # and then check if the checkpoint keys match.
    # Actually, the best way is to load the model *after* we know input_dim from data.
    # But we need the model to run inference.
    
    # Let's assume the checkpoint contains 'input_dim' or we hardcode a reasonable default
    # based on T014b (mid-infrared region, unit spacing).
    # Standard IR range ~400-4000 cm-1. If unit spacing, ~3600 points.
    # Let's assume the data loaded in load_preprocessed_data tells us the length.
    
    # We will defer model instantiation until we have the data shape.
    # But the function signature requires returning the model.
    # We will return a partially initialized model or raise if we can't.
    # Better approach: Load model inside the main function where data is available.
    # However, to keep the function pure, let's assume we can load the model
    # if we know the input_dim.
    
    # Let's assume the checkpoint was saved with the model instance (torch.save(model)).
    # If so, we can just load it.
    # T026 Trainer: "save best checkpoint (model_best.pt)". Usually saves state_dict.
    
    # We will assume the checkpoint has 'model_state_dict' and 'config'.
    config = checkpoint.get("config", {})
    input_dim = config.get("input_dim", None)
    
    if input_dim is None:
        # Fallback: try to infer from state_dict keys
        # Key pattern: 'conv_blocks.0.conv.1.weight' -> (64, 1, kernel_size)
        # We can't easily infer input_dim from the first conv layer without knowing the kernel.
        # Let's assume a default of 3600 (4000-400) or read from the data later.
        # For now, raise an error if we can't find it, as we need to know the architecture.
        # Or, we assume the model was saved with the class definition in the path.
        pass
    
    # Since we can't reliably reconstruct without input_dim or the full object,
    # and T026 likely saves state_dict, we will handle instantiation in main()
    # where we have the data.
    # This function will be a placeholder or we change the design.
    # Let's change: This function will take input_dim as argument.
    raise NotImplementedError("Model loading requires input_dim. Use load_model_with_dim instead.")

def load_model_with_dim(
    checkpoint_path: Path, input_dim: int, device: str = DEVICE
) -> MolecularPropertyCNN:
    """
    Load model with known input dimension.
    """
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Model checkpoint not found at {checkpoint_path}")
    
    logger.info(f"Loading model from {checkpoint_path} with input_dim={input_dim}")
    
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    
    # Reconstruct model
    # T025: MolecularPropertyCNN
    # We need to know the exact hyperparameters used in training.
    # Assuming defaults from T025 if not in checkpoint:
    # kernel_sizes: (9, 64, ...), 3 heads.
    # Let's assume the checkpoint saved the config.
    config = checkpoint.get("config", {})
    kernel_sizes = config.get("kernel_sizes", [9, 64, 16]) # Example defaults
    hidden_dim = config.get("hidden_dim", 128)
    
    # Instantiate
    model = MolecularPropertyCNN(
        input_dim=input_dim,
        kernel_sizes=kernel_sizes,
        hidden_dim=hidden_dim,
        num_heads=3,
        device=device
    )
    
    # Load state
    if "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    elif "state_dict" in checkpoint:
        model.load_state_dict(checkpoint["state_dict"])
    else:
        # If the whole model was saved
        if isinstance(checkpoint, MolecularPropertyCNN):
            model = checkpoint
        else:
            raise ValueError("Checkpoint does not contain model_state_dict or model instance.")
    
    model.to(device)
    model.eval()
    return model

def run_inference(
    model: MolecularPropertyCNN,
    spectra: np.ndarray,
    device: str = DEVICE,
    batch_size: int = 64,
) -> np.ndarray:
    """
    Run inference on the spectra and return predicted properties.
    """
    logger.info(f"Running inference on {len(spectra)} samples")
    
    # Convert to tensor
    x = torch.FloatTensor(spectra).unsqueeze(1).to(device) # (N, 1, L)
    
    dataset = TensorDataset(x)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    
    predictions = []
    
    with torch.no_grad():
        for batch in loader:
            x_batch = batch[0]
            out = model(x_batch) # (N, 3)
            predictions.append(out.cpu().numpy())
    
    return np.vstack(predictions)

def compute_evaluation_results(
    predictions: np.ndarray,
    targets: np.ndarray,
    properties: List[str] = TARGET_PROPERTIES,
) -> Dict[str, Any]:
    """
    Compute metrics and statistical tests.
    """
    logger.info("Computing evaluation metrics and statistics")
    
    # Compute per-property metrics
    metrics_per_prop = {}
    all_metrics = {}
    
    for i, prop in enumerate(properties):
        y_pred = predictions[:, i]
        y_true = targets[:, i]
        
        mae = compute_mae(y_true, y_pred)
        r2 = compute_r2(y_true, y_pred)
        
        metrics_per_prop[prop] = {
            "mae": float(mae),
            "r2": float(r2),
        }
        
        # Statistical tests
        # Paired t-test (mean error = 0)
        t_stat, p_val_t = paired_ttest_mean_zero(y_true, y_pred)
        # TOST
        tost_res = tost_equivalence_test(y_true, y_pred, equivalence_margin=0.1) # Margin example
        # Hotelling's T2
        hotelling_res = hotellings_t2_test(y_true, y_pred)
        
        all_metrics[f"{prop}_ttest_pvalue"] = float(p_val_t)
        all_metrics[f"{prop}_tost_pvalue"] = float(tost_res.get("pvalue", 0.0))
        all_metrics[f"{prop}_hotelling_pvalue"] = float(hotelling_res.get("pvalue", 0.0))
    
    # Aggregate metrics
    aggregate_mae = np.mean([metrics_per_prop[p]["mae"] for p in properties])
    aggregate_r2 = np.mean([metrics_per_prop[p]["r2"] for p in properties])
    
    results = {
        "summary": {
            "mean_mae": float(aggregate_mae),
            "mean_r2": float(aggregate_r2),
            "num_samples": int(len(targets)),
        },
        "per_property": metrics_per_prop,
        "statistical_tests": {
            "paired_ttest": {
                prop: {
                    "p_value": all_metrics[f"{prop}_ttest_pvalue"]
                } for prop in properties
            },
            "tost": {
                prop: {
                    "p_value": all_metrics[f"{prop}_tost_pvalue"]
                } for prop in properties
            },
            "hotelling": {
                prop: {
                    "p_value": all_metrics[f"{prop}_hotelling_pvalue"]
                } for prop in properties
            }
        }
    }
    
    return results

def main(
    model_path: Optional[str] = None,
    data_path: Optional[str] = None,
    output_path: Optional[str] = None,
):
    """
    Main entry point for evaluation.
    """
    # Defaults
    if model_path is None:
        model_path = "models/model_best.pt"
    if data_path is None:
        data_path = "data/preprocessed/aligned_data.npz"
    if output_path is None:
        output_path = "results/evaluation_metrics.json"
    
    model_path = Path(model_path)
    data_path = Path(data_path)
    output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 1. Load Data
    spectra, properties, inchikeys, metadata = load_preprocessed_data(data_path)
    input_dim = spectra.shape[-1]
    logger.info(f"Data loaded: {spectra.shape[0]} samples, input_dim={input_dim}")
    
    # 2. Load Model
    model = load_model_with_dim(model_path, input_dim, device=DEVICE)
    
    # 3. Run Inference
    predictions = run_inference(model, spectra, device=DEVICE)
    
    # 4. Compute Metrics
    results = compute_evaluation_results(predictions, properties)
    
    # 5. Save Results
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Evaluation results saved to {output_path}")
    
    # 6. Update State
    update_artifact_state(output_path, "evaluation_metrics.json")
    
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate model on test set")
    parser.add_argument("--model", type=str, default="models/model_best.pt", help="Path to model checkpoint")
    parser.add_argument("--data", type=str, default="data/preprocessed/aligned_data.npz", help="Path to preprocessed data")
    parser.add_argument("--output", type=str, default="results/evaluation_metrics.json", help="Path to output JSON")
    args = parser.parse_args()
    
    main(model_path=args.model, data_path=args.data, output_path=args.output)