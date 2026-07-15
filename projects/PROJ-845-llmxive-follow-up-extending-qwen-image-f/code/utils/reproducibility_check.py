"""
Reproducibility verification script for llmXive.

This script ensures that the synthetic data generation is deterministic
given a fixed seed from the Config. It runs the generator twice,
computes SHA256 checksums of the resulting CSV files, and exits with
a failure code if they differ.
"""
import hashlib
import os
import sys
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports based on API surface
from config import get_config, Config
from utils.logger import get_logger
from generators.logic_generator import generate_dataset_batch
from generators.dataset_saver import save_problems_to_csv, ensure_data_dir
from models.synthetic_problem import SyntheticProblem

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_reproducibility_check(seed: int, output_dir: Path) -> bool:
    """
    Run the generator twice with the same seed and verify checksums match.

    Args:
        seed: The random seed to use.
        output_dir: Directory to write temporary outputs.

    Returns:
        True if checksums match, False otherwise.
    """
    logger.info(f"Starting reproducibility check with seed {seed}")
    
    # Define output file paths for this run
    csv_filename = "reproducibility_test.csv"
    run1_path = output_dir / "run1" / csv_filename
    run2_path = output_dir / "run2" / csv_filename
    
    run1_path.parent.mkdir(parents=True, exist_ok=True)
    run2_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Run 1
        logger.info("Running generation pass 1...")
        config = Config(seed=seed, max_ram_gb=7.0, max_runtime_hours=6.0)
        problems_run1 = generate_dataset_batch(
            n_samples=100, 
            entropy_level="High", 
            config=config
        )
        save_problems_to_csv(problems_run1, run1_path)
        checksum1 = compute_sha256(run1_path)
        logger.info(f"Run 1 checksum: {checksum1}")

        # Run 2
        logger.info("Running generation pass 2...")
        # Re-instantiate config to ensure fresh state
        config = Config(seed=seed, max_ram_gb=7.0, max_runtime_hours=6.0)
        problems_run2 = generate_dataset_batch(
            n_samples=100, 
            entropy_level="High", 
            config=config
        )
        save_problems_to_csv(problems_run2, run2_path)
        checksum2 = compute_sha256(run2_path)
        logger.info(f"Run 2 checksum: {checksum2}")

        if checksum1 == checksum2:
            logger.info("SUCCESS: Checksums match. Reproducibility verified.")
            return True
        else:
            logger.error("FAILURE: Checksums do not match. Reproducibility failed.")
            logger.error(f"Run 1: {checksum1}")
            logger.error(f"Run 2: {checksum2}")
            return False

    except Exception as e:
        logger.error(f"Error during reproducibility check: {e}")
        raise
    finally:
        # Cleanup temporary files
        if output_dir.exists():
            shutil.rmtree(output_dir)

def main():
    """Main entry point for the script."""
    config = get_config()
    seed = config.seed
    
    # Use a temporary directory for reproducibility test outputs
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir)
        success = run_reproducibility_check(seed, output_path)
        
        if not success:
            logger.critical("Reproducibility check failed. CI should abort.")
            sys.exit(1)
        
        logger.info("Reproducibility check passed.")
        sys.exit(0)

if __name__ == "__main__":
    main()