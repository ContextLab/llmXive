import os
import sys
import logging
from pathlib import Path

from code.config import get_path, ensure_dirs, set_seed, load_config
from code.synthetic_data import run_synthetic_pipeline as run_synthetic_pipeline_func
from code.output_metrics import run_output_pipeline

logger = logging.getLogger(__name__)

def main():
    """
    T018c Execution: Output structured CSV logic.
    """
    logger.info("Running T018c output pipeline.")
    
    # Ensure data exists
    synth_path = get_path("data/processed/synthetic_dataset.csv")
    if not os.path.exists(synth_path):
        logger.info("Synthetic data not found. Generating...")
        synth_path = run_synthetic_pipeline_func(output_path=synth_path)
    
    # Run output pipeline to generate morphological_metrics.csv
    output_path = run_output_pipeline()
    logger.info(f"T018c complete. Output at {output_path}")

if __name__ == "__main__":
    main()
