"""
Orchestration entry point for the Residue Distribution of Euler's Totient Function analysis.

This module provides the base configuration loader and the main execution flow.
It handles:
- Configuration of N (range limit)
- Selection of primes p in {3, 5, 7, 11}
- Memory limit configuration
- Random seed pinning (delegated to sibling modules)
- Orchestration of the sieve and statistical analysis pipelines.
"""

import os
import sys
import argparse
import logging
import random
import numpy as np
from typing import List, Optional, Dict, Any

# Import seed pinning utilities from existing modules
# T007d: Initialize random seed pinning at the orchestration level.
# We import the function from sieve.py (which already has it per API surface)
# and ensure it is called here if a seed is provided.
from sieve import pin_random_seed as sieve_pin_seed, is_seed_pinned

# Import configuration and logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_N = 1000000
DEFAULT_PRIMES = [3, 5, 7, 11]
DEFAULT_MEMORY_LIMIT_MB = 4096  # 4GB default
DEFAULT_SEED = 42


class Config:
    """
    Immutable configuration container for the analysis run.
    
    Attributes:
        N (int): The upper bound for the totient calculation (n in [1, N]).
        primes (List[int]): List of primes to analyze residues for.
        memory_limit_mb (int): Soft memory limit in Megabytes.
        seed (Optional[int]): Random seed for reproducibility.
    """
    
    def __init__(
        self,
        N: int = DEFAULT_N,
        primes: Optional[List[int]] = None,
        memory_limit_mb: int = DEFAULT_MEMORY_LIMIT_MB,
        seed: Optional[int] = DEFAULT_SEED
    ):
        if primes is None:
            primes = DEFAULT_PRIMES
        
        # Validate primes
        allowed_primes = {3, 5, 7, 11}
        for p in primes:
            if p not in allowed_primes:
                raise ValueError(f"Prime {p} is not in allowed set {allowed_primes}. "
                               f"Allowed values: {allowed_primes}")
        
        if N < 1:
            raise ValueError("N must be a positive integer.")
        
        if memory_limit_mb < 64:
            raise ValueError("Memory limit must be at least 64MB.")
        
        self.N = N
        self.primes = primes
        self.memory_limit_mb = memory_limit_mb
        self.seed = seed
        
        logger.info(f"Configuration loaded: N={N}, primes={primes}, "
                  f"mem_limit={memory_limit_mb}MB, seed={seed}")

def load_config(
    N: Optional[int] = None,
    primes: Optional[List[int]] = None,
    memory_limit_mb: Optional[int] = None,
    seed: Optional[int] = None
) -> Config:
    """
    Factory function to create a Config object with overrides.
    
    Args:
        N: Upper bound for totient calculation.
        primes: List of primes to analyze.
        memory_limit_mb: Memory limit in MB.
        seed: Random seed.
        
    Returns:
        Config: A validated configuration object.
    """
    return Config(
        N=N if N is not None else DEFAULT_N,
        primes=primes,
        memory_limit_mb=memory_limit_mb if memory_limit_mb is not None else DEFAULT_MEMORY_LIMIT_MB,
        seed=seed if seed is not None else DEFAULT_SEED
    )

def pin_orchestration_seed(seed: int) -> None:
    """
    Pin random seeds for all relevant libraries at the orchestration level.
    
    This ensures reproducibility across the entire pipeline (sieve, stats, visualize).
    It delegates to the sieve module for the standard `random` module and explicitly
    sets seeds for `numpy` here to ensure consistency at the entry point.
    
    Args:
        seed (int): The seed value to use.
    """
    logger.info(f"Pinning orchestration random seed to {seed}")
    
    # Pin standard library random (via sieve module helper)
    sieve_pin_seed(seed)
    
    # Pin numpy random state
    np.random.seed(seed)
    
    logger.info("Orchestration random seed pinned successfully for all libraries.")

def main():
    """
    Main entry point for the analysis pipeline.
    
    Parses command line arguments, initializes configuration and random seed,
    and orchestrates the analysis flow.
    """
    parser = argparse.ArgumentParser(
        description="Run Residue Distribution Analysis for Euler's Totient Function."
    )
    parser.add_argument(
        "--N", type=int, default=DEFAULT_N,
        help=f"Upper bound for totient calculation (default: {DEFAULT_N})"
    )
    parser.add_argument(
        "--primes", type=int, nargs="+", default=DEFAULT_PRIMES,
        help=f"Primes to analyze (default: {DEFAULT_PRIMES}). Allowed: {3, 5, 7, 11}"
    )
    parser.add_argument(
        "--memory-limit", type=int, default=DEFAULT_MEMORY_LIMIT_MB,
        help=f"Memory limit in MB (default: {DEFAULT_MEMORY_LIMIT_MB})"
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help=f"Random seed for reproducibility (default: {DEFAULT_SEED})"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(
        N=args.N,
        primes=args.primes,
        memory_limit_mb=args.memory_limit,
        seed=args.seed
    )
    
    # Pin random seed for the orchestration level (T007d requirement)
    if config.seed is not None:
        pin_orchestration_seed(config.seed)
        logger.info(f"Random seed pinned to {config.seed} for orchestration.")
    
    logger.info("Starting analysis pipeline...")
    
    # TODO: This is where the orchestration logic would call:
    # 1. sieve.run_sieve_analysis(N, primes, memory_limit)
    # 2. stats.run_full_statistical_analysis(...)
    # 3. visualize.generate_plots(...)
    # For now, we confirm configuration is valid and exit.
    
    logger.info(f"Configuration valid. N={config.N}, primes={config.primes}")
    logger.info("Analysis pipeline ready.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())