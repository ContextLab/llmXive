import os
import sys
import logging
import argparse
from pathlib import Path

# Ensure code directory is in path
code_dir = Path(__file__).parent
sys.path.insert(0, str(code_dir))

from generators import generate_lorenz_trajectory, generate_rossler_trajectory

def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Configures logging for the T015 task.
    """
    handlers = []
    handlers.append(logging.StreamHandler(sys.stdout))

    if log_file:
        handlers.append(logging.FileHandler(log_file, mode='w'))

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    logger = logging.getLogger(__name__)
    logger.info("Logging configured for T015 task.")
    return logger

def main():
    parser = argparse.ArgumentParser(description="T015: Test logging for integration overflow and metadata.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--log-file", type=str, default=None, help="Path to log file")
    parser.add_argument("--system", type=str, default="lorenz", choices=["lorenz", "rossler"], help="System to generate")
    args = parser.parse_args()

    logger = setup_logging(log_file=args.log_file)

    logger.info(f"Starting T015 pipeline for {args.system} system with seed {args.seed}")

    try:
        if args.system == "lorenz":
            trajectory = generate_lorenz_trajectory(seed=args.seed, t_span=(0.0, 100.0), dt=0.01)
        else:
            trajectory = generate_rossler_trajectory(seed=args.seed, t_span=(0.0, 100.0), dt=0.01)
        
        logger.info(f"Successfully generated trajectory with {len(trajectory.time)} points.")
        logger.info(f"Metadata: {trajectory.metadata}")
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}", exc_info=True)
        sys.exit(1)

    logger.info("T015 pipeline completed successfully.")

if __name__ == "__main__":
    main()