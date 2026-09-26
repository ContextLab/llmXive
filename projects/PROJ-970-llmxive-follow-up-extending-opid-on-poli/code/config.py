import os
import random
import sys
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
import json
import numpy as np

# Global Constants
SEED = 42
TIER_NODE_RANGES = {
    1: (5, 10),
    2: (20, 50),
    3: (100, 100)  # Fixed 100 for Tier 3 max as per spec
}
THRESHOLD_STEPS = 11  # np.arange(0.0, 1.01, 0.1) yields 11 steps

# Reproducibility initialization
def initialize_reproducibility(seed: int = SEED) -> None:
    """Initialize all random seeds for reproducibility."""
    np.random.seed(seed)
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

# Initialize immediately on module load
initialize_reproducibility(SEED)

def get_seed() -> int:
    return SEED

def set_seed(seed: int) -> None:
    global SEED
    SEED = seed
    initialize_reproducibility(seed)

def get_tier_config(tier: int) -> Tuple[int, int]:
    """Return the node range for a given tier."""
    if tier not in TIER_NODE_RANGES:
        raise ValueError(f"Invalid tier: {tier}")
    return TIER_NODE_RANGES[tier]

def ensure_directories() -> None:
    """Create required directory structure."""
    dirs = [
        "data/raw/synthetic_graphs",
        "data/processed",
        "figures",
        "logs"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def get_version_hash() -> str:
    """Return a timestamp-based version hash."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def save_config_snapshot(config: Dict[str, Any], path: str) -> None:
    """Save current configuration to a JSON file."""
    with open(path, 'w') as f:
        json.dump(config, f, indent=2)

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of current configuration."""
    return {
        "seed": SEED,
        "tier_node_ranges": TIER_NODE_RANGES,
        "threshold_steps": THRESHOLD_STEPS,
        "version": get_version_hash()
    }

def verify_feasibility() -> None:
    """
    Calculate estimated runtime using deterministic constants.
    
    Worst-case parameters:
    - 100 nodes (Tier 3 max)
    - 200 steps/episode
    - N=1000 episodes
    - 11 threshold settings
    - 3 tiers
    
    Formula: estimated_time = (100 * 200 * 1000 * 11 * 3) * constant_overhead
    
    Raises RuntimeError if estimated time > 6 hours.
    """
    # Constants from spec
    max_nodes = 100
    steps_per_episode = 200
    episodes = 1000
    num_thresholds = 11
    num_tiers = 3
    
    # Estimated operations count (simplified model)
    total_operations = max_nodes * steps_per_episode * episodes * num_thresholds * num_tiers
    
    # Constant overhead factor (operations per second estimate)
    # Based on typical CPU performance for graph operations
    # Conservative estimate: 10^6 operations per second
    constant_overhead = 1.0 / (10**6)  # seconds per operation
    
    estimated_time_seconds = total_operations * constant_overhead
    estimated_time_hours = estimated_time_seconds / 3600
    
    max_allowed_hours = 6.0
    
    if estimated_time_hours > max_allowed_hours:
        raise RuntimeError(
            f"Feasibility check failed: Estimated runtime {estimated_time_hours:.2f} hours "
            f"exceeds maximum allowed {max_allowed_hours} hours. "
            f"Parameters: {max_nodes} nodes, {steps_per_episode} steps, "
            f"{episodes} episodes, {num_thresholds} thresholds, {num_tiers} tiers."
        )

def main():
    """Main entry point for config module."""
    print("Config module loaded successfully")
    print(f"Seed: {SEED}")
    print(f"Tier node ranges: {TIER_NODE_RANGES}")
    print(f"Threshold steps: {THRESHOLD_STEPS}")
    
    # Run feasibility check
    try:
        verify_feasibility()
        print("Feasibility check passed")
    except RuntimeError as e:
        print(f"Feasibility check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()