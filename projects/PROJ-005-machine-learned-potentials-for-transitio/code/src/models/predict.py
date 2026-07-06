"""
T026: Implement prediction script for barrier height estimation.
Generates metrics (MAE, RMSE, Pearson) and residuals for the held-out test set.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from torch_geometric.data import DataLoader
from torch_geometric.data import Data

# Import from project structure
from src.models.schnet import SchNet, get_model_config
from src.utils.config import get_project_root, load_yaml_config
from src.utils.logging import setup_logger, log_progress, log_metric, log_error_summary

logger = logging.getLogger(__name__)

def load_checkpoint(model: SchNet, checkpoint_path: Path, device: torch.device) -> SchNet:
    """Load weights from a checkpoint file."""
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    logger.info(f"Loading checkpoint from {checkpoint_path}")
    checkpoint = torch.load(checkpoint_path, map_location=device)
    model.load_state_dict(checkpoint['state_dict'])
    model.to(device)
    model.eval()
    return model

def predict_batch(
    model: SchNet,
    batch: Data,
    device: torch.device
) -> torch.Tensor:
    """Run inference on a batch of graphs."""
    with torch.no_grad():
        batch = batch.to(device)
        output = model(batch)
        return output.cpu().numpy().flatten()

def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Dict[str, float]:
    """Compute MAE, RMSE, and Pearson correlation."""
    if len(y_true) == 0:
        return {
            "mae": 0.0,
            "rmse": 0.0,
            "pearson_r": 0.0,
            "n_samples": 0
        }

    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
    
    # Pearson correlation
    if np.std(y_true) == 0 or np.std(y_pred) == 0:
        pearson_r = 0.0
    else:
        pearson_r = np.corrcoef(y_true, y_pred)[0, 1]
        if np.isnan(pearson_r):
            pearson_r = 0.0

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "pearson_r": float(pearson_r),
        "n_samples": len(y_true)
    }

def run_prediction_ensemble(
    data_path: Path,
    model_dir: Path,
    output_metrics_path: Path,
    output_residuals_path: Path,
    device: torch.device,
    batch_size: int = 32
) -> Dict[str, Any]:
    """
    Run the ensemble prediction on the test set.
    
    Logic:
    1. Load test data (parquet) containing node/edge features and target (barrier).
    2. Convert to PyG Data objects.
    3. Load 5 model checkpoints.
    4. Aggregate predictions (mean) and compute residuals (ML - DFT).
    5. Compute aggregate metrics.
    6. Save metrics.json and residuals.parquet.
    """
    # 1. Load Data
    logger.info(f"Loading test data from {data_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Test data not found: {data_path}. Ensure T020 (graph generation) is complete.")
    
    df_graphs = pd.read_parquet(data_path)
    
    # Convert dataframe to list of PyG Data objects
    # Assumes columns: 'atomic_numbers' (list), 'pos' (list of lists), 'edge_index' (list of lists), 'edge_attr' (list), 'y' (scalar)
    # We need to reconstruct the Data object structure expected by SchNet
    graphs = []
    for idx, row in df_graphs.iterrows():
        # Handle potential list/string parsing if stored as strings
        atomic_numbers = row.get('atomic_numbers')
        if isinstance(atomic_numbers, str):
            atomic_numbers = eval(atomic_numbers)
        
        pos = row.get('pos')
        if isinstance(pos, str):
            pos = eval(pos)
        
        edge_index = row.get('edge_index')
        if isinstance(edge_index, str):
            edge_index = eval(edge_index)
        
        edge_attr = row.get('edge_attr')
        if isinstance(edge_attr, str):
            edge_attr = eval(edge_attr)
        
        y = row.get('y') # Barrier height
        
        if atomic_numbers is None or pos is None:
            logger.warning(f"Skipping row {idx} due to missing features")
            continue

        # Convert to tensors
        x = torch.tensor(atomic_numbers, dtype=torch.long).unsqueeze(1)
        pos_tensor = torch.tensor(pos, dtype=torch.float)
        
        # Edge index usually [2, num_edges]
        if edge_index and len(edge_index) == 2:
            edge_index_tensor = torch.tensor(edge_index, dtype=torch.long)
        else:
            # Fallback if stored differently, though spec implies standard format
            edge_index_tensor = torch.tensor(edge_index, dtype=torch.long).t().contiguous()

        edge_attr_tensor = torch.tensor(edge_attr, dtype=torch.float) if edge_attr else torch.empty((0, 1))

        graph = Data(
            x=x,
            pos=pos_tensor,
            edge_index=edge_index_tensor,
            edge_attr=edge_attr_tensor,
            y=torch.tensor([y], dtype=torch.float)
        )
        graphs.append(graph)

    logger.info(f"Loaded {len(graphs)} test graphs")
    if len(graphs) == 0:
        raise ValueError("No valid graphs loaded for prediction.")

    # 2. Prepare DataLoader
    loader = DataLoader(graphs, batch_size=batch_size, shuffle=False)

    # 3. Load Models
    model_config = get_model_config()
    device = torch.device(device)
    
    checkpoints = sorted(list(model_dir.glob("seed_*.pt")))
    if len(checkpoints) == 0:
        raise FileNotFoundError(f"No model checkpoints found in {model_dir}. Ensure T025 (training) is complete.")
    
    models = []
    for cp in checkpoints:
        model = SchNet(**model_config)
        load_checkpoint(model, cp, device)
        models.append(model)
    
    logger.info(f"Loaded {len(models)} ensemble models")

    # 4. Predict and Aggregate
    all_true = []
    all_pred_mean = []
    all_residuals = []
    all_pred_variance = [] # Optional: for uncertainty analysis later

    for batch in loader:
        batch_preds = []
        for model in models:
          preds = predict_batch(model, batch, device)
          batch_preds.append(preds)
        
        # Stack: (n_models, n_samples)
        batch_preds = np.stack(batch_preds, axis=0)
        
        # Mean prediction
        mean_pred = np.mean(batch_preds, axis=0)
        # Variance (optional, for SC-005 later)
        variance = np.var(batch_preds, axis=0)
        
        # Get targets
        batch_y = batch.y.cpu().numpy().flatten()
        
        all_true.extend(batch_y)
        all_pred_mean.extend(mean_pred)
        all_pred_variance.extend(variance)

        # Residual = ML - DFT (Predicted - True)
        residuals = mean_pred - batch_y
        all_residuals.extend(residuals.tolist())

    y_true = np.array(all_true)
    y_pred = np.array(all_pred_mean)
    residuals = np.array(all_residuals)

    # 5. Compute Metrics
    metrics = compute_metrics(y_true, y_pred)
    
    # Add ensemble variance info to metrics if needed, or save separately
    # For now, just basic metrics as per FR-004
    log_metric("MAE", metrics["mae"])
    log_metric("RMSE", metrics["rmse"])
    log_metric("Pearson R", metrics["pearson_r"])

    # 6. Save Artifacts
    # Save metrics.json
    output_metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {output_metrics_path}")

    # Save residuals.parquet
    # Create a dataframe with original indices (if available) or just row index
    # We need to map back to the original df to include original features if desired, 
    # but task specifically asks for residuals.parquet containing per-sample error.
    residuals_df = pd.DataFrame({
        "true_barrier": y_true,
        "predicted_barrier": y_pred,
        "residual": residuals,
        "ensemble_variance": all_pred_variance
    })
    
    # Add original index if we want to trace back
    residuals_df["original_index"] = range(len(residuals_df))
    
    output_residuals_path.parent.mkdir(parents=True, exist_ok=True)
    residuals_df.to_parquet(output_residuals_path, index=False)
    logger.info(f"Saved residuals to {output_residuals_path}")

    return metrics

def main():
    """Main entry point for T026."""
    project_root = get_project_root()
    config = load_yaml_config(project_root / "config.yaml")
    
    # Paths
    data_path = project_root / "data" / "processed" / "graphs.parquet"
    model_dir = project_root / "data" / "processed" / "models"
    output_metrics = project_root / "data" / "processed" / "metrics.json"
    output_residuals = project_root / "data" / "processed" / "residuals.parquet"
    
    # Setup logger
    setup_logger(project_root / "data" / "logs" / "predict.log")
    
    logger.info("Starting T026: Prediction and Metrics Generation")
    
    try:
        # Determine device
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if device.type == "cpu":
            logger.warning("Running on CPU. Training was also required to be CPU-compatible.")
        
        metrics = run_prediction_ensemble(
            data_path=data_path,
            model_dir=model_dir,
            output_metrics_path=output_metrics,
            output_residuals_path=output_residuals,
            device=device,
            batch_size=32
        )
        
        logger.info("T026 completed successfully.")
        print(json.dumps(metrics, indent=2))
        
    except Exception as e:
        log_error_summary(e)
        logger.error(f"T026 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
