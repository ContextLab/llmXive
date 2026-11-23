import os
import logging
import pandas as pd
import json
from pathlib import Path
from config import get_output_path
from utils.logging import get_logger

logger = get_logger(__name__)

def calculate_max_delta_pvals(unadjusted_path: str, adjusted_path: str) -> dict:
    """
    Calculate |p_adjusted - p_unadjusted| for each taxon.
    
    Args:
        unadjusted_path: Path to unadjusted_taxa_pvals.csv
        adjusted_path: Path to adjusted_pvals.csv
        
    Returns:
        Dictionary with max_delta and threshold_met
    """
    logger.info(f"Loading unadjusted p-values from {unadjusted_path}")
    try:
        df_unadj = pd.read_csv(unadjusted_path)
        if 'feature' not in df_unadj.columns:
            raise ValueError("Unadjusted p-values file must contain 'feature' column")
        if 'pval_raw' not in df_unadj.columns:
            # Check if it's named differently, e.g., 'p_value'
            pval_col = [c for c in df_unadj.columns if 'pval' in c.lower()][0]
            df_unadj = df_unadj.rename(columns={pval_col: 'pval_raw'})
    except FileNotFoundError:
        logger.error(f"File not found: {unadjusted_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading unadjusted p-values: {e}")
        raise

    logger.info(f"Loading adjusted p-values from {adjusted_path}")
    try:
        df_adj = pd.read_csv(adjusted_path)
        if 'feature' not in df_adj.columns:
            raise ValueError("Adjusted p-values file must contain 'feature' column")
        if 'pval_adj' not in df_adj.columns:
            pval_col = [c for c in df_adj.columns if 'pval_adj' in c.lower() or 'adj' in c.lower()][0]
            df_adj = df_adj.rename(columns={pval_col: 'pval_adj'})
    except FileNotFoundError:
        logger.error(f"File not found: {adjusted_path}")
        raise
    except Exception as e:
        logger.error(f"Error reading adjusted p-values: {e}")
        raise

    # Merge on feature
    merged = pd.merge(df_unadj[['feature', 'pval_raw']], 
                      df_adj[['feature', 'pval_adj']], 
                      on='feature', 
                      how='inner')
    
    if merged.empty:
        logger.warning("No matching features found between unadjusted and adjusted files.")
        return {
            'max_delta': 0.0,
            'threshold_met': False,
            'features_matched': 0,
            'reason': 'No matching features'
        }

    # Calculate absolute delta
    merged['delta'] = (merged['pval_adj'] - merged['pval_raw']).abs()
    
    max_delta = merged['delta'].max()
    threshold_met = max_delta > 0.01

    logger.info(f"Calculated max delta: {max_delta:.6f}")
    logger.info(f"Threshold (0.01) met: {threshold_met}")

    return {
        'max_delta': float(max_delta),
        'threshold_met': bool(threshold_met),
        'features_matched': len(merged),
        'sample_delta': merged['delta'].head(10).to_dict()
    }

def run_covariate_check(unadjusted_path: str = None, adjusted_path: str = None, output_path: str = None) -> dict:
    """
    Run the covariate adjustment check (SC-005).
    
    Args:
        unadjusted_path: Path to unadjusted p-values
        adjusted_path: Path to adjusted p-values
        output_path: Path to write JSON output
        
    Returns:
        Dictionary with results
    """
    if unadjusted_path is None:
        unadjusted_path = get_output_path('data/interim/unadjusted_taxa_pvals.csv')
    if adjusted_path is None:
        adjusted_path = get_output_path('data/interim/adjusted_pvals.csv')
    if output_path is None:
        output_path = get_output_path('results/covariate_delta.json')

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    results = calculate_max_delta_pvals(unadjusted_path, adjusted_path)
    results['unadjusted_file'] = unadjusted_path
    results['adjusted_file'] = adjusted_path
    results['output_file'] = output_path

    # Write to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results written to {output_path}")
    return results

def main():
    """Main entry point for the covariate adjustment check."""
    logging.basicConfig(level=logging.INFO)
    try:
        results = run_covariate_check()
        if results['threshold_met']:
            logger.info("SC-005 Check PASSED: Covariate adjustment caused significant delta (>0.01).")
        else:
            logger.info("SC-005 Check INFO: Covariate adjustment did not cause significant delta.")
        return 0
    except Exception as e:
        logger.error(f"Check failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())