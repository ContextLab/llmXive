import os
import logging
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import from project config to ensure paths are correct
from code.config import get_output_path, ensure_directories

logger = logging.getLogger(__name__)

def calculate_partial_spearman_alpha(
    diversity_col: str,
    mental_health_col: str,
    covariates: List[str],
    df: pd.DataFrame
) -> Tuple[float, float]:
    """
    Calculate partial Spearman correlation between a diversity metric and a mental health score,
    adjusting for covariates (age, BMI).
    
    Returns:
        Tuple of (correlation coefficient, p-value)
    """
    # Drop rows with missing values in key columns
    cols = [diversity_col, mental_health_col] + covariates
    clean_df = df.dropna(subset=cols)
    
    if len(clean_df) < 3:
        logger.warning(f"Not enough data points for partial correlation on {diversity_col}")
        return np.nan, np.nan

    # Regress diversity against covariates
    X = clean_df[covariates].values
    y_div = clean_df[diversity_col].values
    
    reg_div = LinearRegression().fit(X, y_div)
    res_div = y_div - reg_div.predict(X)

    # Regress mental health against covariates
    y_mh = clean_df[mental_health_col].values
    reg_mh = LinearRegression().fit(X, y_mh)
    res_mh = y_mh - reg_mh.predict(X)

    # Calculate Spearman correlation on residuals
    corr, pval = spearmanr(res_div, res_mh)
    return corr, pval

def calculate_partial_spearman_taxa(
    taxa_col: str,
    mental_health_col: str,
    covariates: List[str],
    df: pd.DataFrame
) -> Tuple[float, float]:
    """
    Calculate partial Spearman correlation between a taxa abundance and a mental health score.
    """
    cols = [taxa_col, mental_health_col] + covariates
    clean_df = df.dropna(subset=cols)
    
    if len(clean_df) < 3:
        return np.nan, np.nan

    X = clean_df[covariates].values
    y_taxa = clean_df[taxa_col].values
    y_mh = clean_df[mental_health_col].values

    reg_taxa = LinearRegression().fit(X, y_taxa)
    res_taxa = y_taxa - reg_taxa.predict(X)

    reg_mh = LinearRegression().fit(X, y_mh)
    res_mh = y_mh - reg_mh.predict(X)

    corr, pval = spearmanr(res_taxa, res_mh)
    return corr, pval

def run_analysis_taxa(df: pd.DataFrame, mental_health_cols: List[str], covariates: List[str]) -> pd.DataFrame:
    """
    Run partial Spearman correlation for all taxa against all mental health columns.
    Returns a DataFrame with taxon, mental_health_var, coef, pval.
    """
    results = []
    # Assume first column is taxon name, rest are counts (or handle specific schema)
    # Based on T020a, we need to iterate over taxa columns.
    # We assume the input df has 'taxon' column or index, and other cols are abundances.
    # Let's assume the schema from T017 output: cleaned_dataset.csv likely has sample_id, metadata, and taxa cols.
    # We'll identify taxa columns as those not in metadata/covariates/mh_cols.
    
    exclude_cols = ['sample_id', 'shannon', 'simpson'] + covariates + mental_health_cols
    taxa_cols = [c for c in df.columns if c not in exclude_cols]
    
    logger.info(f"Analyzing {len(taxa_cols)} taxa against {len(mental_health_cols)} mental health metrics.")

    for taxon in taxa_cols:
        for mh_col in mental_health_cols:
            corr, pval = calculate_partial_spearman_taxa(taxon, mh_col, covariates, df)
            results.append({
                'taxon': taxon,
                'mental_health_var': mh_col,
                'coef': corr,
                'pval': pval
            })
    
    return pd.DataFrame(results)

def run_permanova(df: pd.DataFrame, distance_matrix: np.ndarray, group_col: str, covariates: List[str]) -> Dict:
    """
    Perform PERMANOVA on beta diversity with covariate adjustment.
    Note: Skbio's permanova does not natively support covariates in the formula.
    We perform distance matrix residualization manually before running permanova.
    """
    try:
        from skbio.stats.distance import permanova
        from skbio import DistanceMatrix
    except ImportError:
        logger.error("skbio is required for PERMANOVA")
        return {'p_value': np.nan, 'r_squared': np.nan, 'f_value': np.nan}

    # Prepare data
    sample_ids = df['sample_id'].values
    groups = df[group_col].values
    
    # Residualize distance matrix against covariates
    # 1. Create design matrix for covariates
    X = df[covariates].values
    n = X.shape[0]
    intercept = np.ones((n, 1))
    X_design = np.hstack([intercept, X])
    
    # 2. Project distance matrix rows onto covariates and subtract
    # Distance matrix is symmetric. We treat it as a set of vectors.
    # For each row i in distance matrix, regress against X_design to get residuals.
    D = distance_matrix
    n_samples = D.shape[0]
    
    # Residualize
    D_residual = np.zeros_like(D)
    for i in range(n_samples):
        y = D[i, :]
        reg = LinearRegression().fit(X_design, y)
        pred = reg.predict(X_design)
        D_residual[i, :] = y - pred
        
    # Symmetrize just in case
    D_residual = (D_residual + D_residual.T) / 2
    np.fill_diagonal(D_residual, 0)

    # Create DistanceMatrix object
    dm = DistanceMatrix(D_residual, ids=sample_ids)
    
    # Run PERMANOVA
    result = permanova(dm, groups, column_name=group_col)
    
    return {
        'p_value': result['p_value'],
        'r_squared': result['r_squared'],
        'f_value': result['f_value'],
        'n_permutations': result['n_permutations']
    }

def run_analysis(df: pd.DataFrame, alpha_cols: List[str], mh_cols: List[str], covariates: List[str]) -> Dict:
    """
    Run all alpha diversity partial correlations.
    """
    results = []
    for alpha_col in alpha_cols:
        for mh_col in mh_cols:
            corr, pval = calculate_partial_spearman_alpha(alpha_col, mh_col, covariates, df)
            results.append({
                'metric': alpha_col,
                'mental_health_var': mh_col,
                'coef': corr,
                'pval': pval
            })
    return pd.DataFrame(results)

def apply_benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    """
    Apply Benjamini-Hochberg correction to a series of p-values.
    Returns adjusted p-values (q-values).
    """
    p_vals = p_values.values
    n = len(p_vals)
    if n == 0:
        return pd.Series([], dtype=float)
    
    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_vals)
    sorted_p_vals = p_vals[sorted_indices]
    
    # Calculate BH adjusted p-values
    # q_i = p_i * n / i
    # Ensure monotonicity
    q_vals = np.zeros(n)
    for i in range(n):
        rank = i + 1
        q_vals[i] = sorted_p_vals[i] * n / rank
    
    # Enforce monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        q_vals[i] = min(q_vals[i], q_vals[i + 1])
    
    # Clip to [0, 1]
    q_vals = np.clip(q_vals, 0, 1)
    
    # Restore original order
    q_vals_final = np.zeros(n)
    q_vals_final[sorted_indices] = q_vals
    
    return pd.Series(q_vals_final, index=p_values.index)

def main():
    """
    Main entry point for T022: Apply Benjamini-Hochberg correction.
    Loads unadjusted p-values from T020, T020a, T021, applies correction,
    and saves the results.
    """
    logger.info("Starting T022: Benjamini-Hochberg Correction")
    
    # Ensure directories exist
    ensure_directories()
    
    # Define paths
    # T020 output: data/interim/unadjusted_alpha_pvals.csv
    # T020a output: data/interim/unadjusted_taxa_pvals.csv
    # T021 output: PERMANOVA results (likely stored in a JSON or CSV, let's assume a combined interim file or read from specific locations)
    # Based on T021 description, it outputs PERMANOVA stats. We'll assume a file exists or we read from a standard location.
    # Let's assume T021 wrote to data/interim/permanova_results.csv if not specified, 
    # but the task says "from T020, T020a, T021".
    # We will construct the final table from the existing interim files.
    
    alpha_file = get_output_path('data/interim/unadjusted_alpha_pvals.csv')
    taxa_file = get_output_path('data/interim/unadjusted_taxa_pvals.csv')
    # Assuming T021 output is stored in a file, let's look for a standard name or create one if needed.
    # If T021 didn't write a file, we might need to re-run or assume it exists. 
    # Given T021 is marked completed, it should have written output.
    # Let's assume T021 wrote to data/interim/permanova_results.csv
    permanova_file = get_output_path('data/interim/permanova_results.csv')
    
    output_file = get_output_path('data/processed/association_results.csv')
    
    # Load Alpha results
    df_alpha = pd.DataFrame()
    if os.path.exists(alpha_file):
        df_alpha = pd.read_csv(alpha_file)
        if 'pval' in df_alpha.columns:
            df_alpha['qval'] = apply_benjamini_hochberg(df_alpha['pval'])
            df_alpha['type'] = 'alpha'
            logger.info(f"Processed {len(df_alpha)} alpha correlation results.")
        else:
            logger.warning(f"Alpha file {alpha_file} missing 'pval' column.")
    else:
        logger.warning(f"Alpha file not found: {alpha_file}")
    
    # Load Taxa results
    df_taxa = pd.DataFrame()
    if os.path.exists(taxa_file):
        df_taxa = pd.read_csv(taxa_file)
        if 'pval' in df_taxa.columns:
            df_taxa['qval'] = apply_benjamini_hochberg(df_taxa['pval'])
            df_taxa['type'] = 'taxa'
            logger.info(f"Processed {len(df_taxa)} taxa correlation results.")
        else:
            logger.warning(f"Taxa file {taxa_file} missing 'pval' column.")
    else:
        logger.warning(f"Taxa file not found: {taxa_file}")
    
    # Load PERMANOVA results
    df_permanova = pd.DataFrame()
    if os.path.exists(permanova_file):
        df_permanova = pd.read_csv(permanova_file)
        if 'p_value' in df_permanova.columns:
            # Rename to match schema
            df_permanova = df_permanova.rename(columns={'p_value': 'pval'})
            # Apply BH correction
            df_permanova['qval'] = apply_benjamini_hochberg(df_permanova['pval'])
            df_permanova['type'] = 'permanova'
            logger.info(f"Processed {len(df_permanova)} PERMANOVA results.")
        else:
            logger.warning(f"PERMANOVA file {permanova_file} missing 'p_value' column.")
    else:
        logger.warning(f"PERMANOVA file not found: {permanova_file}")
    
    # Combine all results
    # Ensure consistent columns: type, pval, qval, and relevant identifiers
    final_results = []
    
    if not df_alpha.empty:
        final_results.append(df_alpha[['type', 'pval', 'qval', 'metric', 'mental_health_var', 'coef']])
    
    if not df_taxa.empty:
        final_results.append(df_taxa[['type', 'pval', 'qval', 'taxon', 'mental_health_var', 'coef']])
    
    if not df_permanova.empty:
        # PERMANOVA might have different columns, let's standardize
        # Assuming columns: group, pval, r_squared, f_value
        cols_to_keep = ['type', 'pval', 'qval']
        # Add available columns
        for col in df_permanova.columns:
            if col not in cols_to_keep and col != 'p_value': # p_value is already mapped to pval
                cols_to_keep.append(col)
        
        # Map p_value to pval if it exists in original
        if 'p_value' in df_permanova.columns:
            df_permanova['pval'] = df_permanova['p_value']
        
        final_results.append(df_permanova[cols_to_keep])
    
    if final_results:
        final_df = pd.concat(final_results, ignore_index=True)
        final_df.to_csv(output_file, index=False)
        logger.info(f"Saved combined results to {output_file}")
        
        # Log summary of significant findings
        sig_count = (final_df['qval'] < 0.05).sum()
        logger.info(f"Total significant associations (q < 0.05): {sig_count}")
    else:
        logger.error("No results found to combine. Check input files.")

if __name__ == "__main__":
    # Setup logging if not already done
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()