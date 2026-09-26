import os
import logging
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
from code.config import get_output_path
from code.utils.logging import get_logger

logger = get_logger(__name__)

def calculate_partial_spearman_alpha(
    diversity_col: str,
    mental_health_col: str,
    covariates: list,
    df: pd.DataFrame
) -> tuple:
    """
    Calculate partial Spearman rank correlation between alpha diversity
    and mental health scores, adjusting for covariates.

    Implementation: Regress diversity and scores against covariates to obtain
    residuals, then calculate Spearman correlation on residuals.

    Args:
        diversity_col: Column name for alpha diversity metric
        mental_health_col: Column name for mental health score (PHQ-9 or GAD-7)
        covariates: List of column names for covariates (e.g., ['age', 'bmi'])
        df: DataFrame containing all required columns

    Returns:
        tuple: (correlation_coefficient, p_value)
    """
    # Ensure all required columns exist
    required_cols = [diversity_col, mental_health_col] + covariates
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Drop rows with any NaN in required columns
    clean_df = df.dropna(subset=required_cols)

    if len(clean_df) < 3:
        logger.warning(f"Not enough samples ({len(clean_df)}) for partial correlation")
        return 0.0, 1.0

    # Extract variables
    y_div = clean_df[diversity_col].values
    y_mh = clean_df[mental_health_col].values
    X_cov = clean_df[covariates].values

    # Fit linear models to get residuals
    model_div = LinearRegression()
    model_div.fit(X_cov, y_div)
    residuals_div = y_div - model_div.predict(X_cov)

    model_mh = LinearRegression()
    model_mh.fit(X_cov, y_mh)
    residuals_mh = y_mh - model_mh.predict(X_cov)

    # Calculate Spearman correlation on residuals
    corr, pval = spearmanr(residuals_div, residuals_mh)

    return corr, pval

def calculate_partial_spearman_taxa(
    taxa_df: pd.DataFrame,
    mental_health_col: str,
    covariates: list,
    metadata_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Perform partial Spearman correlation for each taxon abundance vs mental health.

    Implementation: Regress each taxon and the mental health score against covariates
    to obtain residuals, then calculate Spearman correlation on residuals.

    Args:
        taxa_df: DataFrame with taxon abundances (rows=samples, cols=taxa)
        mental_health_col: Column name for mental health score (PHQ-9 or GAD-7)
        covariates: List of column names for covariates (e.g., ['age', 'bmi'])
        metadata_df: DataFrame with mental health scores and covariates (indexed by sample_id)

    Returns:
        DataFrame with columns: taxon, correlation, p_value
    """
    # Align taxa and metadata by index (sample_id)
    common_samples = taxa_df.index.intersection(metadata_df.index)
    if len(common_samples) == 0:
        raise ValueError("No common samples between taxa and metadata")

    taxa_aligned = taxa_df.loc[common_samples]
    meta_aligned = metadata_df.loc[common_samples]

    # Ensure mental health and covariates exist
    required_cols = [mental_health_col] + covariates
    missing = [c for c in required_cols if c not in meta_aligned.columns]
    if missing:
        raise ValueError(f"Missing columns in metadata: {missing}")

    # Drop rows with NaN in any required column
    valid_mask = meta_aligned[required_cols].notna().all(axis=1)
    taxa_clean = taxa_aligned[valid_mask]
    meta_clean = meta_aligned[valid_mask]

    if len(meta_clean) < 3:
        logger.warning(f"Not enough valid samples ({len(meta_clean)}) for taxa analysis")
        return pd.DataFrame(columns=['taxon', 'correlation', 'p_value'])

    results = []
    covariates_arr = meta_clean[covariates].values
    mh_scores = meta_clean[mental_health_col].values

    # Pre-fit mental health model (same for all taxa)
    model_mh = LinearRegression()
    model_mh.fit(covariates_arr, mh_scores)
    residuals_mh = mh_scores - model_mh.predict(covariates_arr)

    logger.info(f"Processing {len(taxa_clean.columns)} taxa...")

    for taxon in taxa_clean.columns:
        taxon_abundance = taxa_clean[taxon].values

        # Skip if all zeros or constant
        if np.all(taxon_abundance == 0) or np.std(taxon_abundance) == 0:
            results.append({'taxon': taxon, 'correlation': 0.0, 'p_value': 1.0})
            continue

        # Fit model for this taxon
        model_taxon = LinearRegression()
        model_taxon.fit(covariates_arr, taxon_abundance)
        residuals_taxon = taxon_abundance - model_taxon.predict(covariates_arr)

        # Calculate Spearman correlation
        corr, pval = spearmanr(residuals_taxon, residuals_mh)

        # Handle NaN/inf cases
        if np.isnan(corr):
            corr = 0.0
        if np.isnan(pval):
            pval = 1.0

        results.append({
            'taxon': taxon,
            'correlation': corr,
            'p_value': pval
        })

    return pd.DataFrame(results)

def save_unadjusted_alpha_pvals(
    results_df: pd.DataFrame,
    output_path: str
):
    """
    Save unadjusted alpha diversity p-values to CSV.

    Args:
        results_df: DataFrame with columns: diversity_metric, mental_health, correlation, p_value
        output_path: Path to output CSV file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved alpha p-values to {output_path}")

def save_unadjusted_taxa_pvals(
    results_df: pd.DataFrame,
    output_path: str
):
    """
    Save unadjusted taxa p-values to CSV.

    Args:
        results_df: DataFrame with columns: taxon, correlation, p_value
        output_path: Path to output CSV file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved taxa p-values to {output_path}")

def main():
    """
    Main function to run partial Spearman correlation for taxa abundance vs PHQ-9/GAD-7.
    """
    logger.info("Starting partial Spearman correlation analysis for taxa...")

    # Load preprocessed taxa data
    taxa_path = get_output_path('data/processed/taxa_preprocessed.csv')
    if not os.path.exists(taxa_path):
        raise FileNotFoundError(f"Taxa data not found at {taxa_path}. Run preprocessing first.")

    taxa_df = pd.read_csv(taxa_path, index_col=0)

    # Load metadata with mental health scores and covariates
    metadata_path = get_output_path('data/processed/metadata_cleaned.csv')
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata not found at {metadata_path}. Run data ingestion first.")

    metadata_df = pd.read_csv(metadata_path, index_col=0)

    # Define covariates
    covariates = ['age', 'bmi']

    # Run analysis for PHQ-9
    logger.info("Running analysis for PHQ-9...")
    try:
        phq_results = calculate_partial_spearman_taxa(
            taxa_df, 'phq9', covariates, metadata_df
        )
        phq_output = get_output_path('data/interim/unadjusted_taxa_phq9_pvals.csv')
        save_unadjusted_taxa_pvals(phq_results, phq_output)
    except Exception as e:
        logger.error(f"Failed PHQ-9 analysis: {e}")
        raise

    # Run analysis for GAD-7
    logger.info("Running analysis for GAD-7...")
    try:
        gad_results = calculate_partial_spearman_taxa(
            taxa_df, 'gad7', covariates, metadata_df
        )
        gad_output = get_output_path('data/interim/unadjusted_taxa_gad7_pvals.csv')
        save_unadjusted_taxa_pvals(gad_results, gad_output)
    except Exception as e:
        logger.error(f"Failed GAD-7 analysis: {e}")
        raise

    # Combine results for unified output as requested by T020a
    # The task specifies saving to unadjusted_taxa_pvals.csv
    combined_results = pd.concat([
        phq_results.assign(mental_health='phq9'),
        gad_results.assign(mental_health='gad7')
    ], ignore_index=True)

    output_path = get_output_path('data/interim/unadjusted_taxa_pvals.csv')
    save_unadjusted_taxa_pvals(combined_results, output_path)

    logger.info("Taxa partial Spearman correlation analysis complete.")
    return combined_results

if __name__ == '__main__':
    main()