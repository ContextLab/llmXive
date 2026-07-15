"""
Configuration management for the llmXive pipeline.

This module provides the SeedManager utility to ensure reproducible 
convergence diagnostics for MICE by deriving distinct per-chain seeds 
from a base seed.
"""
import os
from typing import List, Dict, Any, Optional
import numpy as np


class SeedManager:
    """
    Manages random seeds for reproducible stochastic processes.
    
    This class derives distinct per-chain seeds from a base seed to ensure
    that multiple independent MICE chains do not initialize identically,
    which is critical for valid convergence diagnostics.
    
    Attributes:
        base_seed (int): The root seed for the experiment.
        chains (int): The number of distinct chains to generate seeds for.
    """
    
    def __init__(self, base_seed: int, chains: int = 4):
        """
        Initialize the SeedManager.
        
        Args:
            base_seed: The integer base seed for the experiment.
            chains: The number of distinct chains (default is 4 for MICE).
        """
        if not isinstance(base_seed, int) or base_seed < 0:
            raise ValueError("base_seed must be a non-negative integer.")
        if not isinstance(chains, int) or chains < 1:
            raise ValueError("chains must be a positive integer.")
            
        self.base_seed = base_seed
        self.chains = chains
    
    def get_chain_seeds(self) -> List[int]:
        """
        Generate a list of distinct seeds for each chain.
        
        The seeds are derived deterministically using the formula:
            seed_i = base_seed + (i * 1000) + 1
        
        This ensures that:
        1. All seeds are unique.
        2. The sequence is reproducible given the same base_seed.
        3. The seeds are sufficiently spaced to avoid overlapping random states.
        
        Returns:
            A list of integers, one for each chain.
        """
        seeds = []
        for i in range(self.chains):
            # Derive distinct seed: base + offset based on chain index
            # Using a large offset (1000) ensures separation even if base_seed is small
            chain_seed = self.base_seed + (i * 1000) + 1
            seeds.append(chain_seed)
        return seeds
    
    def get_seed_for_chain(self, chain_id: int) -> int:
        """
        Get the specific seed for a given chain ID.
        
        Args:
            chain_id: The index of the chain (0-indexed).
            
        Returns:
            The integer seed for the specified chain.
            
        Raises:
            ValueError: If chain_id is out of range.
        """
        if not isinstance(chain_id, int) or chain_id < 0 or chain_id >= self.chains:
            raise ValueError(f"chain_id must be between 0 and {self.chains - 1}")
        
        return self.base_seed + (chain_id * 1000) + 1
    
    def set_global_seed(self, chain_id: Optional[int] = None) -> None:
        """
        Set the global numpy random seed for reproducibility.
        
        If chain_id is provided, sets the seed for that specific chain.
        Otherwise, sets the base seed for the main process.
        
        Args:
            chain_id: Optional chain index to set the seed for.
        """
        if chain_id is not None:
            seed = self.get_seed_for_chain(chain_id)
        else:
            seed = self.base_seed
        
        np.random.seed(seed)
        # Note: If using other libraries (e.g., torch, tensorflow), 
        # their specific seed setters would be added here.


def get_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables or defaults.
    
    Returns:
        A dictionary containing configuration parameters.
    """
    base_seed = int(os.getenv("MICE_BASE_SEED", "42"))
    num_chains = int(os.getenv("MICE_NUM_CHAINS", "4"))
    
    return {
        "base_seed": base_seed,
        "num_chains": num_chains,
        "max_iter": int(os.getenv("MICE_MAX_ITER", "1000")),
        "missingness_threshold": float(os.getenv("MISSINGNESS_THRESHOLD", "0.30"))
    }


def create_seed_manager() -> SeedManager:
    """
    Factory function to create a SeedManager instance based on environment config.
    
    Returns:
        A configured SeedManager instance.
    """
    config = get_config()
    return SeedManager(
        base_seed=config["base_seed"],
        chains=config["num_chains"]
    )


if __name__ == "__main__":
    # Example usage / simple verification
    import json
    
    # Default config
    manager = create_seed_manager()
    seeds = manager.get_chain_seeds()
    
    print(f"Base Seed: {manager.base_seed}")
    print(f"Number of Chains: {manager.chains}")
    print(f"Generated Seeds: {seeds}")
    
    # Verify uniqueness
    assert len(seeds) == len(set(seeds)), "Seeds must be unique!"
    assert len(seeds) == manager.chains, "Seed count must match chain count!"
    
    print("SeedManager verification passed.")