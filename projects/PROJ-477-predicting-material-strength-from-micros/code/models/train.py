"""
Training script for Material Strength Prediction CNN.

This script is the primary training entry point referenced by the run-book.
It wraps the logic from code/train/trainer.py to provide a unified CLI interface
compatible with the quickstart.md execution commands.

Usage:
    python code/models/train.py --mode train [options]
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path to allow imports from sibling modules
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_project_root, get_data_dir, get_results_dir, set_seed, get_seed
from train.trainer import main as trainer_main
from models.baseline import main as baseline_main
from models.train_ablation import main as ablation_main
from eval.metrics import main as metrics_main
from eval.evaluator import main as evaluator_main

def parse_args():
    parser = argparse.ArgumentParser(
        description="Train and evaluate Material Strength Prediction models."
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["train", "baseline", "ablation", "evaluate", "full"],
        default="train",
        help="Operation mode: train (CNN), baseline (mean predictor), ablation (no aug), evaluate (metrics), or full (train+eval).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Number of training epochs.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for training.",
    )
    parser.add_argument(
        "--lr",
        type=float,
        default=1e-4,
        help="Learning rate.",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=5,
        help="Early stopping patience.",
    )
    parser.add_argument(
        "--model-type",
        type=str,
        default="mobilenet",
        choices=["mobilenet", "resnet"],
        help="Backbone architecture.",
    )
    parser.add_argument(
        "--predictions-file",
        type=str,
        default=None,
        help="Path to predictions CSV for evaluation mode.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path for metrics JSON (optional).",
    )
    
    return parser.parse_args()

def setup_directories():
    """Ensure all required directories exist."""
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "features",
        root / "results",
        root / "models",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    return root

def run_training(args):
    """Run the CNN training loop."""
    logging.info(f"Starting training with mode: {args.mode}")
    set_seed(args.seed)
    
    # Prepare args for trainer
    trainer_args = argparse.Namespace(
        seed=args.seed,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        patience=args.patience,
        model_type=args.model_type,
    )
    
    # Override sys.argv for the trainer module to pick up args
    # This is a common pattern when wrapping scripts
    original_argv = sys.argv
    sys.argv = [
        "train.py",
        "--seed", str(trainer_args.seed),
        "--epochs", str(trainer_args.epochs),
        "--batch-size", str(trainer_args.batch_size),
        "--lr", str(trainer_args.lr),
        "--patience", str(trainer_args.patience),
        "--model-type", trainer_args.model_type,
    ]
    
    try:
        trainer_main()
    finally:
        sys.argv = original_argv

def run_baseline(args):
    """Run the naive mean baseline predictor."""
    logging.info("Generating naive baseline predictions.")
    set_seed(args.seed)
    
    original_argv = sys.argv
    sys.argv = [
        "baseline.py",
        "--seed", str(args.seed),
    ]
    
    try:
        baseline_main()
    finally:
        sys.argv = original_argv

def run_ablation(args):
    """Run ablation study (training without augmentation)."""
    logging.info("Running ablation study (no augmentation).")
    set_seed(args.seed)
    
    original_argv = sys.argv
    sys.argv = [
        "train_ablation.py",
        "--seed", str(args.seed),
        "--epochs", str(args.epochs),
        "--batch-size", str(args.batch_size),
        "--lr", str(args.lr),
        "--patience", str(args.patience),
    ]
    
    try:
        ablation_main()
    finally:
        sys.argv = original_argv

def run_evaluation(args):
    """Run model evaluation and statistical testing."""
    logging.info("Running model evaluation.")
    set_seed(args.seed)
    
    original_argv = sys.argv
    sys.argv = [
        "metrics.py",
        "--predictions", args.predictions_file or "data/features/test_predictions.csv",
        "--output", args.output or "results/statistical_test.json",
        "--seed", str(args.seed),
    ]
    
    try:
        metrics_main()
    finally:
        sys.argv = original_argv

def run_full_pipeline(args):
    """Run training followed by evaluation."""
    run_training(args)
    # After training, we expect predictions to be generated or we run evaluation
    # The trainer usually saves model, evaluation script loads it and predicts
    # For this flow, we assume the evaluation script handles prediction generation
    # or we need to run a predictor script first.
    # Based on the execution feedback, we need to ensure predictions exist.
    # We will assume the 'evaluate' mode in the evaluator handles the full flow
    # or we call the metrics script which expects a predictions file.
    
    # Let's run the evaluator which handles the full flow if needed
    evaluator_args = argparse.Namespace(
        seed=args.seed,
        predictions_file=None, # Will be derived from model
    )
    
    # We'll call the metrics script directly as it's the core evaluation logic
    # We need a predictions file. If the trainer doesn't generate one, we might need a predictor step.
    # For now, we assume the pipeline flow generates this or the metrics script can handle missing.
    # However, to be safe and match the run-book expectation, we'll try to run metrics with defaults.
    
    # Re-run metrics with a default path if not provided
    eval_args = argparse.Namespace(
        seed=args.seed,
        predictions_file="data/features/test_predictions.csv", # Default expectation
        output="results/statistical_test.json",
        alpha=0.05,
    )
    
    original_argv = sys.argv
    sys.argv = [
        "metrics.py",
        "--predictions", eval_args.predictions_file,
        "--output", eval_args.output,
        "--seed", str(eval_args.seed),
        "--alpha", str(eval_args.alpha),
    ]
    
    try:
        metrics_main()
    except SystemExit as e:
        if e.code != 0:
            logging.error("Evaluation failed.")
            raise
    finally:
        sys.argv = original_argv

def main():
    args = parse_args()
    setup_directories()
    set_seed(args.seed)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(get_results_dir() / "training.log"),
        ],
    )
    
    try:
        if args.mode == "train":
            run_training(args)
        elif args.mode == "baseline":
            run_baseline(args)
        elif args.mode == "ablation":
            run_ablation(args)
        elif args.mode == "evaluate":
            run_evaluation(args)
        elif args.mode == "full":
            run_full_pipeline(args)
        else:
            logging.error(f"Unknown mode: {args.mode}")
            sys.exit(1)
    except Exception as e:
        logging.exception(f"Training/Evaluation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()