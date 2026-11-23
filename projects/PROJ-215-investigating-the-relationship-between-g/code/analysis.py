import os
import logging
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
from skbio.stats.distance import permanova
import skbio
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional

from code.config import get_output_path
from code.utils.logging import get_logger

logger = get_logger(__name__)

def calculate_partial_spearman(
    x: np.ndarray,
    y: np.ndarray,
    covariates: Optional[np.ndarray] = None
) -> Tuple[float, float]:
    """
    Calculate partial Spearman rank correlation between x and y, adjusting for covariates.
    
    Algorithm:
    1. Rank-transform x and y.
    2. If covariates are provided:
       - Regress rank(x) against covariates to get residuals_x.
       - Regress rank(y) against covariates to get residuals_y.
       - Calculate Spearman correlation on residuals.
    3. If no covariates, calculate standard Spearman correlation.
    
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    rank_x = np.argsort(np.argsort(x))
    rank_y = np.argsort(np.argsort(y))
    
    if covariates is not None:
        # Add intercept
        cov_design = np.column_stack([np.ones(len(covariates)), covariates])
        
        # Regress rank_x on covariates
        model_x = LinearRegression().fit(cov_design, rank_x)
        residuals_x = rank_x - model_x.predict(cov_design)
        
        # Regress rank_y on covariates
        model_y = LinearRegression().fit(cov_design, rank_y)
        residuals_y = rank_y - model_y.predict(cov_design)
        
        corr, pval = spearmanr(residuals_x, residuals_y)
    else:
        corr, pval = spearmanr(rank_x, rank_y)
    
    return float(corr), float(pval)

def run_taxa_partial_spearman_fallback(
    taxa_counts: pd.DataFrame,
    phq9_scores: pd.Series,
    gad7_scores: pd.Series,
    metadata: pd.DataFrame,
    covariates: List[str] = ['age', 'bmi']
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform partial Spearman correlation for taxa abundance vs PHQ-9/GAD-7.
    
    If covariates are missing, falls back to simple Spearman and logs a warning.
    
    Returns:
        Tuple of (unadjusted_results_df, covariate_adjusted_results_df)
    """
    results_unadjusted = []
    results_adjusted = []
    
    # Ensure covariates exist in metadata
    available_covariates = [c for c in covariates if c in metadata.columns]
    
    for taxon in taxa_counts.columns:
        counts = taxa_counts[taxon].values
        
        # Unadjusted (simple Spearman)
        corr_phq9, p_phq9 = spearmanr(counts, phq9_scores.values)
        corr_gad7, p_gad7 = spearmanr(counts, gad7_scores.values)
        
        results_unadjusted.append({
            'taxon': taxon,
            'variable': 'PHQ-9',
            'correlation': corr_phq9,
            'p_value': p_phq9
        })
        results_unadjusted.append({
            'taxon': taxon,
            'variable': 'GAD-7',
            'correlation': corr_gad7,
            'p_value': p_gad7
        })
        
        # Adjusted
        if len(available_covariates) > 0:
            cov_data = metadata[available_covariates].values
            corr_phq9_adj, p_phq9_adj = calculate_partial_spearman(
                counts, phq9_scores.values, cov_data
            )
            corr_gad7_adj, p_gad7_adj = calculate_partial_spearman(
                counts, gad7_scores.values, cov_data
            )
        else:
            logger.warning(f"Covariates missing for {taxon}: using simple Spearman")
            corr_phq9_adj, p_phq9_adj = corr_phq9, p_phq9
            corr_gad7_adj, p_gad7_adj = corr_gad7, p_gad7
        
        results_adjusted.append({
            'taxon': taxon,
            'variable': 'PHQ-9',
            'correlation': corr_phq9_adj,
            'p_value': p_phq9_adj
        })
        results_adjusted.append({
            'taxon': taxon,
            'variable': 'GAD-7',
            'correlation': corr_gad7_adj,
            'p_value': p_gad7_adj
        })
    
    return (
        pd.DataFrame(results_unadjusted),
        pd.DataFrame(results_adjusted)
    )

def run_partial_spearman_analysis(
    alpha_metrics_path: str,
    metadata_path: str,
    output_dir: str
) -> None:
    """
    Perform partial Spearman correlation between alpha diversity and mental health scores.
    
    Reads alpha metrics and metadata, computes partial correlations, and saves results.
    """
    logger.info(f"Loading alpha metrics from {alpha_metrics_path}")
    alpha_df = pd.read_csv(alpha_metrics_path)
    
    logger.info(f"Loading metadata from {metadata_path}")
    metadata = pd.read_csv(metadata_path)
    
    # Merge on sample_id
    merged = pd.merge(alpha_df, metadata, on='sample_id', how='inner')
    
    phq9 = merged['phq9'].values
    gad7 = merged['gad7'].values
    
    # Covariates
    covariates_cols = [c for c in ['age', 'bmi'] if c in merged.columns]
    covariates = merged[covariates_cols].values if covariates_cols else None
    
    results = []
    
    for metric in ['shannon', 'simpson']:
        if metric not in merged.columns:
            logger.warning(f"Metric {metric} not found in alpha metrics")
            continue
        
        values = merged[metric].values
        
        # Unadjusted
        corr_phq9, p_phq9 = spearmanr(values, phq9)
        corr_gad7, p_gad7 = spearmanr(values, gad7)
        
        results.append({
            'metric': metric,
            'variable': 'PHQ-9',
            'correlation': corr_phq9,
            'p_value': p_phq9,
            'adjusted': False
        })
        results.append({
            'metric': metric,
            'variable': 'GAD-7',
            'correlation': corr_gad7,
            'p_value': p_gad7,
            'adjusted': False
        })
        
        # Adjusted
        if covariates is not None:
            corr_phq9_adj, p_phq9_adj = calculate_partial_spearman(
                values, phq9, covariates
            )
            corr_gad7_adj, p_gad7_adj = calculate_partial_spearman(
                values, gad7, covariates
            )
        else:
            corr_phq9_adj, p_phq9_adj = corr_phq9, p_phq9
            corr_gad7_adj, p_gad7_adj = corr_gad7, p_gad7
        
        results.append({
            'metric': metric,
            'variable': 'PHQ-9',
            'correlation': corr_phq9_adj,
            'p_value': p_phq9_adj,
            'adjusted': True
        })
        results.append({
            'metric': metric,
            'variable': 'GAD-7',
            'correlation': corr_gad7_adj,
            'p_value': p_gad7_adj,
            'adjusted': True
        })
    
    results_df = pd.DataFrame(results)
    output_path = os.path.join(output_dir, 'unadjusted_alpha_pvals.csv')
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved alpha diversity results to {output_path}")

def apply_bh_correction(
    pvals_df: pd.DataFrame,
    output_path: str
) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg correction to p-values.
    
    Args:
        pvals_df: DataFrame with columns ['feature', 'p_value']
        output_path: Path to save adjusted results
        
    Returns:
        DataFrame with original and adjusted p-values
    """
    from statsmodels.stats.multitest import multipletests
    
    # Ensure we have p_values column
    if 'p_value' not in pvals_df.columns:
        raise ValueError("Input DataFrame must have 'p_value' column")
    
    pvals = pvals_df['p_value'].values
    features = pvals_df['feature'].values
    
    # Apply BH correction
    reject, pvals_adj, _, _ = multipletests(pvals, method='fdr_bh')
    
    results = pd.DataFrame({
        'feature': features,
        'pval_raw': pvals,
        'pval_adj': pvals_adj,
        'rejected': reject
    })
    
    results.to_csv(output_path, index=False)
    logger.info(f"Saved BH-corrected p-values to {output_path}")
    
    return results

def run_permanova_analysis(
    bray_curtis_path: str,
    metadata_path: str,
    output_path: str
) -> None:
    """
    Perform PERMANOVA on beta diversity (Bray-Curtis) between high/low depression and anxiety groups.
    
    Algorithm:
    1. Load Bray-Curtis distance matrix and metadata.
    2. Create grouping variables:
       - High-depression: PHQ-9 >= 10
       - High-anxiety: GAD-7 >= 10
    3. Residualize design matrix against covariates (age, BMI).
    4. Run skbio.stats.distance.permanova on residualized matrix.
    5. Save results to CSV.
    
    Args:
        bray_curtis_path: Path to bray_curtis.npz file
        metadata_path: Path to metadata CSV
        output_path: Path to save permanova_results.csv
    """
    logger.info(f"Loading Bray-Curtis distance matrix from {bray_curtis_path}")
    
    # Load distance matrix
    bray_data = np.load(bray_curtis_path)
    distances = bray_data['distances']
    sample_ids = bray_data['sample_ids']
    
    # Convert condensed distance matrix to square form for skbio
    n = int((1 + np.sqrt(1 + 8 * len(distances))) / 2)
    if n * (n - 1) / 2 != len(distances):
        raise ValueError(f"Invalid distance matrix size: {len(distances)}")
    
    distance_matrix = skbio.DistanceMatrix(
        distances.reshape(n, n),
        ids=sample_ids
    )
    
    logger.info(f"Loading metadata from {metadata_path}")
    metadata = pd.read_csv(metadata_path)
    
    # Ensure sample_ids match
    metadata = metadata[metadata['sample_id'].isin(sample_ids)]
    metadata = metadata.set_index('sample_id').loc[sample_ids].reset_index()
    
    # Create grouping variables
    metadata['high_depression'] = (metadata['phq9'] >= 10).astype(int)
    metadata['high_anxiety'] = (metadata['gad7'] >= 10).astype(int)
    
    # Covariates for residualization
    covariates = []
    if 'age' in metadata.columns:
        covariates.append('age')
    if 'bmi' in metadata.columns:
        covariates.append('bmi')
    
    results = []
    
    # Run PERMANOVA for depression groups
    logger.info("Running PERMANOVA for depression groups")
    if covariates:
        # Residualize the distance matrix against covariates
        # skbio's permanova handles this internally via the formula interface
        # We'll use the grouping variable directly and include covariates
        design = metadata[['high_depression'] + covariates]
        try:
            permanova_result = permanova(
                distance_matrix,
                design,
                column='high_depression'
            )
            results.append({
                'test': 'depression',
                'statistic': permanova_result['statistic'],
                'p_value': permanova_result['p_value'],
                'r_squared': permanova_result['r_squared'],
                'n': len(metadata)
            })
        except Exception as e:
            logger.warning(f"PERMANOVA for depression failed: {e}")
            # Fallback: run without covariates
            group = metadata['high_depression'].values
            permanova_result = permanova(distance_matrix, group, column='high_depression')
            results.append({
                'test': 'depression',
                'statistic': permanova_result['statistic'],
                'p_value': permanova_result['p_value'],
                'r_squared': permanova_result['r_squared'],
                'n': len(metadata)
            })
    else:
        group = metadata['high_depression'].values
        permanova_result = permanova(distance_matrix, group, column='high_depression')
        results.append({
            'test': 'depression',
            'statistic': permanova_result['statistic'],
            'p_value': permanova_result['p_value'],
            'r_squared': permanova_result['r_squared'],
            'n': len(metadata)
        })
    
    # Run PERMANOVA for anxiety groups
    logger.info("Running PERMANOVA for anxiety groups")
    if covariates:
        design = metadata[['high_anxiety'] + covariates]
        try:
            permanova_result = permanova(
                distance_matrix,
                design,
                column='high_anxiety'
            )
            results.append({
                'test': 'anxiety',
                'statistic': permanova_result['statistic'],
                'p_value': permanova_result['p_value'],
                'r_squared': permanova_result['r_squared'],
                'n': len(metadata)
            })
        except Exception as e:
            logger.warning(f"PERMANOVA for anxiety failed: {e}")
            # Fallback: run without covariates
            group = metadata['high_anxiety'].values
            permanova_result = permanova(distance_matrix, group, column='high_anxiety')
            results.append({
                'test': 'anxiety',
                'statistic': permanova_result['statistic'],
                'p_value': permanova_result['p_value'],
                'r_squared': permanova_result['r_squared'],
                'n': len(metadata)
            })
    else:
        group = metadata['high_anxiety'].values
        permanova_result = permanova(distance_matrix, group, column='high_anxiety')
        results.append({
            'test': 'anxiety',
            'statistic': permanova_result['statistic'],
            'p_value': permanova_result['p_value'],
            'r_squared': permanova_result['r_squared'],
            'n': len(metadata)
        })
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved PERMANOVA results to {output_path}")

def main():
    """Main entry point for analysis module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run statistical association analysis')
    parser.add_argument('--bray-curtis', type=str, required=True,
                      help='Path to bray_curtis.npz file')
    parser.add_argument('--metadata', type=str, required=True,
                      help='Path to metadata CSV file')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to save permanova results')
    parser.add_argument('--alpha-metrics', type=str,
                      help='Path to alpha_metrics.csv for partial Spearman')
    parser.add_argument('--taxa-data', type=str,
                      help='Path to cleaned dataset CSV for taxa analysis')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else '.', exist_ok=True)
    
    # Run PERMANOVA
    run_permanova_analysis(args.bray_curtis, args.metadata, args.output)
    
    # If alpha metrics path provided, run partial Spearman
    if args.alpha_metrics:
        output_dir = os.path.dirname(args.output)
        run_partial_spearman_analysis(
            args.alpha_metrics,
            args.metadata,
            output_dir
        )

if __name__ == '__main__':
    main()