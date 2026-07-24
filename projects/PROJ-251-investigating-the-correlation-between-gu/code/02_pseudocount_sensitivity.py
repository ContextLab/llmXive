import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Set, Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from scipy.stats import ttest_1samp

# Import shared utilities from the project structure
# Note: We assume the script is run from the project root or code/
# Adjusting imports to match the provided API surface
try:
    from utils.config import get_processed_path, get_output_path, get_random_seed
    from utils.logging_config import get_logger
except ImportError:
    # Fallback for direct execution if path is not set up
    sys.path.insert(0, str(Path(__file__).parent))
    from utils.config import get_processed_path, get_output_path, get_random_seed
    from utils.logging_config import get_logger

# Configure logger
logger = get_logger("pseudocount_sensitivity")

def load_preprocessed_data() -> pd.DataFrame:
    """
    Loads the data after zero-variance exclusion.
    Input: data/processed/filtered_no_zero_var.csv
    Output: DataFrame with subject_id, taxa columns, and titer columns.
    """
    input_path = get_processed_path("filtered_no_zero_var.csv")
    if not input_path.exists():
        # Fallback to the standard filtered data if the specific zero-variance file is missing
        # This handles cases where T019 might have output differently or the file is named standardly
        input_path = get_processed_path("filtered_data.csv")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    
    logger.info(f"Loading preprocessed data from {input_path}")
    df = pd.read_csv(input_path)
    return df

def apply_clr_transformation(df: pd.DataFrame, pseudocount: float) -> pd.DataFrame:
    """
    Applies Centered Log-Ratio transformation to taxonomic abundance columns.
    
    Args:
        df: DataFrame containing 'subject_id', titer columns, and taxon columns.
        pseudocount: Value to add to zeros before log transformation.
        
    Returns:
        DataFrame with CLR-transformed taxon columns.
    """
    # Identify taxon columns (assume everything not 'subject_id' or 'titer' related is taxon)
    # We need to identify which columns are taxa. 
    # Based on schema: subject_id, taxa_abundances (object), titer_baseline, titer_post.
    # In CSV, taxa are likely columns starting with 'taxon_' or similar, or simply all numeric cols except titers.
    # Let's assume columns containing 'titer' are targets, 'subject_id' is ID, rest are taxa.
    
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post']
    # Check if columns exist, if not try common variations
    if 'titer_baseline' not in df.columns and 'baseline_titer' in df.columns:
        exclude_cols = ['subject_id', 'baseline_titer', 'post_titer'] # Adjust if schema varies
    
    taxon_cols = [c for c in df.columns if c not in exclude_cols]
    
    if not taxon_cols:
        raise ValueError("No taxon columns found in the input dataframe.")
    
    # Make a copy to avoid modifying original
    df_clr = df.copy()
    
    # Extract taxon data
    taxon_data = df_clr[taxon_cols].astype(float)
    
    # Add pseudocount
    taxon_data_padded = taxon_data + pseudocount
    
    # Calculate geometric mean for each row (subject)
    # Using log-sum-exp trick for stability if needed, but simple log of mean is standard for CLR
    # CLR(x) = log(x / g(x)) where g(x) is geometric mean
    # log(x) - mean(log(x))
    
    log_data = np.log(taxon_data_padded)
    geo_mean_log = log_data.mean(axis=1)
    
    # Subtract the mean log from each value in the row
    clr_data = log_data.sub(geo_mean_log, axis=0)
    
    df_clr[taxon_cols] = clr_data
    
    return df_clr

def run_correlation_pipeline(df_clr: pd.DataFrame) -> pd.DataFrame:
    """
    Runs Spearman correlation between CLR-transformed taxa and titer change.
    
    Returns:
        DataFrame with correlation results: taxon, coefficient, p-value.
    """
    # Calculate titer change (Post - Baseline) or Log Fold Change?
    # Spec says "titer_post" and "titer_baseline". 
    # Usually immune response is analyzed as fold change or difference. 
    # Let's use difference (Post - Baseline) or log(Post/Baseline) if Post>0.
    # Given T021 implements log-transformation of titers, we might use log titers.
    # However, for correlation with CLR, often the delta is used.
    # Let's assume the target variable is the difference in log titers or just difference.
    # To be safe and robust, let's calculate the response variable here.
    
    # Check column names
    baseline_col = 'titer_baseline'
    post_col = 'titer_post'
    if baseline_col not in df_clr.columns:
        # Try alternatives
        if 'baseline' in df_clr.columns: baseline_col = 'baseline'
        else: raise ValueError("Baseline titer column not found")
    
    if post_col not in df_clr.columns:
        if 'post' in df_clr.columns: post_col = 'post'
        else: raise ValueError("Post titer column not found")
        
    # Calculate response: Log fold change is standard for immunology
    # response = log2(post / baseline)
    # Avoid division by zero
    df_clr['response'] = np.log2((df_clr[post_col] + 1e-6) / (df_clr[baseline_col] + 1e-6))
    
    exclude_cols = ['subject_id', 'titer_baseline', 'titer_post', 'response']
    taxon_cols = [c for c in df_clr.columns if c not in exclude_cols]
    
    results = []
    for taxon in taxon_cols:
        # Spearman correlation
        corr, p_val = spearmanr(df_clr[taxon], df_clr['response'])
        results.append({
            'taxon': taxon,
            'coefficient': corr,
            'p_value': p_val
        })
    
    return pd.DataFrame(results)

def get_significant_taxa(results_df: pd.DataFrame, alpha: float = 0.05) -> Set[str]:
    """
    Identifies taxa with adjusted p-value < alpha.
    Note: This function assumes raw p-values are adjusted externally or we adjust here.
    For the sensitivity analysis, we need the set of significant taxa.
    We will apply BH correction here to ensure consistency.
    """
    from statsmodels.stats.multitest import multipletests
    
    p_vals = results_df['p_value'].values
    # Benjamini-Hochberg correction
    reject, pvals_corrected, _, _ = multipletests(p_vals, alpha=alpha, method='fdr_bh')
    
    results_df['p_value_adj'] = pvals_corrected
    significant_taxa = set(results_df.loc[reject, 'taxon'].tolist())
    return significant_taxa

def calculate_jaccard(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Calculates Jaccard Index between two sets.
    J = |A ∩ B| / |A ∪ B|
    """
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    
    return intersection / union

def run_sensitivity_analysis():
    """
    Main orchestration for pseudocount sensitivity analysis.
    Runs CLR with different pseudocounts, correlates, and compares significant taxa.
    """
    pseudocounts = [1e-4, 1e-6, 1e-8]
    seed = get_random_seed()
    np.random.seed(seed)
    
    logger.info(f"Starting pseudocount sensitivity analysis with pseudocounts: {pseudocounts}")
    
    # Load data
    df = load_preprocessed_data()
    
    results_summary = {
        "pseudocounts_tested": pseudocounts,
        "total_subjects": len(df),
        "significant_taxa_sets": {},
        "jaccard_indices": {},
        "robust": False
    }
    
    significant_sets = {}
    
    for pc in pseudocounts:
        logger.info(f"Processing pseudocount: {pc}")
        
        # 1. CLR Transform
        df_clr = apply_clr_transformation(df, pseudocount=pc)
        
        # 2. Correlation
        corr_results = run_correlation_pipeline(df_clr)
        
        # 3. Identify Significant Taxa
        sig_taxa = get_significant_taxa(corr_results)
        significant_sets[pc] = sig_taxa
        results_summary["significant_taxa_sets"][str(pc)] = list(sig_taxa)
        
        logger.info(f"Pseudocount {pc}: Found {len(sig_taxa)} significant taxa")
        
        # Save individual results for this pseudocount (optional but good for debugging)
        # out_path = get_output_path(f"correlation_pseudocount_{pc}.csv")
        # corr_results.to_csv(out_path, index=False)
    
    # 4. Calculate Jaccard Indices between all pairs
    # We compare each pair (pc1, pc2)
    pairs = []
    for i in range(len(pseudocounts)):
        for j in range(i + 1, len(pseudocounts)):
            pc_a = pseudocounts[i]
            pc_b = pseudocounts[j]
            j_idx = calculate_jaccard(significant_sets[pc_a], significant_sets[pc_b])
            pair_key = f"{pc_a}_vs_{pc_b}"
            results_summary["jaccard_indices"][pair_key] = j_idx
            pairs.append(j_idx)
            logger.info(f"Jaccard Index ({pc_a} vs {pc_b}): {j_idx:.4f}")
    
    # 5. Determine Robustness
    # Robust if Jaccard > 0.5 for all pairs (or average > 0.5? Spec says "Jaccard > 0.5")
    # We'll assume robust if the minimum Jaccard index across pairs is > 0.5
    if pairs:
        min_jaccard = min(pairs)
        results_summary["robust"] = min_jaccard > 0.5
        results_summary["min_jaccard"] = min_jaccard
    else:
        results_summary["robust"] = True # No pairs to compare (only 1 pseudocount)
    
    # 6. Save Results
    output_path = get_output_path("pseudocount_sensitivity.json")
    with open(output_path, 'w') as f:
        json.dump(results_summary, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")
    return results_summary

def save_results(results: Dict[str, Any]):
    """
    Placeholder for additional saving logic if needed.
    Main saving is done in run_sensitivity_analysis.
    """
    pass

def main():
    """Entry point for the script."""
    try:
        run_sensitivity_analysis()
        logger.info("Task T020b completed successfully.")
    except Exception as e:
        logger.error(f"Task T020b failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()