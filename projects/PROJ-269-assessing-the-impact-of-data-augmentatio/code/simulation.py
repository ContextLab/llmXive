import os
import json
import logging
import argparse
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats

# Import from sibling modules as per API surface
from subsample import detect_target_column, create_stratified_subsample

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
SCHEMA_PATH = Path("contracts/simulation_schema.json")
RAW_DATA_DIR = Path("data/raw")
DERIVED_DATA_DIR = Path("data/derived")
RESULTS_DIR = Path("results")

def validate_schema() -> bool:
    """Validate that the simulation schema exists and is valid JSON."""
    if not SCHEMA_PATH.exists():
        logger.error(f"Schema file not found: {SCHEMA_PATH}")
        return False
    try:
        with open(SCHEMA_PATH, 'r') as f:
            json.load(f)
        logger.info("Schema validation successful.")
        return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in schema file: {e}")
        return False

def load_dataset(dataset_name: str) -> pd.DataFrame:
    """Load a dataset from the raw data directory."""
    file_path = RAW_DATA_DIR / f"{dataset_name}.csv"
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    logger.info(f"Loading dataset: {file_path}")
    return pd.read_csv(file_path)

def generate_type_i_condition(df: pd.DataFrame, target_col: str, seed: int, sample_size: int) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Generate data for Type I error (Null Hypothesis is True).
    Logic: Shuffle labels (permutation) to break any association while preserving distribution.
    """
    rng = np.random.default_rng(seed)
    # Stratified subsample first to maintain class balance in the small sample
    sub_df = create_stratified_subsample(df, target_col, sample_size, rng)
    
    # Permute labels
    original_labels = sub_df[target_col].values
    permuted_labels = rng.permutation(original_labels)
    
    # Return features and permuted labels
    features = sub_df.drop(columns=[target_col])
    return features, pd.Series(permuted_labels, index=sub_df.index)

def generate_type_ii_condition(df: pd.DataFrame, target_col: str, seed: int, sample_size: int, effect_size: float = 0.5) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Generate data for Type II error (Alternative Hypothesis is True).
    Logic: Apply a mean shift to features of one class to induce a detectable difference (Cohen's d).
    """
    rng = np.random.default_rng(seed)
    # Stratified subsample
    sub_df = create_stratified_subsample(df, target_col, sample_size, rng)
    
    features = sub_df.drop(columns=[target_col]).values
    labels = sub_df[target_col].values
    
    # Identify class 1 (assuming binary classification for this study)
    # If labels are not 0/1, map them. Usually UCI datasets are 0/1 or 1/2.
    unique_labels = np.unique(labels)
    if len(unique_labels) != 2:
        raise ValueError(f"Type II simulation expects binary classification, found {len(unique_labels)} classes.")
    
    class_1_mask = labels == unique_labels[1]
    class_0_mask = labels == unique_labels[0]
    
    # Calculate standard deviation for normalization (Cohen's d logic)
    # Use pooled std dev approximation from the sample
    std_0 = np.std(features[class_0_mask], axis=0)
    std_1 = np.std(features[class_1_mask], axis=0)
    # Avoid division by zero
    std_pooled = np.sqrt((std_0**2 + std_1**2) / 2)
    std_pooled[std_pooled == 0] = 1e-5 # Small epsilon to prevent div by zero
    
    # Shift mean of class 1 by effect_size * std
    shift = effect_size * std_pooled
    shifted_features = features.copy()
    shifted_features[class_1_mask] += shift
    
    return pd.DataFrame(shifted_features, columns=sub_df.drop(columns=[target_col]).columns), pd.Series(labels, index=sub_df.index)

def run_hypothesis_test(X: pd.DataFrame, y: pd.Series) -> float:
    """
    Run a two-sample t-test (Mann-Whitney U if non-parametric assumption needed, 
    but t-test is standard for power analysis unless specified otherwise).
    Returns the p-value.
    """
    unique_y = np.unique(y)
    if len(unique_y) != 2:
        # Fallback or error? For power analysis, we expect binary.
        # If not binary, we can't do a simple 2-sample t-test.
        logger.warning("Non-binary target in hypothesis test. Skipping.")
        return 1.0
    
    group_0 = X[y == unique_y[0]].values
    group_1 = X[y == unique_y[1]].values
    
    # Flatten if multi-dimensional (though t-test usually on 1D or per-feature)
    # For multivariate data, we often use a multivariate test or univariate per feature + correction.
    # Given the context of "Statistical Power in Small Samples" with UCI data, 
    # a common approach is to test each feature and aggregate, or use a global test.
    # However, standard power analysis for classification often implies testing the classifier's performance.
    # But the task asks for "p-value distributions".
    # Let's assume a univariate approach on the first feature or a multivariate test if available.
    # To be robust and simple for the "Monte Carlo loop" described in FR-004:
    # We will perform a t-test on the first feature for simplicity, OR
    # better: perform a multivariate test if possible, but scipy doesn't have a simple one.
    # Alternative: Use a permutation test on a simple statistic (e.g., difference in means of first feature).
    # Given the constraints and typical "baseline" tasks, let's use the t-test on the first feature 
    # as a proxy for the "signal" in the data, or average p-values if multiple features.
    # Actually, a more standard approach for "hypothesis test" in this context without a classifier is 
    # testing if the means of the groups are different across features.
    # Let's stick to a simple univariate test on the first feature to generate a p-value for the loop.
    # This is a simplification required by the lack of a specified classifier in T013.
    
    # If the dataset has multiple features, we might want to aggregate.
    # For now, let's test the first feature.
    if X.shape[1] > 0:
        x0 = group_0[:, 0]
        x1 = group_1[:, 0]
        t_stat, p_val = stats.ttest_ind(x0, x1, equal_var=False) # Welch's t-test
        return p_val
    else:
        return 1.0

def run_simulation_iteration(df: pd.DataFrame, target_col: str, sample_size: int, 
                             condition: str, seed: int) -> float:
    """
    Run a single iteration of the simulation.
    condition: 'null' (Type I) or 'alt' (Type II)
    """
    if condition == 'null':
        X, y = generate_type_i_condition(df, target_col, seed, sample_size)
    elif condition == 'alt':
        X, y = generate_type_ii_condition(df, target_col, seed, sample_size)
    else:
        raise ValueError(f"Unknown condition: {condition}")
    
    p_val = run_hypothesis_test(X, y)
    return p_val

def run_full_simulation(dataset_name: str, sample_sizes: List[int], 
                        iterations: int = 1000, base_seed: int = 42) -> Dict[str, Any]:
    """
    Run the full Monte Carlo simulation for a dataset and sample sizes.
    """
    if not validate_schema():
        raise RuntimeError("Schema validation failed. Cannot proceed.")
    
    logger.info(f"Starting simulation for dataset: {dataset_name}")
    df = load_dataset(dataset_name)
    target_col = detect_target_column(df)
    logger.info(f"Detected target column: {target_col}")
    
    results = {
        "dataset": dataset_name,
        "sample_sizes": {},
        "metadata": {
            "iterations": iterations,
            "base_seed": base_seed,
            "target_column": target_col,
            "disclaimer": "DISCLAIMER: Findings are associational and do not imply causation."
        }
    }
    
    for size in sample_sizes:
        logger.info(f"Running simulation for sample size N={size}")
        null_p_values = []
        alt_p_values = []
        
        # Null condition (Type I)
        for i in range(iterations):
            seed = base_seed + i
            p_val = run_simulation_iteration(df, target_col, size, 'null', seed)
            null_p_values.append(p_val)
        
        # Alt condition (Type II)
        for i in range(iterations):
            seed = base_seed + iterations + i
            p_val = run_simulation_iteration(df, target_col, size, 'alt', seed)
            alt_p_values.append(p_val)
        
        results["sample_sizes"][str(size)] = {
            "null_p_values": null_p_values,
            "alt_p_values": alt_p_values
        }
    
    return results

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save simulation results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Run baseline Monte Carlo simulation.")
    parser.add_argument("--dataset", type=str, required=True, help="Name of the dataset (without extension)")
    parser.add_argument("--sizes", type=int, nargs="+", default=[15, 25, 40], help="Sample sizes to test")
    parser.add_argument("--iterations", type=int, default=1000, help="Number of iterations per config")
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")
    parser.add_argument("--output", type=str, default=None, help="Output file path (optional)")
    
    args = parser.parse_args()
    
    results = run_full_simulation(args.dataset, args.sizes, args.iterations, args.seed)
    
    if args.output:
        save_results(results, Path(args.output))
    else:
        # Default naming convention based on task requirements
        dataset_slug = args.dataset.lower().replace('-', '_')
        for size in args.sizes:
            # We need to split results per size for the specific file naming convention
            # But run_full_simulation returns all sizes. 
            # Let's save the full run or split it. The task says "Save baseline results to..."
            # We will save the full results object, or we can split here.
            # The task T015 (later) specifies file naming. T013 is just the loop.
            # Let's save the full result to a single file for this dataset.
            pass
        
        # For T013, we just ensure the loop runs and produces data.
        # We'll save to a generic path if not specified, or let the caller handle it.
        # To be safe and follow "Produce real outputs", we'll save to a default location.
        default_path = RESULTS_DIR / f"{dataset_slug}_baseline_full.json"
        save_results(results, default_path)

if __name__ == "__main__":
    main()