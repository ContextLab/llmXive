"""
Global configuration constants and initialization for the llmXive OPID Routing Complexity Analysis.

This module defines all project-wide constants and ensures reproducibility by seeding
random number generators at module load time as per FR-007 and Const I.
"""
import os
import json
import random
import hashlib
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

import numpy as np

# ============================================================================
# GLOBAL CONSTANTS (FR-003, FR-006, FR-007, Const I, Const VII)
# ============================================================================

# Reproducibility Seed (FR-007, Const I)
SEED: int = 42

# Tier Node Ranges (T011, T012, T013)
# Tier 1: 5 to 10 nodes (Deterministic)
# Tier 2: 20 to 50 nodes (Branching/Stochastic)
# Tier 3: 50+ nodes (Sparse/High-Entropy) - using a flexible range starting at 50
TIER_NODE_RANGES: Dict[str, Dict[str, int]] = {
    "tier_1": {"min": 5, "max": 10},
    "tier_2": {"min": 20, "max": 50},
    "tier_3": {"min": 50, "max": 200},  # Scalable upper bound
}

# Minimum episodes per setting (FR-003, Const VII)
EPISODES_PER_SETTING: int = 1000

# Threshold steps (FR-006): 0.0 to 1.0 in 0.1 increments = 11 steps
THRESHOLD_STEPS: int = 11

# Retry limits for graph generation (T011-T013)
MAX_RETRIES: int = 100

# Directory paths (relative to project root)
ROOT_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR: str = os.path.join(ROOT_DIR, "data")
DATA_RAW_DIR: str = os.path.join(DATA_DIR, "raw")
DATA_PROCESSED_DIR: str = os.path.join(DATA_DIR, "processed")
DATA_SYNTHETIC_GRAPHS_DIR: str = os.path.join(DATA_RAW_DIR, "synthetic_graphs")
FIGURES_DIR: str = os.path.join(ROOT_DIR, "figures")
LOGS_DIR: str = os.path.join(ROOT_DIR, "logs")

# ============================================================================
# SEED INITIALIZATION (FR-007, Const I)
# ============================================================================
# MUST be called at module load to ensure reproducibility.
# This satisfies the requirement to seed both numpy and python random at import.

def _initialize_seeds():
    """
    Initialize random seeds for reproducibility.
    Called immediately upon module import.
    """
    random.seed(SEED)
    np.random.seed(SEED)
    # Note: We do not seed os.urandom or other OS-level entropy sources
    # as they are system-dependent and not suitable for deterministic simulation.

# Execute seed initialization immediately
_initialize_seeds()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_seed() -> int:
    """Return the global seed constant."""
    return SEED

def set_seed(new_seed: int) -> None:
    """
    Update the global seed and re-seed random generators.
    Useful for specific experiment overrides while maintaining global state.
    """
    global SEED
    SEED = new_seed
    random.seed(SEED)
    np.random.seed(SEED)

def initialize_reproducibility(seed: Optional[int] = None) -> None:
    """
    Explicitly initialize reproducibility with an optional custom seed.
    If seed is None, uses the global SEED constant.
    """
    if seed is not None:
        set_seed(seed)
    else:
        set_seed(SEED)

def ensure_directories() -> None:
    """
    Create all required directory structures if they do not exist.
    """
    dirs = [
        DATA_DIR,
        DATA_RAW_DIR,
        DATA_PROCESSED_DIR,
        DATA_SYNTHETIC_GRAPHS_DIR,
        FIGURES_DIR,
        LOGS_DIR,
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def get_version_hash() -> str:
    """
    Generate a short hash of the current code state based on file modification times
    or a static identifier. For now, returns a timestamp-based hash.
    """
    now = datetime.now().isoformat()
    return hashlib.sha256(now.encode()).hexdigest()[:8]

def get_tier_config(tier_name: str) -> Dict[str, int]:
    """
    Retrieve the node range configuration for a specific tier.
    Raises KeyError if tier_name is invalid.
    """
    if tier_name not in TIER_NODE_RANGES:
        raise KeyError(f"Unknown tier: {tier_name}. Valid tiers: {list(TIER_NODE_RANGES.keys())}")
    return TIER_NODE_RANGES[tier_name]

def save_config_snapshot(filepath: str) -> None:
    """
    Save the current configuration state to a JSON file.
    """
    config_data = {
        "seed": SEED,
        "tier_node_ranges": TIER_NODE_RANGES,
        "episodes_per_setting": EPISODES_PER_SETTING,
        "threshold_steps": THRESHOLD_STEPS,
        "max_retries": MAX_RETRIES,
        "version_hash": get_version_hash(),
        "timestamp": datetime.now().isoformat(),
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2)

def get_config_summary() -> Dict[str, Any]:
    """
    Return a summary of the current configuration.
    """
    return {
        "seed": SEED,
        "episodes_per_setting": EPISODES_PER_SETTING,
        "threshold_steps": THRESHOLD_STEPS,
        "tiers": list(TIER_NODE_RANGES.keys()),
    }

# ============================================================================
# MAIN ENTRY POINT (for testing/config verification)
# ============================================================================

def main() -> None:
    """
    Main entry point to verify configuration and print summary.
    """
    print("=== llmXive Configuration Verification ===")
    print(f"Seed: {get_seed()}")
    print(f"EPISODES_PER_SETTING: {EPISODES_PER_SETTING}")
    print(f"THRESHOLD_STEPS: {THRESHOLD_STEPS}")
    print("Tier Node Ranges:")
    for tier, range_info in TIER_NODE_RANGES.items():
        print(f"  {tier}: {range_info['min']} - {range_info['max']} nodes")
    print(f"Max Retries: {MAX_RETRIES}")
    print("Directories:")
    ensure_directories()
    for d in [DATA_DIR, FIGURES_DIR, LOGS_DIR]:
        print(f"  {d}: {'Exists' if os.path.exists(d) else 'Missing'}")
    print("==========================================")

if __name__ == "__main__":
    main()