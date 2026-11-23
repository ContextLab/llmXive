"""
Aggregate per-fold predictions from RF and GNN models into a single dataset.

This script loads:
  - RF per-fold predictions: data/processed/rf_fold_predictions.json
  - GNN per-fold predictions: data/processed/gnn_fold_predictions.json

It concatenates them, calculates absolute errors, and saves:
  - data/processed/aggregated_predictions.json
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from evaluation.report_generator import setup_report_logger

def load_json_file(filepath: Path) -> List[Dict[str, Any]]:
    """Load a JSON file containing a list of fold predictions."""
    if not filepath.exists():
        raise FileNotFoundError(f"Required file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list of fold predictions in {filepath}, got {type(data)}")
    
    return data

def aggregate_fold_predictions(
    fold_predictions: List[Dict[str, Any]], 
    model_name: str
) -> Tuple[List[float], List[float], List[float]]:
    """
    Aggregate per-fold predictions into single vectors.
    
    Args:
        fold_predictions: List of dictionaries, each representing a fold's results.
        model_name: Name of the model (for logging).
    
    Returns:
        Tuple of (predictions, true_values, absolute_errors) lists.
    """
    all_predictions = []
    all_true_values = []
    
    for fold_idx, fold_data in enumerate(fold_predictions):
        if 'predictions' not in fold_data:
            raise KeyError(f"Fold {fold_idx} in {model_name} missing 'predictions' key")
        if 'true_values' not in fold_data:
            raise KeyError(f"Fold {fold_idx} in {model_name} missing 'true_values' key")
        
        preds = fold_data['predictions']
        true_vals = fold_data['true_values']
        
        if len(preds) != len(true_vals):
            raise ValueError(
                f"Length mismatch in {model_name} Fold {fold_idx}: "
                f"predictions={len(preds)}, true_values={len(true_vals)}"
            )
        
        all_predictions.extend(preds)
        all_true_values.extend(true_vals)
    
    # Calculate absolute errors
    absolute_errors = [abs(p - t) for p, t in zip(all_predictions, all_true_values)]
    
    return all_predictions, all_true_values, absolute_errors

def save_aggregated_predictions(
    predictions_rf: List[float],
    true_values_rf: List[float],
    errors_rf: List[float],
    predictions_gnn: List[float],
    true_values_gnn: List[float],
    errors_gnn: List[float],
    output_path: Path
):
    """Save aggregated predictions to JSON."""
    data = {
        "rf_model": {
            "predictions": predictions_rf,
            "true_values": true_values_rf,
            "absolute_errors": errors_rf
        },
        "gnn_model": {
            "predictions": predictions_gnn,
            "true_values": true_values_gnn,
            "absolute_errors": errors_gnn
        }
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logging.info(f"Saved aggregated predictions to {output_path}")
    logging.info(f"  RF samples: {len(predictions_rf)}")
    logging.info(f"  GNN samples: {len(predictions_gnn)}")

def main():
    """Main entry point for aggregation."""
    parser = argparse.ArgumentParser(description="Aggregate model predictions")
    parser.add_argument(
        "--rf-input", 
        type=str, 
        default="data/processed/rf_fold_predictions.json",
        help="Path to RF fold predictions JSON"
    )
    parser.add_argument(
        "--gnn-input", 
        type=str, 
        default="data/processed/gnn_fold_predictions.json",
        help="Path to GNN fold predictions JSON"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/aggregated_predictions.json",
        help="Path to output aggregated predictions JSON"
    )
    args = parser.parse_args()

    # Setup logging
    logger = setup_report_logger("aggregate_predictions")
    
    # Resolve paths relative to project root
    rf_path = project_root / args.rf_input
    gnn_path = project_root / args.gnn_input
    output_path = project_root / args.output

    logger.info(f"Loading RF predictions from {rf_path}")
    logger.info(f"Loading GNN predictions from {gnn_path}")

    # Load data
    try:
        rf_data = load_json_file(rf_path)
        gnn_data = load_json_file(gnn_path)
    except (FileNotFoundError, ValueError, KeyError) as e:
        logger.error(f"Failed to load prediction files: {e}")
        sys.exit(1)

    # Aggregate
    logger.info("Aggregating RF predictions...")
    try:
        preds_rf, true_rf, errors_rf = aggregate_fold_predictions(rf_data, "RF")
    except (KeyError, ValueError) as e:
        logger.error(f"Failed to aggregate RF predictions: {e}")
        sys.exit(1)

    logger.info("Aggregating GNN predictions...")
    try:
        preds_gnn, true_gnn, errors_gnn = aggregate_fold_predictions(gnn_data, "GNN")
    except (KeyError, ValueError) as e:
        logger.error(f"Failed to aggregate GNN predictions: {e}")
        sys.exit(1)

    # Verify lengths match (should be same dataset split)
    if len(preds_rf) != len(preds_gnn):
        logger.warning(
            f"Sample count mismatch: RF={len(preds_rf)}, GNN={len(preds_gnn)}. "
            "This may indicate different split configurations."
        )
    
    # Save results
    save_aggregated_predictions(
        preds_rf, true_rf, errors_rf,
        preds_gnn, true_gnn, errors_gnn,
        output_path
    )

    logger.info("Aggregation complete.")

if __name__ == "__main__":
    main()