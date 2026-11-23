import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from config import get_output_path, ensure_directories
from utils.logging import get_logger

logger = get_logger(__name__)

def load_unadjusted_alpha():
    """Load unadjusted alpha diversity p-values."""
    path = get_output_path("data/interim/unadjusted_alpha_pvals.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Unadjusted alpha p-values not found at {path}. "
                                "Ensure T020 has been executed.")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} alpha diversity associations from {path}")
    return df

def load_unadjusted_taxa():
    """Load unadjusted taxa p-values."""
    path = get_output_path("data/interim/unadjusted_taxa_pvals.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Unadjusted taxa p-values not found at {path}. "
                                "Ensure T020a has been executed.")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} taxa associations from {path}")
    return df

def apply_bh_correction(df, pval_col="pval_raw", qval_col="pval_adj"):
    """Apply Benjamini-Hochberg correction to p-values."""
    if pval_col not in df.columns:
        raise ValueError(f"Column '{pval_col}' not found in dataframe")
    
    # Sort by p-value for BH procedure
    df_sorted = df.sort_values(by=pval_col)
    n = len(df_sorted)
    
    # Calculate BH adjusted p-values
    df_sorted[qval_col] = df_sorted[pval_col] * n / (df_sorted.index + 1)
    
    # Ensure monotonicity (cumulative min from bottom)
    df_sorted[qval_col] = df_sorted[qval_col].rolling(n, min_periods=1).min().iloc[::-1].cummin().iloc[::-1]
    
    # Clamp to [0, 1]
    df_sorted[qval_col] = df_sorted[qval_col].clip(0, 1)
    
    # Restore original order
    df_result = df_sorted.sort_index()
    return df_result

def determine_direction(coef):
    """Determine effect direction based on correlation coefficient."""
    if pd.isna(coef):
        return "NA"
    elif coef > 0:
        return "positive"
    elif coef < 0:
        return "negative"
    else:
        return "zero"

def main():
    """
    Main function to generate association_results.csv.
    
    This task (T025) combines results from alpha diversity analysis (T020)
    and taxa abundance analysis (T020a), applies BH correction (T022a),
    and outputs a comprehensive results file with coefficients, p-values,
    q-values, and effect directions.
    """
    logger.info("Starting T025: Output association_results.csv")
    
    # Ensure directories exist
    ensure_directories()
    
    # Load unadjusted results
    logger.info("Loading unadjusted alpha diversity results...")
    alpha_df = load_unadjusted_alpha()
    
    logger.info("Loading unadjusted taxa results...")
    taxa_df = load_unadjusted_taxa()
    
    # Apply BH correction to alpha diversity results
    logger.info("Applying BH correction to alpha diversity results...")
    alpha_df_corrected = apply_bh_correction(alpha_df, "pval_raw", "pval_adj")
    
    # Apply BH correction to taxa results
    logger.info("Applying BH correction to taxa results...")
    taxa_df_corrected = apply_bh_correction(taxa_df, "pval_raw", "pval_adj")
    
    # Determine effect directions for alpha diversity
    logger.info("Determining effect directions for alpha diversity...")
    if 'coef' in alpha_df_corrected.columns:
        alpha_df_corrected['direction'] = alpha_df_corrected['coef'].apply(determine_direction)
    else:
        # If coefficient not present, we can't determine direction
        alpha_df_corrected['direction'] = "unknown"
        logger.warning("Coefficient column not found in alpha results, marking direction as unknown")
    
    # Determine effect directions for taxa
    logger.info("Determining effect directions for taxa...")
    if 'coef' in taxa_df_corrected.columns:
        taxa_df_corrected['direction'] = taxa_df_corrected['coef'].apply(determine_direction)
    else:
        taxa_df_corrected['direction'] = "unknown"
        logger.warning("Coefficient column not found in taxa results, marking direction as unknown")
    
    # Combine results into final association_results.csv
    logger.info("Combining results into final association_results.csv...")
    
    # Prepare final dataframe with required columns
    final_results = pd.DataFrame()
    
    # Add alpha diversity results
    alpha_final = alpha_df_corrected[['feature', 'coef', 'pval_raw', 'pval_adj', 'direction']].copy()
    alpha_final['analysis_type'] = 'alpha_diversity'
    
    # Add taxa results
    taxa_final = taxa_df_corrected[['feature', 'coef', 'pval_raw', 'pval_adj', 'direction']].copy()
    taxa_final['analysis_type'] = 'taxa_abundance'
    
    # Concatenate
    final_results = pd.concat([alpha_final, taxa_final], ignore_index=True)
    
    # Sort by adjusted p-value for readability
    final_results = final_results.sort_values(by='pval_adj')
    
    # Write output
    output_path = get_output_path("data/processed/association_results.csv")
    final_results.to_csv(output_path, index=False)
    
    logger.info(f"Successfully wrote {len(final_results)} association results to {output_path}")
    logger.info(f"Summary: {final_results['analysis_type'].value_counts().to_dict()}")
    
    # Log significant findings (q < 0.05)
    significant = final_results[final_results['pval_adj'] < 0.05]
    logger.info(f"Found {len(significant)} significant associations (q < 0.05)")
    
    return final_results

if __name__ == "__main__":
    main()