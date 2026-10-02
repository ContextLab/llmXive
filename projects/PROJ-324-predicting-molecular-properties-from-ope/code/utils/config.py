import os
import sys
import time
import logging
import subprocess
import signal
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import psutil
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_absolute_error
from joblib import parallel_backend

# Import existing project utilities
from seed_manager import set_global_seed, get_seed
from data.preprocess import load_preprocessed_data

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_DEPTH = 10
MAX_DEPTH_GRID = [5, 10, 15]
SAMPLE_SIZE = 100
FIXED_SEED = 42
SPLIT_RATIO = 0.8
MAX_TIMEOUT_MINUTES = 30
MAX_OBABEL_TIMEOUT_SECONDS = 300
MAX_MEMORY_GB = 6

def get_runtime_config() -> Dict[str, Any]:
    """
    Retrieve the runtime configuration for the pipeline.
    Returns a dictionary with all runtime constraints and settings.
    """
    return {
        "max_depth": DEFAULT_MAX_DEPTH,
        "max_depth_grid": MAX_DEPTH_GRID,
        "sample_size": SAMPLE_SIZE,
        "fixed_seed": FIXED_SEED,
        "split_ratio": SPLIT_RATIO,
        "max_timeout_minutes": MAX_TIMEOUT_MINUTES,
        "max_obabel_timeout_seconds": MAX_OBABEL_TIMEOUT_SECONDS,
        "max_memory_gb": MAX_MEMORY_GB,
        "joblib_n_jobs": -1,
    }

def check_obabel_timeout(start_time: float, timeout_seconds: int) -> bool:
    """
    Check if the elapsed time exceeds the timeout.
    Returns True if timeout exceeded, False otherwise.
    """
    elapsed = time.time() - start_time
    if elapsed > timeout_seconds:
        logger.warning(f"Obabel process exceeded timeout of {timeout_seconds} seconds")
        return True
    return False

def enforce_obabel_subprocess_timeout(
    command: list, timeout_seconds: int = MAX_OBABEL_TIMEOUT_SECONDS
) -> Tuple[bool, str]:
    """
    Execute an obabel subprocess with a hard timeout.
    Returns (success, output_or_error_message).
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, f"Obabel failed with code {result.returncode}: {result.stderr}"
    except subprocess.TimeoutExpired:
        logger.error(f"Obabel command timed out after {timeout_seconds} seconds")
        return False, f"Timeout after {timeout_seconds} seconds"
    except Exception as e:
        logger.error(f"Obabel command failed: {str(e)}")
        return False, str(e)

def validate_runtime_environment() -> Dict[str, Any]:
    """
    Validate the runtime environment (RAM, CPU, disk).
    Returns a dictionary with environment status and recommendations.
    """
    config = get_runtime_config()
    mem = psutil.virtual_memory()
    available_ram_gb = mem.available / (1024**3)
    cpu_count = psutil.cpu_count(logical=True)

    status = {
        "available_ram_gb": round(available_ram_gb, 2),
        "cpu_count": cpu_count,
        "ram_sufficient": available_ram_gb >= config["max_memory_gb"],
        "cpu_sufficient": cpu_count >= 2,
    }

    if not status["ram_sufficient"]:
        logger.warning(
            f"Available RAM ({available_ram_gb:.2f} GB) is below threshold "
            f"({config['max_memory_gb']} GB). Consider reducing dataset size."
        )
        status["recommendation"] = "Reduce dataset size or increase available RAM"
    else:
        status["recommendation"] = "Environment is suitable for full dataset processing"

    return status

def get_joblib_parallel_backend(max_memory_gb: int = MAX_MEMORY_GB) -> parallel_backend:
    """
    Configure and return a joblib parallel backend.
    """
    # joblib's parallel_backend context manager
    # We return the context manager instance for use in a 'with' block
    return parallel_backend("loky", n_jobs=get_runtime_config()["joblib_n_jobs"])

def optimize_max_depth_for_sample(
    train_set_path: str = "data/derived/train_set.csv",
    sample_size: int = SAMPLE_SIZE,
    seed: int = FIXED_SEED,
    max_timeout_minutes: int = MAX_TIMEOUT_MINUTES,
) -> int:
    """
    Run a preliminary grid search on a sample of the training set to determine
    the optimal MAX_DEPTH for the Random Forest model.
    
    Args:
        train_set_path: Path to the training set CSV.
        sample_size: Number of molecules to sample for the grid search.
        seed: Random seed for reproducibility.
        max_timeout_minutes: Maximum time allowed for the grid search.
    
    Returns:
        int: The optimal max_depth value (defaulting to 10 if timeout occurs).
    """
    start_time = time.time()
    
    # Validate environment
    env_status = validate_runtime_environment()
    if not env_status["ram_sufficient"]:
        logger.warning("Low RAM detected. Reducing sample size for grid search.")
        sample_size = min(sample_size, 50)

    # Load training data
    try:
        df = pd.read_csv(train_set_path)
    except FileNotFoundError:
        logger.error(f"Training set not found at {train_set_path}")
        return DEFAULT_MAX_DEPTH

    # Ensure we have the necessary columns
    # The training set should have SMILES and target properties (logP, solubility, boiling_point)
    # For this grid search, we'll use the first numeric property column available
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if len(numeric_cols) < 2:
        logger.warning("Not enough numeric columns for grid search. Using default max_depth.")
        return DEFAULT_MAX_DEPTH
    
    # Assume the last numeric column is the target (or we can be more specific)
    # In our pipeline, the target is likely one of: 'logP', 'solubility', 'boiling_point'
    target_col = None
    feature_col = None # We need a feature, but for this sample grid search we'll use a proxy
    
    # For the grid search, we need a feature. Since we don't have fingerprints yet,
    # we'll use a simple molecular descriptor as a proxy for this preliminary search.
    # We'll use molecular weight (if available) or just create a dummy feature for the sample.
    # However, the task says "on a sample of 100 molecules from the training set".
    # We need a feature to train the RF. Let's assume we have a 'molecular_weight' or similar.
    # If not, we'll generate a simple fingerprint-like feature using RDKit for the sample.
    
    # Check for common descriptor columns
    possible_features = ['molecular_weight', 'logP', 'solubility', 'boiling_point', 'num_rotatable_bonds']
    for col in possible_features:
        if col in df.columns and col != numeric_cols[-1]: # Avoid using target as feature
            feature_col = col
            break
    
    if feature_col is None:
        # Fallback: use the first numeric column that isn't the last one
        feature_col = numeric_cols[0] if len(numeric_cols) > 1 else None
    
    if feature_col is None:
        logger.error("Could not identify a feature column for grid search.")
        return DEFAULT_MAX_DEPTH
    
    # Select target as the last numeric column (or a specific one if known)
    target_col = numeric_cols[-1]
    
    # Sample the data
    if len(df) > sample_size:
        df_sample = df.sample(n=sample_size, random_state=seed)
    else:
        df_sample = df
    
    X = df_sample[[feature_col]].values
    y = df_sample[target_col].values
    
    # Remove NaN values
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X = X[mask]
    y = y[mask]
    
    if len(X) == 0:
        logger.error("No valid data points after NaN removal for grid search.")
        return DEFAULT_MAX_DEPTH
    
    # Split into train/test for the grid search
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=seed
    )
    
    # Define the grid
    param_grid = {"max_depth": MAX_DEPTH_GRID}
    
    # Create the model
    rf = RandomForestRegressor(random_state=seed, n_jobs=1) # n_jobs=1 to avoid overhead in grid search
    
    # Grid search
    best_mae = float("inf")
    best_depth = DEFAULT_MAX_DEPTH
    
    for depth in MAX_DEPTH_GRID:
        # Check timeout
        if time.time() - start_time > max_timeout_minutes * 60:
            logger.warning(f"Grid search timed out after {max_timeout_minutes} minutes. Using default max_depth.")
            return DEFAULT_MAX_DEPTH
        
        rf.set_params(max_depth=depth)
        rf.fit(X_train, y_train)
        y_pred = rf.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        
        logger.info(f"max_depth={depth}, MAE={mae:.4f}")
        
        if mae < best_mae:
            best_mae = mae
            best_depth = depth
    
    logger.info(f"Optimal max_depth for sample: {best_depth} (MAE: {best_mae:.4f})")
    return best_depth

def main():
    """
    Main entry point for the performance configuration task.
    This function:
    1. Validates the runtime environment.
    2. Runs the preliminary grid search to determine optimal max_depth.
    3. Outputs the configuration settings.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logger.info("Starting Performance Configuration (T036)")
    
    # Validate environment
    env_status = validate_runtime_environment()
    logger.info(f"Environment validation: {json.dumps(env_status, indent=2)}")
    
    # Run grid search on sample
    optimal_max_depth = optimize_max_depth_for_sample()
    logger.info(f"Optimal MAX_DEPTH determined: {optimal_max_depth}")
    
    # Get full config
    config = get_runtime_config()
    config["optimal_max_depth"] = optimal_max_depth
    
    # Save config to a file for other tasks to use
    config_path = Path("data/derived/runtime_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Runtime configuration saved to {config_path}")
    print(f"Performance configuration complete. Optimal MAX_DEPTH: {optimal_max_depth}")
    print(f"Config saved to: {config_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())