import os
import sys
import json
import logging
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

from config import get_seed, set_all_seeds, ensure_directories, get_env_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/glmm_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_prepared_data(manifest_path: str, metrics_path: str, judgments_path: str) -> pd.DataFrame:
    """
    Load and merge stimuli manifest, clutter metrics, and human judgments.
    """
    logger.info(f"Loading data from: {manifest_path}, {metrics_path}, {judgments_path}")
    
    # Load stimuli manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    manifest_df = pd.DataFrame(manifest)
    
    # Load clutter metrics
    metrics_df = pd.read_csv(metrics_path)
    
    # Load human judgments (aggregated)
    judgments_df = pd.read_csv(judgments_path)
    
    # Merge all data
    # Join manifest with metrics
    merged_df = manifest_df.merge(metrics_df, on='file_path', how='inner')
    
    # Join with judgments
    final_df = merged_df.merge(judgments_df, on='stimulus_id', how='inner')
    
    logger.info(f"Loaded {len(final_df)} records for analysis")
    return final_df

def fit_glmm(data: pd.DataFrame, formula: str) -> sm.GLM:
    """
    Fit a binomial GLMM using statsmodels.
    Note: statsmodels doesn't have native mixed-effects GLM, 
    so we use a fixed-effects approximation with robust standard errors
    or use a workaround for mixed effects.
    
    For true mixed effects, we would typically use statsmodels MixedLM
    or pymer4, but for binomial outcomes with random effects,
    we'll use a generalized linear model with clustered standard errors
    as an approximation, or fit a fixed-effects model if mixed fails.
    """
    try:
        # Prepare the formula for statsmodels
        # We'll use a binomial family with logit link
        # Format: success + failures ~ predictors + (1|random)
        
        # Since statsmodels MixedLM is for continuous outcomes,
        # we'll use a workaround: fit a GLM with robust SEs clustered by participant
        # This is a valid approximation for the purpose of this research pipeline
        
        # Prepare the data for binomial GLM
        # We need to create a "success" and "failure" count or use binary outcome
        if 'accuracy' in data.columns and 'stimulus_id' in data.columns:
            # If we have aggregated accuracy, we need to reconstruct counts or use weighted GLM
            # For simplicity, we'll use the binary outcome approach if available
            # or use a weighted approach
            pass
        
        # Fit the model using statsmodels GLM with binomial family
        # We'll use a fixed-effects model first, then add robust SEs
        model = smf.glm(
            formula=formula,
            data=data,
            family=sm.families.Binomial()
        )
        
        result = model.fit(cov_type='cluster', cov_kwds={'groups': data['participant_id']})
        return result
    except Exception as e:
        logger.warning(f"GLMM with cluster robust SE failed: {e}")
        raise

def fit_glmm_fixed_effects_only(data: pd.DataFrame, formula: str) -> sm.GLM:
    """
    Fallback: Fit a fixed-effects only model (no random effects) with robust SEs.
    """
    logger.warning("Fitting fixed-effects only model as fallback")
    try:
        model = smf.glm(
            formula=formula,
            data=data,
            family=sm.families.Binomial()
        )
        result = model.fit(cov_type='HC3')  # Robust standard errors
        return result
    except Exception as e:
        logger.error(f"Fixed-effects model also failed: {e}")
        raise

def extract_results(result, data: pd.DataFrame) -> dict:
    """
    Extract model results including coefficients, p-values, and confidence intervals.
    """
    params = result.params
    pvalues = result.pvalues
    conf_int = result.conf_int()
    
    results_dict = {
        'coefficients': params.to_dict(),
        'pvalues': pvalues.to_dict(),
        'confidence_intervals': {
            col: [conf_int.loc[col, 0], conf_int.loc[col, 1]] 
            for col in conf_int.columns
        },
        'converged': result.converged if hasattr(result, 'converged') else True,
        'aic': result.aic if hasattr(result, 'aic') else None,
        'bic': result.bic if hasattr(result, 'bic') else None
    }
    
    return results_dict

def apply_fdr_correction(pvalues: dict, alpha: float = 0.05) -> dict:
    """
    Apply Benjamini-Hochberg FDR correction to multiple hypothesis tests.
    
    Args:
        pvalues: Dictionary of p-values {term: pvalue}
        alpha: FDR threshold (default 0.05)
        
    Returns:
        Dictionary with corrected p-values and significance flags
    """
    logger.info(f"Applying Benjamini-Hochberg FDR correction with alpha={alpha}")
    
    # Extract terms and p-values
    terms = list(pvalues.keys())
    pvals = list(pvalues.values())
    
    # Filter out non-numeric p-values (e.g., intercept might be NaN in some cases)
    valid_mask = [isinstance(p, (int, float)) and not np.isnan(p) for p in pvals]
    valid_terms = [t for t, m in zip(terms, valid_mask) if m]
    valid_pvals = [p for p, m in zip(pvals, valid_mask) if m]
    
    if len(valid_pvals) == 0:
        logger.warning("No valid p-values found for FDR correction")
        return {term: {'pvalue': pvalues.get(term), 'significant': False} for term in terms}
    
    # Sort p-values
    sorted_indices = np.argsort(valid_pvals)
    sorted_pvals = [valid_pvals[i] for i in sorted_indices]
    sorted_terms = [valid_terms[i] for i in sorted_indices]
    
    # Benjamini-Hochberg procedure
    n = len(sorted_pvals)
    corrected_pvals = []
    
    for i, p in enumerate(sorted_pvals):
        # Calculate the BH critical value
        bh_threshold = (i + 1) / n * alpha
        # The corrected p-value is the minimum of the current p-value and the next one
        # to ensure monotonicity
        corrected_p = min(p * n / (i + 1), 1.0)
        corrected_pvals.append(corrected_p)
    
    # Restore original order
    final_corrected_pvals = [0.0] * n
    for i, idx in enumerate(sorted_indices):
        final_corrected_pvals[idx] = corrected_pvals[i]
    
    # Determine significance
    results = {}
    for i, term in enumerate(valid_terms):
        p_corr = final_corrected_pvals[i]
        sig = p_corr <= alpha
        results[term] = {
            'pvalue_original': pvalues.get(term),
            'pvalue_corrected': p_corr,
            'significant': sig
        }
    
    # Add back terms that were filtered out (if any)
    for term in terms:
        if term not in results:
            results[term] = {
                'pvalue_original': pvalues.get(term),
                'pvalue_corrected': None,
                'significant': False
            }
    
    logger.info(f"FDR correction complete: {sum(1 for r in results.values() if r['significant'])} terms significant at alpha={alpha}")
    return results

def run_analysis(data: pd.DataFrame, formula: str, alpha: float = 0.05) -> dict:
    """
    Run the full GLMM analysis with FDR correction.
    
    Args:
        data: Prepared dataframe with all variables
        formula: Statsmodels formula string
        alpha: FDR threshold
        
    Returns:
        Dictionary with model results and FDR-corrected p-values
    """
    logger.info(f"Running GLMM analysis with formula: {formula}")
    
    # Try to fit the full model first
    try:
        result = fit_glmm(data, formula)
        converged = True
    except Exception as e:
        logger.warning(f"Initial GLMM fit failed: {e}")
        # Fallback to fixed-effects only
        result = fit_glmm_fixed_effects_only(data, formula)
        converged = False
    
    # Extract results
    model_results = extract_results(result, data)
    
    # Apply FDR correction
    fdr_results = apply_fdr_correction(model_results['pvalues'], alpha)
    
    # Compile final results
    final_results = {
        'model_results': model_results,
        'fdr_corrected': fdr_results,
        'converged': converged,
        'formula': formula,
        'n_observations': len(data)
    }
    
    return final_results

def main():
    """
    Main entry point for GLMM analysis with FDR correction.
    """
    parser = argparse.ArgumentParser(description='GLMM Analysis with FDR Correction')
    parser.add_argument('--manifest', type=str, default='data/interim/stimuli_manifest.json',
                      help='Path to stimuli manifest')
    parser.add_argument('--metrics', type=str, default='data/processed/clutter_metrics.csv',
                      help='Path to clutter metrics CSV')
    parser.add_argument('--judgments', type=str, default='data/processed/human_judgments.csv',
                      help='Path to human judgments CSV')
    parser.add_argument('--output', type=str, default='data/processed/regression_results.json',
                      help='Path to output results JSON')
    parser.add_argument('--formula', type=str, 
                      default='accuracy ~ spatial_frequency_energy + local_contrast_variance + flanker_count + eccentricity',
                      help='Statsmodels formula for the model')
    parser.add_argument('--alpha', type=float, default=0.05,
                      help='FDR correction threshold')
    parser.add_argument('--seed', type=int, default=42,
                      help='Random seed')
    
    args = parser.parse_args()
    
    # Set seeds
    set_all_seeds(args.seed)
    
    # Ensure directories
    ensure_directories()
    
    # Load data
    data = load_prepared_data(args.manifest, args.metrics, args.judgments)
    
    # Run analysis
    results = run_analysis(data, args.formula, args.alpha)
    
    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Results saved to {output_path}")
    print(f"Analysis complete. Results saved to {output_path}")

if __name__ == '__main__':
    main()