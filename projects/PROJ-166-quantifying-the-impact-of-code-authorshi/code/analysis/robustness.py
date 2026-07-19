import os
import sys
import json
import logging
import warnings
from pathlib import Path
import pandas as pd
import numpy as np
from statsmodels.stats.multitest import multipletests

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/robustness.log')
    ]
)
logger = logging.getLogger(__name__)

# Import config for paths
from config import ensure_directories

def load_data():
    """
    Load the main processed dataset used for analysis.
    Assumes T009 has produced data/processed/repo_metrics.csv
    """
    ensure_directories()
    path = Path("data/processed/repo_metrics.csv")
    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}. Run T009 first.")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    return df

def filter_zero_kloc(df):
    """
    Filter out rows where kloc is zero or NaN, as log(kloc) is undefined.
    """
    initial_count = len(df)
    # Handle potential NaNs in kloc
    df_clean = df.dropna(subset=['kloc'])
    df_clean = df_clean[df_clean['kloc'] > 0]
    dropped = initial_count - len(df_clean)
    if dropped > 0:
        logger.warning(f"Filtered out {dropped} rows with kloc <= 0 or NaN.")
    return df_clean

def calculate_shannon_entropy(df):
    """
    Calculate Shannon entropy for author contributions.
    H = -sum(p_i * log(p_i))
    This function assumes the dataframe has columns needed to calculate
    entropy, but for this specific task (T023), we are aggregating results
    from T021 and T022. The entropy calculation itself was done in T022.
    We include this for completeness if called elsewhere, but T023 focuses
    on aggregation.
    """
    # Placeholder for consistency with API, though T023 doesn't recalculate entropy
    # It relies on pre-calculated values in the input files.
    return df

def fit_negative_binomial_glm(df, predictor_col='unique_authors', offset_col='kloc'):
    """
    Fits a Negative Binomial GLM.
    This is a helper for T021/T022, but T023 focuses on aggregation.
    We include a minimal stub here to satisfy imports if this file is run standalone,
    though T023's main logic is aggregation.
    """
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    # Ensure we have the necessary columns
    required_cols = ['cve_count', predictor_col, offset_col]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Column {col} missing from dataframe for GLM fit.")

    # Create offset term: log(kloc)
    df['log_kloc'] = np.log(df[offset_col])

    formula = f"cve_count ~ {predictor_col} + primary_language + project_age + release_count"
    
    try:
        model = smf.glm(
            formula=formula,
            data=df,
            family=sm.families.NegativeBinomial()
        ).fit(offset=df['log_kloc'])
        return model
    except Exception as e:
        logger.error(f"GLM fitting failed: {e}")
        raise

def extract_results(model, predictor_name='unique_authors'):
    """
    Extract coefficients, p-values, etc. from a fitted GLM model.
    """
    results = {
        'predictor': predictor_name,
        'coefficient': float(model.params[predictor_name]),
        'std_err': float(model.bse[predictor_name]),
        'pvalue': float(model.pvalues[predictor_name]),
        'conf_int_low': float(model.conf_int().loc[predictor_name, 0]),
        'conf_int_high': float(model.conf_int().loc[predictor_name, 1]),
        'converged': model.converged
    }
    return results

def run_entropy_analysis(df):
    """
    Placeholder for T022 logic. T023 assumes T022 has already run and produced
    data/processed/robustness_entropy_pvalues.csv.
    """
    pass

def benjamini_hochberg(p_values):
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    Returns adjusted p-values.
    """
    m = len(p_values)
    if m == 0:
        return []
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_pvals = np.array(p_values)[sorted_indices]
    
    # Calculate BH adjusted p-values
    # rank is 1-based
    ranks = np.arange(1, m + 1)
    # BH formula: p_adj = p * m / rank
    # Ensure monotonicity (cumulative min from the end)
    adj_pvals = sorted_pvals * m / ranks
    
    # Enforce monotonicity: p_adj[i] = min(p_adj[i], p_adj[i+1], ..., p_adj[m])
    # We iterate backwards
    for i in range(m - 2, -1, -1):
        adj_pvals[i] = min(adj_pvals[i], adj_pvals[i+1])
    
    # Clip to 1.0
    adj_pvals = np.clip(adj_pvals, 0, 1.0)
    
    # Map back to original order
    final_adj_pvals = np.empty(m)
    final_adj_pvals[sorted_indices] = adj_pvals
    
    return final_adj_pvals.tolist()

def aggregate_and_correct():
    """
    T023 Implementation:
    1. Load robustness_subsample_pvalues.csv (from T021)
    2. Load robustness_entropy_pvalues.csv (from T022)
    3. Combine all p-values into a single list.
    4. Apply Benjamini-Hochberg correction globally.
    5. Update data/processed/robustness_results.json with adjusted p-values.
    """
    ensure_directories()
    
    subsample_path = Path("data/processed/robustness_subsample_pvalues.csv")
    entropy_path = Path("data/processed/robustness_entropy_pvalues.csv")
    results_path = Path("data/processed/robustness_results.json")

    # Check dependencies
    if not subsample_path.exists():
        raise FileNotFoundError(f"Dependency missing: {subsample_path}. Run T021 first.")
    if not entropy_path.exists():
        raise FileNotFoundError(f"Dependency missing: {entropy_path}. Run T022 first.")

    logger.info("Aggregating p-values from subsample and entropy analyses...")

    # Load subsample p-values
    df_sub = pd.read_csv(subsample_path)
    # Expected columns: language, predictor, pvalue (based on T021 description)
    # We need to be flexible with column names, looking for 'pvalue' or 'p_value'
    pval_col_sub = 'pvalue' if 'pvalue' in df_sub.columns else 'p_value'
    if pval_col_sub not in df_sub.columns:
        raise ValueError(f"Could not find p-value column in {subsample_path}")
    
    subsample_pvals = df_sub[pval_col_sub].tolist()
    subsample_rows = df_sub.to_dict(orient='records') # Keep context for output

    # Load entropy p-values
    df_ent = pd.read_csv(entropy_path)
    pval_col_ent = 'pvalue' if 'pvalue' in df_ent.columns else 'p_value'
    if pval_col_ent not in df_ent.columns:
        raise ValueError(f"Could not find p-value column in {entropy_path}")
    
    entropy_pvals = df_ent[pval_col_ent].tolist()
    entropy_rows = df_ent.to_dict(orient='records')

    # Combine all p-values
    all_pvals = subsample_pvals + entropy_pvals
    logger.info(f"Total p-values to correct: {len(all_pvals)}")

    if len(all_pvals) == 0:
        logger.warning("No p-values found to correct.")
        adjusted_pvals = []
    else:
        # Apply BH correction
        adjusted_pvals = benjamini_hochberg(all_pvals)
        logger.info("Benjamini-Hochberg correction applied globally.")

    # Reconstruct the full result list with adjusted p-values
    # We need to map the adjusted p-values back to the original rows
    results_list = []
    
    idx = 0
    for row in subsample_rows:
        row['pvalue_adjusted'] = adjusted_pvals[idx]
        row['correction_method'] = 'Benjamini-Hochberg (Global)'
        results_list.append(row)
        idx += 1
    
    for row in entropy_rows:
        row['pvalue_adjusted'] = adjusted_pvals[idx]
        row['correction_method'] = 'Benjamini-Hochberg (Global)'
        results_list.append(row)
        idx += 1

    # Prepare final JSON structure
    output_data = {
        'summary': {
            'total_tests': len(all_pvals),
            'correction_method': 'Benjamini-Hochberg (Global)',
            'significant_at_0.05': sum(1 for p in adjusted_pvals if p < 0.05)
        },
        'results': results_list
    }

    # Write to JSON
    with open(results_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Updated robustness results saved to {results_path}")
    return output_data

def main():
    """
    Entry point for T023: Global BH Correction.
    """
    logger.info("Starting T023: Global Benjamini-Hochberg Correction")
    try:
        result = aggregate_and_correct()
        logger.info("T023 completed successfully.")
        return result
    except Exception as e:
        logger.error(f"T023 failed: {e}")
        raise

if __name__ == "__main__":
    main()