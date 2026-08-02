"""
Script to run the microcircuit training experiment (T011d).

This script wraps the MicrocircuitRunner to ensure the artifact
data/logs/gradient_norms_microcircuit.json is produced on disk.
"""
import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.experiments.microcircuit_runner import MicrocircuitRunner, MicrocircuitConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Run Microcircuit Training (T011d)")
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--lr", type=float, default=1e-3, help="Learning rate")
    args = parser.parse_args()

    logger.info(f"Starting Microcircuit Training with {args.epochs} epochs...")
    
    config = MicrocircuitConfig(
        hidden_dim=64,
        num_layers=4,
        neurons_per_layer=128,
        epochs=args.epochs,
        learning_rate=args.lr,
        seed=args.seed,
        gradient_log_path="data/logs/gradient_norms_microcircuit.json",
        metrics_path="data/results/microcircuit_metrics.json"
    )

    runner = MicrocircuitRunner(config)
    result = runner.run_with_logging()

    logger.info(f"Success. Output artifacts:")
    logger.info(f"  - {result.gradient_log_path}")
    logger.info(f"  - {result.metrics_path}")

if __name__ == "__main__":
    main()
