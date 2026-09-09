import os
import sys
import argparse
import logging
import random
import numpy as np

# Import from sieve module
from sieve import run_sieve_analysis, pin_random_seed, ResidueDataset, StatisticalResult

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def pin_orchestration_seed(seed: int):
    """Pin all random seeds for the orchestration."""
    pin_random_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run totient residue analysis')
    parser.add_argument('--N', type=int, default=1000000, help='Range limit N')
    parser.add_argument('--primes', type=int, nargs='+', default=[3, 5, 7, 11], help='Primes to analyze')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--memory-limit-mb', type=int, default=6000, help='Memory limit in MB')
    parser.add_argument('--memory-check-interval', type=int, default=10000, help='Memory check interval')
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    config = {
        'N': args.N,
        'primes': args.primes,
        'memory_limit_mb': args.memory_limit_mb,
        'seed': args.seed,
        'memory_check_interval': args.memory_check_interval
    }
    
    pin_orchestration_seed(args.seed)
    
    logger.info(f"Running analysis with config: {config}")
    
    run_sieve_analysis(args.N, args.primes, config)
    
    logger.info("Analysis complete.")

if __name__ == '__main__':
    main()
