"""
Seed configuration management for model training module.
Provides CLI argument parsing and seed enforcement.
"""
import argparse
import sys
from typing import Optional
import logging

# Import from the shared utility module
from utils.seed_manager import set_seed, get_seed, ensure_seed_set

logger = logging.getLogger(__name__)

def parse_seed_args(args: Optional[list] = None) -> argparse.Namespace:
    """
    Parse command-line arguments for seed configuration.

    Args:
        args: Optional list of arguments. If None, uses sys.argv[1:].

    Returns:
        Parsed namespace with seed-related arguments.
    """
    parser = argparse.ArgumentParser(
        description="Configure random seed for model training reproducibility"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (default: None uses system random)"
    )
    parser.add_argument(
        "--set-seed",
        action="store_true",
        help="Explicitly set the random seed before execution"
    )
    parser.add_argument(
        "--log-seed",
        action="store_true",
        help="Log the current seed value"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cpu",
        help="Device to use for training (default: cpu)"
    )

    return parser.parse_args(args)

def main():
    """
    Main entry point for seed configuration CLI.
    Sets up logging and enforces seed based on arguments.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    args = parse_seed_args()

    if args.set_seed or args.seed is not None:
        seed_value = args.seed if args.seed is not None else 42
        set_seed(seed_value)
        logger.info(f"Random seed set to: {seed_value}")

    if args.log_seed:
        current_seed = get_seed()
        if current_seed is not None:
            logger.info(f"Current active seed: {current_seed}")
        else:
            logger.warning("No seed has been set yet")

    # Ensure seed is set if requested
    if args.set_seed:
        ensure_seed_set()

    logger.info(f"Seed configuration module initialized for device: {args.device}")

if __name__ == "__main__":
    main()
