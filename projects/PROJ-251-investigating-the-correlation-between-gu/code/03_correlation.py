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

from utils.config import get_use_synthetic_data, get_processed_path, get_results_path
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_preprocessed_data(filepath: str) -> pd.DataFrame:
    """Load the preprocessed dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Preprocessed data file not found: {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded data with shape {df.shape} from {filepath}")
    return df

def identify_taxa_columns(df: pd.DataFrame) -> List[str]:
    """Identify columns representing taxa (typically starting with 'taxa_' or specific naming convention)."""
    # Assuming CLR transformed columns are named 'taxa_{taxon_name}' or similar based on previous steps
    # We filter for numeric columns that are not target variables
    exclude_cols = {'subject_id', 'shannon_diversity', 'titer_baseline', 'titer_post', 
                    'titer_pre_log', 'titer_post_log', 'log_titer'}
    taxa_cols = [col for col in df.columns if col not in exclude_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    # If specific naming convention exists (e.g. from CLR step), refine:
    # Assuming CLR output columns might be prefixed or named specifically. 
    # Based on typical pipeline, we look for columns that are not metadata.
    # Let's assume the previous step (T020a) produced columns named 'taxa_{name}' or just the taxon names.
    # We will select all numeric columns that are not the known metadata columns.
    # If the dataset has 'log_titer' as target, we exclude it from features.
    
    return taxa_cols

def identify_zero_variance_taxa(df: pd.DataFrame, taxa_cols: List[str], threshold: float = 1e-9) -> List[str]:
    """Identify taxa with variance below the threshold."""
    zero_var_taxa = []
    for col in taxa_cols:
        if df[col].var() < threshold:
            zero_var_taxa.append(col)
    return zero_var_taxa

def filter_zero_variance_taxa(df: pd.DataFrame, taxa_cols: List[str], threshold: float = 1e-9) -> List[str]:
    """Filter out taxa with zero variance."""
    zero_var_taxa = identify_zero_variance_taxa(df, taxa_cols, threshold)
    filtered_taxa = [col for col in taxa_cols if col not in zero_var_taxa]
    logger.info(f"Filtered {len(zero_var_taxa)} zero-variance taxa. Remaining: {len(filtered_taxa)}")
    return filtered_taxa

def perform_spearman_correlation(df: pd.DataFrame, taxa_cols: List[str], target_col: str) -> pd.DataFrame:
    """Perform Spearman rank correlation between each taxon and the target variable."""
    results = []
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe. Available: {df.columns.tolist()}")
    
    for taxon in taxa_cols:
        try:
            corr, p_value = spearmanr(df[taxon], df[target_col])
            results.append({
                'taxon': taxon,
                'coefficient': corr,
                'raw_pvalue': p_value
            })
        except Exception as e:
            logger.warning(f"Could not compute correlation for {taxon}: {e}")
            results.append({
                'taxon': taxon,
                'coefficient': np.nan,
                'raw_pvalue': np.nan
            })
    
    return pd.DataFrame(results)

def apply_bh_correction(df_results: pd.DataFrame) -> pd.DataFrame:
    """Apply Benjamini-Hochberg correction to raw p-values."""
    if df_results.empty or 'raw_pvalue' not in df_results.columns:
        return df_results
    
    p_values = df_results['raw_pvalue'].values
    # multipletests returns (reject, pvals_corrected, pvals_corrected_raw, alphacSidak, alphacBonf)
    # We use method='fdr_bh' for Benjamini-Hochberg
    try:
        _, adj_p_values, _, _ = multipletests(p_values, method='fdr_bh')
        df_results['adj_pvalue'] = adj_p_values
    except Exception as e:
        logger.error(f"Error applying BH correction: {e}")
        df_results['adj_pvalue'] = np.nan
    
    return df_results

def select_significant_taxa(df_results: pd.DataFrame, alpha: float = 0.05) -> List[str]:
    """Select taxa with adjusted p-value < alpha."""
    significant = df_results[df_results['adj_pvalue'] < alpha]['taxon'].tolist()
    logger.info(f"Selected {len(significant)} significant taxa at alpha={alpha}")
    return significant

def save_results(df_results: pd.DataFrame, significant_taxa: List[str], output_path: Path):
    """Save correlation results to JSON and list of significant taxa to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save full results
    results_json_path = output_path / "correlation_results.json"
    df_results.to_json(results_json_path, orient='records', indent=2)
    logger.info(f"Saved correlation results to {results_json_path}")
    
    # Save significant taxa list (for fallback logic in modeling)
    significant_taxa_path = output_path / "significant_taxa.json"
    with open(significant_taxa_path, 'w') as f:
        json.dump(significant_taxa, f, indent=2)
    logger.info(f"Saved significant taxa to {significant_taxa_path}")

def run_correlation_pipeline(input_path: Path, output_dir: Path, target_col: str = 'log_titer') -> None:
    """Run the full correlation and feature selection pipeline."""
    logger.info("Starting correlation pipeline...")
    
    # Load data
    df = load_preprocessed_data(str(input_path))
    
    # Identify taxa columns
    taxa_cols = identify_taxa_columns(df)
    if not taxa_cols:
        raise ValueError("No taxa columns found in the dataset.")
    
    # Variance filtering (as per T032a dependency, though T032a might have already done this, 
    # we re-apply or ensure we are working on the filtered set if passed. 
    # The task description says Input: cleared_final.csv AND variance_filtered_taxa.json.
    # We should load the variance filtered list if it exists, otherwise filter here.)
    
    variance_filtered_path = output_dir / "variance_filtered_taxa.json"
    if variance_filtered_path.exists():
        with open(variance_filtered_path, 'r') as f:
            taxa_cols = json.load(f)
        logger.info(f"Loaded variance-filtered taxa list from {variance_filtered_path}")
        # Ensure these columns exist in df
        taxa_cols = [c for c in taxa_cols if c in df.columns]
    else:
        logger.warning(f"Variance filtered list not found at {variance_filtered_path}. Filtering now.")
        taxa_cols = filter_zero_variance_taxa(df, taxa_cols)
    
    if not taxa_cols:
        # Fallback if no taxa passed variance filter (though T032a should handle error)
        logger.error("No taxa remaining after variance filtering.")
        # Create empty results
        results_df = pd.DataFrame(columns=['taxon', 'coefficient', 'raw_pvalue', 'adj_pvalue'])
        save_results(results_df, [], output_dir)
        return

    # Perform Spearman correlation
    results_df = perform_spearman_correlation(df, taxa_cols, target_col)
    
    # Apply BH correction
    results_df = apply_bh_correction(results_df)
    
    # Select significant taxa
    significant_taxa = select_significant_taxa(results_df, alpha=0.05)
    
    # Save results
    save_results(results_df, significant_taxa, output_dir)
    
    # Write methodology note to assumptions.md
    assumptions_path = output_dir.parent / "assumptions.md"
    if not assumptions_path.exists():
        assumptions_path.write_text("# Assumptions\n\n")
    
    note = "Methodology Note: Spearman rank correlation with Benjamini-Hochberg correction is used as the primary method per Spec FR-004. This overrides the Plan's initial mention of permutation testing.\n"
    with open(assumptions_path, 'a') as f:
        f.write(note)
    
    logger.info("Correlation pipeline completed successfully.")

def main():
    """Main entry point for the correlation task."""
    processed_dir = get_processed_path()
    results_dir = get_results_path()
    
    input_file = processed_dir / "cleared_final.csv"
    output_dir = results_dir
    
    run_correlation_pipeline(input_file, output_dir)

if __name__ == "__main__":
    main()
