"""
T037: Wrapper script to invoke train, eval_high_res, and analysis in correct order.
Ensures the run-book matches the implementation.

Execution Order:
1. code/train.py (generates codebook_v0.pth)
2. code/eval_high_res.py (generates embeddings_high_res.h5 and ground_truth_images)
3. code/analysis.py (generates fidelity_metrics.json, correlation_plot.png, etc.)
"""
import subprocess
import sys
import argparse
import os
import logging
from pathlib import Path

# Configure logging for the pipeline
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(cmd: list, description: str) -> None:
    """Run a command and check for success."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        if result.returncode != 0:
            raise RuntimeError(f"Command failed with exit code {result.returncode}: {description}")
        logger.info(f"Completed: {description}\n")
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {description}")
        raise RuntimeError(f"Pipeline step failed: {description}") from e

def ensure_directories():
    """Ensure required output directories exist."""
    dirs = [
        'data/results',
        'data/processed/ground_truth_images',
        'data/raw',
        'data/processed'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory: {d}")

def main():
    parser = argparse.ArgumentParser(
        description="Run the full evaluation pipeline: Train -> High-Res Eval -> Analysis"
    )
    parser.add_argument(
        '--checkpoint',
        type=str,
        default='data/results/codebook_v0.pth',
        help='Path to the VQ-VAE checkpoint (default: data/results/codebook_v0.pth)'
    )
    parser.add_argument(
        '--skip-train',
        action='store_true',
        help='Skip training if the checkpoint already exists'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='code/config.py',
        help='Path to the configuration file'
    )
    args = parser.parse_args()

    # 0. Setup
    ensure_directories()
    checkpoint_path = Path(args.checkpoint)

    # 1. Train (Codebook Initialization)
    # Only run if checkpoint is missing or --skip-train is False
    if not args.skip_train or not checkpoint_path.exists():
        if not checkpoint_path.exists():
            logger.info(f"Checkpoint {checkpoint_path} not found. Starting training.")
        else:
            logger.warning(f"Checkpoint {checkpoint_path} exists but --skip-train not set. Re-running training.")
        
        train_cmd = [
            sys.executable, 'code/train.py',
            '--config', args.config
        ]
        run_command(train_cmd, "Training (Codebook Initialization)")
    else:
        logger.info(f"Skipping training. Using existing checkpoint: {checkpoint_path}")

    # 2. High-Resolution Evaluation
    # This step depends on the checkpoint from step 1
    if not checkpoint_path.exists():
        raise RuntimeError(
            f"Checkpoint {checkpoint_path} does not exist after training step. "
            "Cannot proceed to high-resolution evaluation."
        )

    eval_high_res_cmd = [
        sys.executable, 'code/eval_high_res.py',
        '--checkpoint', str(checkpoint_path)
    ]
    run_command(eval_high_res_cmd, "High-Resolution Evaluation")

    # 3. Correlation Analysis & Fidelity Metrics
    # This step depends on outputs from step 2 (embeddings_high_res.h5, ground truth images)
    analysis_cmd = [
        sys.executable, 'code/analysis.py'
    ]
    run_command(analysis_cmd, "Correlation Analysis & Fidelity Metrics")

    logger.info("=" * 50)
    logger.info("Pipeline completed successfully.")
    logger.info(f"Artifacts should be available in:")
    logger.info(f"  - {checkpoint_path}")
    logger.info(f"  - data/results/embeddings_high_res.h5")
    logger.info(f"  - data/results/fidelity_metrics.json")
    logger.info(f"  - data/results/correlation_plot.png")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()