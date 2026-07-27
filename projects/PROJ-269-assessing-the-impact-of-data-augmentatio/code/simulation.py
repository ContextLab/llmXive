import os
import json
import logging
import argparse
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from imblearn.over_sampling import SMOTE, RandomOverSampler

# Local imports based on API surface
from augment import inject_gaussian_noise, apply_smote, apply_random_oversampling, detect_zero_variance_columns
from subsample import detect_target_column

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SCHEMA_PATH = Path("contracts/simulation_schema.json")
RESULTS_DIR = Path("results")
RAW_DATA_DIR = Path("data/raw")
DERIVED_DATA_DIR = Path("data/derived")

def validate_schema():
    """Validates the existence and validity of the simulation schema."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    try:
        with open(SCHEMA_PATH, 'r') as f:
            json.load(f)
        logger.info("Schema validation successful.")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in schema: {e}")
        raise

def load_dataset(dataset_name: str) -> pd.DataFrame:
    """Loads a dataset from the raw data directory."""
    file_path = RAW_DATA_DIR / f"{dataset_name}.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    df = pd.read_csv(file_path)
    return df

def generate_type_i_condition(df: pd.DataFrame, seed: int) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Generates Type I condition (Null Hypothesis) by shuffling labels.
    Returns features and shuffled labels.
    """
    rng = np.random.default_rng(seed)
    target_col = detect_target_column(df)
    X = df.drop(columns=[target_col])
    y = df[target_col].values
    
    # Permute labels to break association
    y_shuffled = rng.permutation(y)
    return X, y_shuffled

def generate_type_ii_condition(df: pd.DataFrame, seed: int, effect_size: float = 0.5) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    Generates Type II condition (Alternative Hypothesis) by shifting means.
    Returns features and original labels (with shifted mean for one class).
    """
    rng = np.random.default_rng(seed)
    target_col = detect_target_column(df)
    X = df.drop(columns=[target_col]).values
    y = df[target_col].values
    
    # Identify minority class or class 1 for shift
    # Simple approach: shift mean of class 1 relative to class 0
    # Calculate global std for scaling
    std_dev = np.std(X)
    if std_dev == 0:
        std_dev = 1.0
        
    shift_amount = effect_size * std_dev
    
    # Create shifted X
    X_shifted = X.copy()
    # Shift samples where y == 1 (assuming binary)
    mask = (y == 1)
    if np.sum(mask) > 0:
        X_shifted[mask] += shift_amount
        
    return X_shifted, y

def run_hypothesis_test(X: np.ndarray, y: np.ndarray, seed: int) -> float:
    """
    Runs a hypothesis test (t-test or similar) and returns the p-value.
    For this simulation, we use a simple t-test on the first feature
    or a classifier-based permutation test if features are complex.
    Here we implement a simple t-test on the first feature for demonstration,
    or a classifier score if we want to be more robust.
    
    Given the context of "Statistical Power", a classifier-based approach
    is often more relevant for multivariate data. We will use a simple
    logistic regression or t-test on a summary statistic.
    
    Let's use a t-test on the first feature for simplicity and speed in Monte Carlo,
    as the task implies checking impact of augmentation on standard tests.
    """
    rng = np.random.default_rng(seed)
    
    # If X is 1D, reshape
    if X.ndim == 1:
        X = X.reshape(-1, 1)
        
    # Use first feature for t-test
    x0 = X[y == 0, 0]
    x1 = X[y == 1, 0]
    
    if len(x0) < 2 or len(x1) < 2:
        return 1.0 # Not enough data
        
    t_stat, p_val = stats.ttest_ind(x0, x1)
    return float(p_val)

def run_simulation_iteration(df: pd.DataFrame, config: Dict[str, Any], iteration_seed: int, 
                             augmentation_method: Optional[str] = None, 
                             noise_std: float = 0.0) -> Dict[str, Any]:
    """
    Runs a single iteration of the simulation.
    Handles both Null (Type I) and Alt (Type II) conditions.
    Handles augmentation if specified.
    """
    seed = iteration_seed
    condition_type = config.get('condition', 'type_i') # 'type_i' or 'type_ii'
    n_samples = config.get('n_samples', 25)
    
    # 1. Subsample (Stratified)
    target_col = detect_target_column(df)
    # Simple random subsample for iteration to save time, or stratified
    # Using stratified to maintain class balance as per T005 logic
    try:
        X_full = df.drop(columns=[target_col])
        y_full = df[target_col]
        
        if len(y_full.unique()) > 1:
            X_sub, y_sub = train_test_split(
                df, 
                test_size=1 - (n_samples / len(df)), 
                stratify=y_full, 
                random_state=seed
            )
        else:
            X_sub, y_sub = train_test_split(
                df, 
                test_size=1 - (n_samples / len(df)), 
                random_state=seed
            )
        
        # Ensure we have exactly n_samples if possible
        if len(X_sub) > n_samples:
            X_sub = X_sub.sample(n=n_samples, random_state=seed)
            y_sub = X_sub[target_col]
            X_sub = X_sub.drop(columns=[target_col])
        elif len(X_sub) < n_samples:
            # Not enough samples, skip or pad? Skip for now
            return None
            
    except ValueError as e:
        logger.warning(f"Subsampling failed: {e}")
        return None

    X = X_sub.values
    y = y_sub.values

    # 2. Generate Condition (Null or Alt)
    if condition_type == 'type_i':
        X_cond, y_cond = generate_type_i_condition(pd.concat([X_sub, y_sub], axis=1), seed)
    else:
        X_cond, y_cond = generate_type_ii_condition(pd.concat([X_sub, y_sub], axis=1), seed)

    # 3. Apply Augmentation (if requested)
    if augmentation_method:
        # Convert back to DataFrame for augment.py functions if needed
        # augment.py expects DataFrame or handles arrays? 
        # Looking at API: inject_gaussian_noise, apply_smote, apply_random_oversampling
        # They likely take DataFrame. Let's reconstruct.
        df_cond = pd.DataFrame(X_cond, columns=X_sub.columns)
        df_cond[target_col] = y_cond

        if augmentation_method == 'gaussian':
            df_aug, y_aug = inject_gaussian_noise(df_cond, target_col, std=noise_std, seed=seed)
        elif augmentation_method == 'smote':
            df_aug, y_aug = apply_smote(df_cond, target_col, seed=seed)
        elif augmentation_method == 'random_oversample':
            df_aug, y_aug = apply_random_oversampling(df_cond, target_col, seed=seed)
        else:
            raise ValueError(f"Unknown augmentation method: {augmentation_method}")
        
        X_final = df_aug.drop(columns=[target_col]).values
        y_final = df_aug[target_col].values
    else:
        X_final = X_cond
        y_final = y_cond

    # 4. Run Hypothesis Test
    p_val = run_hypothesis_test(X_final, y_final, seed)

    return {
        "iteration": seed,
        "p_value": p_val,
        "condition": condition_type,
        "augmentation": augmentation_method,
        "n_samples": n_samples,
        "dataset": config.get('dataset_name', 'unknown')
    }

def run_full_simulation(configs: List[Dict[str, Any]], iterations: int = 1000) -> List[Dict[str, Any]]:
    """
    Runs the full Monte Carlo simulation for a list of configurations.
    """
    all_results = []
    
    for config in configs:
        dataset_name = config['dataset_name']
        logger.info(f"Starting simulation for {dataset_name} with {config['condition']}")
        
        df = load_dataset(dataset_name)
        
        for i in range(iterations):
            # Generate a unique seed for this iteration
            iter_seed = config.get('base_seed', 42) + i
            
            # Determine augmentation method for this config
            aug_method = config.get('augmentation', None)
            noise_std = config.get('noise_std', 0.1)
            
            result = run_simulation_iteration(
                df, 
                config, 
                iter_seed, 
                augmentation_method=aug_method,
                noise_std=noise_std
            )
            
            if result:
                all_results.append(result)
                
        logger.info(f"Completed {dataset_name}. Total results: {len(all_results)}")
        
    return all_results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """Saves simulation results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run Monte Carlo Simulation for Augmentation Impact")
    parser.add_argument('--config', type=str, required=True, help='Path to config JSON')
    parser.add_argument('--iterations', type=int, default=1000, help='Number of iterations')
    parser.add_argument('--output', type=str, default='results/simulation_output.json', help='Output file path')
    args = parser.parse_args()

    # Validate schema
    validate_schema()

    # Load configs
    with open(args.config, 'r') as f:
        configs = json.load(f)

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Run simulation
    results = run_full_simulation(configs, iterations=args.iterations)

    # Save results
    save_results(results, args.output)

if __name__ == "__main__":
    main()