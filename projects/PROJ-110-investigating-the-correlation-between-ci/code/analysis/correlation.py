"""
Correlation Analysis Module for Circadian Gene Expression and Metabolic Traits.

Implements FR-007: Compute correlations between circadian gene expression
and continuous metabolic traits (BMI, Glucose, BP, TG, HDL).
"""

import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats

from utils.logging import get_logger

logger = get_logger(__name__)


def _check_normality(data: pd.Series) -> Tuple[bool, float]:
    """
    Perform Shapiro-Wilk test for normality.

    Args:
        data: A pandas Series of values.

    Returns:
        Tuple of (is_normal, p_value).
        Returns False if sample size is too small (< 3).
    """
    if len(data) < 3:
        logger.warning(f"Sample size too small ({len(data)}) for Shapiro-Wilk test. Assuming non-normal.")
        return False, 0.0

    try:
        _, p_value = stats.shapiro(data.dropna())
        is_normal = p_value > 0.05
        return is_normal, p_value
    except Exception as e:
        logger.warning(f"Shapiro-Wilk test failed for series: {e}. Assuming non-normal.")
        return False, 0.0


def generate_correlation_analysis(
    expression_df: pd.DataFrame,
    phenotype_df: pd.DataFrame,
    gene_list: List[str],
    trait_columns: List[str],
    fdr_threshold: float = 0.05,
    fdr_adjusted_pvalues: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Compute Spearman or Pearson correlations between gene expression and continuous traits.

    The method (Spearman vs Pearson) is selected dynamically based on a normality check
    (Shapiro-Wilk) of the combined data. If data is non-normal, Spearman is used.

    Args:
        expression_df: DataFrame of gene expression (rows=samples, cols=genes).
        phenotype_df: DataFrame of phenotypic traits (rows=samples, cols=traits).
        gene_list: List of gene symbols to analyze.
        trait_columns: List of continuous trait column names in phenotype_df.
        fdr_threshold: Threshold for FDR-adjusted p-values to determine significance.
        fdr_adjusted_pvalues: Optional DataFrame of pre-computed FDR-adjusted p-values
                             (e.g., from T024). If provided, significance is determined
                             by checking if the gene's FDR < fdr_threshold.
                             If None, significance is determined by raw p-value < fdr_threshold.

    Returns:
        DataFrame with columns: [gene, trait, r, p, significance_flag]
        where significance_flag is "significant" if criteria met, else "exploratory".
    """
    logger.info(f"Starting correlation analysis for {len(gene_list)} genes and {len(trait_columns)} traits.")

    # Ensure common index (sample IDs)
    # Assuming both dataframes have a common identifier or index.
    # If not, we assume they are aligned by index.
    if not expression_df.index.equals(phenotype_df.index):
        # Attempt to align by index if possible, or warn
        logger.warning("Expression and Phenotype indices do not match. Attempting alignment.")
        common_idx = expression_df.index.intersection(phenotype_df.index)
        if len(common_idx) == 0:
            raise ValueError("No common sample indices found between expression and phenotype data.")
        expression_df = expression_df.loc[common_idx]
        phenotype_df = phenotype_df.loc[common_idx]
        logger.info(f"Aligned on {len(common_idx)} common samples.")

    results = []

    # Determine correlation method per gene-trait pair or globally?
    # FR-007 implies checking normality. We will check normality for each gene-trait pair
    # or conservatively check the expression data distribution.
    # For robustness, we check the distribution of the gene expression and the trait.
    # If either is non-normal, use Spearman.

    for gene in gene_list:
        if gene not in expression_df.columns:
            logger.warning(f"Gene {gene} not found in expression data. Skipping.")
            continue

        gene_series = expression_df[gene]

        for trait in trait_columns:
            if trait not in phenotype_df.columns:
                logger.warning(f"Trait {trait} not found in phenotype data. Skipping.")
                continue

            trait_series = phenotype_df[trait]

            # Drop pairs with missing values
            mask = ~(gene_series.isna() | trait_series.isna())
            if mask.sum() < 3:
                logger.warning(f"Insufficient data for {gene} vs {trait} ({mask.sum()} samples). Skipping.")
                continue

            g_clean = gene_series[mask]
            t_clean = trait_series[mask]

            # Check normality (Shapiro-Wilk) on the cleaned data
            # We check the combined distribution or the marginal distributions?
            # Standard practice: if either variable is non-normal, use Spearman.
            g_normal, _ = _check_normality(g_clean)
            t_normal, _ = _check_normality(t_clean)

            if g_normal and t_normal:
                method = "pearson"
            else:
                method = "spearman"

            try:
                if method == "pearson":
                    r, p = stats.pearsonr(g_clean, t_clean)
                else:
                    r, p = stats.spearmanr(g_clean, t_clean)

                # Determine significance
                # If FDR adjusted p-values are provided, we use those for significance
                # However, the FDR correction from T024 is typically for differential expression (MetS vs Control).
                # The task says: "significance_flag is 'significant' if FDR < 0.05 (from T024) else 'exploratory'".
                # This implies we are re-using the FDR status of the gene from the DE analysis.
                # If T024 provided a mapping of gene -> FDR, we use that.
                # If not, we fall back to raw p-value for this specific correlation test,
                # but the prompt specifically references T024's FDR.
                
                is_significant = False
                if fdr_adjusted_pvalues is not None:
                    # Check if the gene is in the FDR table
                    if gene in fdr_adjusted_pvalues.index:
                        # Assuming fdr_adjusted_pvalues has a column 'p_adj' or similar
                        # We need to be flexible here. Let's assume it has 'p_adj'
                        fdr_val = fdr_adjusted_pvalues.loc[gene, 'p_adj'] if isinstance(fdr_adjusted_pvalues, pd.DataFrame) else fdr_adjusted_pvalues.get(gene)
                        if isinstance(fdr_val, pd.Series):
                            fdr_val = fdr_val['p_adj']
                        if pd.notna(fdr_val) and fdr_val < fdr_threshold:
                            is_significant = True
                    else:
                        # Gene not in DE results, treat as exploratory
                        is_significant = False
                else:
                    # Fallback: use raw p-value if no FDR table provided
                    if p < fdr_threshold:
                        is_significant = True

                flag = "significant" if is_significant else "exploratory"

                results.append({
                    "gene": gene,
                    "trait": trait,
                    "r": r,
                    "p": p,
                    "method": method,
                    "significance_flag": flag
                })

            except Exception as e:
                logger.error(f"Error computing correlation for {gene} vs {trait}: {e}")
                continue

    if not results:
        logger.warning("No correlation results generated.")
        return pd.DataFrame(columns=["gene", "trait", "r", "p", "significance_flag"])

    df_results = pd.DataFrame(results)
    # Ensure column order
    df_results = df_results[["gene", "trait", "r", "p", "significance_flag"]]
    
    logger.info(f"Correlation analysis complete. Generated {len(df_results)} results.")
    return df_results
