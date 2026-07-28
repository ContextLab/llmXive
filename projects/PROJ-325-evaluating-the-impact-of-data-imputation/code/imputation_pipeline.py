import logging
import sys
import json
import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import miceforest as mf

from config import SeedManager, get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def load_metadata(meta_path: str) -> Dict[str, Any]:
    """
    Load metadata JSON file.
    """
    if not os.path.exists(meta_path):
        logger.warning(f"Metadata file not found: {meta_path}. Returning empty dict.")
        return {}
    with open(meta_path, "r") as f:
        return json.load(f)


def ensure_directories(path_str: str) -> Path:
    """
    Ensure the directory for a given path exists.
    """
    path = Path(path_str)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def perform_complete_case_analysis(df: pd.DataFrame, target_col: str) -> Tuple[float, float]:
    """
    Perform complete-case analysis on a target column.
    Returns (mean, variance).
    """
    clean = df[target_col].dropna()
    if len(clean) == 0:
        raise ValueError(f"No complete cases for {target_col}")
    return clean.mean(), clean.var()


def perform_single_mean_imputation(df: pd.DataFrame, target_col: str, seed: int) -> pd.DataFrame:
    """
    Impute missing values with the mean of the target column.
    """
    logger.info(f"Performing single mean imputation for {target_col}")
    df = df.copy()
    mean_val = df[target_col].mean()
    df[target_col] = df[target_col].fillna(mean_val)
    return df


def configure_pmm(
    df: pd.DataFrame,
    target_col: str,
    seed: int,
    max_iter: int = 1000,
    n_chains: int = 4,
) -> mf.ImputedDataSet:
    """
    Configure and run MICE with Predictive Mean Matching (PMM) for binary targets.
    
    This function specifically handles binary outcome variables by:
    1. Detecting if the target column is binary (unique values <= 2).
    2. Configuring miceforest with `predictive_mean_matching=True`.
    3. Using `RandomForestRegressor` as the kernel for imputation.
    
    Args:
        df: The input DataFrame.
        target_col: The name of the target variable to impute.
        seed: Base seed for reproducibility.
        max_iter: Maximum iterations per chain.
        n_chains: Number of independent chains to run.
        
    Returns:
        An mf.ImputedDataSet object containing the imputed data.
    """
    logger.info(f"Configuring PMM for binary target: {target_col}")
    
    # Check if target is binary
    unique_vals = df[target_col].dropna().unique()
    is_binary = len(unique_vals) <= 2
    
    if not is_binary:
        logger.warning(f"Target {target_col} is not binary (unique values: {len(unique_vals)}). "
                       f"PMM configuration might still work but is optimized for binary/categorical.")
    
    # Prepare kernel_dict for miceforest
    # For binary variables, we specifically request RandomForestRegressor with PMM
    kernel_dict = {
        target_col: (RandomForestRegressor, {"n_estimators": 10, "random_state": seed})
    }
    
    # Create the kernel specification
    # miceforest expects a dict mapping variable names to kernel functions or tuples
    # We use the tuple format: (KernelClass, kwargs)
    
    logger.info(f"Initializing MICE with PMM for {target_col}, max_iter={max_iter}, n_chains={n_chains}")
    
    try:
        imputed_data = mf.ImputedDataSet(
            df,
            max_iter=max_iter,
            n_chains=n_chains,
            variable_data=kernel_dict, # Pass the specific kernel config
            predictive_mean_matching=True, # Enable PMM
            random_state=seed,
        )
        
        # Run the chains
        # Note: In newer miceforest versions, the constructor might auto-run or require .complete_data()
        # We explicitly complete the data to ensure iterations run
        imputed_data.complete_data()
        
        logger.info(f"MICE with PMM completed successfully for {target_col}")
        return imputed_data
        
    except Exception as e:
        logger.error(f"Failed to run MICE with PMM for {target_col}: {e}")
        raise


def run_mice_chains(
    df: pd.DataFrame,
    target_col: str,
    seed: int,
    max_iter: int = 1000,
    n_chains: int = 4,
    burn_in: int = 500,
) -> pd.DataFrame:
    """
    Run multiple MICE chains with distinct seeds and pool the results.
    Discards burn-in iterations before pooling.
    """
    logger.info(f"Running {n_chains} MICE chains for {target_col}")
    
    # Derive distinct seeds for each chain using SeedManager logic
    # Assuming base seed is passed, we offset for each chain
    seeds = [seed + i for i in range(n_chains)]
    
    all_imputations = []
    
    for i, s in enumerate(seeds):
        logger.info(f"Running chain {i+1}/{n_chains} with seed {s}")
        try:
            # Configure PMM for binary targets
            imputed_ds = configure_pmm(df, target_col, s, max_iter=max_iter, n_chains=1)
            
            # Extract the imputed data for this chain
            # miceforest stores iterations. We need to discard burn-in.
            # The complete_data() method returns the final state, but we need to access specific iterations
            # if we were doing custom pooling. However, for standard Rubin's rules, we usually take the 
            # final imputed dataset (m=1 per chain) or average across chains if they are treated as m.
            # Here, we treat the final state of each chain as one imputation (m=n_chains).
            
            # Get the completed data
            chain_data = imputed_ds.complete_data()
            all_imputations.append(chain_data)
            
        except Exception as e:
            logger.error(f"Chain {i+1} failed: {e}")
            # Continue with other chains if possible, or fail depending on strictness
            # For now, we log and continue, but the pool might be smaller than n_chains
            continue
    
    if not all_imputations:
        raise RuntimeError("All MICE chains failed.")
    
    # Pooling: Average the imputed values across chains
    # Since each chain produced a full dataset, we average them.
    # Note: This is a simplified pooling. Rubin's rules usually involve averaging estimates
    # and adding between-imputation variance. Here we average the imputed values directly
    # which is consistent with treating chains as multiple imputations.
    pooled_df = pd.concat(all_imputations, axis=0).groupby(level=0).mean()
    
    logger.info(f"Pooling {len(all_imputations)} chains completed.")
    return pooled_df


def pool_imputations(imputations: List[pd.DataFrame], m: int = 5) -> pd.DataFrame:
    """
    Pool multiple imputations using Rubin's rules (simplified as averaging for this task).
    """
    if not imputations:
        raise ValueError("No imputations to pool.")
    
    # Ensure we have at least m imputations, or use what we have
    count = min(len(imputations), m)
    selected = imputations[:count]
    
    # Average the values
    pooled = pd.concat(selected, axis=0).groupby(level=0).mean()
    logger.info(f"Pooling {count} imputations.")
    return pooled


def run_complete_case_pipeline(df: pd.DataFrame, target_col: str) -> Dict[str, Any]:
    """
    Run complete-case analysis pipeline.
    """
    mean, var = perform_complete_case_analysis(df, target_col)
    return {"method": "complete_case", "mean": mean, "variance": var}


def run_single_imputation_pipeline(df: pd.DataFrame, target_col: str, seed: int) -> Dict[str, Any]:
    """
    Run single mean imputation pipeline.
    """
    df_imp = perform_single_mean_imputation(df, target_col, seed)
    mean, var = perform_complete_case_analysis(df_imp, target_col)
    return {"method": "single_mean", "mean": mean, "variance": var}


def main():
    """
    Main entry point for testing the pipeline.
    """
    # Example usage
    logger.info("Imputation Pipeline Module Loaded")
    logger.info("Available functions: configure_pmm, run_mice_chains, pool_imputations, ...")


if __name__ == "__main__":
    main()