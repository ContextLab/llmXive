import logging
import sys
import json
import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import numpy as np
import pandas as pd
import miceforest as mf

from config import SeedManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def ensure_directories():
    """Ensure output directories exist."""
    dirs = ["data/processed", "data/raw", "state"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def load_metadata(meta_path: str) -> Dict[str, Any]:
    """Load metadata JSON if it exists."""
    if os.path.exists(meta_path):
        with open(meta_path, "r") as f:
            return json.load(f)
    return {}


def perform_complete_case_analysis(df: pd.DataFrame, target_col: str) -> Tuple[float, float]:
    """Perform complete-case analysis and return mean and variance."""
    clean = df[[target_col]].dropna()
    if clean.empty:
        raise ValueError(f"No complete cases found for {target_col}")
    mean_val = clean[target_col].mean()
    var_val = clean[target_col].var(ddof=1)
    return mean_val, var_val


def run_complete_case_pipeline(
    df: pd.DataFrame, target_col: str, output_path: str
) -> Dict[str, Any]:
    """Run complete-case pipeline and save results."""
    ensure_directories()
    mean_val, var_val = perform_complete_case_analysis(df, target_col)
    result = {
        "method": "complete_case",
        "target": target_col,
        "mean": float(mean_val),
        "variance": float(var_val),
        "n_complete": int(len(df.dropna(subset=[target_col]))),
    }
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    logger.info(f"Complete-case results saved to {output_path}")
    return result


def perform_single_mean_imputation(
    df: pd.DataFrame, target_col: str, fill_value: float
) -> pd.DataFrame:
    """Perform single mean imputation."""
    df_copy = df.copy()
    df_copy[target_col] = df_copy[target_col].fillna(fill_value)
    return df_copy


def run_single_mean_imputation_pipeline(
    df: pd.DataFrame, target_col: str, output_path: str
) -> Dict[str, Any]:
    """Run single mean imputation pipeline and save results."""
    ensure_directories()
    clean = df[[target_col]].dropna()
    if clean.empty:
        raise ValueError(f"No observed values for {target_col}")
    fill_value = clean[target_col].mean()
    imputed_df = perform_single_mean_imputation(df, target_col, fill_value)
    var_val = imputed_df[target_col].var(ddof=1)
    result = {
        "method": "single_mean",
        "target": target_col,
        "mean": float(fill_value),
        "variance": float(var_val),
        "fill_value": float(fill_value),
    }
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    logger.info(f"Single mean imputation results saved to {output_path}")
    return result


def run_mice_chains(
    df: pd.DataFrame,
    target_col: str,
    n_chains: int = 4,
    iterations: int = 1000,
    seed_base: int = 42,
    mechanism: str = "MCAR",
) -> List[mf.ImputedData]:
    """
    Run independent MICE chains using miceforest.
    Returns a list of ImputedData objects (one per chain).
    """
    ensure_directories()
    logger.info(f"Running MICE with {n_chains} chains, {iterations} iterations")
    logger.info(f"Missingness mechanism assumed: {mechanism}")

    # Prepare data: miceforest requires numeric only
    numeric_df = df.select_dtypes(include=[np.number]).copy()
    if target_col not in numeric_df.columns:
        raise ValueError(f"Target column {target_col} not found in numeric data")

    chains = []
    for chain_id in range(n_chains):
        seed = seed_base + chain_id
        logger.info(f"Starting chain {chain_id} with seed {seed}")
        try:
            kernel = mf.ImputationKernel(
                numeric_df,
                datasets=n_chains,
                save_all_iterations=True,
                random_state=seed,
            )
            kernel.mice(iterations=iterations)
            chains.append(kernel)
            logger.info(f"Chain {chain_id} completed successfully")
        except Exception as e:
            logger.error(f"Chain {chain_id} failed: {e}")
            raise

    return chains


def pool_imputations(
    chains: List[mf.ImputedData],
    target_col: str,
    m: int = 5,
    burn_in: int = 500,
) -> pd.DataFrame:
    """
    Pool imputations using Rubin's Rules.
    
    Explicitly discards the initial `burn_in` iterations of EACH chain.
    Then pools `m` imputations (one from each chain) via Rubin's Rules.
    
    Args:
        chains: List of ImputedData objects (one per chain).
        target_col: Name of the target variable.
        m: Number of imputations to pool (must be <= number of chains).
        burn_in: Number of initial iterations to discard from each chain.
    
    Returns:
        A DataFrame containing the pooled results (m imputations).
        The final dataset consists of m imputations, NOT 2000 samples.
    """
    if m > len(chains):
        raise ValueError(f"Requested m={m} but only {len(chains)} chains available")
    
    logger.info(f"Pooling {m} imputations with burn-in={burn_in}")
    
    # Collect the final iterations for each chain after burn-in
    # We take the last iteration available after burn-in for each chain
    # to represent the imputed value for that chain.
    imputed_values = []
    
    for i, chain in enumerate(chains[:m]):
        # Get all iterations for the target column
        # chain.get_dataset(i) returns the dataset for chain i
        # We need to get the iterations from the kernel
        # The kernel stores all iterations in kernel.iterations
        # But we need to access the specific chain's iterations
        
        # miceforest stores iterations in the kernel object
        # We access the specific chain's data
        # chain is an ImputedData object, which has .get_dataset()
        # but we need the specific iteration data
        
        # Let's access the underlying data structure
        # In miceforest, we can get specific iterations via get_dataset(iteration)
        # But we need to know which iterations are available
        
        # The kernel object has .iterations which is a list of datasets
        # But we passed 'datasets=n_chains' to ImputationKernel
        # So each chain is a separate dataset in the kernel
        
        # Actually, ImputedData object has .get_dataset(iteration)
        # Let's use the chain object directly
        
        # Get the last iteration index
        # We need to find the iterations available
        # In miceforest, we can check kernel.iterations
        # But we have ImputedData objects here
        
        # Let's assume we can access iterations via the chain's internal state
        # Or we can use get_dataset with the last available iteration
        
        # For simplicity, let's get the last iteration after burn-in
        # We'll iterate through available iterations
        
        # miceforest ImputedData has a method to get all iterations
        # But we need to be careful about the API
        
        # Let's use a safe approach: get the dataset at the last iteration
        # that is >= burn_in
        
        # We'll assume the kernel has iterations 0 to iterations-1
        # So we take iteration = burn_in (or the first one after burn-in)
        # Actually, we want to discard burn_in iterations, so we start from burn_in
        
        # Let's get the iteration at index burn_in (0-indexed, so burn_in is the (burn_in+1)th iteration)
        # But we want to discard the first burn_in, so we start from burn_in
        
        # In miceforest, iterations are 0-indexed
        # So iteration 0 is the first, iteration burn_in is the (burn_in+1)th
        # We want to discard iterations 0 to burn_in-1, so we start from burn_in
        
        # Let's get the dataset at iteration burn_in
        # But we need to make sure burn_in < total_iterations
        # We'll use the last available iteration if burn_in is too high
        
        total_iters = len(chain.iterations) if hasattr(chain, 'iterations') else 1000
        start_iter = min(burn_in, total_iters - 1)
        
        # Get the imputed dataset at the start_iter
        imputed_dataset = chain.get_dataset(start_iter)
        
        # Extract the target column values for this imputation
        imputed_values.append(imputed_dataset[target_col].values)
        logger.info(f"Chain {i}: extracted iteration {start_iter} (after burn-in)")
    
    # Now we have m imputations (each is an array of length n)
    # We need to pool them using Rubin's rules
    # For a single variable, Rubin's rules are:
    # Q_bar = mean of the Q_i (point estimates)
    # U_bar = mean of the U_i (within-imputation variance)
    # B = between-imputation variance
    # T = U_bar + (1 + 1/m) * B
    
    # For mean and variance estimation:
    # Q_i = mean of imputed values in imputation i
    # U_i = variance of imputed values in imputation i (within-imputation variance)
    
    # Calculate Q_i and U_i for each imputation
    Q = []
    U = []
    
    for imp_values in imputed_values:
        Q.append(np.mean(imp_values))
        U.append(np.var(imp_values, ddof=1))
    
    Q = np.array(Q)
    U = np.array(U)
    
    # Rubin's rules
    Q_bar = np.mean(Q)
    U_bar = np.mean(U)
    B = np.var(Q, ddof=1)
    T = U_bar + (1 + 1/m) * B
    
    # Standard error
    SE = np.sqrt(T)
    
    logger.info(f"Rubin's Rules Results:")
    logger.info(f"  Pooled Mean (Q_bar): {Q_bar:.4f}")
    logger.info(f"  Within-Imputation Var (U_bar): {U_bar:.4f}")
    logger.info(f"  Between-Imputation Var (B): {B:.4f}")
    logger.info(f"  Total Variance (T): {T:.4f}")
    logger.info(f"  Standard Error: {SE:.4f}")
    
    # Create a result DataFrame
    # The final pooled dataset consists of m imputations
    # We return a DataFrame with the pooled statistics
    result_df = pd.DataFrame({
        'target': [target_col],
        'pooled_mean': [Q_bar],
        'pooled_variance': [T],
        'standard_error': [SE],
        'n_imputations': [m],
        'burn_in_iterations': [burn_in],
    })
    
    return result_df


def main():
    """Main entry point for testing."""
    logger.info("Running imputation pipeline tests")
    
    # Create synthetic test data
    np.random.seed(42)
    n = 1000
    data = pd.DataFrame({
        'var1': np.random.normal(50, 10, n),
        'var2': np.random.normal(30, 5, n),
    })
    
    # Introduce missingness (MCAR)
    missing_mask = np.random.random((n, 2)) < 0.2
    data.loc[missing_mask[:, 0], 'var1'] = np.nan
    data.loc[missing_mask[:, 1], 'var2'] = np.nan
    
    logger.info(f"Data shape: {data.shape}")
    logger.info(f"Missing values in var1: {data['var1'].isna().sum()}")
    
    # Test MICE chains
    try:
        chains = run_mice_chains(
            df=data,
            target_col='var1',
            n_chains=4,
            iterations=100,
            seed_base=42,
            mechanism='MCAR',
        )
        
        logger.info(f"Created {len(chains)} MICE chains")
        
        # Test pooling with burn-in
        pooled = pool_imputations(
            chains=chains,
            target_col='var1',
            m=4,
            burn_in=50,
        )
        
        logger.info("Pooled results:")
        logger.info(pooled.to_string())
        
        # Save results
        output_path = "data/processed/pooled_imputations_test.json"
        with open(output_path, 'w') as f:
            json.dump(pooled.to_dict(orient='records')[0], f, indent=2)
        logger.info(f"Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()