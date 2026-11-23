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

from src.utils.logging import get_logger
from src.utils.config import get_config

logger = get_logger(__name__)

def load_aligned_data(data_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load the aligned dataset from CSV.
    
    Args:
        data_path: Path to data/aligned_data.csv
        
    Returns:
        DataFrame containing aligned data
    """
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Aligned data file not found at {path}")
    
    logger.info(f"Loading aligned data from {path}")
    df = pd.read_csv(path)
    
    # Ensure required columns exist
    required_cols = ['subject_id', 'mmn_amplitude', 'accuracy', 'learning_phase']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in aligned data: {missing}")
    
    return df

def fit_lme_model(df: pd.DataFrame, formula: str = None) -> Tuple[Any, Dict[str, Any]]:
    """
    Fit a Gaussian Linear Mixed Effects model.
    
    Args:
        df: DataFrame with aligned data
        formula: Model formula (default: MMN_Amplitude ~ Accuracy + Learning_Phase + (1|Subject))
        
    Returns:
        Tuple of (fitted model object, results dictionary)
    """
    if formula is None:
        formula = "mmn_amplitude ~ accuracy + learning_phase + (1|subject_id)"
    
    logger.info(f"Fitting LME model with formula: {formula}")
    
    # Convert categorical variables
    df['learning_phase'] = df['learning_phase'].astype('category')
    df['subject_id'] = df['subject_id'].astype('category')
    
    try:
        # Use statsmodels mixedlm for LME
        # Note: statsmodels uses different syntax than lme4 in R
        # We'll use the formula interface
        model = smf.mixedlm(formula.replace("(1|subject_id)", ""), 
                          df, 
                          groups=df['subject_id'])
        result = model.fit()
        
        # Extract coefficients and p-values
        params = result.params
        p_values = result.pvalues
        std_err = result.bse
        
        results_dict = {
            'formula': formula,
            'coefficients': params.to_dict(),
            'p_values': p_values.to_dict(),
            'std_errors': std_err.to_dict(),
            'log_likelihood': result.llf,
            'aic': result.aic,
            'bic': result.bic,
            'converged': result.converged
        }
        
        logger.info(f"Model converged: {result.converged}")
        logger.info(f"AIC: {result.aic:.4f}, BIC: {result.bic:.4f}")
        
        return result, results_dict
        
    except Exception as e:
        logger.error(f"Failed to fit LME model: {str(e)}")
        raise

def apply_fdr_correction(p_values: Dict[str, float], alpha: float = 0.05) -> Dict[str, float]:
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Args:
        p_values: Dictionary of p-values
        alpha: Significance threshold
        
    Returns:
        Dictionary of FDR-corrected p-values
    """
    logger.info("Applying FDR correction")
    
    names = list(p_values.keys())
    raw_p = list(p_values.values())
    
    if len(raw_p) == 0:
        return {}
    
    # Apply BH correction
    reject, pvals_corrected, _, _ = multipletests(raw_p, alpha=alpha, method='fdr_bh')
    
    corrected_dict = {name: p for name, p in zip(names, pvals_corrected)}
    
    logger.info(f"Original p-values: {raw_p}")
    logger.info(f"Corrected p-values: {list(corrected_dict.values())}")
    
    return corrected_dict

def run_permutation_test(df: pd.DataFrame, n_permutations: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """
    Run a permutation test for the LME model.
    
    Args:
        df: DataFrame with aligned data
        n_permutations: Number of permutations
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary with permutation test results
    """
    logger.info(f"Running permutation test with {n_permutations} permutations")
    
    np.random.seed(seed)
    
    # Fit original model to get observed statistic
    _, orig_results = fit_lme_model(df)
    observed_stat = abs(orig_results['coefficients'].get('accuracy', 0))
    
    perm_stats = []
    
    for i in range(n_permutations):
        # Shuffle the outcome variable (mmn_amplitude) to break the relationship
        shuffled_df = df.copy()
        shuffled_df['mmn_amplitude'] = np.random.permutation(shuffled_df['mmn_amplitude'].values)
        
        try:
            _, perm_results = fit_lme_model(shuffled_df)
            perm_stat = abs(perm_results['coefficients'].get('accuracy', 0))
            perm_stats.append(perm_stat)
        except Exception as e:
            logger.warning(f"Permutation {i} failed: {str(e)}")
            continue
    
    if len(perm_stats) == 0:
        raise RuntimeError("All permutation tests failed")
    
    # Calculate permutation p-value
    # Two-tailed test: proportion of permuted stats >= observed stat
    p_perm = np.mean(np.array(perm_stats) >= observed_stat)
    
    # Stability check
    if n_permutations >= 1000:
        # Check variance of p-value in chunks
        chunk_size = 100
        chunk_p_values = []
        for start in range(0, len(perm_stats), chunk_size):
            chunk = perm_stats[start:start+chunk_size]
            if len(chunk) > 0:
                chunk_p = np.mean(np.array(chunk) >= observed_stat)
                chunk_p_values.append(chunk_p)
        
        if len(chunk_p_values) >= 3:
            variance = np.var(chunk_p_values)
            logger.info(f"P-value variance across chunks: {variance:.4f}")
            
            results = {
                'n_permutations': n_permutations,
                'observed_statistic': observed_stat,
                'permutation_p_value': p_perm,
                'p_value_variance': variance,
                'stable': variance < 0.05
            }
        else:
            results = {
                'n_permutations': n_permutations,
                'observed_statistic': observed_stat,
                'permutation_p_value': p_perm,
                'p_value_variance': None,
                'stable': True
            }
    else:
        results = {
            'n_permutations': n_permutations,
            'observed_statistic': observed_stat,
            'permutation_p_value': p_perm,
            'p_value_variance': None,
            'stable': True
        }
    
    logger.info(f"Permutation p-value: {p_perm:.4f}, Stable: {results['stable']}")
    return results

def analyze_multiple_electrodes(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """
    Run analysis for multiple electrodes (CP3, CP4, C3, C4).
    
    Args:
        df: DataFrame with aligned data (assumes mmn_amplitude is aggregated or per-electrode)
        
    Returns:
        Dictionary of results per electrode
    """
    # If data is already aggregated, just run one model
    # If per-electrode, we'd need to split by electrode column
    
    # For now, assume single mmn_amplitude column (aggregated or single electrode)
    # If the schema supports multiple electrodes, we'd iterate over them
    
    results = {}
    result, stats = fit_lme_model(df)
    results['all_electrodes'] = stats
    
    return results

def run_modeling_pipeline(data_path: Union[str, Path], output_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Run the full modeling pipeline.
    
    Args:
        data_path: Path to aligned data CSV
        output_path: Path to output JSON file
        
    Returns:
        Dictionary containing all model results
    """
    logger.info("Starting modeling pipeline")
    
    # Load data
    df = load_aligned_data(data_path)
    logger.info(f"Loaded {len(df)} rows of aligned data")
    
    # Check for power status
    warnings = []
    if 'power_status' in df.columns:
        underpowered_count = len(df[df['power_status'] == 'underpowered_primary'])
        if underpowered_count > 0:
            warnings.append("Underpowered dataset")
            logger.warning(f"Dataset has {underpowered_count} underpowered subjects")
    
    # Fit LME model
    result, model_stats = fit_lme_model(df)
    
    # Apply FDR correction if multiple tests (for now, single test)
    fdr_p_values = apply_fdr_correction(model_stats['p_values'])
    model_stats['fdr_p_values'] = fdr_p_values
    
    # Run permutation test
    perm_results = run_permutation_test(df, n_permutations=1000)
    
    # Compile final output
    output = {
        'model_type': 'Gaussian LME',
        'link_function': 'identity',
        'formula': model_stats['formula'],
        'coefficients': model_stats['coefficients'],
        'p_values': model_stats['p_values'],
        'fdr_p_values': model_stats['fdr_p_values'],
        'permutation_p_value': perm_results['permutation_p_value'],
        'permutation_details': {
            'n_permutations': perm_results['n_permutations'],
            'observed_statistic': perm_results['observed_statistic'],
            'stable': perm_results['stable']
        },
        'model_fit': {
            'log_likelihood': model_stats['log_likelihood'],
            'aic': model_stats['aic'],
            'bic': model_stats['bic'],
            'converged': model_stats['converged']
        },
        'warnings': warnings,
        'data_rows': len(df),
        'data_path': str(data_path)
    }
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    logger.info(f"Model output written to {output_path}")
    return output

def main():
    """Main entry point for the modeling task."""
    config = get_config()
    
    data_dir = Path(config.get('data_dir', 'data'))
    analysis_dir = Path(config.get('analysis_dir', 'analysis'))
    
    aligned_data_path = data_dir / 'aligned_data.csv'
    output_path = analysis_dir / 'results' / 'model_output.json'
    
    # Ensure directories exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        results = run_modeling_pipeline(str(aligned_data_path), str(output_path))
        logger.info("Modeling pipeline completed successfully")
        print(f"Results saved to {output_path}")
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Modeling pipeline failed: {e}")
        raise

if __name__ == '__main__':
    main()