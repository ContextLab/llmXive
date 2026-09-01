import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from statsmodels.stats.multitest import multipletests

from utils.logging_config import get_logger
from utils.validators import validate_correlation_results_schema

logger = get_logger(__name__)

def load_preprocessed_data(input_path: str) -> pd.DataFrame:
    """Load the preprocessed dataset containing CLR transformed taxa and log_titer."""
    logger.info(f"Loading preprocessed data from {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Identify CLR columns (suffix '_clr')
    clr_columns = [col for col in df.columns if col.endswith('_clr')]
    if not clr_columns:
        raise ValueError("No CLR-transformed taxon columns found in the dataset.")
    
    if 'log_titer' not in df.columns:
        raise ValueError("Column 'log_titer' not found in the dataset.")
    
    return df, clr_columns

def identify_zero_variance_taxa(df: pd.DataFrame, clr_columns: List[str], threshold: float = 1e-9) -> List[str]:
    """Identify taxa with zero or near-zero variance."""
    zero_var_taxa = []
    for col in clr_columns:
        if df[col].var() < threshold:
            zero_var_taxa.append(col)
    return zero_var_taxa

def filter_zero_variance_taxa(df: pd.DataFrame, clr_columns: List[str], variance_filtered_taxa: List[str]) -> Tuple[pd.DataFrame, List[str]]:
    """Filter out zero-variance taxa and return the dataframe and remaining columns."""
    remaining_columns = [col for col in clr_columns if col in variance_filtered_taxa]
    if not remaining_columns:
        logger.warning("All taxa filtered out due to zero variance. Reverting to variance-filtered set.")
        # If variance filter logic failed to pass any, use all available CLR columns that passed variance check previously
        # But here we assume variance_filtered_taxa was passed from T032a correctly.
        # If it's empty, we raise an error as per T032a logic.
        raise ValueError("No taxa remain after variance filtering.")
    
    subset_df = df[remaining_columns + ['log_titer']].copy()
    return subset_df, remaining_columns

def perform_spearman_correlation(df: pd.DataFrame, feature_columns: List[str], target_column: str = 'log_titer') -> List[Dict[str, Any]]:
    """Perform Spearman correlation between each feature and the target."""
    results = []
    for col in feature_columns:
        # Handle potential NaNs in correlation
        valid_pairs = df[[col, target_column]].dropna()
        if len(valid_pairs) < 2:
            corr, p_val = 0.0, 1.0
        else:
            try:
                corr, p_val = spearmanr(valid_pairs[col], valid_pairs[target_column])
                if np.isnan(corr):
                    corr, p_val = 0.0, 1.0
            except Exception as e:
                logger.warning(f"Correlation failed for {col}: {e}")
                corr, p_val = 0.0, 1.0
        
        results.append({
            'taxon': col.replace('_clr', ''),
            'coefficient': float(corr),
            'raw_pvalue': float(p_val)
        })
    return results

def apply_bh_correction(correlation_results: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """Apply Benjamini-Hochberg correction to p-values."""
    p_values = [item['raw_pvalue'] for item in correlation_results]
    n = len(p_values)
    if n == 0:
        return correlation_results
    
    # multipletests returns (reject, pvals_corrected, alphacSidak, alphacBonf)
    try:
        _, p_adj, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')
    except Exception as e:
        logger.error(f"BH correction failed: {e}")
        p_adj = [1.0] * n
    
    for i, item in enumerate(correlation_results):
        item['adj_pvalue'] = float(p_adj[i])
        item['significant'] = bool(p_adj[i] < alpha)
    
    return correlation_results

def select_significant_taxa(correlation_results: List[Dict[str, Any]]) -> List[str]:
    """Select taxa that are significant after BH correction."""
    significant = [item['taxon'] for item in correlation_results if item['significant']]
    return significant

def save_results(correlation_results: List[Dict[str, Any]], output_path: str):
    """Save correlation results to JSON."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w') as f:
        json.dump(correlation_results, f, indent=2)
    logger.info(f"Correlation results saved to {output_path}")

def run_correlation_pipeline(
    input_path: str, 
    variance_filtered_path: str, 
    output_path: str
) -> Dict[str, Any]:
    """
    Run the full correlation analysis pipeline:
    1. Load data
    2. Filter zero-variance taxa (using variance_filtered_taxa list)
    3. Perform Spearman correlation
    4. Apply BH correction
    5. Save results
    """
    logger.info("Starting correlation analysis pipeline")
    
    # Load preprocessed data
    df, clr_columns = load_preprocessed_data(input_path)
    logger.info(f"Loaded {len(df)} samples and {len(clr_columns)} taxa")
    
    # Load variance filtered taxa
    if not os.path.exists(variance_filtered_path):
        raise FileNotFoundError(f"Variance filtered taxa file not found: {variance_filtered_path}")
    
    with open(variance_filtered_path, 'r') as f:
        variance_filtered_taxa = json.load(f)
    
    logger.info(f"Loaded {len(variance_filtered_taxa)} variance-filtered taxa")
    
    # Filter data to only include variance-filtered taxa
    # Note: variance_filtered_taxa contains taxon names (without '_clr'), so we need to map back
    target_clr_columns = [col for col in clr_columns if col.replace('_clr', '') in variance_filtered_taxa]
    
    if not target_clr_columns:
        logger.warning("No taxa from variance filter found in CLR columns. Using all CLR columns.")
        target_clr_columns = clr_columns
    
    # Perform correlation
    correlation_results = perform_spearman_correlation(df, target_clr_columns)
    logger.info(f"Performed Spearman correlation on {len(correlation_results)} taxa")
    
    # Apply BH correction
    correlation_results = apply_bh_correction(correlation_results)
    
    # Identify significant taxa
    significant_taxa = select_significant_taxa(correlation_results)
    logger.info(f"Found {len(significant_taxa)} significant taxa (adj p < 0.05)")
    
    # Save results
    save_results(correlation_results, output_path)
    
    # Validate output schema
    validate_correlation_results_schema(output_path)
    
    return {
        'total_taxa_tested': len(correlation_results),
        'significant_taxa_count': len(significant_taxa),
        'significant_taxa': significant_taxa,
        'output_path': output_path
    }

def main():
    """Main entry point for the correlation analysis task."""
    # Paths
    input_path = os.getenv('INPUT_PATH', 'data/processed/cleared_with_diversity.csv')
    variance_filtered_path = os.getenv('VARIANCE_FILTERED_PATH', 'data/results/variance_filtered_taxa.json')
    output_path = os.getenv('OUTPUT_PATH', 'data/results/correlation_results.json')
    
    # Ensure paths are absolute relative to project root if needed
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / input_path
    variance_filtered_path = project_root / variance_filtered_path
    output_path = project_root / output_path
    
    try:
        result = run_correlation_pipeline(
            str(input_path),
            str(variance_filtered_path),
            str(output_path)
        )
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        print(json.dumps({'error': str(e)}, indent=2))
        sys.exit(1)

if __name__ == '__main__':
    main()
