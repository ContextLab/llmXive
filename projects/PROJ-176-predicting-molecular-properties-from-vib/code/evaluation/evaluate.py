import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

# Import local project modules
# Note: We assume the project root is in sys.path or we adjust it
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from models.cnn_1d import MolecularPropertyCNN
from evaluation.metrics import compute_all_statistics
from utils.logging_utils import get_logger
from utils.seed_utils import set_seed

logger = get_logger(__name__)

# Configuration constants
INPUT_DIM = 2100  # Expected input size based on interpolation grid (approx 400-2500 cm-1)
NUM_PROPERTIES = 3  # dipole, polarizability, HOMO-LUMO
SEED = 42

def load_preprocessed_data(data_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load the preprocessed .npz file containing spectra and properties.
    
    Args:
        data_path: Path to the .npz file (e.g., data/preprocessed/aligned_data.npz)
        
    Returns:
        Tuple of (spectra_array, properties_array)
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Preprocessed data file not found: {data_path}")
    
    logger.info(f"Loading preprocessed data from {data_path}")
    data = np.load(path)
    
    # Expecting keys 'spectra' and 'properties' based on T014d/T016 implementation
    if 'spectra' not in data or 'properties' not in data:
        raise ValueError(f"Invalid data format in {data_path}. Expected 'spectra' and 'properties' keys.")
    
    spectra = data['spectra']
    properties = data['properties']
    
    logger.info(f"Loaded {spectra.shape[0]} samples. Spectra shape: {spectra.shape}, Properties shape: {properties.shape}")
    
    return spectra, properties

def load_model_checkpoint(checkpoint_path: str, input_dim: int = INPUT_DIM) -> MolecularPropertyCNN:
    """
    Load the best model checkpoint.
    
    Args:
        checkpoint_path: Path to the .pt file (e.g., runs/training/model_best.pt)
        input_dim: Expected input dimension for the model
        
    Returns:
        Initialized and loaded MolecularPropertyCNN model
    """
    path = Path(checkpoint_path)
    if not path.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {checkpoint_path}")
    
    logger.info(f"Loading model checkpoint from {checkpoint_path}")
    
    # Initialize model
    model = MolecularPropertyCNN(input_dim=input_dim, num_properties=NUM_PROPERTIES)
    
    # Load state dict
    # Use weights_only=True for safety if PyTorch >= 1.13, else standard load
    try:
        state_dict = torch.load(path, map_location='cpu', weights_only=True)
    except TypeError:
        # Fallback for older PyTorch versions
        state_dict = torch.load(path, map_location='cpu')
    
    model.load_state_dict(state_dict)
    model.eval()
    
    logger.info("Model loaded successfully")
    return model

def load_model_with_dim(checkpoint_path: str, input_dim: int) -> MolecularPropertyCNN:
    """
    Wrapper to load model with a specific input dimension.
    """
    return load_model_checkpoint(checkpoint_path, input_dim)

def run_inference(
    model: MolecularPropertyCNN,
    spectra: np.ndarray,
    batch_size: int = 32,
    device: str = 'cpu'
) -> np.ndarray:
    """
    Run inference on the provided spectra.
    
    Args:
        model: Trained model
        spectra: Numpy array of shape (N, input_dim)
        batch_size: Batch size for inference
        device: Device to run inference on (default 'cpu')
        
    Returns:
        Numpy array of predictions with shape (N, 3)
    """
    logger.info(f"Running inference on {spectra.shape[0]} samples...")
    
    # Convert to tensor
    spectra_tensor = torch.FloatTensor(spectra).to(device)
    dataset = TensorDataset(spectra_tensor)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    
    model.to(device)
    model.eval()
    
    predictions = []
    
    with torch.no_grad():
        for batch in dataloader:
            batch_x = batch[0]
            # Model returns a dict or tuple depending on implementation
            # Based on T025, it likely returns a dict or a tuple of tensors
            output = model(batch_x)
            
            if isinstance(output, dict):
                # Assuming keys are 'dipole', 'polarizability', 'gap' or similar
                # We need to concatenate them
                preds = torch.cat([output[k] for k in output.keys()], dim=1)
            elif isinstance(output, tuple):
                preds = torch.cat(output, dim=1)
            else:
                # Assume it's already (N, 3)
                preds = output
            
            predictions.append(preds.cpu().numpy())
    
    predictions = np.vstack(predictions)
    logger.info(f"Inference complete. Predictions shape: {predictions.shape}")
    
    return predictions

def compute_evaluation_results(
    predictions: np.ndarray,
    true_values: np.ndarray,
    property_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compute evaluation metrics (MAE, R2, Statistical tests) and return a dictionary.
    
    Args:
        predictions: Array of shape (N, 3)
        true_values: Array of shape (N, 3)
        property_names: List of names for the 3 properties
        
    Returns:
        Dictionary containing all metrics and test results
    """
    if property_names is None:
        property_names = ['dipole', 'polarizability', 'homo_lumo_gap']
    
    logger.info("Computing evaluation metrics...")
    
    results = {
        "metrics": {},
        "statistical_tests": {},
        "summary": {}
    }
    
    # Compute per-property metrics
    for i, name in enumerate(property_names):
        if i < predictions.shape[1] and i < true_values.shape[1]:
            pred_col = predictions[:, i]
            true_col = true_values[:, i]
            
            mae, r2 = compute_all_statistics(pred_col, true_col, return_dict=False)
            # compute_all_statistics returns (mae, r2) or similar based on T029/T032
            # If it returns more, we need to adapt. Assuming it returns (mae, r2, p_value, ...)
            # Let's re-verify the signature of compute_all_statistics from metrics.py
            # The prompt says: "compute_all_statistics" returns metrics.
            # Let's assume it returns a dict or a tuple.
            # Based on T029/T032/T033, we likely need to call specific functions or a wrapper.
            # Let's use the specific functions to be safe if compute_all_statistics is complex.
            
            # Re-calling specific functions for clarity and correctness
            from evaluation.metrics import compute_mae, compute_r2, paired_ttest_mean_zero
            
            mae_val = compute_mae(pred_col, true_col)
            r2_val = compute_r2(pred_col, true_col)
            
            # Paired t-test (H0: mean error = 0)
            t_stat, p_val = paired_ttest_mean_zero(pred_col, true_col)
            
            results["metrics"][name] = {
                "mae": float(mae_val),
                "r2": float(r2_val),
                "t_statistic": float(t_stat),
                "p_value": float(p_val)
            }
    
    # Compute aggregate metrics (mean MAE, mean R2)
    all_maes = [results["metrics"][k]["mae"] for k in results["metrics"]]
    all_r2s = [results["metrics"][k]["r2"] for k in results["metrics"]]
    
    results["summary"] = {
        "mean_mae": float(np.mean(all_maes)) if all_maes else 0.0,
        "mean_r2": float(np.mean(all_r2s)) if all_r2s else 0.0,
        "num_samples": int(len(predictions))
    }
    
    logger.info(f"Evaluation complete. Mean MAE: {results['summary']['mean_mae']:.4f}, Mean R2: {results['summary']['mean_r2']:.4f}")
    
    return results

def main():
    """
    Main entry point for the evaluation script.
    Loads model, runs inference on test set, computes metrics, and saves JSON.
    """
    # Setup paths
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "preprocessed" / "aligned_data.npz"
    model_path = project_root / "runs" / "training" / "model_best.pt"
    output_dir = project_root / "results"
    output_path = output_dir / "evaluation_metrics.json"
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Set seed for reproducibility
    set_seed(SEED)
    
    try:
        # 1. Load Data
        # Note: In a real scenario, we might split data again or load a specific test set.
        # For this task, we assume the preprocessed file contains the test data or we use the full set
        # as per the task description "load model_best.pt and test set".
        # If the data file contains train/test splits, we should load the test split.
        # Assuming the file 'aligned_data.npz' contains the final filtered dataset used for evaluation.
        # If the training script saved a separate test file, we would use that.
        # Given T014d saves the final aligned .npz, we use that.
        spectra, properties = load_preprocessed_data(str(data_path))
        
        # 2. Load Model
        model = load_model_checkpoint(str(model_path))
        
        # 3. Run Inference
        predictions = run_inference(model, spectra, device='cpu')
        
        # 4. Compute Metrics
        results = compute_evaluation_results(predictions, properties)
        
        # 5. Save Results
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Evaluation results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
