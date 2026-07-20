"""
Runner script for Task T018: Output Morphological Metrics.

This script orchestrates the generation of the final morphological metrics CSV.
It handles both the real data path (expecting upstream T013-T017 output) and
the synthetic data path for validation purposes.

Usage:
    python code/run_t018_output.py [--mode synthetic|real]
"""
import os
import sys
import logging
from pathlib import Path

from code.config import get_path, ensure_dirs, set_seed, load_config
from code.synthetic_data import run_synthetic_pipeline
from code.output_metrics import run_output_pipeline
from code.logging_utils import get_logger

logger = get_logger(__name__)


def main(mode: str = "real"):
    """
    Main entry point for T018.
    
    Args:
        mode: Either 'real' (default) or 'synthetic'.
              'synthetic' generates synthetic data first, then runs the output pipeline.
              'real' assumes upstream data (T013-T017) has already been generated.
    """
    logging.basicConfig(level=logging.INFO)
    set_seed(42)
    
    logger.info(f"Starting T018 in '{mode}' mode.")
    
    if mode == "synthetic":
        logger.info("Generating synthetic data for validation (T012b)...")
        try:
            synthetic_path = run_synthetic_pipeline()
            logger.info(f"Synthetic data generated at {synthetic_path}")
            # Note: The synthetic data generator writes to data_processed/synthetic_dataset.csv.
            # The output_metrics.py expects data in data_intermediates/processed_morphology.csv.
            # For validation, we assume the synthetic data IS the processed data for this step,
            # or we copy it to the expected location.
            # However, the spec says T007 is for logic validation ONLY.
            # To make T018 run end-to-end for validation, we will treat the synthetic output
            # as the input to T018.
            # We need to ensure the intermediate file exists.
            import shutil
            intermediate_path = get_path("data_intermediates", "processed_morphology.csv")
            ensure_dirs(os.path.dirname(intermediate_path))
            shutil.copy(synthetic_path, intermediate_path)
            logger.info(f"Copied synthetic data to intermediate path: {intermediate_path}")
        except Exception as e:
            logger.error(f"Failed to generate synthetic data: {e}")
            raise
    
    elif mode == "real":
        logger.info("Running T018 on real data (assuming T013-T017 completed).")
        # No synthetic generation. The output_metrics.py will fail loudly if
        # the intermediate file is missing.
    
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'real' or 'synthetic'.")
    
    # Run the T018 output pipeline
    try:
        output_path = run_output_pipeline()
        logger.info(f"T018 completed successfully. Output: {output_path}")
        return output_path
    except FileNotFoundError as e:
        logger.error(f"T018 failed: {e}")
        logger.error("Ensure T013-T017 (morphometry pipeline) has run and produced "
                     "data/intermediates/processed_morphology.csv")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in T018: {e}")
        raise


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run T018: Output Morphological Metrics")
    parser.add_argument("--mode", choices=["real", "synthetic"], default="real",
                        help="Mode: 'real' for production, 'synthetic' for validation")
    args = parser.parse_args()
    
    main(mode=args.mode)
