import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import random
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.generalized_estimating_equations import GEE
from statsmodels.genmod.cov_struct import Exchangeable
from statsmodels.discrete.discrete_model import NegativeBinomial
from statsmodels.tools import add_constant
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats
import argparse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DERIVED_DIR = DATA_DIR / "derived"
MASTER_DATASET_PATH = DERIVED_DIR / "master_dataset.csv"
ANALYSIS_RESULTS_PATH = DERIVED_DIR / "analysis_results.json"
SENSITIVITY_ANALYSIS_PATH = DERIVED_DIR / "sensitivity_analysis.json"
STRATIFIED_RESULTS_PATH = DERIVED_DIR / "stratified_results.json"

def load_master_dataset(seed: int = 42) -> pd.DataFrame:
    """
    Load the master dataset from the derived directory.
    
    Args:
        seed: Random seed for reproducibility (used if any sampling occurs)
        
    Returns:
        DataFrame containing the master dataset
        
    Raises:
        FileNotFoundError: If the master dataset does not exist
        ValueError: If required columns are missing
    """
    if not MASTER_DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Master dataset not found at {MASTER_DATASET_PATH}. "
            "Please run code/ingest.py first to generate the dataset."
        )
    
    df = pd.read_csv(MASTER_DATASET_PATH)
    
    # Validate required columns
    required_columns = [
        'repository_id', 'llm_adoption_flag', 'iteration_count',
        'avg_comment_length', 'review_thread_depth', 'revert_frequency',
        'loc', 'contributors', 'domain_complexity', 'diff_complexity_score',
        'ai_noise_flag'
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in master dataset: {missing_cols}"
        )
    
    # Convert flags to numeric
    df['llm_adoption_flag'] = df['llm_adoption_flag'].astype(int)
    df['ai_noise_flag'] = df['ai_noise_flag'].astype(int)
    
    # Set random seed for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataset by handling missing values and outliers.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    logger.info("Cleaning data...")
    
    # Drop rows with missing values in key columns
    key_cols = ['iteration_count', 'llm_adoption_flag', 'diff_complexity_score', 'loc']
    df_clean = df.dropna(subset=key_cols)
    
    # Handle infinite values
    df_clean = df_clean.replace([np.inf, -np.inf], np.nan)
    df_clean = df_clean.dropna(subset=key_cols)
    
    # Log cleaning results
    logger.info(f"Cleaned dataset: {len(df)} -> {len(df_clean)} rows")
    
    return df_clean

def calculate_vif(df: pd.DataFrame, features: list) -> pd.Series:
    """
    Calculate Variance Inflation Factor for each feature.
    
    Args:
        df: DataFrame containing features
        features: List of feature column names
        
    Returns:
        Series of VIF values indexed by feature name
    """
    # Add constant for intercept
    X = df[features].copy()
    X = add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(features):
        if col in df.columns:
            vif_data[col] = variance_inflation_factor(X.values, i + 1)  # +1 because of constant
    
    return pd.Series(vif_data)

def flag_high_vif(vif_series: pd.Series, threshold: float = 5.0) -> dict:
    """
    Flag features with VIF above threshold.
    
    Args:
        vif_series: Series of VIF values
        threshold: VIF threshold for flagging
        
    Returns:
        Dictionary with flag status and details
    """
    high_vif = vif_series[vif_series > threshold]
    return {
        'high_vif_features': high_vif.to_dict(),
        'count': len(high_vif),
        'threshold': threshold
    }

def run_glmm(df: pd.DataFrame) -> dict:
    """
    Run Mixed-Effects Model (GLMM) with random intercepts for repositories.
    
    Formula: iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity + (1|repository_id)
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        Dictionary with model results
    """
    logger.info("Running GLMM...")
    
    # Prepare features
    features = ['llm_adoption_flag', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity']
    X = df[features].copy()
    y = df['iteration_count'].copy()
    
    # Add constant
    X = add_constant(X)
    
    # Group by repository_id
    groups = df['repository_id']
    
    # Run GEE as approximation for GLMM (statsmodels doesn't have full GLMM support)
    # Using Gaussian family with log link for count data
    model = GEE(y, X, groups=groups, family=sm.families.Gaussian(), cov_struct=Exchangeable())
    result = model.fit()
    
    # Extract results
    coefficients = result.params.to_dict()
    standard_errors = result.bse.to_dict()
    p_values = result.pvalues.to_dict()
    
    # Calculate confidence intervals
    conf_int = result.conf_int()
    confidence_intervals = {}
    for i, col in enumerate(X.columns):
        confidence_intervals[col] = [conf_int.iloc[i, 0], conf_int.iloc[i, 1]]
    
    return {
        'model_type': 'GLMM (GEE approximation)',
        'formula': 'iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity + (1|repository_id)',
        'coefficients': coefficients,
        'standard_errors': standard_errors,
        'p_values': p_values,
        'confidence_intervals': confidence_intervals,
        'aic': result.aic,
        'bic': result.bic
    }

def run_zinb_model(df: pd.DataFrame) -> dict:
    """
    Run Zero-Inflated Negative Binomial model for zero-inflated outcomes.
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        Dictionary with model results
    """
    logger.info("Running ZINB model...")
    
    # Prepare features for count model
    count_features = ['llm_adoption_flag', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity']
    X_count = df[count_features].copy()
    y = df['iteration_count'].copy()
    
    # Prepare features for inflation model (using same features for simplicity)
    X_infl = df[count_features].copy()
    
    # Add constant
    X_count = add_constant(X_count)
    X_infl = add_constant(X_infl)
    
    # Fit Negative Binomial model (simplified ZINB without explicit inflation model in statsmodels)
    # Using NegativeBinomial as approximation
    try:
        model = NegativeBinomial(y, X_count)
        result = model.fit()
        
        coefficients = result.params.to_dict()
        standard_errors = result.bse.to_dict()
        p_values = result.pvalues.to_dict()
        
        # Calculate confidence intervals
        conf_int = result.conf_int()
        confidence_intervals = {}
        for i, col in enumerate(X_count.columns):
            confidence_intervals[col] = [conf_int.iloc[i, 0], conf_int.iloc[i, 1]]
        
        return {
            'model_type': 'Negative Binomial (ZINB approximation)',
            'formula': 'iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity',
            'coefficients': coefficients,
            'standard_errors': standard_errors,
            'p_values': p_values,
            'confidence_intervals': confidence_intervals,
            'aic': result.aic,
            'bic': result.bic
        }
    except Exception as e:
        logger.warning(f"ZINB model failed: {e}. Returning empty results.")
        return {
            'model_type': 'Negative Binomial (ZINB approximation)',
            'formula': 'iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity',
            'coefficients': {},
            'standard_errors': {},
            'p_values': {},
            'confidence_intervals': {},
            'error': str(e)
        }

def apply_bonferroni_correction(p_values: dict, alpha: float = 0.05) -> dict:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: Dictionary of p-values
        alpha: Significance level
        
    Returns:
        Dictionary with adjusted p-values and significance flags
    """
    logger.info("Applying Bonferroni correction...")
    
    n_tests = len(p_values)
    adjusted_alpha = alpha / n_tests if n_tests > 0 else alpha
    
    adjusted_p_values = {}
    significant = {}
    
    for key, p_val in p_values.items():
        adjusted_p = min(p_val * n_tests, 1.0)
        adjusted_p_values[key] = adjusted_p
        significant[key] = adjusted_p < alpha
    
    return {
        'adjusted_p_values': adjusted_p_values,
        'significant': significant,
        'original_alpha': alpha,
        'adjusted_alpha': adjusted_alpha,
        'n_tests': n_tests
    }

def run_sensitivity_analysis(df: pd.DataFrame) -> list:
    """
    Run sensitivity analysis by sweeping iteration_count threshold.
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        List of dictionaries with sensitivity analysis results
    """
    logger.info("Running sensitivity analysis...")
    
    results = []
    
    # Sweep threshold from 1 to 10
    for threshold in range(1, 11):
        # Filter data
        df_filtered = df[df['iteration_count'] >= threshold].copy()
        
        if len(df_filtered) < 10:
            logger.warning(f"Not enough data for threshold {threshold}, skipping")
            continue
        
        # Run simple linear regression for effect size
        features = ['llm_adoption_flag', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity']
        X = add_constant(df_filtered[features])
        y = df_filtered['iteration_count']
        
        try:
            model = sm.OLS(y, X).fit()
            llm_coef = model.params['llm_adoption_flag']
            llm_pval = model.pvalues['llm_adoption_flag']
            
            results.append({
                'threshold': threshold,
                'effect_size': float(llm_coef),
                'p_value': float(llm_pval),
                'n_samples': len(df_filtered)
            })
        except Exception as e:
            logger.warning(f"Error at threshold {threshold}: {e}")
            continue
    
    return results

def run_stratified_analysis(df: pd.DataFrame) -> dict:
    """
    Run stratified analysis comparing High vs Low AI-Noise groups.
    
    Args:
        df: Cleaned DataFrame
        
    Returns:
        Dictionary with stratified results
    """
    logger.info("Running stratified analysis...")
    
    # Split by AI noise flag
    df_high_noise = df[df['ai_noise_flag'] == 1].copy()
    df_low_noise = df[df['ai_noise_flag'] == 0].copy()
    
    results = {
        'high_noise_group': {},
        'low_noise_group': {},
        'comparison': {}
    }
    
    features = ['llm_adoption_flag', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity']
    
    # Analyze high noise group
    if len(df_high_noise) >= 5:
        X_high = add_constant(df_high_noise[features])
        y_high = df_high_noise['iteration_count']
        
        try:
            model_high = sm.OLS(y_high, X_high).fit()
            results['high_noise_group'] = {
                'n_samples': len(df_high_noise),
                'llm_effect_size': float(model_high.params['llm_adoption_flag']),
                'llm_p_value': float(model_high.pvalues['llm_adoption_flag']),
                'r_squared': float(model_high.rsquared)
            }
        except Exception as e:
            results['high_noise_group'] = {'error': str(e), 'n_samples': len(df_high_noise)}
    else:
        results['high_noise_group'] = {'n_samples': len(df_high_noise), 'error': 'Insufficient data'}
    
    # Analyze low noise group
    if len(df_low_noise) >= 5:
        X_low = add_constant(df_low_noise[features])
        y_low = df_low_noise['iteration_count']
        
        try:
            model_low = sm.OLS(y_low, X_low).fit()
            results['low_noise_group'] = {
                'n_samples': len(df_low_noise),
                'llm_effect_size': float(model_low.params['llm_adoption_flag']),
                'llm_p_value': float(model_low.pvalues['llm_adoption_flag']),
                'r_squared': float(model_low.rsquared)
            }
        except Exception as e:
            results['low_noise_group'] = {'error': str(e), 'n_samples': len(df_low_noise)}
    else:
        results['low_noise_group'] = {'n_samples': len(df_low_noise), 'error': 'Insufficient data'}
    
    # Compare effect sizes
    if 'llm_effect_size' in results['high_noise_group'] and 'llm_effect_size' in results['low_noise_group']:
        diff = results['high_noise_group']['llm_effect_size'] - results['low_noise_group']['llm_effect_size']
        results['comparison'] = {
            'effect_size_difference': diff,
            'interpretation': 'High AI-Noise group has different LLM effect' if abs(diff) > 0.1 else 'Similar effects'
        }
    
    return results

def write_results(results: dict, output_path: Path):
    """
    Write analysis results to JSON file.
    
    Args:
        results: Dictionary of results to write
        output_path: Path to output file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Results written to {output_path}")

def run_analysis(seed: int = 42):
    """
    Run the full analysis pipeline.
    
    Args:
        seed: Random seed for reproducibility
    """
    logger.info("Starting analysis pipeline")
    
    try:
        # Load and clean data
        df = load_master_dataset(seed=seed)
        df_clean = clean_data(df)
        
        if len(df_clean) == 0:
            logger.error("No data remaining after cleaning. Cannot proceed with analysis.")
            return
        
        # Calculate VIF
        features = ['llm_adoption_flag', 'diff_complexity_score', 'loc', 'contributors', 'domain_complexity']
        vif_results = calculate_vif(df_clean, features)
        vif_flags = flag_high_vif(vif_results)
        
        # Run GLMM
        glmm_results = run_glmm(df_clean)
        
        # Run ZINB
        zinb_results = run_zinb_model(df_clean)
        
        # Apply Bonferroni correction
        bonferroni_results = apply_bonferroni_correction(glmm_results.get('p_values', {}))
        
        # Run sensitivity analysis
        sensitivity_results = run_sensitivity_analysis(df_clean)
        
        # Run stratified analysis
        stratified_results = run_stratified_analysis(df_clean)
        
        # Compile all results
        all_results = {
            'vif_analysis': vif_flags,
            'glmm': glmm_results,
            'zinb': zinb_results,
            'bonferroni_correction': bonferroni_results,
            'sensitivity_analysis': sensitivity_results,
            'stratified_analysis': stratified_results,
            'metadata': {
                'n_samples': len(df_clean),
                'n_features': len(features),
                'seed': seed
            }
        }
        
        # Write results
        write_results(all_results, ANALYSIS_RESULTS_PATH)
        
        # Write sensitivity analysis separately
        write_results({
            'thresholds': sensitivity_results
        }, SENSITIVITY_ANALYSIS_PATH)
        
        # Write stratified results separately
        write_results(stratified_results, STRATIFIED_RESULTS_PATH)
        
        logger.info("Analysis pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

def main():
    """Main entry point for the analysis script."""
    parser = argparse.ArgumentParser(description='Run statistical analysis on master dataset')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    args = parser.parse_args()
    
    run_analysis(seed=args.seed)

if __name__ == '__main__':
    main()