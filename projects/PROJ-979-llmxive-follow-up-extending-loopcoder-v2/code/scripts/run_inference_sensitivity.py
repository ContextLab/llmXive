import os
import sys
import logging
from pathlib import Path

# Ensure src is in path
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from src.inference import main as run_inference_main

def main():
    """
    Entry point for T013b: Sensitivity Convergence (k=4).
    Runs the inference pipeline specifically for k=4 on the full splits
    (including underpowered strata) to produce convergence_results_sensitivity.csv.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger("run_inference_sensitivity")

    # Define arguments matching the task specification
    # Input: full_splits.json (includes underpowered strata)
    # Output: convergence_results_sensitivity.csv
    # k_range: 4 only
    # Device: cuda (as per spec, though local runner might need cpu fallback if unavailable)
    # Seed: 42

    input_path = "data/processed/full_splits.json"
    output_path = "data/processed/convergence_results_sensitivity.csv"
    k_range = [4]
    device = "cuda"
    seed = 42

    logger.info(f"Starting Sensitivity Convergence Inference (k=4)")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"K-Range: {k_range}")
    logger.info(f"Device: {device}")
    logger.info(f"Seed: {seed}")

    # Construct args namespace expected by src.inference.main
    # We simulate the argparse Namespace object
    class Args:
        input = input_path
        output = output_path
        k_range = k_range
        device = device
        seed = seed
        sample_size = None  # Not specified for full run, defaults to all

    args = Args()

    try:
        run_inference_main(args)
        logger.info("Sensitivity Convergence Inference completed successfully.")
    except Exception as e:
        logger.error(f"Sensitivity Convergence Inference failed: {e}")
        raise

if __name__ == "__main__":
    main()
