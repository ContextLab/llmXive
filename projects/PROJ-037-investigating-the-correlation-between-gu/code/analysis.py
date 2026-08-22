"""
analysis.py
Associational analysis pipeline.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from scipy.stats import spearmanr, pearsonr
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_utils import get_logger
from utils.seeding import set_seed

logger = get_logger(__name__)
set_seed(42)

DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_OUTPUTS_DIR = PROJECT_ROOT / "data" / "outputs"

def load_processed_cohort(path: Path = None) -> pd.DataFrame:
    if path is None:
        path = DATA_PROCESSED_DIR / "cohort_merged.csv"
    if not path.exists():
        logger.error(f"Cohort file not found: {path}")
        raise FileNotFoundError(f"Missing cohort file: {path}")
    return pd.read_csv(path)

def load_biom_table(path: Path) -> pd.DataFrame:
    """Load BIOM table for diversity calculations."""
    try:
        from biom import load_table
        table = load_table(str(path))
        obs_ids = table.ids(axis='observation')
        sample_ids = table.ids(axis='sample')
        data = table.matrix_data.toarray()
        df = pd.DataFrame(data, index=sample_ids, columns=obs_ids)
        return df.reset_index().rename(columns={'index': 'sample_id'})
    except Exception as e:
        logger.error(f"Failed to load BIOM table: {e}")
        raise

def load_metadata(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep='\t')

def calculate_alpha_diversity(biom_df: pd.DataFrame, method: str = 'shannon') -> pd.Series:
    """Calculate alpha diversity metrics."""
    from skbio.diversity import alpha_diversity
    import numpy as np
    
    # Convert to numpy array, excluding sample_id column
    counts = biom_df.iloc[:, 1:].values.astype(float)
    ids = biom_df['sample_id'].values
    
    if method == 'shannon':
        diversity = alpha_diversity('shannon', counts, ids=ids)
    elif method == 'simpson':
        diversity = alpha_diversity('simpson', counts, ids=ids)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return pd.Series(diversity, index=ids)

def calculate_beta_diversity(biom_df: pd.DataFrame, metric: str = 'braycurtis'):
    """Calculate beta diversity distance matrix."""
    from skbio.diversity import beta_diversity
    
    counts = biom_df.iloc[:, 1:].values.astype(float)
    ids = biom_df['sample_id'].values
    
    dist_matrix = beta_diversity(metric, counts, ids=ids)
    return dist_matrix

def calculate_correlations(df: pd.DataFrame, var1: str, var2: str) -> Tuple[float, float]:
    """Calculate Spearman and Pearson correlations."""
    # Spearman
    spearman_r, spearman_p = spearmanr(df[var1], df[var2])
    # Pearson
    pearson_r, pearson_p = pearsonr(df[var1], df[var2])
    return spearman_r, spearman_p

def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Benjamini-Hochberg FDR correction."""
    _, q_values, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    return q_values

def run_dbRDA(biom_df: pd.DataFrame, metadata: pd.DataFrame, sleep_var: str):
    """Run distance-based redundancy analysis."""
    from skbio.stats.ordination import pcoa
    from skbio.stats.distance import permanova
    
    # Calculate beta diversity
    dist_matrix = calculate_beta_diversity(biom_df, 'braycurtis')
    
    # Merge metadata with distance matrix
    # Note: dbRDA implementation depends on specific library support
    # For now, we log the intent
    logger.info(f"Running dbRDA for {sleep_var} vs beta diversity")
    return None

def run_permanova(dist_matrix, metadata: pd.DataFrame, grouping_var: str):
    """Run PERMANOVA for categorical sleep variables."""
    from skbio.stats.distance import permanova
    
    # Ensure grouping variable is categorical
    groups = metadata[grouping_var].astype(str)
    result = permanova(dist_matrix, groups)
    return result

def run_glm_adjusted(df: pd.DataFrame, outcome: str, predictors: List[str]) -> pd.DataFrame:
    """Run GLM adjusting for confounders."""
    # Prepare design matrix
    X = df[predictors].copy()
    X = sm.add_constant(X)
    y = df[outcome]
    
    # Fit GLM
    model = sm.GLM(y, X, family=sm.families.Gaussian())
    result = model.fit()
    
    # Extract coefficients
    coeffs = result.params
    pvalues = result.pvalues
    
    return pd.DataFrame({
        'predictor': coeffs.index,
        'coefficient': coeffs.values,
        'p_value': pvalues.values
    })

def save_results(results_df: pd.DataFrame, path: Path):
    """Save results to CSV."""
    results_df.to_csv(path, index=False)
    logger.info(f"Saved results to {path}")

def run_all_correlations(df: pd.DataFrame, sleep_vars: List[str], diversity_vars: List[str]) -> pd.DataFrame:
    """Run all correlations between sleep and diversity variables."""
    results = []
    
    for sleep_var in sleep_vars:
        for div_var in diversity_vars:
            if sleep_var in df.columns and div_var in df.columns:
                r, p = calculate_correlations(df, sleep_var, div_var)
                results.append({
                    'sleep_variable': sleep_var,
                    'diversity_variable': div_var,
                    'spearman_r': r,
                    'spearman_p': p,
                    'pearson_r': None,  # Could calculate if needed
                    'pearson_p': None
                })
    
    results_df = pd.DataFrame(results)
    
    # Apply FDR correction
    if not results_df.empty:
        results_df['fdr_p'] = apply_fdr_correction(results_df['spearman_p'].tolist())
    
    return results_df

def main():
    """
    Main analysis pipeline.
    """
    try:
        # Load data
        logger.info("Loading processed cohort...")
        cohort_df = load_processed_cohort()
        
        # Calculate diversity metrics (if not already in cohort)
        # Assuming diversity metrics are pre-calculated or will be added
        # For this implementation, we assume they exist in the cohort
        diversity_vars = ['shannon', 'simpson']
        sleep_vars = ['sleep_duration', 'sleep_quality', 'chronotype']
        
        # Run correlations
        logger.info("Running correlations...")
        results_df = run_all_correlations(cohort_df, sleep_vars, diversity_vars)
        
        # Run GLM
        logger.info("Running GLM with adjustments...")
        confounders = ['age', 'bmi', 'diet_type', 'antibiotic_history']
        glm_results = run_glm_adjusted(cohort_df, 'shannon', confounders + ['sleep_duration'])
        
        # Prepare final results
        final_results = results_df.merge(glm_results, on='predictor', how='left', suffixes=('', '_glm'))
        
        # Save results
        output_path = DATA_OUTPUTS_DIR / "correlation_results.csv"
        DATA_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        save_results(final_results, output_path)
        
        # Log limitation note
        logger.info("Methodological Limitation: 'diet timing' is unavailable in AGP; 'diet type' used as substitute.")
        
        return 0
    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}", exc_info=True)
        return 1
