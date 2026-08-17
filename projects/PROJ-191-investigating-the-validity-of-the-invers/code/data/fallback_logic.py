"""
Fallback logic module for handling cases with insufficient independent runs.
Implements bootstrap resampling when fewer than 3 independent runs are detected.
"""
import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional

from config import get_logger
from data.state_manager import get_state_path, read_state, write_state, set_bootstrap_flag

logger = get_logger(__name__)


def detect_independent_runs(harmonized_data_path: Path) -> int:
    """
    Detect the number of independent experimental runs in the harmonized dataset.
    
    Args:
        harmonized_data_path: Path to the harmonized dataset CSV file
        
    Returns:
        Number of independent runs detected
    """
    if not harmonized_data_path.exists():
        logger.warning(f"Harmonized data file not found at {harmonized_data_path}")
        return 0
        
    try:
        df = pd.read_csv(harmonized_data_path)
        
        # Check for run identifier columns
        run_columns = [col for col in df.columns if 'run' in col.lower() or 'experiment' in col.lower()]
        
        if not run_columns:
            # If no explicit run column, try to infer from unique combinations
            # of other identifiers or assume single run
            logger.info("No explicit run identifier found, assuming single run")
            return 1
            
        # Count unique run identifiers
        unique_runs = df[run_columns[0]].nunique()
        logger.info(f"Detected {unique_runs} independent runs from column '{run_columns[0]}'")
        return unique_runs
        
    except Exception as e:
        logger.error(f"Error detecting independent runs: {e}")
        return 0


def bootstrap_resample_dataset(
    df: pd.DataFrame,
    n_bootstrap: int = 1000,
    random_seed: Optional[int] = None
) -> List[pd.DataFrame]:
    """
    Generate bootstrap resamples of the dataset for statistical analysis.
    
    Args:
        df: Input dataframe to resample
        n_bootstrap: Number of bootstrap samples to generate
        random_seed: Random seed for reproducibility
        
    Returns:
        List of bootstrap resampled dataframes
    """
    if random_seed is not None:
        np.random.seed(random_seed)
        
    bootstrap_samples = []
    n_rows = len(df)
    
    for i in range(n_bootstrap):
        # Sample with replacement
        indices = np.random.choice(n_rows, size=n_rows, replace=True)
        bootstrap_df = df.iloc[indices].reset_index(drop=True)
        bootstrap_samples.append(bootstrap_df)
        
    logger.info(f"Generated {n_bootstrap} bootstrap samples")
    return bootstrap_samples


def prepare_analysis_dataset(
    df: pd.DataFrame,
    use_bootstrap: bool,
    n_bootstrap: int = 1000,
    random_seed: Optional[int] = None
) -> Tuple[pd.DataFrame, bool]:
    """
    Prepare the analysis dataset, applying bootstrap resampling if needed.
    
    Args:
        df: Input dataframe
        use_bootstrap: Whether to use bootstrap resampling
        n_bootstrap: Number of bootstrap samples if using bootstrap
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (prepared dataset, bootstrap flag)
    """
    if use_bootstrap:
        logger.info("Preparing bootstrap resampling for analysis")
        bootstrap_samples = bootstrap_resample_dataset(df, n_bootstrap, random_seed)
        # For analysis, we'll return the original df with a flag indicating
        # that bootstrap should be used in downstream processing
        logger.info(f"Bootstrap resampling will generate {n_bootstrap} samples during analysis")
        return df, True
    else:
        logger.info("Using full dataset for analysis without bootstrap")
        return df, False


def main():
    """
    Main entry point for fallback logic execution.
    
    This function:
    1. Reads the harmonized dataset
    2. Detects the number of independent runs
    3. Writes the appropriate state flag (USE_BOOTSTRAP) to data/processed/state.json
    """
    logger.info("Starting fallback logic execution (T016)")
    
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    harmonized_data_path = project_root / "data" / "processed" / "harmonized_data.csv"
    state_path = project_root / "data" / "processed" / "state.json"
    
    # Ensure state directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Detect independent runs
    n_runs = detect_independent_runs(harmonized_data_path)
    logger.info(f"Detected {n_runs} independent runs")
    
    # Determine if bootstrap is needed (fewer than 3 runs)
    use_bootstrap = n_runs < 3
    
    if use_bootstrap:
        logger.warning(f"Only {n_runs} independent runs detected. Bootstrap resampling will be used.")
    else:
        logger.info(f"{n_runs} independent runs detected. Standard analysis will be used.")
    
    # Write state flag to state.json
    try:
        # Read existing state if it exists
        current_state = read_state(state_path) if state_path.exists() else {}
        
        # Update with bootstrap flag
        current_state["USE_BOOTSTRAP"] = use_bootstrap
        current_state["detected_runs"] = n_runs
        current_state["bootstrap_threshold"] = 3
        
        # Write updated state
        write_state(state_path, current_state)
        
        logger.info(f"Successfully wrote state to {state_path}")
        logger.info(f"USE_BOOTSTRAP flag set to: {use_bootstrap}")
        
    except Exception as e:
        logger.error(f"Failed to write state file: {e}")
        raise RuntimeError(f"Failed to write bootstrap state flag: {e}")
    
    logger.info("Fallback logic execution completed successfully")
    return use_bootstrap


if __name__ == "__main__":
    main()
