"""
Linear Mixed-Effects Models for Visual Search Analysis.

Implements primary analysis (continuous predictor) and exploratory analysis
(cluster-based strategy) with fallback logic for convergence issues.
"""
import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

# Try to import statsmodels, but allow graceful degradation if missing
try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    logging.warning("statsmodels not installed. LMM analysis will be skipped.")

from config import get_config
from utils.logging import get_logger

# --- Utility Functions ---

def get_logger_wrapper(name: str = __name__) -> logging.Logger:
    """Get a logger configured for this module."""
    return get_logger(name)

def load_processed_features(logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """
    Load the processed features dataset.
    
    Returns:
        pd.DataFrame: The features dataset.
        
    Raises:
        FileNotFoundError: If the features file does not exist.
    """
    config = get_config()
    features_path = config.get_path('data_processed') / 'features.csv'
    
    if logger:
        logger.info(f"Loading processed features from {features_path}")
    
    if not features_path.exists():
        raise FileNotFoundError(f"Processed features file not found at {features_path}. "
                              "Run feature extraction tasks first.")
    
    df = pd.read_csv(features_path)
    if logger:
        logger.info(f"Loaded {len(df)} records")
    return df

def fit_lmm_with_fallback(
    df: pd.DataFrame,
    outcome: str,
    predictor: str,
    subject_col: str = 'participant_id',
    max_iter: int = 500,
    logger: Optional[logging.Logger] = None
) -> Tuple[Any, bool, str]:
    """
    Fit a Linear Mixed-Effects Model with a fallback to OLS if convergence fails.
    
    Args:
        df: Input dataframe.
        outcome: Name of the outcome variable.
        predictor: Name of the fixed effect predictor.
        subject_col: Name of the subject identifier column.
        max_iter: Maximum iterations for optimization.
        logger: Logger instance.
        
    Returns:
        Tuple of (model_result, converged, message)
    """
    if not HAS_STATSMODELS:
        if logger:
            logger.error("statsmodels is required for LMM fitting.")
        return None, False, "statsmodels not installed"

    if logger:
        logger.info(f"Fitting LMM: {outcome} ~ {predictor} | ({subject_col})")

    # Prepare formula
    formula = f"{outcome} ~ {predictor} + (1|{subject_col})"
    
    # Try LMM first
    try:
        model = smf.mixedlm(formula, df, groups=df[subject_col])
        result = model.fit(maxiter=max_iter, disp=False)
        
        if result.converged:
            if logger:
                logger.info("LMM converged successfully.")
            return result, True, "LMM converged"
        else:
            if logger:
                logger.warning("LMM did not converge. Attempting OLS fallback.")
    except Exception as e:
        if logger:
            logger.warning(f"LMM fitting failed: {e}. Attempting OLS fallback.")
    
    # Fallback to OLS (Linear Regression)
    # Note: This ignores the random effect but provides a coefficient estimate
    if logger:
        logger.info("Fitting OLS fallback model.")
    
    try:
        # Prepare data for OLS
        y = df[outcome].dropna()
        X = df[[predictor]].dropna()
        
        # Ensure alignment
        common_idx = y.index.intersection(X.index)
        y = y.loc[common_idx]
        X = X.loc[common_idx]
        
        if len(X) == 0:
            raise ValueError("No valid data points after alignment")
            
        X = sm.add_constant(X)
        ols_model = sm.OLS(y, X)
        ols_result = ols_model.fit()
        
        if logger:
            logger.info("OLS fallback completed.")
        return ols_result, False, "LMM failed; OLS fallback used"
        
    except Exception as e:
        if logger:
            logger.error(f"OLS fallback also failed: {e}")
        return None, False, f"Both LMM and OLS failed: {e}"

def extract_results_table(result: Any, predictor_name: str = "predictor") -> pd.DataFrame:
    """
    Extract coefficients table from a fitted model result.
    
    Args:
        result: Fitted model result object.
        predictor_name: Name to use for the predictor in the table.
        
    Returns:
        pd.DataFrame: Table of coefficients.
    """
    if result is None:
        return pd.DataFrame()
        
    # Handle statsmodels results
    if hasattr(result, 'summary2') or hasattr(result, 'params'):
        df_summary = result.summary2().tables[1]
        # Convert to DataFrame if it's a numpy array or similar
        if not isinstance(df_summary, pd.DataFrame):
            df_summary = pd.DataFrame(df_summary)
        
        # Standardize column names if necessary
        # statsmodels summary2 tables often have index as variable names
        if isinstance(df_summary.index, pd.Index):
            df_summary.index.name = 'term'
            df_summary = df_summary.reset_index()
            
        # Ensure we have the right columns
        required_cols = ['term', 'coef', 'std err', 't', 'P>|t|']
        # Map common variations
        col_map = {}
        if 'coef' not in df_summary.columns:
            if 'Coef.' in df_summary.columns: col_map['Coef.'] = 'coef'
            if 'coef' in df_summary.columns: col_map['coef'] = 'coef'
        if 'std err' not in df_summary.columns:
            if 'Std Err' in df_summary.columns: col_map['Std Err'] = 'std err'
        if 't' not in df_summary.columns:
            if 't-value' in df_summary.columns: col_map['t-value'] = 't'
        if 'P>|t|' not in df_summary.columns:
            if 'P>|t|' in df_summary.columns: col_map['P>|t|'] = 'P>|t|'
            
        df_summary = df_summary.rename(columns=col_map)
        
        # Filter for the predictor of interest if needed, or return all
        # For this task, we return the full table for the model
        return df_summary
        
    return pd.DataFrame()

# --- Analysis Functions ---

def run_primary_analysis(
    df: pd.DataFrame,
    outcome: str = 'detection_time',
    predictor: str = 'fixation_ratio',
    output_path: Optional[Path] = None,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Run the primary analysis: LMM with continuous predictor.
    
    Args:
        df: Processed features dataframe.
        outcome: Outcome variable name.
        predictor: Continuous predictor name.
        output_path: Path to save results.
        logger: Logger instance.
        
    Returns:
        Dictionary with results summary.
    """
    if logger:
        logger.info("Starting Primary Analysis (Continuous Predictor)")
    
    result, converged, message = fit_lmm_with_fallback(
        df, outcome, predictor, logger=logger
    )
    
    if result is None:
        if logger:
            logger.error("Model fitting failed completely.")
        return {"success": False, "message": message}
    
    table = extract_results_table(result)
    
    # Save to CSV if path provided
    if output_path:
        table.to_csv(output_path, index=False)
        if logger:
            logger.info(f"Primary analysis results saved to {output_path}")
    
    return {
        "success": True,
        "converged": converged,
        "message": message,
        "results": table.to_dict('records') if not table.empty else []
    }

def run_exploratory_analysis(
    df: pd.DataFrame,
    outcome: str = 'detection_time',
    predictor: str = 'strategy_cluster',
    output_path: Optional[Path] = None,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Run the exploratory analysis: LMM with cluster label (Descriptive Only).
    
    WARNING: This is Exploratory/Descriptive Only and NOT for primary inference
    due to circularity risks per Plan.
    
    Args:
        df: Processed features dataframe.
        outcome: Outcome variable name.
        predictor: Cluster label column name.
        output_path: Path to save results.
        logger: Logger instance.
        
    Returns:
        Dictionary with results summary.
    """
    if logger:
        logger.warning("Starting Exploratory Analysis (Cluster Label). "
                     "WARNING: This is Descriptive Only. Not for primary inference.")
    
    # Check if predictor exists
    if predictor not in df.columns:
        if logger:
            logger.error(f"Predictor '{predictor}' not found in dataframe. "
                       "Available columns: {list(df.columns)}")
        return {"success": False, "message": f"Predictor '{predictor}' missing"}
    
    # Ensure predictor is treated as categorical if it's numeric but discrete
    # (optional, depends on statsmodels formula behavior)
    # In formula, we can use C() to force categorical treatment if needed
    formula_predictor = f"C({predictor})" if df[predictor].dtype in [np.int64, np.int32] else predictor
    
    result, converged, message = fit_lmm_with_fallback(
        df, outcome, formula_predictor, logger=logger
    )
    
    if result is None:
        if logger:
            logger.error("Exploratory model fitting failed completely.")
        return {"success": False, "message": message}
    
    table = extract_results_table(result)
    
    # Save to CSV if path provided
    if output_path:
        table.to_csv(output_path, index=False)
        if logger:
            logger.info(f"Exploratory analysis results saved to {output_path}")
    
    return {
        "success": True,
        "converged": converged,
        "message": message,
        "results": table.to_dict('records') if not table.empty else []
    }

def run_permutation_test(
    df: pd.DataFrame,
    outcome: str = 'detection_time',
    predictor: str = 'fixation_ratio',
    n_permutations: int = 1000,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Run a permutation test to establish null distribution.
    
    Args:
        df: Processed features dataframe.
        outcome: Outcome variable name.
        predictor: Predictor variable name.
        n_permutations: Number of permutations.
        logger: Logger instance.
        
    Returns:
        Dictionary with permutation test results.
    """
    if logger:
        logger.info(f"Running Permutation Test with {n_permutations} iterations")
    
    # Extract valid data
    valid_mask = df[outcome].notna() & df[predictor].notna()
    y = df.loc[valid_mask, outcome].values
    X = df.loc[valid_mask, predictor].values
    
    if len(X) == 0:
        return {"success": False, "message": "No valid data for permutation test"}
    
    # Fit original model to get observed statistic
    # Using simple OLS for permutation test statistic (slope)
    if HAS_STATSMODELS:
        X_sm = sm.add_constant(X)
        original_model = sm.OLS(y, X_sm).fit()
        observed_stat = original_model.params[1] # Slope
    else:
        # Fallback to numpy
        coeffs = np.polyfit(X, y, 1)
        observed_stat = coeffs[0]
    
    if logger:
        logger.info(f"Observed statistic: {observed_stat:.4f}")
    
    # Permutation loop
    perm_stats = []
    for i in range(n_permutations):
        np.random.shuffle(y) # Shuffle outcome
        
        if HAS_STATSMODELS:
            perm_model = sm.OLS(y, X_sm).fit()
            stat = perm_model.params[1]
        else:
            stat = np.polyfit(X, y, 1)[0]
        
        perm_stats.append(stat)
        
        if (i + 1) % 100 == 0 and logger:
            logger.debug(f"Permutation {i+1}/{n_permutations} completed")
    
    perm_stats = np.array(perm_stats)
    
    # Calculate p-value (two-tailed)
    p_value = np.mean(np.abs(perm_stats) >= np.abs(observed_stat))
    
    return {
        "success": True,
        "observed_statistic": float(observed_stat),
        "p_value": float(p_value),
        "n_permutations": n_permutations,
        "null_distribution_mean": float(np.mean(perm_stats)),
        "null_distribution_std": float(np.std(perm_stats))
    }

def main():
    """Main entry point for running analyses."""
    logger = get_logger(__name__)
    config = get_config()
    
    # Load data
    try:
        df = load_processed_features(logger)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Define output paths
    results_dir = config.get_path('results')
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Primary Analysis (Continuous)
    logger.info("--- Primary Analysis ---")
    primary_output = results_dir / 'lmm_continuous.csv'
    primary_results = run_primary_analysis(
        df, 
        outcome='detection_time', 
        predictor='fixation_ratio',
        output_path=primary_output,
        logger=logger
    )
    logger.info(f"Primary Analysis Status: {primary_results.get('message', 'Unknown')}")
    
    # 2. Exploratory Analysis (Cluster)
    logger.info("--- Exploratory Analysis ---")
    cluster_output = results_dir / 'lmm_cluster.csv'
    exploratory_results = run_exploratory_analysis(
        df,
        outcome='detection_time',
        predictor='strategy_cluster', # Expected column from T021/T023a
        output_path=cluster_output,
        logger=logger
    )
    logger.info(f"Exploratory Analysis Status: {exploratory_results.get('message', 'Unknown')}")
    
    # 3. Permutation Test
    logger.info("--- Permutation Test ---")
    perm_output = results_dir / 'permutation_test.json'
    perm_results = run_permutation_test(
        df,
        outcome='detection_time',
        predictor='fixation_ratio',
        n_permutations=1000,
        logger=logger
    )
    
    # Save permutation results
    with open(perm_output, 'w') as f:
        json.dump(perm_results, f, indent=2)
    logger.info(f"Permutation test results saved to {perm_output}")
    
    logger.info("Analysis pipeline completed.")

if __name__ == '__main__':
    main()