import os
import json
import logging
import warnings
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union

import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

from config.settings import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_data(file_path: str) -> pd.DataFrame:
    """Load processed data from a CSV file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {file_path}")
    return pd.read_csv(path)

def fit_beta_regression(
    df: pd.DataFrame,
    formula: str,
    data_col: str,
    offset_col: Optional[str] = None
) -> Any:
    """
    Fit a Beta regression model using statsmodels.
    Beta regression is suitable for bounded outcomes (0, 1).
    """
    # Ensure response is strictly in (0, 1) for Beta regression
    if data_col in df.columns:
        # Simple transformation to avoid 0 and 1 boundaries
        y = df[data_col]
        # Use a small epsilon to push values into (0, 1) if they are exactly 0 or 1
        epsilon = 1e-4
        y = y.clip(lower=epsilon, upper=1 - epsilon)
        df = df.copy()
        df[data_col] = y

    try:
        model = smf.glm(formula=formula, data=df, family=sm.families.Beta())
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Beta regression failed: {e}")
        raise

def fit_gamma_regression(
    df: pd.DataFrame,
    formula: str,
    data_col: str
) -> Any:
    """Fit a Gamma regression model for positive continuous outcomes."""
    try:
        model = smf.glm(formula=formula, data=df, family=sm.families.Gamma(link=sm.links.log()))
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"Gamma regression failed: {e}")
        raise

def fit_count_regression(
    df: pd.DataFrame,
    formula: str,
    data_col: str
) -> Any:
    """Fit a Poisson or Negative Binomial regression for count outcomes."""
    try:
        # Try Poisson first
        model = smf.glm(formula=formula, data=df, family=sm.families.Poisson())
        result = model.fit()
        return result
    except Exception as e:
        logger.warning(f"Poisson regression failed, trying Negative Binomial: {e}")
        try:
            # Negative Binomial requires statsmodels >= 0.13 or specific import
            # Using GLM with NegativeBinomial family
            model = smf.glm(formula=formula, data=df, family=sm.families.NegativeBinomial())
            result = model.fit()
            return result
        except Exception as e2:
            logger.error(f"Count regression failed completely: {e2}")
            raise

def fit_glmm_with_random_intercepts(
    df: pd.DataFrame,
    formula: str,
    data_col: str,
    random_group: str
) -> Any:
    """
    Fit a Generalized Linear Mixed Model with random intercepts.
    Uses statsmodels MixedLM for Gaussian outcomes or similar approximations.
    For non-Gaussian GLMMs, we might need specific handling or fallback.
    """
    try:
        # For simplicity in this pipeline, we use MixedLM for Gaussian-like outcomes
        # or GLM with cluster robust SEs as a fallback if MixedLM is too complex for the distribution.
        # Assuming the outcome is continuous for GLMM here as per typical decision quality metrics.
        # If the outcome is binary/count, we would need specific GLMM families which statsmodels supports
        # but often requires more setup.
        
        # Prepare data: ensure random_group is categorical
        df[random_group] = df[random_group].astype(str)
        
        # Fit MixedLM (Gaussian by default)
        # If the outcome is not Gaussian, this might need transformation or a different approach.
        # For this implementation, we assume the target variable has been transformed or is continuous.
        model = smf.mixedlm(formula=formula, data=df, groups=df[random_group])
        result = model.fit()
        return result
    except Exception as e:
        logger.error(f"GLMM fitting failed: {e}")
        # Fallback to GLM with robust SEs if MixedLM fails
        logger.warning("Falling back to GLM with robust standard errors.")
        try:
            model = smf.glm(formula=formula, data=df, family=sm.families.Gaussian())
            result = model.fit(cov_type='cluster', cov_kwds={'groups': df[random_group]})
            return result
        except Exception as e2:
            logger.error(f"Fallback GLM also failed: {e2}")
            raise

def run_wald_tests(
    model_result: Any,
    parameter_names: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Perform Wald tests on model parameters.
    Returns a DataFrame with coefficients, standard errors, z/t statistics, and p-values.
    """
    if parameter_names is None:
        # Default to all parameters except intercept if not specified
        parameter_names = list(model_result.params.index)
    
    results_data = []
    for param in parameter_names:
        if param in model_result.params.index:
            coef = model_result.params[param]
            se = model_result.bse[param]
            # z or t statistic
            stat = coef / se if se != 0 else 0
            # P-value (two-sided)
            pval = 2 * (1 - stats.norm.cdf(abs(stat))) # Approximation for large samples
            
            results_data.append({
                'parameter': param,
                'coefficient': coef,
                'std_error': se,
                'statistic': stat,
                'p_value': pval
            })
    
    return pd.DataFrame(results_data)

def apply_multiple_comparison_correction(
    p_values: List[float],
    method: str = 'fdr_bh'
) -> Tuple[List[float], List[bool]]:
    """
    Apply multiple comparison correction (Bonferroni or Benjamini-Hochberg FDR).
    Returns corrected p-values and rejection booleans.
    """
    if len(p_values) < 3:
        logger.warning("Fewer than 3 tests, skipping multiple comparison correction.")
        return p_values, [False] * len(p_values)
    
    try:
        reject, pvals_corrected, _, _ = multipletests(p_values, alpha=0.05, method=method)
        return pvals_corrected, reject
    except Exception as e:
        logger.error(f"Multiple comparison correction failed: {e}")
        return p_values, [False] * len(p_values)

def run_sensitivity_analysis(
    df: pd.DataFrame,
    agreement_cutoffs: List[float] = [0.5, 0.6, 0.7],
    entropy_thresholds: List[float] = [0.2, 0.4, 0.6]
) -> pd.DataFrame:
    """
    Run sensitivity analysis by sweeping agreement cutoff and entropy threshold.
    Computes correlation between contagion_index and agreement_proportion for each combination.
    Also computes FP and FN rates of Consensus vs Ground Truth.
    """
    results = []
    
    # Ensure required columns exist
    required_cols = ['contagion_index', 'agreement_proportion', 'entropy', 'external_validation_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns for sensitivity analysis: {missing}")
        return pd.DataFrame()

    for cutoff in agreement_cutoffs:
        for thresh in entropy_thresholds:
            # Filter based on thresholds (example logic: agreement_proportion >= cutoff AND entropy >= thresh)
            # Adjust logic based on specific definition of "Consensus" in the project
            subset = df[
                (df['agreement_proportion'] >= cutoff) & 
                (df['entropy'] >= thresh)
            ]
            
            if subset.empty:
                results.append({
                    'agreement_cutoff': cutoff,
                    'entropy_threshold': thresh,
                    'correlation_coefficient': np.nan,
                    'false_positive_rate': np.nan,
                    'false_negative_rate': np.nan
                })
                continue
            
            # Compute Pearson correlation
            corr_matrix = subset[['contagion_index', 'agreement_proportion']].corr()
            corr_val = corr_matrix.loc['contagion_index', 'agreement_proportion']
            
            # Compute FP and FN rates
            # Assuming external_validation_score is the ground truth (1=valid/solved, 0=not)
            # and some threshold on agreement_proportion defines "Consensus"
            # This logic depends on how "Consensus" is defined relative to ground truth.
            # Here we assume: Consensus = (agreement_proportion >= cutoff)
            # Ground Truth = (external_validation_score >= 0.5) or similar boolean conversion
            
            # Create boolean masks
            # Assuming external_validation_score is a probability or score where >0.5 is positive
            ground_truth_pos = subset['external_validation_score'] > 0.5
            consensus_pos = subset['agreement_proportion'] >= cutoff
            
            # Confusion matrix components
            tp = ((ground_truth_pos) & (consensus_pos)).sum()
            fp = ((~ground_truth_pos) & (consensus_pos)).sum()
            fn = ((ground_truth_pos) & (~consensus_pos)).sum()
            tn = ((~ground_truth_pos) & (~consensus_pos)).sum()
            
            fp_rate = fp / (fp + tn) if (fp + tn) > 0 else np.nan
            fn_rate = fn / (tp + fn) if (tp + fn) > 0 else np.nan
            
            results.append({
                'agreement_cutoff': cutoff,
                'entropy_threshold': thresh,
                'correlation_coefficient': corr_val,
                'false_positive_rate': fp_rate,
                'false_negative_rate': fn_rate
            })
    
    return pd.DataFrame(results)

def run_modeling_pipeline(
    input_file: str,
    output_file: str,
    model_specs: Optional[List[Dict[str, Any]]] = None
) -> pd.DataFrame:
    """
    Run the full modeling pipeline: fit models, run tests, apply corrections.
    """
    logger.info(f"Loading data from {input_file}")
    df = load_processed_data(input_file)
    
    if model_specs is None:
        # Default model specification
        model_specs = [
            {
                'type': 'beta',
                'formula': 'agreement_proportion ~ contagion_index + external_validation_score',
                'data_col': 'agreement_proportion'
            },
            {
                'type': 'gamma',
                'formula': 'time_to_decision ~ contagion_index + external_validation_score',
                'data_col': 'time_to_decision'
            }
        ]
    
    all_results = []
    
    for spec in model_specs:
        logger.info(f"Fitting {spec['type']} model: {spec['formula']}")
        try:
            if spec['type'] == 'beta':
                res = fit_beta_regression(df, spec['formula'], spec['data_col'])
            elif spec['type'] == 'gamma':
                res = fit_gamma_regression(df, spec['formula'], spec['data_col'])
            else:
                logger.warning(f"Unknown model type: {spec['type']}")
                continue
            
            # Run Wald tests
            wald_results = run_wald_tests(res)
            wald_results['model_type'] = spec['type']
            wald_results['formula'] = spec['formula']
            all_results.append(wald_results)
            
        except Exception as e:
            logger.error(f"Failed to fit {spec['type']} model: {e}")
            continue
    
    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        # Apply multiple comparison correction if needed
        # Group by model type or formula if necessary, here we apply globally for simplicity
        if len(final_df) >= 3:
            p_vals = final_df['p_value'].tolist()
            corrected_p, reject = apply_multiple_comparison_correction(p_vals)
            final_df['p_value_corrected'] = corrected_p
            final_df['significant'] = reject
        else:
            final_df['p_value_corrected'] = final_df['p_value']
            final_df['significant'] = final_df['p_value'] < 0.05
        
        final_df.to_csv(output_file, index=False)
        logger.info(f"Modeling results saved to {output_file}")
        return final_df
    else:
        logger.warning("No models were successfully fitted.")
        return pd.DataFrame()

def save_model_results(results_df: pd.DataFrame, output_path: str) -> None:
    """Save model results to a CSV file."""
    results_df.to_csv(output_path, index=False)
    logger.info(f"Model results saved to {output_path}")

def compute_external_validation_correlation(
    df: pd.DataFrame,
    metrics: List[str] = ['contagion_index', 'agreement_proportion', 'entropy', 'time_to_decision']
) -> pd.DataFrame:
    """
    Compute the correlation between the external validation score and various decision quality metrics.
    Output: DataFrame with columns [metric, correlation_coefficient, p_value].
    """
    results = []
    
    if 'external_validation_score' not in df.columns:
        logger.error("external_validation_score column not found in input data.")
        return pd.DataFrame()
    
    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric {metric} not found in data, skipping.")
            continue
        
        # Drop rows with NaN in either column
        valid_data = df[[metric, 'external_validation_score']].dropna()
        
        if len(valid_data) < 2:
            logger.warning(f"Not enough data points for {metric}, skipping correlation.")
            results.append({
                'metric': metric,
                'correlation_coefficient': np.nan,
                'p_value': np.nan
            })
            continue
        
        # Compute Pearson correlation
        corr, p_val = stats.pearsonr(
            valid_data['external_validation_score'], 
            valid_data[metric]
        )
        
        results.append({
            'metric': metric,
            'correlation_coefficient': corr,
            'p_value': p_val
        })
    
    return pd.DataFrame(results)

def main():
    """
    Main entry point for the modeling pipeline and correlation analysis.
    """
    config = get_config()
    processed_dir = Path(config.dataset_paths.processed_data_dir)
    
    # Define input/output paths
    # Assuming thread_metrics.csv contains contagion_index and other metrics
    # and valid_threads.csv contains external_validation_score
    # We need to merge them or ensure they are in one file.
    # For this task, we assume a merged file or that the required columns exist in one of them.
    # Let's assume we are reading from a merged file or the metrics file has been updated with external_validation_score.
    
    input_file = processed_dir / "thread_metrics.csv"
    if not input_file.exists():
        # Fallback to valid_threads.csv if thread_metrics doesn't exist, but we need to merge data
        # For simplicity in this task, we assume the data is prepared in a way that columns are available.
        # If not, we try to load valid_threads and merge with metrics if possible.
        logger.warning("thread_metrics.csv not found. Attempting to use valid_threads.csv.")
        input_file = processed_dir / "valid_threads.csv"
    
    output_file = processed_dir / "external_validation_correlation.csv"
    
    if not input_file.exists():
        logger.error(f"Input file {input_file} does not exist.")
        return
    
    logger.info(f"Running external validation correlation analysis on {input_file}")
    df = load_processed_data(str(input_file))
    
    # Ensure we have the necessary columns. If not, log and exit.
    required_cols = ['external_validation_score']
    if not all(c in df.columns for c in required_cols):
        logger.error(f"Missing required column 'external_validation_score' in {input_file}")
        return
    
    # Define metrics to correlate
    metrics_to_check = ['contagion_index', 'agreement_proportion', 'entropy', 'time_to_decision']
    
    # Run correlation analysis
    corr_results = compute_external_validation_correlation(df, metrics=metrics_to_check)
    
    if not corr_results.empty:
        corr_results.to_csv(output_file, index=False)
        logger.info(f"Correlation analysis results saved to {output_file}")
    else:
        logger.warning("No correlation results to save.")

if __name__ == "__main__":
    main()
