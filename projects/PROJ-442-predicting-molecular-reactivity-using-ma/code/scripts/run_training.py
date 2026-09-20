"""
Script to run the training pipeline for T027.
This script ensures that the training artifacts are generated.
"""
import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.modeling.train import main as train_main


def main():
    parser = argparse.ArgumentParser(description="Run training pipeline")
    parser.add_argument(
        "--config",
        type=str,
        default="code/src/modeling/config.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--features",
        type=str,
        default="data/processed/feature_matrix.parquet",
        help="Path to feature matrix",
    )
    parser.add_argument(
        "--model-output",
        type=str,
        default="data/models/xgboost_model.json",
        help="Path to save model",
    )
    parser.add_argument(
        "--log-output",
        type=str,
        default="data/processed/training_log.json",
        help="Path to save training log",
    )
    parser.add_argument(
        "--cv-results",
        type=str,
        default="data/results/cv_results.csv",
        help="Path to save CV results",
    )

    args = parser.parse_args()

    # Set up arguments for train.py main
    sys.argv = [
        "run_training.py",
        "--config", args.config,
        "--features", args.features,
        "--model-output", args.model_output,
        "--log-output", args.log_output,
        "--cv-results", args.cv_results,
    ]

    train_main()


if __name__ == "__main__":
    main()