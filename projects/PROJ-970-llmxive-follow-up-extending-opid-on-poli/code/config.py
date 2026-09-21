"""
Global configuration and reproducibility initialization for the OPID routing complexity analysis.

This module handles:
- Global constants (SEED, TIER_NODE_RANGES, etc.)
- Reproducibility initialization (seeding random, numpy, random modules)
- Directory structure management
- Configuration snapshots and summaries
"""

import os
import json
import random
import hashlib
import sys
from datetime import datetime
from typing import Dict, Any, Optional, List

import numpy as np

# ============================================================================
# GLOBAL CONSTANTS
# ============================================================================

SEED = 42
"""Global random seed for reproducibility (FR-007, Const I)."""

# Tier node ranges: (min_nodes, max_nodes)
TIER_NODE_RANGES = {
    "tier_1": (10, 20),      # Deterministic, single path
    "tier_2": (20, 50),      # Branching, stochastic
    "tier_3": (50, 100),     # Complex, sparse rewards
}
"""Node count ranges for each complexity tier."""

# Deferred value: minimum 1000 based on G*Power analysis, to be determined in research
EPISODES_PER_SETTING = 1000
"""Number of episodes to run per (tier, threshold) combination."""

THRESHOLD_STEPS = 11
"""Number of threshold steps from 0.0 to 1.0 (inclusive, step=0.1)."""

# Project metadata
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "0.1.0"

# ============================================================================
# REPRODUCIBILITY INITIALIZATION (T008)
# ============================================================================

def set_seed(seed: int) -> None:
    """
    Set the random seed for all relevant modules to ensure reproducibility.
    
    Args:
        seed: The integer seed value to use.
    """
    random.seed(seed)
    np.random.seed(seed)
    # Note: os.environ['PYTHONHASHSEED'] is typically set before Python starts
    # for full reproducibility, but we seed the standard libraries here.

def get_seed() -> int:
    """
    Get the current global seed value.
    
    Returns:
        The current seed (defaults to SEED if not explicitly set).
    """
    # We maintain the seed in a module-level variable for retrieval
    return getattr(_seed_manager, 'current_seed', SEED)

class _SeedManager:
    """Internal manager to track the current seed state."""
    current_seed = SEED

def initialize_reproducibility(seed: Optional[int] = None) -> int:
    """
    Initialize reproducibility by setting seeds for all random number generators.
    
    This function MUST be called at the start of any experiment to ensure
    deterministic behavior across runs (FR-007, Const I).
    
    Args:
        seed: Optional seed value. If None, uses the global SEED constant.
    
    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = SEED
    
    _SeedManager.current_seed = seed
    set_seed(seed)
    
    # Log the initialization (avoid circular imports by using basic logging)
    print(f"[config] Reproducibility initialized with seed: {seed}")
    
    return seed

# ============================================================================
# DIRECTORY MANAGEMENT
# ============================================================================

def ensure_directories() -> None:
    """
    Create the required directory structure if it doesn't exist.
    
    Creates:
    - data/raw/synthetic_graphs/
    - data/processed/
    - figures/
    - logs/
    """
    directories = [
        os.path.join(PROJECT_ROOT, "data", "raw", "synthetic_graphs"),
        os.path.join(PROJECT_ROOT, "data", "processed"),
        os.path.join(PROJECT_ROOT, "figures"),
        os.path.join(PROJECT_ROOT, "logs"),
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

def get_version_hash() -> str:
    """
    Generate a hash of the current code version for reproducibility tracking.
    
    Returns:
        A short hash string representing the current code state.
    """
    try:
        # Try to get git hash if available
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    
    # Fallback: hash of the config file itself
    with open(__file__, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()[:8]

def get_tier_config(tier: str) -> Dict[str, Any]:
    """
    Get configuration for a specific complexity tier.
    
    Args:
        tier: The tier identifier (e.g., "tier_1", "tier_2", "tier_3").
    
    Returns:
        A dictionary containing the node range and other tier-specific settings.
    
    Raises:
        ValueError: If the tier is not recognized.
    """
    if tier not in TIER_NODE_RANGES:
        raise ValueError(f"Unknown tier: {tier}. Must be one of {list(TIER_NODE_RANGES.keys())}")
    
    return {
        "tier": tier,
        "node_range": TIER_NODE_RANGES[tier],
        "min_nodes": TIER_NODE_RANGES[tier][0],
        "max_nodes": TIER_NODE_RANGES[tier][1],
    }

def save_config_snapshot(output_path: str) -> None:
    """
    Save a snapshot of the current configuration to a JSON file.
    
    Args:
        output_path: The path where the configuration snapshot will be saved.
    """
    config_data = {
        "seed": get_seed(),
        "tier_node_ranges": TIER_NODE_RANGES,
        "episodes_per_setting": EPISODES_PER_SETTING,
        "threshold_steps": THRESHOLD_STEPS,
        "version": VERSION,
        "version_hash": get_version_hash(),
        "timestamp": datetime.now().isoformat(),
        "project_root": PROJECT_ROOT,
    }
    
    with open(output_path, "w") as f:
        json.dump(config_data, f, indent=2)

def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of the current configuration for logging purposes.
    
    Returns:
        A dictionary containing key configuration values.
    """
    return {
        "seed": get_seed(),
        "episodes_per_setting": EPISODES_PER_SETTING,
        "threshold_steps": THRESHOLD_STEPS,
        "version": VERSION,
        "version_hash": get_version_hash(),
    }

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Initialize reproducibility at module load time to ensure deterministic behavior
# This satisfies FR-007 and Const I requirements
_SeedManager.current_seed = SEED
set_seed(SEED)