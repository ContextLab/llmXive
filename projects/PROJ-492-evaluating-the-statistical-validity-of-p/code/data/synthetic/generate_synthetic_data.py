"""
Wrapper script to generate synthetic data and ground truth.
"""
import json
import logging
import sys
from pathlib import Path
from code.src.audit.synthetic import main as generate_synthetic_main
from code.src.utils.logger import get_default_logger

logger = get_default_logger()

def main():
    """Orchestrate generation of synthetic data and ground truth."""
    logger.info("Starting synthetic data generation pipeline...")

    # Step 1: Generate synthetic summaries
    generate_synthetic_main()

    # Step 2: Generate ground truth based on the generated summaries
    # Import here to avoid circular dependency if this script is imported
    import importlib.util
    spec = importlib.util.spec_from_file_location("ground_truth", "data/synthetic/generate_ground_truth.py")
    gt_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gt_module)
    gt_module.main()

    logger.info("Synthetic data generation pipeline complete.")

if __name__ == "__main__":
    main()
