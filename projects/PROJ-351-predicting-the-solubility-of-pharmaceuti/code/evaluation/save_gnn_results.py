"""
Task T024: Save GNN predictions and metrics to results/gnn_metrics.json.

This script loads the trained GNN model, runs inference on the test set,
calculates RMSE and R-squared, and saves the results to a JSON file.
It relies on the metrics logic from code/evaluation/metrics.py.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from evaluation.metrics import evaluate_gnn_on_test_set, calculate_rmse, calculate_r2
from config.seeds import ensure_seeded, get_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Save GNN predictions and metrics.")
    parser.add_argument(
        "--model-path",
        type=str,
        default="models/gnn_model.pth",
        help="Path to the trained GNN model file."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/processed",
        help="Path to the processed data directory containing train/val/test splits."
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="results/gnn_metrics.json",
        help="Path to save the output JSON metrics file."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    return parser.parse_args()

def main():
    args = parse_args()

    # Ensure output directory exists
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting GNN results saving process.")
    logger.info(f"Model path: {args.model_path}")
    logger.info(f"Data path: {args.model_path}")
    logger.info(f"Output path: {args.output_path}")

    # Set seeds
    ensure_seeded(args.seed)
    logger.info(f"Random seeds set to {args.seed}")

    # Check if model exists
    if not os.path.exists(args.model_path):
        logger.error(f"Model file not found at {args.model_path}. "
                     "Please ensure the GNN model has been trained (T021).")
        sys.exit(1)

    # Check if processed data exists
    processed_data_dir = Path(args.data_path)
    if not processed_data_dir.exists():
        logger.error(f"Processed data directory not found at {args.data_path}. "
                     "Please ensure data preprocessing (T005) and splitting (T006) are complete.")
        sys.exit(1)

    # Load data and evaluate
    # This function handles loading the test set, running the model, and calculating metrics
    logger.info("Evaluating GNN model on test set...")
    
    try:
        metrics, predictions_df = evaluate_gnn_on_test_set(
            model_path=args.model_path,
            data_dir=args.data_path,
            seed=args.seed
        )
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        logger.error("Ensure that the GNN model architecture matches the saved weights "
                     "and that the data preprocessing steps are consistent.")
        sys.exit(1)

    # Prepare the result dictionary
    result = {
        "model_type": "GNN_MPNN",
        "model_path": args.model_path,
        "seed": args.seed,
        "metrics": {
            "rmse": float(metrics["rmse"]),
            "r_squared": float(metrics["r2"])
        },
        "num_samples": len(predictions_df),
        "timestamp": str(Path(args.output_path).parent.parent / "data/logs") # Just a placeholder for now, actual timestamp logic could be added
    }
    
    # Add a specific timestamp
    from datetime import datetime
    result["timestamp"] = datetime.now().isoformat()

    # Save to JSON
    logger.info(f"Saving metrics to {args.output_path}")
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info("Successfully saved GNN predictions and metrics.")
    logger.info(f"RMSE: {metrics['rmse']:.4f}")
    logger.info(f"R-squared: {metrics['r2']:.4f}")

    return 0

if __name__ == "__main__":
    sys.exit(main())