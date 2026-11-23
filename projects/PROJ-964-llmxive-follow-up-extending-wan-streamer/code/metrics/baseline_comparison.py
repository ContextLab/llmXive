"""
Baseline comparison logic for T020.
Compares the GRU Estimator against a zero-delta predictor baseline.

Outputs:
    data/metrics/baseline_comparison.json with MSE values and p-values.

Defers FID stability correlation to T043.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
import torch
from scipy import stats

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.config import get_config_summary, set_seed
from utils.validators import validate_json_file
from data.preprocess import load_config

logger = logging.getLogger(__name__)

# Paths
DATA_METRICS_DIR = PROJECT_ROOT / "data" / "metrics"
BASELINE_OUTPUT_PATH = DATA_METRICS_DIR / "baseline_comparison.json"
MODEL_CHECKPOINT_PATH = PROJECT_ROOT / "data" / "models" / "estimator_checkpoint.pt"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "final_dataset.parquet"

def load_model_data() -> Tuple[pd.DataFrame, Optional[torch.nn.Module]]:
    """
    Loads the preprocessed dataset and the trained GRU model.
    """
    if not PROCESSED_DATA_PATH.exists():
        raise FileNotFoundError(
            f"Processed data not found at {PROCESSED_DATA_PATH}. "
            "Please run T014 (preprocess.py) first."
        )
    
    df = pd.read_parquet(PROCESSED_DATA_PATH)
    
    # Verify required columns for baseline comparison
    required_cols = ["latent_delta_magnitude", "features"] # features might be a list/json or separate cols
    # If features are separate columns, we need to reconstruct X. 
    # Assuming 'features' column exists as a string representation or we need to select numeric cols.
    # For robustness, we select all numeric cols except target if 'features' isn't explicit.
    
    if "latent_delta_magnitude" not in df.columns:
        raise ValueError("Dataset missing 'latent_delta_magnitude' column.")

    # Attempt to load model
    model = None
    if MODEL_CHECKPOINT_PATH.exists():
        try:
            checkpoint = torch.load(MODEL_CHECKPOINT_PATH, map_location="cpu")
            # We need to reconstruct the model architecture. 
            # Since we can't import the class directly without circular issues or if it's not exported cleanly,
            # we try to infer input size from data or use a generic loader if the checkpoint has the model dict.
            # However, the task requires comparing against the model trained in T018/T019.
            # We will assume the checkpoint contains 'model_state_dict' and we need the architecture.
            # To keep it self-contained, we will re-instantiate the GRUEstimator if possible, 
            # or if T018 saved the architecture params, load them.
            # Given the constraints, we will try to load the model if the class is available.
            from models.gru_estimator import GRUEstimator
            
            # Heuristic: assume input size is based on remaining numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            numeric_cols = [c for c in numeric_cols if c != "latent_delta_magnitude"]
            input_size = len(numeric_cols)
            
            # Default hidden size if not specified
            hidden_size = 64 
            
            model = GRUEstimator(input_size=input_size, hidden_size=hidden_size, output_size=2)
            model.load_state_dict(checkpoint['model_state_dict'])
            model.eval()
            logger.info(f"Model loaded from {MODEL_CHECKPOINT_PATH}")
        except Exception as e:
            logger.warning(f"Failed to load model for inference: {e}. Proceeding with zero-delta baseline only.")
            model = None
    else:
        logger.warning(f"Model checkpoint not found at {MODEL_CHECKPOINT_PATH}. Comparing against zero-delta baseline only.")

    return df, model

def compute_zero_delta_mse(df: pd.DataFrame) -> float:
    """
    Computes MSE for a zero-delta predictor (always predicts 0).
    """
    y_true = df["latent_delta_magnitude"].values
    y_pred = np.zeros_like(y_true)
    mse = np.mean((y_true - y_pred) ** 2)
    return float(mse)

def compute_model_mse(df: pd.DataFrame, model: Optional[torch.nn.Module]) -> Optional[float]:
    """
    Computes MSE for the trained GRU model.
    """
    if model is None:
        return None

    # Prepare data
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [c for c in numeric_cols if c != "latent_delta_magnitude"]
    
    if len(numeric_cols) == 0:
        raise ValueError("No numeric feature columns found for model input.")

    X = df[numeric_cols].values
    y_true = df["latent_delta_magnitude"].values

    # Convert to tensors
    X_tensor = torch.FloatTensor(X)
    
    # Inference
    with torch.no_grad():
        outputs = model(X_tensor)
        # Output column 0 is predicted delta magnitude
        y_pred = outputs[:, 0].numpy()

    mse = np.mean((y_true - y_pred) ** 2)
    return float(mse)

def perform_statistical_test(
    df: pd.DataFrame, 
    model_preds: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Performs a paired t-test (or one-sample t-test if model is absent) to compare
    errors against the zero-delta baseline.
    
    Returns dict with t_statistic, p_value, significant.
    """
    y_true = df["latent_delta_magnitude"].values
    zero_preds = np.zeros_like(y_true)
    zero_errors = y_true - zero_preds # This is just y_true
    
    if model_preds is not None:
        model_errors = y_true - model_preds
        
        # Paired t-test: is the difference in errors significant?
        # H0: mean(zero_errors - model_errors) == 0
        differences = zero_errors - model_errors
        t_stat, p_val = stats.ttest_rel(zero_errors, model_errors)
        
        return {
            "t_statistic": float(t_stat),
            "p_value": float(p_val),
            "significant_at_0.05": bool(p_val < 0.05)
        }
    else:
        # If no model, we can't do a paired test. 
        # We can test if the mean error of the zero-delta baseline is significantly different from 0?
        # But the task asks to validate MSE improvement. Without a model, there is no improvement to test.
        # We return nulls as per the placeholder structure, or indicate "N/A".
        return {
            "t_statistic": None,
            "p_value": None,
            "significant_at_0.05": None
        }

def run_baseline_comparison(args: argparse.Namespace) -> None:
    """
    Main execution function for T020.
    """
    set_seed(42) # From T007
    
    DATA_METRICS_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading data and model...")
    df, model = load_model_data()
    
    logger.info("Computing Zero-Delta MSE...")
    zero_mse = compute_zero_delta_mse(df)
    
    logger.info("Computing Model MSE...")
    model_mse = compute_model_mse(df, model)
    
    # Prepare predictions for stats if model exists
    model_preds = None
    if model is not None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c != "latent_delta_magnitude"]
        X = df[numeric_cols].values
        X_tensor = torch.FloatTensor(X)
        with torch.no_grad():
            outputs = model(X_tensor)
            model_preds = outputs[:, 0].numpy()
    
    logger.info("Performing statistical test...")
    stats_result = perform_statistical_test(df, model_preds)
    
    improvement = None
    if model_mse is not None:
        improvement = zero_mse - model_mse
    
    result = {
        "zero_delta_mse": zero_mse,
        "model_mse": model_mse,
        "improvement": improvement,
        "statistical_test": stats_result,
        "note": "Correlation with FID stability (r >= 0.7) is deferred to T043.",
        "status": "completed" if model is not None else "completed_no_model"
    }
    
    logger.info(f"Writing results to {BASELINE_OUTPUT_PATH}")
    with open(BASELINE_OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    
    # Validate the output file
    validate_json_file(BASELINE_OUTPUT_PATH)
    
    logger.info("Baseline comparison complete.")
    print(f"Results saved to: {BASELINE_OUTPUT_PATH}")
    if model_mse is not None:
        print(f"Model MSE: {model_mse:.4f}, Zero-Delta MSE: {zero_mse:.4f}, Improvement: {improvement:.4f}")
    else:
        print("Model not available for comparison.")

def main():
    parser = argparse.ArgumentParser(description="Baseline comparison for T020")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    run_baseline_comparison(args)

if __name__ == "__main__":
    main()
