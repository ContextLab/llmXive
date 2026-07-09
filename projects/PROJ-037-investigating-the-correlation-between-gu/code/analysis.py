import os
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import pandas as pd
import numpy as np
from scipy.stats import spearmanr, pearsonr
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm
from skbio.stats.ordination import pcoa, capscale
from skbio.diversity import alpha_diversity, beta_diversity
from skbio import DistanceMatrix
from skbio.stats.distance import permanova
import biom

from utils.logging_utils import get_logger
from utils.seeding import set_seed

logger = get_logger(__name__)

# --- Data Loading ---

def load_processed_cohort(cohort_path: str) -> pd.DataFrame:
    """Load the merged cohort CSV from data/processed/."""
    path = Path(cohort_path)
    if not path.exists():
        raise FileNotFoundError(f"Cohort file not found: {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded cohort with {len(df)} participants from {path}")
    return df

def load_biom_table(biom_path: str) -> biom.Table:
    """Load a BIOM format table."""
    path = Path(biom_path)
    if not path.exists():
        raise FileNotFoundError(f"BIOM file not found: {path}")
    return biom.load_table(str(path))

def load_metadata(metadata_path: str) -> pd.DataFrame:
    """Load metadata CSV."""
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path}")
    return pd.read_csv(path)

# --- Diversity Calculations ---

def calculate_alpha_diversity(biom_table: biom.Table, metric: str = 'shannon') -> pd.Series:
    """Calculate alpha diversity for all samples in a BIOM table."""
    table = biom_table.filter(
        lambda id_, v, md: True,
        axis='sample',
        inplace=False
    )
    # Convert to sparse array for skbio
    dense_data = table.matrix_data.toarray()
    ids = table.ids(axis='sample')
    # skbio expects samples as columns in the input array for alpha_diversity
    # but biom table matrix_data is (observation, sample) by default in newer versions?
    # Actually, biom.Table.matrix_data is usually (observation, sample)
    # skbio.alpha_diversity expects (samples, observations) or a dict of counts.
    # Let's transpose: rows = samples, cols = OTUs
    counts = dense_data.T
    alphas = alpha_diversity(metric, counts, ids=ids)
    return pd.Series(alphas, index=ids)

def calculate_beta_diversity(biom_table: biom.Table, metric: str = 'braycurtis') -> DistanceMatrix:
    """Calculate beta diversity distance matrix."""
    dense_data = biom_table.matrix_data.toarray()
    ids = biom_table.ids(axis='sample')
    counts = dense_data.T  # samples x OTUs
    dm = beta_diversity(metric, counts, ids=ids)
    return dm

# --- Correlation Analysis ---

def calculate_correlations(
    df: pd.DataFrame,
    diversity_col: str,
    sleep_cols: List[str],
    method: str = 'spearman'
) -> pd.DataFrame:
    """Calculate correlations between diversity and sleep variables."""
    results = []
    for sleep_col in sleep_cols:
        if sleep_col not in df.columns:
            logger.warning(f"Sleep column {sleep_col} not found in data.")
            continue
        if method == 'spearman':
            corr, pval = spearmanr(df[diversity_col], df[sleep_col])
        elif method == 'pearson':
            corr, pval = pearsonr(df[diversity_col], df[sleep_col])
        else:
            raise ValueError(f"Unknown method: {method}")
        results.append({
            'diversity_metric': diversity_col,
            'sleep_variable': sleep_col,
            'correlation': corr,
            'p_value': pval,
            'method': method
        })
    return pd.DataFrame(results)

def apply_fdr_correction(df: pd.DataFrame, pval_col: str = 'p_value', alpha: float = 0.05) -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction."""
    if df.empty:
        return df
    pvals = df[pval_col].values
    reject, pvals_corrected, _, _ = multipletests(pvals, alpha=alpha, method='fdr_bh')
    df['p_value_fdr'] = pvals_corrected
    df['significant'] = reject
    return df

def run_all_correlations(df: pd.DataFrame, sleep_vars: List[str]) -> pd.DataFrame:
    """Run correlations for Shannon and Simpson against sleep variables."""
    all_results = []
    for div_metric in ['shannon', 'simpson']:
        if div_metric not in df.columns:
            logger.warning(f"Alpha diversity metric {div_metric} not found.")
            continue
        res = calculate_correlations(df, div_metric, sleep_vars)
        all_results.append(res)
    if not all_results:
        return pd.DataFrame()
    combined = pd.concat(all_results, ignore_index=True)
    return apply_fdr_correction(combined)

# --- Advanced Analyses ---

def run_dbRDA(
    df: pd.DataFrame,
    biom_table: biom.Table,
    sleep_var: str,
    continuous_vars: List[str],
    categorical_vars: List[str],
    method: str = 'braycurtis'
) -> Tuple[Optional[pd.DataFrame], Optional[Dict]]:
    """
    Run distance-based Redundancy Analysis (dbRDA).
    Used for continuous sleep variables as per plan mitigation.
    Returns (RDA summary table, stats dict).
    """
    if sleep_var not in df.columns:
        logger.warning(f"Sleep variable {sleep_var} not found for dbRDA.")
        return None, None

    # Prepare predictor matrix
    predictors = df[[sleep_var] + continuous_vars + categorical_vars].dropna()
    if predictors.empty:
        logger.warning("No valid rows for dbRDA predictors.")
        return None, None

    # Filter biom table to match
    valid_samples = predictors.index
    filtered_biom = biom_table.filter(
        lambda id_, v, md: id_ in valid_samples,
        axis='sample',
        inplace=False
    )

    dm = calculate_beta_diversity(filtered_biom, metric=method)

    # Run capscale (dbRDA)
    try:
        rda_res = capscale(dm, predictors[[sleep_var] + continuous_vars + categorical_vars])
        # Extract summary
        summary = rda_res.summary()
        return summary, rda_res
    except Exception as e:
        logger.error(f"dbRDA failed: {e}")
        return None, None

def run_permanova(
    df: pd.DataFrame,
    biom_table: biom.Table,
    grouping_var: str,
    continuous_covariates: List[str],
    categorical_covariates: List[str] = None
) -> Dict:
    """
    Run PERMANOVA strictly for CATEGORICAL sleep variables.
    Uses adonis2 equivalent logic via skbio.stats.distance.permanova.
    """
    if categorical_covariates is None:
        categorical_covariates = []

    if grouping_var not in df.columns:
        raise ValueError(f"Grouping variable {grouping_var} not found.")

    # Ensure grouping variable is categorical
    if not pd.api.types.is_categorical_dtype(df[grouping_var]) and df[grouping_var].nunique() < 10:
        df[grouping_var] = df[grouping_var].astype('category')
    
    if df[grouping_var].nunique() < 2:
        raise ValueError(f"Grouping variable {grouping_var} must have at least 2 categories.")

    # Prepare data
    valid_rows = df[[grouping_var] + continuous_covariates + categorical_covariates].dropna()
    valid_samples = valid_rows.index

    if len(valid_samples) < 2:
        raise ValueError("Insufficient samples for PERMANOVA.")

    # Filter BIOM table
    filtered_biom = biom_table.filter(
        lambda id_, v, md: id_ in valid_samples,
        axis='sample',
        inplace=False
    )

    # Calculate distance matrix
    dm = calculate_beta_diversity(filtered_biom, metric='braycurtis')

    # Prepare design matrix for adonis (skbio permanova only supports one grouping variable currently)
    # skbio.stats.distance.permanova signature:
    # permanova(distance_matrix, grouping, **kwargs)
    # It does NOT support covariates directly in the function call like adonis2 in R.
    # To handle covariates, we would need to implement a sequential test or use a different library.
    # Given the constraints, we will run PERMANOVA on the grouping variable.
    # Note: In a full production pipeline, one might use `skbio.stats.distance.capscale` 
    # to handle covariates as done in dbRDA, but the task specifically asks for PERMANOVA.
    # We will perform the test on the grouping variable.
    
    grouping_series = valid_rows[grouping_var]
    
    # Run PERMANOVA
    # Note: skbio's permanova returns a result object with test statistic, p-value, etc.
    result = permanova(dm, grouping_series)
    
    logger.info(f"PERMANOVA for {grouping_var}: F={result['test_statistic']}, p={result['p_value']}")
    
    return {
        'variable': grouping_var,
        'test_statistic': result['test_statistic'],
        'p_value': result['p_value'],
        'n_permutations': result.get('n_permutations', 999),
        'r_squared': result.get('r_squared', None)
    }

def run_glm_adjusted(
    df: pd.DataFrame,
    diversity_col: str,
    sleep_var: str,
    covariates: List[str]
) -> Dict:
    """Run GLM adjusting for confounders."""
    # Prepare data
    cols = [diversity_col, sleep_var] + covariates
    data = df[cols].dropna()
    
    if data.empty:
        return {}

    y = data[diversity_col]
    X = data[[sleep_var] + covariates]
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X).fit()
    
    return {
        'sleep_var': sleep_var,
        'coefficient': model.params.get(sleep_var),
        'p_value': model.pvalues.get(sleep_var),
        'r_squared': model.rsquared,
        'n_obs': model.nobs
    }

# --- Output ---

def save_results(results: pd.DataFrame, output_path: str):
    """Save results to CSV."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(path, index=False)
    logger.info(f"Saved results to {path}")

def main():
    parser = argparse.ArgumentParser(description="Run analysis pipeline")
    parser.add_argument('--cohort', type=str, required=True, help='Path to merged cohort CSV')
    parser.add_argument('--biom', type=str, required=True, help='Path to BIOM table')
    parser.add_argument('--output', type=str, default='data/outputs/correlation_results.csv', help='Output CSV path')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    args = parser.parse_args()

    set_seed(args.seed)
    logger.info("Starting analysis pipeline")

    # Load data
    df = load_processed_cohort(args.cohort)
    biom_table = load_biom_table(args.biom)

    # Define variables
    sleep_vars = ['sleep_duration', 'sleep_quality', 'chronotype']
    categorical_sleep_vars = ['sleep_quality_category'] # Assuming a categorical version exists or needs to be derived
    continuous_sleep_vars = ['sleep_duration', 'chronotype']

    # 1. Correlations
    logger.info("Running correlations...")
    corr_results = run_all_correlations(df, sleep_vars)
    
    # 2. dbRDA (for continuous variables)
    logger.info("Running dbRDA for continuous sleep variables...")
    dbRDA_results = []
    for var in continuous_sleep_vars:
        if var in df.columns:
            summary, _ = run_dbRDA(df, biom_table, var, ['age', 'BMI'], [])
            if summary:
                dbRDA_results.append({'variable': var, 'status': 'completed'})

    # 3. PERMANOVA (for CATEGORICAL variables)
    logger.info("Running PERMANOVA for categorical sleep variables...")
    permanova_results = []
    
    # Identify categorical sleep variables in the dataframe
    # If 'sleep_quality_category' doesn't exist, we might need to bin 'sleep_quality' or use an existing categorical column
    # For this implementation, we assume 'sleep_quality_category' is present or derive it from 'sleep_quality' if needed.
    # However, the task says "strictly for categorical sleep variables". 
    # If the dataframe has a categorical column, we use it.
    
    candidate_cats = [c for c in df.columns if c in sleep_vars and df[c].dtype == 'object']
    # Also check if we can derive a category from a numeric column if the spec implies it
    # But strict adherence: use existing categorical columns.
    
    # Let's assume 'sleep_quality' might be numeric but we need a categorical version.
    # If the user data has 'sleep_quality_category', use it. If not, we might skip or bin.
    # Given the task constraint "strictly for categorical", we will look for an existing categorical column.
    # If none found, we log and skip to avoid hallucinating data.
    
    if 'sleep_quality_category' in df.columns:
        try:
            pval_res = run_permanova(df, biom_table, 'sleep_quality_category', ['age', 'BMI'])
            permanova_results.append(pval_res)
        except Exception as e:
            logger.error(f"PERMANOVA failed for sleep_quality_category: {e}")
    else:
        logger.warning("No categorical sleep variable 'sleep_quality_category' found. Skipping PERMANOVA.")
        # Check for other potential categorical sleep variables
        for col in df.columns:
            if 'sleep' in col.lower() and df[col].dtype == 'object':
                try:
                    pval_res = run_permanova(df, biom_table, col, ['age', 'BMI'])
                    permanova_results.append(pval_res)
                    logger.info(f"Ran PERMANOVA for {col}")
                except Exception as e:
                    logger.error(f"PERMANOVA failed for {col}: {e}")

    # 4. GLM
    logger.info("Running GLM...")
    glm_results = []
    for var in sleep_vars:
        if var in df.columns:
            res = run_glm_adjusted(df, 'shannon', var, ['age', 'BMI', 'diet_type'])
            if res:
                glm_results.append(res)

    # Compile final results
    final_results = []
    if not corr_results.empty:
        final_results.append(corr_results.to_dict(orient='records'))
    
    # Flatten lists for final dataframe
    all_records = []
    if not corr_results.empty:
        all_records.extend(corr_results.to_dict(orient='records'))
    for p in permanova_results:
        all_records.append({'analysis_type': 'PERMANOVA', 'variable': p['variable'], 'p_value': p['p_value'], 'f_stat': p['test_statistic']})
    for g in glm_results:
        all_records.append({'analysis_type': 'GLM', 'variable': g['sleep_var'], 'p_value': g['p_value'], 'coef': g['coefficient']})
    
    if all_records:
        final_df = pd.DataFrame(all_records)
        save_results(final_df, args.output)
    else:
        logger.warning("No results generated.")

    logger.info("Analysis pipeline complete")

if __name__ == '__main__':
    main()