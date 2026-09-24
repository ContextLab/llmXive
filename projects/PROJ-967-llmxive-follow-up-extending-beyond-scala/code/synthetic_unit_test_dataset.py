"""
Task T037b: Synthetic Unit-Test Dataset Generator

Generates a small synthetic dataset (N=50) for unit testing via simulate.py.
Includes mock human annotations (not for final analysis).
"""
import argparse
import logging
import os
import sys
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Generate synthetic unit-test dataset."""
    parser = argparse.ArgumentParser(description="Generate synthetic unit-test dataset")
    parser.add_argument("--n-samples", type=int, default=50, help="Number of samples to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/raw/mock_oxford_pets.parquet", help="Output file path")
    args = parser.parse_args()

    logger.info(f"Generating synthetic dataset with {args.n_samples} samples, seed={args.seed}")
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Call simulate.py with the specified parameters
    simulate_script = Path(__file__).parent / "simulate.py"
    
    if not simulate_script.exists():
        logger.error(f"simulate.py not found at {simulate_script}")
        raise FileNotFoundError(f"simulate.py not found at {simulate_script}")
    
    cmd = [
        sys.executable,
        str(simulate_script),
        "--n-samples", str(args.n_samples),
        "--seed", str(args.seed),
        "--output", str(args.output)
    ]
    
    logger.info(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Synthetic dataset generation completed successfully")
        logger.info(f"Output written to: {args.output}")
        
        # Log the command output for debugging
        if result.stdout:
            logger.debug(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            logger.debug(f"STDERR:\n{result.stderr}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to generate synthetic dataset: {e}")
        logger.error(f"STDERR: {e.stderr}")
        raise RuntimeError(f"Synthetic dataset generation failed: {e}")

if __name__ == "__main__":
    main()
