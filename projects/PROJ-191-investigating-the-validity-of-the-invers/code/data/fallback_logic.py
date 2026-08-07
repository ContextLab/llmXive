import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional

from config import get_logger, ProjectConfig
from data.loaders import HarmonizedDataset

logger = get_logger(__name__)

def detect_independent_runs(harmonized_data: HarmonizedDataset) -> int:
    """
    Detect the number of independent experimental runs in the harmonized dataset.
    
    This function analyzes the 'source' or 'experiment_id' column in the dataset
    to count unique independent runs. If the dataset is structured as a list of
    DataFrames or has a metadata field tracking runs, it handles that logic.
    
    Args:
        harmonized_data: The harmonized dataset object.
        
    Returns:
        int: The count of independent runs detected.
    """
    if not harmonized_data.data:
        logger.warning("No data found in HarmonizedDataset.")
        return 0
    
    # The harmonized_data.data is expected to be a DataFrame or a list of them.
    # Based on typical harmonization, it's likely a single DataFrame with a 'source' column.
    df = harmonized_data.data if isinstance(harmonized_data.data, pd.DataFrame) else pd.concat(harmonized_data.data, ignore_index=True)
    
    # Look for common columns indicating run identity
    run_columns = ['source', 'experiment_id', 'run_id', 'dataset_id', 'arxiv_id']
    run_col = None
    
    for col in run_columns:
        if col in df.columns:
            run_col = col
            break
    
    if run_col is None:
        # Fallback: if no explicit column, assume the whole dataset is one run
        # or check if it's a multi-index
        logger.warning(f"No standard run identifier column found in {df.columns}. Assuming 1 run.")
        return 1
    
    unique_runs = df[run_col].nunique()
    logger.info(f"Detected {unique_runs} independent runs via column '{run_col}'.")
    return unique_runs

def bootstrap_resample_dataset(df: pd.DataFrame, n_bootstrap: int = 1000, seed: int = 42) -> List[pd.DataFrame]:
    """
    Generate bootstrap resamples of the dataset for statistical analysis.
    
    Args:
        df: The original DataFrame.
        n_bootstrap: Number of bootstrap samples to generate.
        seed: Random seed for reproducibility.
        
    Returns:
        List of resampled DataFrames.
    """
    rng = np.random.default_rng(seed)
    resamples = []
    n = len(df)
    
    for _ in range(n_bootstrap):
        indices = rng.choice(n, size=n, replace=True)
        resamples.append(df.iloc[indices].reset_index(drop=True))
        
    return resamples

def prepare_analysis_dataset(harmonized_data: HarmonizedDataset, use_bootstrap: bool = False, n_bootstrap: int = 1000) -> Optional[List[pd.DataFrame]]:
    """
    Prepare the dataset for analysis, applying bootstrap resampling if requested.
    
    Args:
        harmonized_data: The input harmonized dataset.
        use_bootstrap: If True, perform bootstrap resampling.
        n_bootstrap: Number of bootstrap iterations.
        
    Returns:
        List of DataFrames to use for analysis, or None if bootstrap is not used.
    """
    if not use_bootstrap:
        return None
        
    df = harmonized_data.data if isinstance(harmonized_data.data, pd.DataFrame) else pd.concat(harmonized_data.data, ignore_index=True)
    logger.info(f"Preparing {n_bootstrap} bootstrap resamples for analysis.")
    return bootstrap_resample_dataset(df, n_bootstrap=n_bootstrap)

def main():
    """
    Main entry point for T016: Implement fallback logic.
    
    This script:
    1. Loads the harmonized dataset (assumed to be in data/processed/harmonized.csv or similar).
    2. Detects the number of independent runs.
    3. If fewer than 3 runs are detected, writes USE_BOOTSTRAP: true to data/processed/state.json.
    4. Logs the decision.
    """
    config = ProjectConfig()
    logger.info("Starting T016: Fallback Logic Implementation")
    
    # Determine path to harmonized data
    # Assuming the harmonized data is stored in data/processed/harmonized_data.csv or similar
    # We need to find the actual file or load the object if it was serialized.
    # Since T014/T015 produce the data, we look for the processed output.
    
    processed_dir = Path(config.data_dir) / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Try to load the harmonized dataset. 
    # The exact file name might vary, but usually it's 'harmonized.csv' or 'harmonized_data.csv'
    # or it might be a pickle. We'll try common extensions.
    possible_files = [
        processed_dir / "harmonized.csv",
        processed_dir / "harmonized_data.csv",
        processed_dir / "harmonized.parquet",
        processed_dir / "harmonized.pkl",
        processed_dir / "harmonized_dataset.json"
    ]
    
    harmonized_data = None
    found_file = None
    
    for f_path in possible_files:
        if f_path.exists():
            found_file = f_path
            logger.info(f"Loading harmonized data from {f_path}")
            if f_path.suffix == '.csv':
                harmonized_data = pd.read_csv(f_path)
            elif f_path.suffix == '.parquet':
                harmonized_data = pd.read_parquet(f_path)
            elif f_path.suffix == '.pkl':
                import pickle
                with open(f_path, 'rb') as f:
                    harmonized_data = pickle.load(f)
            elif f_path.suffix == '.json':
                # Assuming it's a serialized dataset object or raw data
                import json
                with open(f_path, 'r') as f:
                    raw = json.load(f)
                    harmonized_data = pd.DataFrame(raw)
            break
    
    if harmonized_data is None:
        logger.error("Could not find harmonized dataset in processed directory.")
        # If no data, we assume 0 runs, which triggers bootstrap? Or maybe we should fail.
        # The task says "if fewer than three independent runs are detected".
        # If no data, we can't detect, so we might default to bootstrap or raise.
        # Let's assume 0 runs -> < 3 -> True.
        run_count = 0
        harmonized_data_obj = HarmonizedDataset(data=pd.DataFrame())
    else:
        # Wrap in HarmonizedDataset if it's a raw DataFrame
        if isinstance(harmonized_data, pd.DataFrame):
            harmonized_data_obj = HarmonizedDataset(data=harmonized_data)
        else:
            harmonized_data_obj = harmonized_data
        
        run_count = detect_independent_runs(harmonized_data_obj)
    
    # Logic: if runs < 3, set USE_BOOTSTRAP = True
    state_file = processed_dir / "state.json"
    use_bootstrap = run_count < 3
    
    logger.info(f"Detected {run_count} independent runs. USE_BOOTSTRAP flag: {use_bootstrap}")
    
    # Read existing state if it exists, otherwise start fresh
    state_data = {}
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                state_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read existing state file: {e}. Starting fresh.")
    
    # Update state
    state_data['USE_BOOTSTRAP'] = use_bootstrap
    state_data['detected_runs'] = run_count
    state_data['last_updated'] = str(pd.Timestamp.now())
    
    # Write atomically
    temp_file = state_file.with_suffix('.tmp')
    with open(temp_file, 'w') as f:
        json.dump(state_data, f, indent=2)
    
    temp_file.replace(state_file)
    
    logger.info(f"State updated at {state_file}")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
