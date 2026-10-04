"""
Main entry point for running the analysis pipeline.
"""
import os
import sys
import argparse
import logging
import random
import numpy as np

from config import load_config, parse_cli_args, create_argument_parser
from sieve import run_sieve_analysis, pin_random_seed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def pin_orchestration_seed(config: dict) -> None:
    """Pin all random seeds for deterministic execution."""
    seed = config.get('seed', 42)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Seeds pinned to {seed}")

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = create_argument_parser()
    return parser.parse_args()

def main() -> None:
    """Main entry point."""
    config = parse_cli_args()
    pin_orchestration_seed(config)
    
    logger.info(f"Starting analysis with N={config['N']}, primes={config['primes']}")
    
    run_sieve_analysis(
        N=config['N'],
        primes=config['primes'],
        memory_limit_mb=config['memory_limit_mb']
    )
    
    logger.info("Analysis complete.")

if __name__ == '__main__':
    main()
