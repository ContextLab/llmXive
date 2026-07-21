"""
T030b: Write results from permutation test to results/results.json.

This script reads the metrics calculated by T030a (via code/evaluate.py)
and serializes them to the final results artifact.

It expects the evaluation script to have populated a temporary state
or for the metrics to be passed via arguments. To ensure robustness
and independence, this script re-runs the evaluation logic from
code/evaluate.py if the results file does not exist, or loads
pre-computed metrics if they were passed as arguments.

However, per the strict dependency chain (T030a -> T030b), the
standard pattern is that T030a (evaluate.py) performs the calculation
and T030b (this script) ensures the final serialization happens
correctly to the canonical path.

In this implementation, we assume the evaluation script (T030a)
has already computed the values. If `evaluate.py` is designed to
print them but not save, we call it here to ensure the save happens.
If `evaluate.py` already saves, this script acts as a verification
and finalization step.

To strictly follow the "Write results" task without re-computing,
we will implement a mechanism to accept the metrics from the
previous step's output (e.g., via a temporary file or arguments)
or re-run the evaluation logic if needed.

Given the API surface of `code/evaluate.py` includes `save_results`,
the most robust approach for T030b is to ensure `save_results` is
called with the correct data. Since T030a is the one that calculates
the values, T030b's primary job is to persist them.

We will implement this by re-invoking the evaluation logic from
`evaluate.py` to generate the metrics and save them, ensuring
the data flow is consistent.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path to allow imports if run directly
# (though typically run as python code/write_results.py)
script_dir = Path(__file__).parent
project_root = script_dir.parent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("write_results")

def parse_args():
    parser = argparse.ArgumentParser(description="Write final evaluation results to results/results.json")
    parser.add_argument(
        "--features-path",
        type=str,
        default=str(project_root / "data" / "processed" / "features.json"),
        help="Path to the features JSON file"
    )
    parser.add_argument(
        "--model-path",
        type=str,
        default=str(project_root / "results" / "model.pkl"),
        help="Path to the trained model pickle file"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=str(project_root / "results" / "results.json"),
        help="Path to the output results JSON file"
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=1000,
        help="Number of permutations for the test"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for permutation test"
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    return parser.parse_args()

def save_results(results: dict, output_path: str):
    """
    Serialize the results dictionary to a JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, sort_keys=True)

    logger.info(f"Results successfully written to {output_path}")
    return output_path

def main():
    args = parse_args()

    logger.info(f"Starting result serialization for T030b.")
    logger.info(f"Features: {args.features_path}")
    logger.info(f"Model: {args.model_path}")
    logger.info(f"Output: {args.output_path}")

    # Import the evaluation module to reuse logic
    # We need to ensure we are in the correct path context
    sys.path.insert(0, str(script_dir))
    from evaluate import load_features, load_model, calculate_metrics, calculate_baseline_mae, perform_permutation_test, evaluate_model

    # Load features
    if not os.path.exists(args.features_path):
        logger.error(f"Features file not found: {args.features_path}")
        logger.error("Please ensure T025 (compute_all_features) has run successfully.")
        sys.exit(1)

    features = load_features(args.features_path)
    logger.info(f"Loaded {len(features)} samples from features.")

    # Load model
    if not os.path.exists(args.model_path):
        logger.error(f"Model file not found: {args.model_path}")
        logger.error("Please ensure T027b/T027c (train_and_save) has run successfully.")
        sys.exit(1)

    model = load_model(args.model_path)
    logger.info("Model loaded successfully.")

    # Perform the full evaluation including permutation test
    # This re-computes the metrics to ensure they are fresh and consistent
    # with the current state of features and model.
    # The evaluate_model function in evaluate.py is designed to do exactly this.
    
    # Note: We pass the arguments to override defaults if necessary
    results = evaluate_model(
        features=features,
        model=model,
        n_permutations=args.n_permutations,
        alpha=args.alpha,
        random_state=args.random_state
    )

    # Save results
    save_results(results, args.output_path)

    # Print summary
    logger.info("=== Final Results Summary ===")
    for key, value in results.items():
        logger.info(f"{key}: {value}")

    logger.info("T030b completed successfully.")

if __name__ == "__main__":
    main()