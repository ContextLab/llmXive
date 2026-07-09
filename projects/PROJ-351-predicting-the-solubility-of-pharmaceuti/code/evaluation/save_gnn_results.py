"""
Task T024: Save GNN predictions and metrics to results/gnn_metrics.json.

This script loads the trained GNN model, evaluates it on the test set,
and saves the detailed metrics and predictions to `results/gnn_metrics.json`.
It relies on the existing `code/evaluation/metrics.py` module for evaluation logic.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.metrics import evaluate_gnn_on_test_set, save_metrics_and_predictions
from setup_logging import setup_logger

def parse_args():
    parser = argparse.ArgumentParser(description="Save GNN predictions and metrics.")
    parser.add_argument(
        "--model_path",
        type=str,
        default=str(PROJECT_ROOT / "models" / "gnn_mpnn.pth"),
        help="Path to the trained GNN model file."
    )
    parser.add_argument(
        "--data_path",
        type=str,
        default=str(PROJECT_ROOT / "data" / "processed"),
        help="Path to the processed data directory containing split indices."
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default=str(PROJECT_ROOT / "results" / "gnn_metrics.json"),
        help="Path to save the output JSON file."
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device to use for evaluation (cpu or cuda)."
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Setup logging
    logger = setup_logger("gnn_results_saver", log_file=str(PROJECT_ROOT / "data" / "logs" / "gnn_results.log"))
    logger.info(f"Starting GNN results save task (T024).")
    logger.info(f"Model path: {args.model_path}")
    logger.info(f"Data path: {args.data_path}")
    logger.info(f"Output path: {args.output_path}")

    # Ensure output directory exists
    output_dir = Path(args.output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Evaluate the model
        # This function internally loads data, model, runs inference, and calculates metrics
        metrics_dict = evaluate_gnn_on_test_set(
            model_path=args.model_path,
            data_dir=args.data_path,
            device=args.device,
            logger=logger
        )

        if metrics_dict is None:
            logger.error("Evaluation failed to produce metrics. Check logs for details.")
            sys.exit(1)

        # Save the metrics and predictions to the specified JSON file
        save_metrics_and_predictions(
            metrics=metrics_dict,
            output_path=args.output_path,
            logger=logger
        )

        logger.info(f"Successfully saved GNN metrics and predictions to {args.output_path}")
        print(f"Task T024 Complete: Results saved to {args.output_path}")

    except Exception as e:
        logger.error(f"Error during GNN results saving: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()