import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM
import matplotlib.pyplot as plt
import seaborn as sns

from config import get_project_root, get_config_dict
from utils import get_logger

logger = get_logger(__name__)

def load_user_track_pairs() -> pd.DataFrame:
    """
    Load the aggregated User-Track pairs dataset.
    
    Returns:
        pd.DataFrame: The user_track_pairs dataset
    """
    project_root = get_project_root()
    file_path = project_root / "data" / "processed" / "user_track_pairs.parquet"
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"User-Track pairs file not found at {file_path}. "
            "Please run the data ingestion and aggregation pipeline first."
        )
    
    df = pd.read_parquet(file_path)
    logger.info(f"Loaded {len(df)} User-Track pairs from {file_path}")
    return df

def fit_mixed_model(df: pd.DataFrame, outcome: str = "mean_vividness") -> Tuple[MixedLM, Dict[str, float]]:
    """
    Fit a linear mixed-effects model for the given outcome variable.
    
    Model formula: outcome ~ residualized_exposure_score + overall_popularity_score + (1|user_id)
    
    Args:
        df: User-Track pairs DataFrame
        outcome: The outcome variable to model (default: "mean_vividness")
        
    Returns:
        Tuple of (fitted model result, VIF dictionary)
    """
    # Prepare data
    data = df.copy()
    data = data.dropna(subset=[outcome, "residualized_exposure_score", "overall_popularity_score"])
    
    if len(data) == 0:
        raise ValueError("No valid data remaining after dropping NaNs for model fitting.")
    
    # Define formula
    formula = f"{outcome} ~ residualized_exposure_score + overall_popularity_score"
    groups = data["user_id"]
    
    # Fit model
    model = MixedLM.from_formula(formula, groups=groups, data=data)
    result = model.fit()
    
    # Calculate VIF for fixed effects
    vif_dict = {}
    X = sm.add_constant(data[["residualized_exposure_score", "overall_popularity_score"]])
    for col in X.columns:
        if col == "const":
            continue
        # VIF = 1 / (1 - R^2) where R^2 is from regressing this variable on others
        others = [c for c in X.columns if c != col and c != "const"]
        if len(others) > 0:
            r_squared = sm.OLS(X[col], sm.add_constant(X[others])).fit().rsquared
            vif = 1 / (1 - r_squared)
            vif_dict[col] = vif
        else:
            vif_dict[col] = 0.0
    
    logger.info(f"Fitted mixed model for {outcome}: {result.summary().tables[1].as_csv()}")
    return result, vif_dict

def run_permutation_test(df: pd.DataFrame, n_iterations: int = 1000, seed: int = 42) -> pd.DataFrame:
    """
    Perform a block-permutation test on the User-Track Pair dataset.
    
    Procedure:
    1. Pin the random seed.
    2. Shuffle the `residualized_exposure_score` values across the entire pool of unique `track_id`s.
    3. Apply this new mapping to the User-Track pairs.
    4. Ensure that the number of pairs per track remains constant.
    5. Re-fit the model and record the t-statistic for the `residualized_exposure` coefficient.
    6. Repeat for n_iterations.
    
    Args:
        df: User-Track pairs DataFrame
        n_iterations: Number of permutation iterations (default: 1000)
        seed: Random seed for reproducibility (default: 42)
        
    Returns:
        pd.DataFrame: Permutation results with columns: iteration, statistic
    """
    config = get_config_dict()
    seed = config.get("RANDOM_SEED", seed)
    np.random.seed(seed)
    
    # Calculate observed statistic first
    logger.info("Calculating observed statistic...")
    obs_result, _ = fit_mixed_model(df, "mean_vividness")
    observed_stat = obs_result.tvalues["residualized_exposure_score"]
    logger.info(f"Observed t-statistic: {observed_stat:.4f}")
    
    # Store permutation statistics
    permutation_stats = []
    
    # Get unique tracks and their counts
    unique_tracks = df["track_id"].unique()
    track_counts = df["track_id"].value_counts().to_dict()
    
    logger.info(f"Starting permutation test with {n_iterations} iterations...")
    
    for i in range(n_iterations):
        # Shuffle exposure scores across tracks
        # We need to shuffle the scores assigned to tracks, not the pairs themselves
        # This preserves the number of pairs per track
        
        # Get all exposure scores
        all_scores = df["residualized_exposure_score"].values.copy()
        
        # Shuffle the scores
        np.random.shuffle(all_scores)
        
        # Create a shuffled version of the dataframe
        shuffled_df = df.copy()
        shuffled_df["residualized_exposure_score"] = all_scores
        
        # Fit model on shuffled data
        try:
            perm_result, _ = fit_mixed_model(shuffled_df, "mean_vividness")
            perm_stat = perm_result.tvalues["residualized_exposure_score"]
            permutation_stats.append(perm_stat)
        except Exception as e:
            logger.warning(f"Permutation iteration {i} failed: {e}. Skipping.")
            permutation_stats.append(np.nan)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Completed {i + 1}/{n_iterations} iterations")
    
    # Create results DataFrame
    results_df = pd.DataFrame({
        "iteration": range(1, n_iterations + 1),
        "statistic": permutation_stats
    })
    
    # Add observed statistic as a marker
    results_df["observed"] = observed_stat
    
    logger.info(f"Permutation test completed. Mean null statistic: {np.nanmean(permutation_stats):.4f}")
    
    return results_df

def calculate_permutation_pvalue(permutation_results: pd.DataFrame, observed_statistic: float) -> float:
    """
    Calculate the permutation p-value by comparing the observed statistic against
    the null distribution of permuted statistics.
    
    Two-tailed test: p-value = (number of |permuted| >= |observed|) / (total permutations)
    
    Args:
        permutation_results: DataFrame with 'statistic' column from run_permutation_test
        observed_statistic: The t-statistic from the original (unpermuted) model
        
    Returns:
        float: The calculated p-value
    """
    # Get the null distribution statistics
    null_stats = permutation_results["statistic"].dropna().values
    
    if len(null_stats) == 0:
        raise ValueError("No valid permutation statistics found to calculate p-value.")
    
    # Calculate two-tailed p-value
    # Count how many null statistics are as or more extreme than the observed
    extreme_count = np.sum(np.abs(null_stats) >= np.abs(observed_statistic))
    p_value = extreme_count / len(null_stats)
    
    logger.info(f"Calculated p-value: {p_value:.6f} (extreme_count={extreme_count}, n={len(null_stats)})")
    
    return p_value

def main():
    """
    Main function to run the permutation test and calculate p-value.
    """
    logger.info("Starting permutation test and p-value calculation...")
    
    # Load data
    df = load_user_track_pairs()
    
    # Run permutation test
    perm_results = run_permutation_test(df, n_iterations=1000)
    
    # Calculate observed statistic
    obs_result, _ = fit_mixed_model(df, "mean_vividness")
    observed_stat = obs_result.tvalues["residualized_exposure_score"]
    
    # Calculate p-value
    p_value = calculate_permutation_pvalue(perm_results, observed_stat)
    
    # Add p-value to results
    perm_results["p_value"] = p_value
    
    # Save results
    project_root = get_project_root()
    output_path = project_root / "data" / "final" / "permutation_results.csv"
    perm_results.to_csv(output_path, index=False)
    
    logger.info(f"Saved permutation results to {output_path}")
    logger.info(f"Final p-value: {p_value:.6f}")
    
    return perm_results, p_value

if __name__ == "__main__":
    main()
