"""
Evaluation metrics for GNN model on the test set.
Calculates RMSE and R-squared.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Tuple, List

import numpy as np
import torch
from torch_geometric.data import Data

# Project imports based on existing API surface
from models.gnn_mpnn import GNNMPNN
from training.train_gnn import load_graph_data
from config.seeds import get_seed

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/evaluation_metrics.log')
    ]
)
logger = logging.getLogger(__name__)

def calculate_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Root Mean Squared Error.
    
    Args:
        y_true: Array of true values.
        y_pred: Array of predicted values.
        
    Returns:
        RMSE value.
    """
    return np.sqrt(np.mean((y_true - y_pred) ** 2))

def calculate_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate R-squared (Coefficient of Determination).
    
    Args:
        y_true: Array of true values.
        y_pred: Array of predicted values.
        
    Returns:
        R-squared value.
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        return 0.0 if ss_res == 0 else 1.0
        
    return 1 - (ss_res / ss_tot)

def evaluate_gnn_on_test_set(
    model_path: str,
    test_data_path: str,
    device: str = 'cpu'
) -> Tuple[float, float, np.ndarray, np.ndarray]:
    """
    Load the trained GNN model, run inference on the test set,
    and calculate RMSE and R-squared.
    
    Args:
        model_path: Path to the saved GNN model checkpoint.
        test_data_path: Path to the test graph data (JSON format).
        device: Device to run inference on (default: 'cpu').
        
    Returns:
        Tuple of (RMSE, R2, y_true, y_pred).
    """
    logger.info(f"Loading model from {model_path}")
    logger.info(f"Loading test data from {test_data_path}")
    
    # Load data
    test_data_list = load_graph_data(test_data_path)
    
    if not test_data_list:
        raise ValueError("No test data found at the specified path.")
    
    # Initialize model
    # Assuming a standard architecture based on typical GNN setups
    # We need to infer hidden_channels and num_layers from the checkpoint or use defaults
    # For now, we'll use common defaults and hope the checkpoint matches or we load state dict strictly
    # A robust way is to store hyperparams in the checkpoint, but we'll assume standard here
    hidden_channels = 128
    num_layers = 3
    
    model = GNNMPNN(
        input_dim=10,  # Standard atom feature dim used in preprocessing
        hidden_channels=hidden_channels,
        output_dim=1,
        num_layers=num_layers,
        dropout=0.1
    )
    
    # Load state dict
    checkpoint = torch.load(model_path, map_location=device, weights_only=True)
    if 'model_state_dict' in checkpoint:
        model.load_state_dict(checkpoint['model_state_dict'])
    else:
        model.load_state_dict(checkpoint)
        
    model.to(device)
    model.eval()
    
    y_true_list = []
    y_pred_list = []
    
    logger.info("Running inference on test set...")
    
    with torch.no_grad():
        for data in test_data_list:
            data = data.to(device)
            y = data.y
            pred = model(data)
            
            y_true_list.extend(y.cpu().numpy().flatten())
            y_pred_list.extend(pred.cpu().numpy().flatten())
    
    y_true = np.array(y_true_list)
    y_pred = np.array(y_pred_list)
    
    rmse = calculate_rmse(y_true, y_pred)
    r2 = calculate_r2(y_true, y_pred)
    
    logger.info(f"Test Set Evaluation Results:")
    logger.info(f"  RMSE: {rmse:.4f}")
    logger.info(f"  R-squared: {r2:.4f}")
    
    return rmse, r2, y_true, y_pred

def save_metrics_and_predictions(
    rmse: float,
    r2: float,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    output_path: str
) -> None:
    """
    Save metrics and predictions to a JSON file.
    
    Args:
        rmse: Calculated RMSE.
        r2: Calculated R-squared.
        y_true: Array of true values.
        y_pred: Array of predicted values.
        output_path: Path to save the JSON file.
    """
    metrics = {
        "rmse": float(rmse),
        "r_squared": float(r2),
        "num_samples": len(y_true),
        "predictions": {
            "true": y_true.tolist(),
            "predicted": y_pred.tolist()
        }
    }
    
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    logger.info(f"Metrics and predictions saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Evaluate GNN model on test set")
    parser.add_argument(
        "--model_path",
        type=str,
        default="models/gnn_model.pt",
        help="Path to the trained GNN model checkpoint"
    )
    parser.add_argument(
        "--test_data_path",
        type=str,
        default="data/processed/test_graphs.json",
        help="Path to the test graph data"
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="results/gnn_metrics.json",
        help="Path to save the metrics and predictions"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device to run evaluation on (cpu or cuda)"
    )
    
    args = parser.parse_args()
    
    try:
        rmse, r2, y_true, y_pred = evaluate_gnn_on_test_set(
            args.model_path,
            args.test_data_path,
            args.device
        )
        
        save_metrics_and_predictions(
            rmse,
            r2,
            y_true,
            y_pred,
            args.output_path
        )
        
        logger.info("Evaluation completed successfully.")
        
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
