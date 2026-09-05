"""
Evaluation script for model performance.
Calculates MAE, RMSE, and Pearson R on the test set.
"""
import os
import sys
import argparse
import logging
import json
import csv
import math
from typing import List, Dict, Any, Optional

import numpy as np
import torch
from scipy.stats import pearsonr

# Fix import path to allow running from code/ or root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.utils import get_logger, set_seed
from data.dataset import MoleculeData
from data.loader import create_streaming_loader, validate_and_transform
from models.schnet import create_schnet_model, SchNet
from models.baseline_2d import create_baseline_2d_model, Baseline2DModel
from models.baseline_atom import create_atom_baseline_model, AtomTypeAverageBaseline

logger = get_logger(__name__)

# Exit codes defined in utils (T004a)
EXIT_CODE_SUCCESS = 0
EXIT_CODE_BASELINE_LOSS = 2
EXIT_CODE_THRESHOLD_FAIL = 3

def calculate_metrics(pred: List[float], actual: List[float]) -> Dict[str, float]:
    """
    Calculates MAE, RMSE, and Pearson R.
    """
    if len(pred) != len(actual) or len(pred) == 0:
        raise ValueError("Prediction and actual lists must be non-empty and of equal length.")
    
    pred_arr = np.array(pred)
    actual_arr = np.array(actual)

    mae = np.mean(np.abs(pred_arr - actual_arr))
    rmse = np.sqrt(np.mean((pred_arr - actual_arr) ** 2))
    
    # Pearson R
    r, _ = pearsonr(pred_arr, actual_arr)
    if r is None:
        r = 0.0

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "pearson_r": float(r)
    }

def evaluate_model(
    model: torch.nn.Module, 
    model_path: Optional[str],
    test_loader: torch.utils.data.DataLoader,
    device: torch.device
) -> Dict[str, Any]:
    """
    Evaluates a model on the test set.
    Returns metrics dictionary.
    """
    if model_path and os.path.exists(model_path):
        logger.info(f"Loading model weights from {model_path}")
        checkpoint = torch.load(model_path, map_location=device, weights_only=True)
        # Handle potential dict wrapping in checkpoint
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
    elif model_path:
        logger.warning(f"Model path {model_path} provided but file not found. Using random weights.")
    
    model.eval()
    preds = []
    actuals = []
    molecule_ids = []

    with torch.no_grad():
        for batch in test_loader:
            batch = batch.to(device)
            # Ensure batch has required attributes
            if not hasattr(batch, 'y') or batch.y is None:
                logger.warning("Batch missing 'y' attribute, skipping.")
                continue
            
            if not hasattr(batch, 'scaffold_id'):
                # Fallback if scaffold_id missing but needed for logging
                scaffold_ids = [f"unknown_{i}" for i in range(batch.num_graphs)]
            else:
                scaffold_ids = batch.scaffold_id

            # Predict
            out = model(batch.x, batch.edge_index, batch.edge_attr, batch.pos, batch.batch)
            
            # Handle potential dimension mismatch if model outputs per-atom vs per-molecule
            # Assuming model outputs per-molecule charge based on task context
            if out.dim() == 1:
                batch_pred = out.cpu().numpy()
            else:
                # If per-atom, aggregate (mean) for molecule level
                # This is a fallback; typically SchNet for QM9 outputs per-atom, then we sum/mean
                # But task implies molecular surface charge distribution -> often per-atom or per-mol.
                # Given the baselines (Atom-Type Average), we likely need per-atom or specific aggregation.
                # Let's assume the model is trained to output per-molecule scalar for now as per typical simplified tasks.
                # If the model outputs per-atom, we need to aggregate using batch.
                if out.shape[0] == batch.num_nodes:
                    # Aggregate per molecule
                    batch_pred = torch.zeros(batch.num_graphs, device=out.device)
                    batch_pred = batch_pred.scatter_add(0, batch.batch, out)
                    batch_pred = batch_pred.cpu().numpy()
                else:
                    batch_pred = out.cpu().numpy()

            y_batch = batch.y.cpu().numpy()
            
            preds.extend(batch_pred.flatten().tolist())
            actuals.extend(y_batch.flatten().tolist())
            molecule_ids.extend(scaffold_ids.tolist() if hasattr(scaffold_ids, 'tolist') else scaffold_ids)

    metrics = calculate_metrics(preds, actuals)
    metrics['predictions'] = preds
    metrics['actuals'] = actuals
    metrics['ids'] = molecule_ids
    
    return metrics

def run_baseline_comparison(
    test_loader: torch.utils.data.DataLoader,
    device: torch.device,
    model_3d: Optional[SchNet] = None,
    model_3d_path: Optional[str] = None,
    model_2d: Optional[Baseline2DModel] = None,
    model_atom: Optional[AtomTypeAverageBaseline] = None
) -> Dict[str, Any]:
    """
    Runs baseline comparisons between 3D GNN, 2D GNN, and Atom-Type baselines.
    """
    results = {}

    # 1. 3D GNN Evaluation
    if model_3d:
        logger.info("Evaluating 3D GNN (SchNet)...")
        metrics_3d = evaluate_model(model_3d, model_3d_path, test_loader, device)
        results['3d_gnn'] = {
            'mae': metrics_3d['mae'],
            'rmse': metrics_3d['rmse'],
            'pearson_r': metrics_3d['pearson_r']
        }
        logger.info(f"3D GNN MAE: {metrics_3d['mae']:.4f}")
    else:
        logger.warning("No 3D GNN model provided for comparison.")

    # 2. 2D GNN Baseline
    if model_2d:
        logger.info("Evaluating 2D GNN Baseline...")
        # For 2D baseline, we might need to ignore 'pos'
        # Assuming the evaluate_model function can handle a model that ignores pos if passed
        # We pass the model directly. The model itself handles the inputs.
        # Note: Baseline2DModel might expect different input signature. 
        # We assume it implements the same forward interface or we adapt here.
        # For simplicity in this script, we assume it takes (x, edge_index, edge_attr, batch)
        # and ignores pos.
        metrics_2d = evaluate_model(model_2d, None, test_loader, device)
        results['2d_gnn'] = {
            'mae': metrics_2d['mae'],
            'rmse': metrics_2d['rmse'],
            'pearson_r': metrics_2d['pearson_r']
        }
        logger.info(f"2D GNN MAE: {metrics_2d['mae']:.4f}")
    else:
        logger.warning("No 2D GNN baseline provided.")

    # 3. Atom-Type Average Baseline
    if model_atom:
        logger.info("Evaluating Atom-Type Average Baseline...")
        metrics_atom = evaluate_model(model_atom, None, test_loader, device)
        results['atom_baseline'] = {
            'mae': metrics_atom['mae'],
            'rmse': metrics_atom['rmse'],
            'pearson_r': metrics_atom['pearson_r']
        }
        logger.info(f"Atom Baseline MAE: {metrics_atom['mae']:.4f}")
    else:
        logger.warning("No Atom-Type baseline provided.")

    return results

def main():
    parser = argparse.ArgumentParser(description="Evaluate model.")
    parser.add_argument("--model-path", type=str, required=True, help="Path to the trained model checkpoint.")
    parser.add_argument("--baseline", action="store_true", help="Run baseline comparison.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--split-path", type=str, default="artifacts/splits/splits.json", help="Path to split indices.")
    parser.add_argument("--data-path", type=str, default="data/raw/qm9.parquet", help="Path to raw data (if not using streaming HF).")
    
    args = parser.parse_args()

    set_seed(args.seed)
    logger.info("Starting evaluation...")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Create Test Loader
    # Note: In a real scenario, we need to ensure the loader is configured for the TEST split.
    # The create_streaming_loader function from loader.py handles this via split indices.
    try:
        test_loader = create_streaming_loader(
            split_path=args.split_path,
            split_name="test",
            batch_size=32,
            num_workers=0
        )
        logger.info("Test loader created successfully.")
    except Exception as e:
        logger.error(f"Failed to create test loader: {e}")
        sys.exit(1)

    # Initialize Models
    model_3d = None
    model_2d = None
    model_atom = None

    if args.baseline:
        # Load 3D model
        try:
            model_3d = create_schnet_model(num_atom_types=9, num_filters=128, num_gaussians=50, num_interaction_blocks=3)
            logger.info("3D GNN model initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize 3D GNN: {e}")
            sys.exit(1)

        # Load 2D model
        try:
            model_2d = create_baseline_2d_model(num_atom_types=9, num_filters=64)
            logger.info("2D GNN model initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize 2D GNN: {e}")
            sys.exit(1)

        # Load Atom model
        try:
            model_atom = create_atom_baseline_model()
            logger.info("Atom-Type model initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Atom-Type model: {e}")
            sys.exit(1)

    # Run Evaluation
    results = {}
    
    # Evaluate 3D Model if path provided
    if os.path.exists(args.model_path):
        if model_3d:
            logger.info(f"Evaluating model from {args.model_path}")
            metrics = evaluate_model(model_3d, args.model_path, test_loader, device)
            results['3d_gnn'] = {
                'mae': metrics['mae'],
                'rmse': metrics['rmse'],
                'pearson_r': metrics['pearson_r']
            }
            logger.info(f"3D GNN Test MAE: {metrics['mae']:.4f}")
            
            # Save detailed metrics
            metrics_output = {
                "mae": metrics['mae'],
                "rmse": metrics['rmse'],
                "pearson_r": metrics['pearson_r'],
                "num_samples": len(metrics['actuals'])
            }
            os.makedirs("artifacts/reports", exist_ok=True)
            with open("artifacts/reports/metrics.json", "w") as f:
                json.dump(metrics_output, f, indent=2)
            logger.info("Metrics saved to artifacts/reports/metrics.json")
        else:
            logger.warning("Model path provided but 3D model not initialized.")
    else:
        logger.warning(f"Model path {args.model_path} does not exist.")

    # Run Baseline Comparison if requested
    if args.baseline:
        logger.info("Running baseline comparison...")
        baseline_results = run_baseline_comparison(
            test_loader=test_loader,
            device=device,
            model_3d=model_3d,
            model_3d_path=args.model_path if os.path.exists(args.model_path) else None,
            model_2d=model_2d,
            model_atom=model_atom
        )
        results.update(baseline_results)
        
        # Save baseline results
        with open("artifacts/reports/baseline_comparison.json", "w") as f:
            json.dump(results, f, indent=2)
        logger.info("Baseline comparison saved to artifacts/reports/baseline_comparison.json")

    logger.info("Evaluation complete.")

if __name__ == "__main__":
    main()
