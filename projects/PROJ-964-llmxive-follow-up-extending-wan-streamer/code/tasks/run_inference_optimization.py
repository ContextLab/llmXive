"""
Task Runner for T035: Performance optimization for CPU inference speed.

This script executes the optimization pipeline defined in `code/utils/inference_optimizer.py`.
It loads the final model, tunes batch sizes, compiles with TorchScript, and saves the stats.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.inference_optimizer import main as optimizer_main

def main():
    parser = argparse.ArgumentParser(description="Run Inference Optimization Task (T035)")
    parser.add_argument(
        "--model-path",
        type=str,
        default="data/models/estimator_checkpoint_final.pt",
        help="Path to the final model checkpoint."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/processed/sampled_dataset.parquet",
        help="Path to the sampled dataset for tuning."
    )
    parser.add_argument(
        "--output-stats",
        type=str,
        default="data/metrics/inference_optimization_stats.json",
        help="Path to save optimization statistics."
    )

    args = parser.parse_args()

    # Verify inputs exist
    if not os.path.exists(args.model_path):
        print(f"Error: Model not found at {args.model_path}")
        print("Ensure T024/T018a has completed and the final checkpoint exists.")
        sys.exit(1)

    if not os.path.exists(args.data_path):
        print(f"Error: Data not found at {args.data_path}")
        print("Ensure T014 has completed and the sampled dataset exists.")
        sys.exit(1)

    # Run the optimization
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.info(f"Starting T035: Optimizing inference for {args.model_path}")

    # We call the main function from the optimizer module directly
    # but we need to inject the arguments.
    # Since the `main` in inference_optimizer uses argparse, we can simulate sys.argv
    # or refactor. For simplicity in this task runner, we will re-implement the
    # logic here to ensure control, or call the class directly.

    from utils.inference_optimizer import InferenceOptimizer
    import torch
    from models.gru_estimator import GRUEstimator
    import json

    # Load Model
    logger.info(f"Loading model from {args.model_path}")
    checkpoint = torch.load(args.model_path, map_location="cpu", weights_only=False)
    model_state = checkpoint.get('model_state_dict', checkpoint)
    config = checkpoint.get('config', {})

    input_size = config.get('input_size', 10)
    hidden_size = config.get('hidden_size', 64)
    num_layers = config.get('num_layers', 2)

    model = GRUEstimator(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers)
    model.load_state_dict(model_state)
    model.eval()

    optimizer = InferenceOptimizer(model, device="cpu")

    # Run Optimization
    stats = optimizer.optimize_inference_pipeline(
        data_path=args.data_path,
        output_path=args.output_stats
    )

    logger.info("T035 Complete. Optimization stats saved.")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
