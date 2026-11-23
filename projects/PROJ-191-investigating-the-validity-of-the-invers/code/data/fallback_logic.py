"""
Fallback logic for handling insufficient independent runs in the dataset.

This module provides functions to detect the number of independent runs,
manage the bootstrap flag in the state file, and prepare datasets for
analysis when run counts are low.
"""
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional
from config import get_logger, ProjectConfig
from data.state_manager import read_state, write_state, set_bootstrap_flag

logger = get_logger(__name__)

def detect_independent_runs(raw_data_dir: Path) -> int:
    """
    Count the number of independent experimental runs found in the raw data directory.
    
    Args:
        raw_data_dir: Path to the directory containing raw data files.
        
    Returns:
        The number of independent runs detected.
    """
    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")
        return 0
        
    # Count CSV files as independent runs (assuming each run is a separate file)
    csv_files = list(raw_data_dir.glob("*.csv"))
    return len(csv_files)

def check_and_set_bootstrap_flag(run_count: int, state_path: Path) -> bool:
    """
    Check if the run count is sufficient and set the bootstrap flag accordingly.
    
    This function implements the core logic for T016:
    - If fewer than three independent runs are detected, set USE_BOOTSTRAP to true.
    - If 3 or more runs are detected, set USE_BOOTSTRAP to false.
    
    Args:
        run_count: The number of independent runs detected.
        state_path: Path to the state.json file.
        
    Returns:
        True if bootstrap mode is enabled, False otherwise.
    """
    logger.info(f"Checking run count: {run_count} runs detected")
    
    # Read existing state or create new one
    state = read_state(state_path)
    
    # Determine if bootstrap is needed
    use_bootstrap = run_count < 3
    
    # Update state with bootstrap flag
    state['USE_BOOTSTRAP'] = use_bootstrap
    state['run_count'] = run_count
    state['bootstrap_required'] = use_bootstrap
    
    # Write updated state
    write_state(state_path, state)
    
    if use_bootstrap:
        logger.warning(f"Bootstrap fallback triggered: Only {run_count} runs found (< 3 required)")
    else:
        logger.info(f"Sufficient runs found: {run_count} runs detected (>= 3 required)")
        
    return use_bootstrap

def bootstrap_resample_dataset(
    dataset: pd.DataFrame,
    n_samples: Optional[int] = None,
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Perform bootstrap resampling on the dataset.
    
    Args:
        dataset: The original dataset to resample.
        n_samples: Number of samples to draw. If None, uses the original dataset size.
        random_seed: Random seed for reproducibility.
        
    Returns:
        A bootstrap resampled dataset.
    """
    if random_seed is not None:
        np.random.seed(random_seed)
        
    n = n_samples if n_samples is not None else len(dataset)
    
    # Sample with replacement
    indices = np.random.choice(len(dataset), size=n, replace=True)
    resampled = dataset.iloc[indices].reset_index(drop=True)
    
    logger.info(f"Bootstrap resampled {n} points from {len(dataset)} original points")
    return resampled

def prepare_analysis_dataset(
    dataset: pd.DataFrame,
    use_bootstrap: bool,
    n_bootstrap_samples: int = 1000,
    random_seed: Optional[int] = None
) -> Tuple[pd.DataFrame, dict]:
    """
    Prepare the dataset for analysis, applying bootstrap resampling if needed.
    
    Args:
        dataset: The original dataset.
        use_bootstrap: Whether to apply bootstrap resampling.
        n_bootstrap_samples: Number of bootstrap samples to generate.
        random_seed: Random seed for reproducibility.
        
    Returns:
        A tuple of (processed_dataset, metadata_dict).
    """
    metadata = {
        'original_size': len(dataset),
        'use_bootstrap': use_bootstrap,
        'n_bootstrap_samples': n_bootstrap_samples if use_bootstrap else 0
    }
    
    if use_bootstrap:
        logger.info("Preparing dataset with bootstrap resampling")
        # For bootstrap mode, we'll keep the original dataset but note that
        # analysis should be performed on resampled versions
        metadata['bootstrap_note'] = "Analysis should use bootstrap_resample_dataset for each iteration"
        processed_dataset = dataset
    else:
        logger.info("Preparing dataset without bootstrap resampling")
        processed_dataset = dataset
        
    return processed_dataset, metadata

def main():
    """
    Main entry point for the fallback logic script.
    
    This script checks the number of independent runs in the raw data directory
    and updates the state.json file with the appropriate bootstrap flag.
    """
    config = ProjectConfig()
    raw_data_dir = config.raw_data_dir
    state_path = config.state_path
    
    logger.info(f"Checking independent runs in {raw_data_dir}")
    
    # Detect independent runs
    run_count = detect_independent_runs(raw_data_dir)
    
    # Check and set bootstrap flag
    use_bootstrap = check_and_set_bootstrap_flag(run_count, state_path)
    
    logger.info(f"Bootstrap flag set to: {use_bootstrap}")
    
    return use_bootstrap

if __name__ == "__main__":
    main()
