import os
import sys
import logging
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.inference_engine import run_batch_inference

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    """
    Execute T024: Save inference results to data/results/inference_pilot_{seed}.json.
    
    This script reads the pilot dataset generated in T016, performs parameter estimation
    using the inference engine, and saves the results including 90% credible intervals.
    """
    # Configuration
    seed = 42
    input_file = project_root / "data" / "processed" / f"waveforms_pilot_{seed}.h5"
    output_dir = project_root / "data" / "results"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T016 (dataset generation) has been completed first.")
        sys.exit(1)
    
    logger.info(f"Starting T024: Inference on {input_file}")
    
    try:
        output_path = run_batch_inference(
            h5_path=input_file,
            seed=seed,
            output_dir=output_dir
        )
        logger.info(f"T024 Completed successfully. Output: {output_path}")
    except Exception as e:
        logger.error(f"T024 Failed: {e}")
        raise

if __name__ == "__main__":
    run()