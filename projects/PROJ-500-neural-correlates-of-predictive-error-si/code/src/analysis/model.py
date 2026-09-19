"""
Statistical Modeling Module for Neural Correlates of Predictive Error Signals.

Implements Gaussian Linear Mixed-Effects (LME) modeling to analyze the relationship
between MMN amplitude, accuracy, and learning phase.

Model Specification: MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject)
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

from src.utils.logging import get_logger, log_event, log_error
from src.utils.env_config import get_env_config

# Initialize logger
logger = get_logger(__name__)

# Constants
RESULTS_DIR = Path("code/analysis/results")
DATA_DIR = Path("code/data")

def load_aligned_data(filepath: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """
    Load the aligned dataset from CSV.
    
    Args:
        filepath: Path to the aligned_data.csv file. Defaults to code/data/aligned_data.csv.
        
    Returns:
        DataFrame containing the aligned data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    if filepath is None:
        filepath = DATA_DIR / "aligned_data.csv"
    else:
        filepath = Path(filepath)
        
    logger.info(f"Loading aligned data from {filepath}")
    
    if not filepath.exists():
        logger.error(f"Aligned data file not found: {filepath}")
        raise FileNotFoundError(f"Aligned data file not found: {filepath}")
        
    df = pd.read_csv(filepath)
    
    if df.empty:
        logger.error("Aligned data file is empty.")
        raise ValueError("Aligned data file is empty.")
        
    required_columns = ['subject_id', 'block_id', 'mmn_amplitude', 'accuracy', 'learning_phase']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} rows from aligned data.")
    return df

def fit_lme_model(
    df: pd.DataFrame,
    formula: str = "mmn_amplitude ~ accuracy + learning_phase + (1|subject_id)",
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fit a Gaussian Linear Mixed-Effects model to the data.
    
    Args:
        df: DataFrame containing the aligned data.
        formula: Model formula in R-style syntax (using patsy/statsmodels).
        random_state: Random seed for reproducibility.
        
    Returns:
        Dictionary containing model results (coefficients, p-values, etc.).
    """
    logger.info(f"Fitting LME model with formula: {formula}")
    
    # Ensure learning_phase is treated as categorical
    df['learning_phase'] = df['learning_phase'].astype('category')
    df['subject_id'] = df['subject_id'].astype('category')
    
    # Handle missing values
    df_clean = df.dropna(subset=['mmn_amplitude', 'accuracy', 'learning_phase'])
    
    if len(df_clean) == 0:
        logger.error("No valid data points remaining after dropping NaNs.")
        raise ValueError("No valid data points remaining after dropping NaNs.")
        
    if len(df_clean) < len(df):
        logger.warning(f"Dropped {len(df) - len(df_clean)} rows with missing values.")
        
    # Fit the model using MixedLM (statsmodels)
    # Note: statsmodels MixedLM uses a different syntax than lme4 in R.
    # We need to parse the formula or use a simpler approach.
    # For the formula "y ~ x1 + x2 + (1|group)", we use:
    # endog = y, exog = [x1, x2], groups = group
    
    # Parse formula components manually for statsmodels compatibility
    # Expected format: "mmn_amplitude ~ accuracy + learning_phase + (1|subject_id)"
    parts = formula.split('~')
    if len(parts) != 2:
        raise ValueError(f"Invalid formula format: {formula}")
        
    lhs = parts[0].strip()
    rhs = parts[1].strip()
    
    # Extract random effects group
    if "(1|" in rhs:
        # Extract group name from (1|subject_id)
        group_part = rhs.split("+ (1|")[1].split(")")[0]
        rhs_fixed = rhs.replace(f" + (1|{group_part})", "")
        group_col = group_part
    else:
        rhs_fixed = rhs
        group_col = None
        
    # Build design matrix for fixed effects
    # Use patsy to create design matrices if available, otherwise manual
    try:
        import patsy
        y, X = patsy.dmatrices(f"{lhs} ~ {rhs_fixed}", data=df_clean, return_type='dataframe')
    except ImportError:
        logger.warning("patsy not found, using manual design matrix construction.")
        # Fallback: create dummy variables manually
        # This is a simplified approach; patsy is preferred.
        formula_simple = f"{lhs} ~ {rhs_fixed}"
        y, X = patsy.dmatrices(formula_simple, data=df_clean, return_type='dataframe')
        
    # Fit the model
    if group_col:
        # Mixed Linear Model
        model = sm.MixedLM(y, X, groups=df_clean[group_col])
        result = model.fit(reml=False) # Use ML for fixed effects inference
    else:
        # OLS if no random effects
        model = sm.OLS(y, X)
        result = model.fit()
        
    # Extract results
    coefficients = result.params.to_dict()
    p_values = result.pvalues.to_dict()
    std_errors = result.bse.to_dict()
    
    # Log results
    log_event("model_fit_complete", {
        "num_observations": len(df_clean),
        "num_groups": df_clean[group_col].nunique() if group_col else 1,
        "converged": result.converged,
        "log_likelihood": result.llf
    })
    
    logger.info(f"Model fit complete. Converged: {result.converged}")
    
    return {
        "coefficients": coefficients,
        "p_values": p_values,
        "std_errors": std_errors,
        "log_likelihood": result.llf,
        "converged": result.converged,
        "num_observations": len(df_clean),
        "num_groups": df_clean[group_col].nunique() if group_col else 1
    }

def apply_fdr_correction(p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, float]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        p_values: Dictionary of p-values.
        alpha: Significance level.
        
    Returns:
        Dictionary of FDR-corrected p-values.
    """
    logger.info(f"Applying FDR correction with alpha={alpha}")
    
    # Filter out non-numeric or NaN p-values
    valid_p_values = {k: v for k, v in p_values.items() if isinstance(v, (int, float)) and not np.isnan(v)}
    
    if not valid_p_values:
        logger.warning("No valid p-values to correct.")
        return {}
        
    names = list(valid_p_values.keys())
    raw_pvals = list(valid_p_values.values())
    
    # Apply BH correction
    rejected, corrected_pvals, _, _ = multipletests(raw_pvals, alpha=alpha, method='fdr_bh')
    
    fdr_p_values = {name: pval for name, pval in zip(names, corrected_pvals)}
    
    logger.info(f"FDR correction complete. {sum(rejected)} hypotheses rejected.")
    
    return fdr_p_values

def run_permutation_test(
    df: pd.DataFrame,
    formula: str = "mmn_amplitude ~ accuracy + learning_phase + (1|subject_id)",
    n_permutations: int = 1000,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run a permutation test to assess the significance of the main effect of accuracy.
    
    Args:
        df: DataFrame containing the aligned data.
        formula: Model formula.
        n_permutations: Number of permutations.
        random_state: Random seed.
        
    Returns:
        Dictionary containing permutation test results.
    """
    logger.info(f"Running permutation test with n={n_permutations}")
    
    if random_state is not None:
        np.random.seed(random_state)
        
    # Prepare data
    df_clean = df.dropna(subset=['mmn_amplitude', 'accuracy', 'learning_phase'])
    if len(df_clean) < 10:
        logger.error("Insufficient data for permutation test.")
        raise ValueError("Insufficient data for permutation test.")
        
    # Fit original model to get observed statistic
    # We will use the t-statistic for the 'accuracy' coefficient
    try:
        import patsy
        y, X = patsy.dmatrices(f"mmn_amplitude ~ accuracy + learning_phase", data=df_clean, return_type='dataframe')
        group = df_clean['subject_id'].values
    except ImportError:
        raise ImportError("patsy is required for permutation test.")
        
    # Fit original model
    model_orig = sm.MixedLM(y, X, groups=group)
    result_orig = model_orig.fit(reml=False)
    obs_stat = result_orig.tvalues['accuracy']
    
    # Permutation loop
    perm_stats = []
    for i in range(n_permutations):
        # Shuffle the predictor of interest (accuracy)
        df_perm = df_clean.copy()
        df_perm['accuracy'] = np.random.permutation(df_perm['accuracy'].values)
        
        y_perm, X_perm = patsy.dmatrices(f"mmn_amplitude ~ accuracy + learning_phase", data=df_perm, return_type='dataframe')
        
        try:
            model_perm = sm.MixedLM(y_perm, X_perm, groups=df_perm['subject_id'].values)
            result_perm = model_perm.fit(reml=False)
            perm_stats.append(result_perm.tvalues['accuracy'])
        except Exception as e:
            # If model fails to converge, skip this permutation
            logger.debug(f"Permutation {i} failed: {e}")
            continue
            
    perm_stats = np.array(perm_stats)
    
    # Calculate p-value (two-tailed)
    p_value = np.mean(np.abs(perm_stats) >= np.abs(obs_stat))
    
    logger.info(f"Permutation test complete. Observed t={obs_stat:.4f}, p={p_value:.4f}")
    
    return {
        "observed_statistic": obs_stat,
        "p_value": p_value,
        "n_permutations": len(perm_stats),
        "null_distribution": perm_stats.tolist()
    }

def analyze_multiple_electrodes(
    df: pd.DataFrame,
    electrode_columns: List[str] = ['mmn_amplitude_cp3', 'mmn_amplitude_cp4', 'mmn_amplitude_c3', 'mmn_amplitude_c4'],
    formula: str = "mmn_amplitude ~ accuracy + learning_phase + (1|subject_id)"
) -> Dict[str, Dict[str, Any]]:
    """
    Analyze multiple electrode columns if present in the data.
    
    Args:
        df: DataFrame containing the aligned data.
        electrode_columns: List of column names for MMN amplitudes at different electrodes.
        formula: Model formula.
        
    Returns:
        Dictionary of results for each electrode.
    """
    results = {}
    
    # Check which electrode columns exist
    existing_cols = [col for col in electrode_columns if col in df.columns]
    
    if not existing_cols:
        logger.warning("No electrode columns found. Using default 'mmn_amplitude'.")
        # Fall back to single column analysis if specific electrodes not found
        if 'mmn_amplitude' in df.columns:
            results['mmn_amplitude'] = fit_lme_model(df, formula)
        else:
            logger.error("No MMN amplitude column found.")
            return results
    else:
        for col in existing_cols:
            logger.info(f"Analyzing electrode: {col}")
            # Create a temporary dataframe with the specific electrode column
            df_temp = df.copy()
            df_temp['mmn_amplitude'] = df_temp[col]
            
            try:
                res = fit_lme_model(df_temp, formula)
                res['electrode'] = col
                results[col] = res
            except Exception as e:
                logger.error(f"Failed to fit model for {col}: {e}")
                results[col] = {"error": str(e)}
                
    return results

def run_modeling_pipeline(
    data_path: Optional[Union[str, Path]] = None,
    output_path: Optional[Union[str, Path]] = None,
    n_permutations: int = 1000
) -> Dict[str, Any]:
    """
    Run the full modeling pipeline: load data, fit LME, apply FDR, run permutation test.
    
    Args:
        data_path: Path to aligned_data.csv.
        output_path: Path to save results JSON.
        n_permutations: Number of permutations for the permutation test.
        
    Returns:
        Dictionary containing all results.
    """
    logger.info("Starting modeling pipeline.")
    
    # Load data
    df = load_aligned_data(data_path)
    
    # Fit LME model
    lme_results = fit_lme_model(df)
    
    # Apply FDR correction
    fdr_p_values = apply_fdr_correction(lme_results['p_values'])
    lme_results['fdr_p_values'] = fdr_p_values
    
    # Run permutation test
    perm_results = run_permutation_test(df, n_permutations=n_permutations)
    
    # Compile final results
    final_results = {
        "model_type": "Gaussian LME",
        "formula": "mmn_amplitude ~ accuracy + learning_phase + (1|subject_id)",
        "lme_results": lme_results,
        "permutation_test": perm_results,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    # Save results
    if output_path is None:
        output_path = RESULTS_DIR / "model_output.json"
    else:
        output_path = Path(output_path)
        
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to Python types for JSON serialization
    def convert_numpy_types(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(i) for i in obj]
        return obj
        
    final_results = convert_numpy_types(final_results)
    
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
        
    logger.info(f"Results saved to {output_path}")
    log_event("modeling_pipeline_complete", {"output_file": str(output_path)})
    
    return final_results

def main():
    """Main entry point for the modeling script."""
    logger.info("Running model.py as main script.")
    
    try:
        # Get paths from environment or use defaults
        config = get_env_config()
        data_path = config.get('DATA_DIR', 'code/data')
        if isinstance(data_path, Path):
            data_path = data_path / 'aligned_data.csv'
        else:
            data_path = Path(data_path) / 'aligned_data.csv'
            
        output_path = Path("code/analysis/results/model_output.json")
        
        results = run_modeling_pipeline(
            data_path=data_path,
            output_path=output_path,
            n_permutations=1000
        )
        
        print(f"Modeling pipeline completed successfully.")
        print(f"Results saved to: {output_path}")
        
    except Exception as e:
        log_error("model_main_error", str(e))
        logger.exception("Error in main:")
        raise

if __name__ == "__main__":
    main()