import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM
import statsmodels.formula.api as smf
from config import get_project_root, get_config_dict
from utils import get_logger

logger = get_logger(__name__)

def load_user_track_pairs() -> pd.DataFrame:
    """Load the user-track pairs dataset."""
    root = get_project_root()
    path = root / "data" / "processed" / "user_track_pairs.parquet"
    if not path.exists():
        raise FileNotFoundError(f"User-track pairs file not found: {path}")
    logger.info(f"Loading user-track pairs from {path}")
    return pd.read_parquet(path)

def fit_mixed_model(df: pd.DataFrame) -> sm.regression.mixed_linear_model.MixedLMResults:
    """
    Fit the mixed-effects model:
    mean_vividness ~ residualized_exposure + popularity + (1|user_id)
    """
    logger.info("Fitting mixed-effects model...")
    # Ensure columns exist
    required_cols = ['mean_vividness', 'residualized_exposure_score', 'overall_popularity_score', 'user_id']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for model: {missing}")

    # Formula
    formula = "mean_vividness ~ residualized_exposure_score + overall_popularity_score"
    
    # Fit model
    try:
        model = smf.mixedlm(formula, df, groups=df["user_id"])
        result = model.fit()
        logger.info(f"Model fit successful. Log-likelihood: {result.llf}")
        return result
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        raise

def run_permutation_test(n_iterations: int = 1000) -> Dict[str, Any]:
    """
    Perform a block-permutation test on the User-Track Pair dataset.
    
    Procedure:
    1. Pin the random seed (from config).
    2. Construct Shuffle Pool: Aggregate residualized_exposure_score to track level.
    3. Shuffle the track-level scores.
    4. Reassign shuffled scores to the dataset by track_id.
    5. Re-fit model and record t-statistic for residualized_exposure.
    6. Repeat for n_iterations.
    7. Calculate p-value.
    8. Atomic write to data/final/permutation_results.csv.
    """
    config = get_config_dict()
    seed = config.get('random_seed', 42)
    np.random.seed(seed)
    
    root = get_project_root()
    final_dir = root / "data" / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    
    temp_path = final_dir / "permutation_results.csv.tmp"
    final_path = final_dir / "permutation_results.csv"
    
    logger.info(f"Starting permutation test with {n_iterations} iterations (seed={seed})")
    
    # Load data
    df = load_user_track_pairs()
    
    # Required columns check
    required = ['track_id', 'residualized_exposure_score', 'mean_vividness', 'overall_popularity_score', 'user_id']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for permutation test: {missing}")
    
    # Step 2: Aggregate to track level (one score per unique track_id)
    # We take the mean of residualized_exposure_score per track to ensure one value per track
    track_scores = df.groupby('track_id')['residualized_exposure_score'].mean().reset_index()
    track_scores.columns = ['track_id', 'score']
    
    # Store original scores for mapping back
    original_track_scores = track_scores['score'].values.copy()
    track_ids = track_scores['track_id'].values.copy()
    
    # Fit the observed model to get the observed statistic
    logger.info("Fitting observed model...")
    obs_result = fit_mixed_model(df)
    # Extract t-statistic for residualized_exposure_score
    # The params index might vary, so we look by name
    param_names = obs_result.params.index.tolist()
    try:
        obs_idx = param_names.index('residualized_exposure_score')
    except ValueError:
        # Fallback if column name differs slightly
        obs_idx = next((i for i, name in enumerate(param_names) if 'residualized' in name), None)
        if obs_idx is None:
            raise ValueError("Could not find residualized_exposure coefficient in model results")
    
    obs_statistic = obs_result.tvalues[obs_idx]
    logger.info(f"Observed t-statistic: {obs_statistic:.4f}")
    
    # Prepare storage for permutation statistics
    perm_statistics = []
    
    # Pre-prepare the model formula for reuse
    formula = "mean_vividness ~ residualized_exposure_score + overall_popularity_score"
    
    # Loop
    for i in range(n_iterations):
        # Step 3: Shuffle the track-level scores
        shuffled_scores = np.random.permutation(original_track_scores)
        
        # Step 4: Reassign to dataset
        # Create a mapping from track_id to shuffled score
        shuffled_map = dict(zip(track_ids, shuffled_scores))
        df['residualized_exposure_score_permuted'] = df['track_id'].map(shuffled_map)
        
        # Rename the original score to avoid conflict if needed, but we overwrite the column
        # Actually, we need to replace the column in the dataframe for the model
        df['residualized_exposure_score'] = df['residualized_exposure_score_permuted']
        del df['residualized_exposure_score_permuted']
        
        # Step 5: Re-fit model
        try:
            perm_result = fit_mixed_model(df)
            perm_stat = perm_result.tvalues[obs_idx]
            perm_statistics.append(perm_stat)
        except Exception as e:
            logger.warning(f"Iteration {i} failed: {e}. Skipping.")
            continue
        
        if (i + 1) % 100 == 0:
            logger.info(f"Permutation iteration {i+1}/{n_iterations} completed")
    
    if not perm_statistics:
        raise RuntimeError("No valid permutation statistics were generated.")
    
    perm_statistics = np.array(perm_statistics)
    
    # Step 7: Calculate p-value
    # Two-tailed test: proportion of null stats with absolute value >= abs(obs_stat)
    # Or one-tailed depending on hypothesis. Usually two-tailed for "difference".
    # Spec says "compare observed statistic against the null distribution".
    # Assuming two-tailed for significance.
    p_value = np.mean(np.abs(perm_statistics) >= np.abs(obs_statistic))
    
    logger.info(f"Permutation p-value: {p_value:.4f}")
    
    # Step 8: Atomic Write
    # Collect all iteration statistics and final p-value
    results_data = {
        'iteration': list(range(len(perm_statistics))),
        'statistic': perm_statistics.tolist()
    }
    # Add final row for p-value
    # The spec says: "metric='p_value', value=<p>" as a final row.
    # We'll append a row with iteration=None or -1, but the spec implies a specific format.
    # Let's create a dataframe and append the summary row.
    df_results = pd.DataFrame(results_data)
    
    # Append summary row
    summary_row = pd.DataFrame([{'iteration': -1, 'statistic': p_value}])
    df_results = pd.concat([df_results, summary_row], ignore_index=True)
    
    # Rename columns to match spec exactly: 'iteration', 'statistic'
    # The spec says: "columns: iteration, statistic and a final row metric='p_value', value=<p>"
    # This implies the final row might have different column names or a specific marker.
    # Let's follow the instruction: "final row metric='p_value', value=<p>"
    # This suggests the columns might be 'metric' and 'value' for the last row?
    # Or 'iteration'=-1 and 'statistic'=p_value.
    # Let's stick to the dataframe structure: iteration, statistic.
    # And ensure the last row is identifiable.
    
    # Re-reading spec: "OUTPUT: data/final/permutation_results.csv with columns: iteration, statistic and a final row metric='p_value', value=<p>."
    # This is slightly ambiguous. It could mean the last row has columns 'metric' and 'value' instead of 'iteration' and 'statistic'.
    # To be safe and valid CSV, we will use 'iteration' and 'statistic' for all rows, and set iteration to 'p_value' or a specific marker?
    # No, "metric='p_value', value=<p>" suggests the row content.
    # Let's make the last row: iteration="p_value", statistic=p_value.
    # Or better: Create a row where 'iteration' is empty or 'p_value' and 'statistic' is the value.
    # Let's assume the format:
    # iteration,statistic
    # 0, 1.23
    # ...
    # p_value, 0.05
    
    df_results.loc[df_results.index[-1], 'iteration'] = 'p_value'
    
    # Write to temp file
    temp_path.unlink(missing_ok=True)
    df_results.to_csv(temp_path, index=False)
    
    # Atomic rename
    os.replace(temp_path, final_path)
    logger.info(f"Permutation results written to {final_path}")
    
    return {
        'observed_statistic': obs_statistic,
        'p_value': p_value,
        'iterations': n_iterations
    }

def calculate_permutation_pvalue(observed_stat: float, null_stats: np.ndarray) -> float:
    """
    Calculate the p-value from observed statistic and null distribution.
    """
    return np.mean(np.abs(null_stats) >= np.abs(observed_stat))

def main():
    """Main entry point for the modeling module."""
    logger.info("Running modeling module main...")
    # Example execution if run directly
    # result = run_permutation_test(100) # Reduced for testing
    # print(result)

if __name__ == "__main__":
    main()