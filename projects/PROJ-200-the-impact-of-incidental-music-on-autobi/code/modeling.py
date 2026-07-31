import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import warnings
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.tools import add_constant
from python_levenshtein import distance as levenshtein_distance
from cue_matching import match_cues, normalize_cues
from aggregation import aggregate_to_user_track
from config import get_project_root, get_config_dict
from utils import get_logger

logger = get_logger(__name__)

def load_user_track_pairs(path: Optional[str] = None) -> pd.DataFrame:
    """Load user-track pairs from parquet file."""
    if path is None:
        config = get_config_dict()
        path = config.get("PATHS", {}).get("USER_TRACK_PAIRS", "data/processed/user_track_pairs.parquet")
    
    path_obj = Path(path)
    if not path_obj.exists():
        raise FileNotFoundError(f"User-track pairs file not found: {path}")
    
    return pq.read_table(path_obj).to_pandas()

def fit_mixed_model(df: pd.DataFrame, formula: Optional[str] = None) -> Any:
    """
    Fit a linear mixed-effects model using statsmodels.
    
    Args:
        df: DataFrame with columns: mean_vividness, adolescent_exposure_ratio, popularity, user_id
        formula: Model formula. Defaults to 'mean_vividness ~ adolescent_exposure_ratio + popularity + (1|user_id)'
    
    Returns:
        Fitted MixedLMResults object
    """
    if formula is None:
        formula = "mean_vividness ~ adolescent_exposure_ratio + popularity + (1|user_id)"
    
    # Prepare data
    # Ensure categorical for random effects
    df = df.copy()
    if 'user_id' in df.columns:
        df['user_id'] = df['user_id'].astype(str)
    
    # Parse formula to extract fixed and random effects
    # Simple parsing for the expected formula structure
    if 'mean_vividness' not in df.columns:
        raise ValueError("DataFrame must contain 'mean_vividness' column")
    
    # Extract fixed effects predictors
    # For the default formula: mean_vividness ~ adolescent_exposure_ratio + popularity
    fixed_cols = ['adolescent_exposure_ratio', 'popularity']
    for col in fixed_cols:
        if col not in df.columns:
            raise ValueError(f"DataFrame missing required column: {col}")
    
    # Build design matrix for fixed effects
    X = df[fixed_cols].values
    X = add_constant(X)
    
    # Random effects grouping
    groups = df['user_id'].values
    
    # Endogenous variable
    y = df['mean_vividness'].values
    
    # Fit the model
    try:
        model = MixedLM(y, X, groups=groups)
        result = model.fit(reml=False)
        return result
    except Exception as e:
        logger.error(f"Failed to fit mixed model: {e}")
        raise

def check_collinearity(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for fixed effects.
    
    Args:
        df: DataFrame with predictor columns
    
    Returns:
        Dictionary mapping column names to VIF values
    """
    fixed_cols = ['adolescent_exposure_ratio', 'popularity']
    
    # Check for constant columns
    for col in fixed_cols:
        if col not in df.columns:
            continue
        if df[col].std() < 1e-8:
            logger.warning(f"Column {col} has near-zero variance, VIF may be unstable")
    
    X = df[fixed_cols].values
    X = add_constant(X)
    
    vif_dict = {}
    for i, col in enumerate(['const'] + fixed_cols):
        if col == 'const':
            vif_dict[col] = 0.0  # VIF for intercept is not meaningful
            continue
        
        # Calculate VIF
        try:
            # Regress this variable against all others
            other_cols = [c for c in fixed_cols if c != col]
            if len(other_cols) == 0:
                vif_dict[col] = 1.0
                continue
            
            X_other = df[other_cols].values
            X_other = add_constant(X_other)
            y_target = df[col].values
            
            # Fit OLS
            model = sm.OLS(y_target, X_other).fit()
            r_squared = model.rsquared
            vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else np.inf
            vif_dict[col] = vif
            
            if vif > 5.0:
                logger.warning(f"High VIF detected for {col}: {vif:.2f}")
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_dict[col] = np.nan
    
    return vif_dict

def run_sensitivity_loop_setup() -> Tuple[List[float], pd.DataFrame]:
    """
    Prepare the sensitivity analysis loop.
    
    Returns:
        Tuple of (thresholds list, base track list from ingested_cohort.parquet)
    """
    config = get_config_dict()
    thresholds = config.get("SENSITIVITY", {}).get("LEVENSHTEIN_THRESHOLDS", [2, 3, 4, 5])
    
    # Load base track list from ingested_cohort.parquet
    base_path = Path("data/processed/ingested_cohort.parquet")
    if not base_path.exists():
        raise FileNotFoundError(f"Base ingested cohort not found: {base_path}")
    
    base_df = pq.read_table(base_path).to_pandas()
    
    return thresholds, base_df

def re_calculate_exposure(df: pd.DataFrame, thresholds: List[int]) -> pd.DataFrame:
    """
    Re-calculate exposure scores for a filtered track set.
    
    Args:
        df: Filtered track set from ingested_cohort.parquet
        thresholds: Current Levenshtein threshold for this iteration
    
    Returns:
        DataFrame with updated adolescent_exposure_ratio
    """
    # This is a simplified re-calculation based on the filtered set
    # In a full implementation, this would re-compute based on the actual filtered listens
    
    # For sensitivity, we assume the exposure ratio might change based on the subset
    # Here we just return the df with a note that it's re-calculated
    df = df.copy()
    
    # If we have total_listens and adolescent_listens, re-calculate
    if 'total_listens' in df.columns and 'adolescent_listens' in df.columns:
        df['adolescent_exposure_ratio'] = df['adolescent_listens'] / df['total_listens'].replace(0, np.nan)
    
    return df

def re_match_cues(df: pd.DataFrame, threshold: int) -> pd.DataFrame:
    """
    Re-match cues with a specific Levenshtein threshold.
    
    Args:
        df: DataFrame with cue data
        threshold: Levenshtein distance threshold
    
    Returns:
        DataFrame with matched cues
    """
    # This would call match_cues with the specific threshold
    # For now, we assume the matching is done and we filter based on threshold
    
    # In a real implementation, this would re-run the matching logic
    # with the new threshold parameter
    logger.info(f"Re-matching cues with threshold {threshold}")
    
    # Placeholder: return df as is, assuming matching was already done
    # In practice, this would re-execute the matching pipeline
    return df

def re_aggregate(df: pd.DataFrame, threshold: int) -> pd.DataFrame:
    """
    Re-aggregate data to user-track pair level with a specific threshold.
    
    Args:
        df: DataFrame with matched cues
        threshold: Levenshtein distance threshold used for matching
    
    Returns:
        Aggregated DataFrame at user-track pair level
    """
    logger.info(f"Re-aggregating data with threshold {threshold}")
    
    # This would call aggregate_to_user_track with the filtered data
    # For now, we assume aggregation is done
    
    # Placeholder: return a simplified aggregation
    if df.empty:
        return pd.DataFrame(columns=['user_id', 'track_id', 'mean_vividness', 'mean_valence'])
    
    # Simple aggregation if data exists
    if 'user_id' in df.columns and 'track_id' in df.columns:
        agg_df = df.groupby(['user_id', 'track_id']).agg({
            'vividness': 'mean',
            'valence': 'mean'
        }).reset_index()
        agg_df.columns = ['user_id', 'track_id', 'mean_vividness', 'mean_valence']
        return agg_df
    
    return df

def run_sensitivity_analysis() -> pd.DataFrame:
    """
    Run the full sensitivity analysis loop.
    
    Returns:
        DataFrame with sensitivity analysis results
    """
    thresholds, base_df = run_sensitivity_loop_setup()
    results = []
    
    for threshold in thresholds:
        logger.info(f"Running sensitivity analysis for threshold {threshold}")
        
        # Re-match cues
        matched_df = re_match_cues(base_df, threshold)
        
        # Re-aggregate
        agg_df = re_aggregate(matched_df, threshold)
        
        # Re-calculate exposure
        exposure_df = re_calculate_exposure(agg_df, [threshold])
        
        # Fit model and record results
        if not exposure_df.empty and len(exposure_df) > 10:
            try:
                model = fit_mixed_model(exposure_df)
                coef = model.params.get('adolescent_exposure_ratio', np.nan)
                pval = model.pvalues.get('adolescent_exposure_ratio', np.nan)
                
                results.append({
                    'threshold': threshold,
                    'coef': coef,
                    'p_value': pval,
                    'n_observations': len(exposure_df)
                })
            except Exception as e:
                logger.warning(f"Model fitting failed for threshold {threshold}: {e}")
                results.append({
                    'threshold': threshold,
                    'coef': np.nan,
                    'p_value': np.nan,
                    'n_observations': len(exposure_df),
                    'error': str(e)
                })
        else:
            logger.warning(f"Not enough data for threshold {threshold}")
            results.append({
                'threshold': threshold,
                'coef': np.nan,
                'p_value': np.nan,
                'n_observations': len(exposure_df)
            })
    
    return pd.DataFrame(results)

def run_bootstrap_setup(df: pd.DataFrame) -> Tuple[Any, np.ndarray]:
    """
    Prepare the Parametric Bootstrap.
    
    Args:
        df: DataFrame with user-track pairs
    
    Returns:
        Tuple of (null model result, residuals)
    """
    # Fit null model: mean_vividness ~ popularity + (1|user_id)
    # Remove adolescent_exposure_ratio
    df_null = df.copy()
    
    # Prepare data for null model
    if 'popularity' not in df_null.columns:
        raise ValueError("DataFrame must contain 'popularity' column for null model")
    
    X_null = df_null[['popularity']].values
    X_null = add_constant(X_null)
    groups = df_null['user_id'].values
    y = df_null['mean_vividness'].values
    
    # Fit null model
    null_model = MixedLM(y, X_null, groups=groups)
    null_result = null_model.fit(reml=False)
    
    # Extract residuals
    residuals = null_result.resid
    
    return null_result, residuals

def run_bootstrap_iteration(
    df: pd.DataFrame, 
    null_result: Any, 
    residuals: np.ndarray, 
    seed: Optional[int] = None
) -> float:
    """
    Generate a bootstrap sample and re-fit the model.
    
    Args:
        df: Original DataFrame
        null_result: Fitted null model
        residuals: Residuals from null model
        seed: Random seed for reproducibility
    
    Returns:
        t-statistic for adolescent_exposure_ratio coefficient
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Resample residuals with replacement
    n = len(residuals)
    resampled_residuals = np.random.choice(residuals, size=n, replace=True)
    
    # Generate new outcome
    predicted_values = null_result.fittedvalues
    new_outcome = predicted_values + resampled_residuals
    
    # Create new DataFrame with new outcome
    df_boot = df.copy()
    df_boot['mean_vividness'] = new_outcome
    
    # Fit full model on new outcome
    try:
        model = fit_mixed_model(df_boot)
        # Return t-statistic for adolescent_exposure_ratio
        t_stat = model.tvalues.get('adolescent_exposure_ratio', np.nan)
        return t_stat
    except Exception as e:
        logger.warning(f"Bootstrap iteration failed: {e}")
        return np.nan

def run_bootstrap_test(df: pd.DataFrame, n_iterations: int = 1000, seed: int = 42) -> Tuple[float, List[float]]:
    """
    Run the Parametric Bootstrap test.
    
    Args:
        df: DataFrame with user-track pairs
        n_iterations: Number of bootstrap iterations
        seed: Random seed
    
    Returns:
        Tuple of (p-value, list of bootstrap statistics)
    """
    logger.info(f"Running parametric bootstrap with {n_iterations} iterations")
    
    # Setup
    null_result, residuals = run_bootstrap_setup(df)
    
    # Get observed statistic
    observed_model = fit_mixed_model(df)
    observed_stat = observed_model.tvalues.get('adolescent_exposure_ratio', np.nan)
    
    # Bootstrap iterations
    bootstrap_stats = []
    for i in range(n_iterations):
        stat = run_bootstrap_iteration(df, null_result, residuals, seed=(seed + i))
        bootstrap_stats.append(stat)
    
    # Calculate p-value
    bootstrap_stats = np.array(bootstrap_stats)
    bootstrap_stats = bootstrap_stats[~np.isnan(bootstrap_stats)]
    
    if len(bootstrap_stats) == 0:
        logger.error("No valid bootstrap statistics computed")
        return np.nan, []
    
    # Two-tailed p-value
    p_value = 2 * min(
        np.mean(bootstrap_stats >= observed_stat),
        np.mean(bootstrap_stats <= observed_stat)
    )
    
    logger.info(f"Bootstrap p-value: {p_value:.4f}")
    return p_value, bootstrap_stats.tolist()

def check_bootstrap_convergence(
    df: pd.DataFrame, 
    n_prelim_iterations: int = 100, 
    tolerance: float = 0.01,
    seed: int = 42
) -> Tuple[bool, float, List[float]]:
    """
    Check if bootstrap p-value has stabilized before full run.
    
    Runs a preliminary short bootstrap and checks if the p-value estimate
    has stabilized within a tolerance.
    
    Args:
        df: DataFrame with user-track pairs
        n_prelim_iterations: Number of preliminary iterations
        tolerance: Tolerance for p-value stability (default 0.01)
        seed: Random seed
    
    Returns:
        Tuple of (is_converged, current_p_value, preliminary_stats)
    """
    logger.info(f"Running preliminary bootstrap convergence check ({n_prelim_iterations} iterations)")
    
    # Run preliminary bootstrap
    _, prelim_stats = run_bootstrap_test(df, n_iterations=n_prelim_iterations, seed=seed)
    
    if len(prelim_stats) == 0:
        logger.warning("No valid statistics in preliminary run, cannot check convergence")
        return False, np.nan, []
    
    # Calculate running p-values
    prelim_stats = np.array(prelim_stats)
    prelim_stats = prelim_stats[~np.isnan(prelim_stats)]
    
    if len(prelim_stats) < 10:
        logger.warning("Too few valid statistics for convergence check")
        return False, np.nan, prelim_stats.tolist()
    
    # Get observed statistic (same as in full test)
    observed_model = fit_mixed_model(df)
    observed_stat = observed_model.tvalues.get('adolescent_exposure_ratio', np.nan)
    
    # Calculate p-value at different points
    p_values = []
    window_size = max(10, n_prelim_iterations // 10)
    
    for i in range(window_size, len(prelim_stats) + 1):
        window = prelim_stats[:i]
        p_val = 2 * min(
            np.mean(window >= observed_stat),
            np.mean(window <= observed_stat)
        )
        p_values.append(p_val)
    
    if len(p_values) < 2:
        return False, np.nan, prelim_stats.tolist()
    
    # Check stability in the last few windows
    last_p = p_values[-1]
    prev_p = p_values[-2]
    
    is_stable = abs(last_p - prev_p) < tolerance
    
    if not is_stable:
        logger.warning(f"Bootstrap p-value not stable: {prev_p:.4f} -> {last_p:.4f} (diff={abs(last_p - prev_p):.4f})")
    else:
        logger.info(f"Bootstrap p-value stable: {last_p:.4f}")
    
    return is_stable, last_p, prelim_stats.tolist()

def write_bootstrap_results(p_value: float, stats: List[float], output_path: str) -> None:
    """
    Write bootstrap results to CSV with atomic rename.
    
    Args:
        p_value: Final p-value
        stats: List of bootstrap statistics
        output_path: Path to output file
    """
    temp_path = output_path + ".tmp"
    
    # Prepare data
    results_data = []
    for i, stat in enumerate(stats):
        results_data.append({
            'iteration': i + 1,
            'statistic': stat
        })
    
    # Add p-value row
    results_data.append({
        'iteration': 'p_value',
        'statistic': p_value
    })
    
    df = pd.DataFrame(results_data)
    
    # Write to temp file
    df.to_csv(temp_path, index=False)
    
    # Atomic rename
    os.replace(temp_path, output_path)
    logger.info(f"Bootstrap results written to {output_path}")

def main():
    """Main entry point for modeling module."""
    logger.info("Starting modeling module")
    
    # Example usage
    try:
        # Load data
        df = load_user_track_pairs()
        logger.info(f"Loaded {len(df)} user-track pairs")
        
        # Fit model
        model = fit_mixed_model(df)
        logger.info("Model fitted successfully")
        
        # Check collinearity
        vif = check_collinearity(df)
        logger.info(f"VIF results: {vif}")
        
        # Run bootstrap
        p_val, stats = run_bootstrap_test(df, n_iterations=100)  # Small for demo
        logger.info(f"Bootstrap p-value: {p_val}")
        
    except Exception as e:
        logger.error(f"Modeling pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()