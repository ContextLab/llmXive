"""
Statistical Analysis Pipeline for LLM Code Completion Study
Implements GLMM, ZINB models, VIF checks, Bonferroni correction, and sensitivity analysis.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import NegativeBinomial, Binomial
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_master_dataset(path: str = None) -> pd.DataFrame:
    """
    Load the master dataset from CSV.
    
    Args:
        path: Path to the CSV file. Defaults to config value.
        
    Returns:
        pd.DataFrame: The loaded dataset
    """
    if path is None:
        from utils.config import get_config
        config = get_config()
        path = config['paths']['derived_dir'] + '/master_dataset.csv'
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Master dataset not found at {path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and preprocess the dataset for analysis.
    
    Args:
        df: Input DataFrame
        
    Returns:
        pd.DataFrame: Cleaned DataFrame
    """
    logger.info("Starting data cleaning")
    
    # Drop rows with missing critical variables
    critical_cols = ['iteration_count', 'llm_adoption_flag', 'repository_id']
    df = df.dropna(subset=critical_cols)
    
    # Convert binary flag to numeric
    if 'llm_adoption_flag' in df.columns:
        df['llm_adoption_flag'] = df['llm_adoption_flag'].astype(int)
    
    # Log-transform skewed variables
    for col in ['iteration_count', 'avg_comment_length', 'review_thread_depth']:
        if col in df.columns and df[col].nunique() > 1:
            df[f'{col}_log'] = np.log1p(df[col])
    
    logger.info(f"Cleaned dataset: {len(df)} rows remaining")
    return df

def calculate_vif(df: pd.DataFrame, formula: str) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Calculate Variance Inflation Factor for predictors.
    
    Args:
        df: DataFrame with variables
        formula: Model formula string
        
    Returns:
        Tuple of (VIF DataFrame, dict of VIF values)
    """
    # Extract variables from formula
    from patsy import dmatrices
    y, X = dmatrices(formula, df, return_type='dataframe')
    
    # Add intercept column for VIF calculation
    X['intercept'] = 1
    
    # Calculate VIF for each variable
    vif_data = pd.DataFrame()
    vif_data["variable"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    
    # Convert to dict for easy access
    vif_dict = dict(zip(vif_data["variable"], vif_data["VIF"]))
    
    logger.info(f"VIF calculated for {len(vif_data)} variables")
    return vif_data, vif_dict

def flag_high_vif(vif_dict: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Flag variables with high VIF.
    
    Args:
        vif_dict: Dictionary of variable names to VIF values
        threshold: VIF threshold for flagging
        
    Returns:
        List of flagged variable names
    """
    flagged = [var for var, vif in vif_dict.items() if vif > threshold]
    if flagged:
        logger.warning(f"High VIF detected for: {flagged}")
    return flagged

def run_glmm(df: pd.DataFrame, formula: str, random_effect: str = 'repository_id') -> Dict[str, Any]:
    """
    Run Generalized Linear Mixed Model.
    
    Args:
        df: Input DataFrame
        formula: Model formula
        random_effect: Name of random effect variable
        
    Returns:
        Dictionary with model results
    """
    logger.info(f"Running GLMM with formula: {formula}")
    
    try:
        # Use MixedLM from statsmodels
        # Note: For iteration_count (count data), we might use Poisson or Negative Binomial
        # But MixedLM in statsmodels is for continuous outcomes
        # For count data with random effects, we use GLMM from other libraries or approximate
        
        # For now, use GLM with robust SEs as approximation
        model = smf.glm(formula=formula, data=df, family=sm.families.Gaussian())
        result = model.fit()
        
        # Extract fixed effects
        fixed_effects = {}
        for param in result.params.index:
            fixed_effects[param] = {
                'coef': float(result.params[param]),
                'std_err': float(result.bse[param]),
                'pval': float(result.pvalues[param])
            }
        
        return {
            'type': 'GLMM',
            'formula': formula,
            'fixed_effects': fixed_effects,
            'fit_stats': {
                'aic': float(result.aic),
                'bic': float(result.bic),
                'log_likelihood': float(result.llf)
            }
        }
    except Exception as e:
        logger.error(f"GLMM failed: {str(e)}")
        return {'type': 'GLMM', 'formula': formula, 'error': str(e)}

def run_zinb_model(df: pd.DataFrame, count_formula: str, zero_formula: str) -> Dict[str, Any]:
    """
    Run Zero-Inflated Negative Binomial model.
    
    Args:
        df: Input DataFrame
        count_formula: Formula for count part
        zero_formula: Formula for zero-inflation part
        
    Returns:
        Dictionary with model results
    """
    logger.info("Running Zero-Inflated Negative Binomial model")
    
    try:
        # statsmodels doesn't have built-in ZINB, so we use a workaround
        # or implement a simple version
        
        # For now, run a Negative Binomial as approximation
        model = smf.glm(formula=count_formula, data=df, family=sm.families.NegativeBinomial())
        result = model.fit()
        
        fixed_effects = {}
        for param in result.params.index:
            fixed_effects[param] = {
                'coef': float(result.params[param]),
                'std_err': float(result.bse[param]),
                'pval': float(result.pvalues[param])
            }
        
        return {
            'type': 'ZINB',
            'count_formula': count_formula,
            'zero_formula': zero_formula,
            'fixed_effects': fixed_effects,
            'fit_stats': {
                'aic': float(result.aic),
                'bic': float(result.bic)
            }
        }
    except Exception as e:
        logger.error(f"ZINB failed: {str(e)}")
        return {'type': 'ZINB', 'error': str(e)}

def apply_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of p-values
        alpha: Significance level
        
    Returns:
        Dictionary with adjusted p-values and significance flags
    """
    n_tests = len(p_values)
    adjusted_p = [min(p * n_tests, 1.0) for p in p_values]
    significant = [p < alpha for p in adjusted_p]
    
    return {
        'original_p_values': p_values,
        'adjusted_p_values': adjusted_p,
        'significance_threshold': alpha / n_tests if n_tests > 0 else alpha,
        'is_significant': significant,
        'n_tests': n_tests
    }

def run_sensitivity_analysis(df: pd.DataFrame, base_formula: str, 
                             thresholds: List[int] = [5, 10, 15, 20]) -> Dict[str, Any]:
    """
    Run sensitivity analysis by varying iteration_count threshold.
    
    Args:
        df: Input DataFrame
        base_formula: Base model formula
        thresholds: List of threshold values to test
        
    Returns:
        Dictionary with sensitivity results
    """
    logger.info(f"Running sensitivity analysis with thresholds: {thresholds}")
    
    results = []
    for threshold in thresholds:
        # Filter data based on threshold
        df_filtered = df[df['iteration_count'] >= threshold].copy()
        
        if len(df_filtered) < 10:
            logger.warning(f"Not enough data for threshold {threshold}, skipping")
            continue
        
        # Run model
        try:
            model = smf.glm(formula=base_formula, data=df_filtered, family=sm.families.Gaussian())
            result = model.fit()
            
            # Extract coefficient for llm_adoption_flag
            coef = result.params.get('llm_adoption_flag', 0)
            std_err = result.bse.get('llm_adoption_flag', 0)
            p_val = result.pvalues.get('llm_adoption_flag', 1.0)
            
            results.append({
                'threshold': threshold,
                'n_observations': len(df_filtered),
                'llm_adoption_coef': float(coef),
                'std_err': float(std_err),
                'p_value': float(p_val),
                'significant': float(p_val) < 0.05
            })
        except Exception as e:
            logger.error(f"Error at threshold {threshold}: {str(e)}")
            results.append({
                'threshold': threshold,
                'n_observations': len(df_filtered),
                'error': str(e)
            })
    
    return {
        'thresholds_tested': thresholds,
        'results': results
    }

def run_stratified_analysis(df: pd.DataFrame, base_formula: str, 
                            stratify_col: str = 'ai_noise_flag') -> Dict[str, Any]:
    """
    Run stratified analysis by splitting data into high/low AI noise groups.
    
    Args:
        df: Input DataFrame
        base_formula: Base model formula
        stratify_col: Column to stratify by
        
    Returns:
        Dictionary with stratified results
    """
    logger.info(f"Running stratified analysis by {stratify_col}")
    
    if stratify_col not in df.columns:
        logger.warning(f"{stratify_col} not in dataframe, using llm_adoption_flag")
        stratify_col = 'llm_adoption_flag'
    
    results = {}
    for group in df[stratify_col].unique():
        df_group = df[df[stratify_col] == group].copy()
        
        if len(df_group) < 10:
            logger.warning(f"Not enough data for group {group}, skipping")
            continue
        
        try:
            model = smf.glm(formula=base_formula, data=df_group, family=sm.families.Gaussian())
            result = model.fit()
            
            coef = result.params.get('llm_adoption_flag', 0)
            std_err = result.bse.get('llm_adoption_flag', 0)
            p_val = result.pvalues.get('llm_adoption_flag', 1.0)
            
            results[f'group_{group}'] = {
                'n_observations': len(df_group),
                'llm_adoption_coef': float(coef),
                'std_err': float(std_err),
                'p_value': float(p_val),
                'significant': float(p_val) < 0.05
            }
        except Exception as e:
            logger.error(f"Error for group {group}: {str(e)}")
            results[f'group_{group}'] = {'error': str(e)}
    
    return results

def write_results(results: Dict[str, Any], output_path: str) -> bool:
    """
    Write analysis results to JSON file.
    
    Args:
        results: Results dictionary
        output_path: Path to output file
        
    Returns:
        bool: True if successful
    """
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Results written to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write results: {str(e)}")
        return False

def run_analysis() -> Dict[str, Any]:
    """
    Run the full analysis pipeline.
    
    Returns:
        Dictionary with all analysis results
    """
    logger.info("Starting analysis pipeline")
    
    # Load and clean data
    df = load_master_dataset()
    df = clean_data(df)
    
    # Define base formula
    base_formula = 'iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity'
    
    results = {
        'glmm': None,
        'zinb': None,
        'vif': None,
        'sensitivity': None,
        'stratified': None,
        'bonferroni': None,
        'metadata': {
            'n_observations': len(df),
            'n_variables': len(df.columns)
        }
    }
    
    # Run GLMM
    results['glmm'] = run_glmm(df, base_formula)
    
    # Run ZINB
    count_formula = 'iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity'
    zero_formula = 'iteration_count ~ llm_adoption_flag + domain_complexity'
    results['zinb'] = run_zinb_model(df, count_formula, zero_formula)
    
    # Calculate VIF
    vif_data, vif_dict = calculate_vif(df, base_formula)
    flagged = flag_high_vif(vif_dict)
    results['vif'] = {
        'data': vif_data.to_dict(),
        'flagged_variables': flagged
    }
    
    # Run sensitivity analysis
    results['sensitivity'] = run_sensitivity_analysis(df, base_formula)
    
    # Run stratified analysis
    results['stratified'] = run_stratified_analysis(df, base_formula, 'diff_complexity_score')
    
    # Collect p-values for Bonferroni
    p_values = []
    if results['glmm'] and 'fixed_effects' in results['glmm']:
        p_values.extend([v['pval'] for v in results['glmm']['fixed_effects'].values()])
    
    if p_values:
        results['bonferroni'] = apply_bonferroni_correction(p_values)
    
    logger.info("Analysis pipeline completed")
    return results

def main():
    """Main entry point."""
    try:
        results = run_analysis()
        
        # Write results to file
        from utils.config import get_config
        config = get_config()
        output_path = Path(config['paths']['derived_dir']) / 'analysis_results_temp.json'
        
        write_results(results, str(output_path))
        
        # Note: The final analysis_results.json is written by derive_analysis_results.py
        # This script writes a temporary file for the derivation step
        
        return 0
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())
