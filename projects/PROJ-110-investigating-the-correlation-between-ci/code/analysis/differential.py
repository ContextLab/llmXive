import logging
from typing import Dict, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from scipy import stats
from utils.logging import get_logger

logger = get_logger(__name__)

def stratify_by_tissue(
    expression_df: pd.DataFrame,
    phenotype_df: pd.DataFrame,
    min_samples_per_group: int = 20
) -> Dict[str, Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Group samples by tissue type and filter out tissues with insufficient sample sizes.
    
    Args:
        expression_df: DataFrame with gene expression data (index: sample_id)
        phenotype_df: DataFrame with phenotype data including 'tissue' and 'MetS_status'
        min_samples_per_group: Minimum samples required per group (MetS/Control) in a tissue
        
    Returns:
        Dictionary mapping tissue name to (expression_subset, phenotype_subset)
    """
    logger.info(f"Stratifying by tissue with minimum {min_samples_per_group} samples per group")
    
    if 'tissue' not in phenotype_df.columns or 'MetS_status' not in phenotype_df.columns:
        raise ValueError("Phenotype DataFrame must contain 'tissue' and 'MetS_status' columns")
        
    strata = {}
    
    for tissue, group in phenotype_df.groupby('tissue'):
        # Count samples in each MetS status group for this tissue
        met_s_count = group[group['MetS_status'] == 'MetS'].shape[0]
        control_count = group[group['MetS_status'] == 'Control'].shape[0]
        
        if met_s_count >= min_samples_per_group and control_count >= min_samples_per_group:
            tissue_phenotype = group
            tissue_samples = tissue_phenotype.index.tolist()
            
            # Filter expression data to these samples
            if expression_df.index.isin(tissue_samples).all():
                tissue_expression = expression_df.loc[tissue_samples]
            else:
                # Handle case where expression index might not match exactly
                common_samples = [s for s in tissue_samples if s in expression_df.index]
                if len(common_samples) >= min_samples_per_group * 2:
                    tissue_expression = expression_df.loc[common_samples]
                    tissue_phenotype = phenotype_df.loc[common_samples]
                else:
                    logger.warning(f"Tissue {tissue} has insufficient matching samples after merge")
                    continue
            
            strata[tissue] = (tissue_expression, tissue_phenotype)
            logger.info(f"Tissue '{tissue}': {met_s_count} MetS, {control_count} Control (kept)")
        else:
            logger.warning(f"Tissue '{tissue}' excluded: {met_s_count} MetS, {control_count} Control (min {min_samples_per_group} required)")
            
    logger.info(f"Stratification complete. {len(strata)} tissues passed power filter.")
    return strata

def run_wilcoxon_tests(
    expression_df: pd.DataFrame,
    phenotype_df: pd.DataFrame,
    genes: List[str]
) -> pd.DataFrame:
    """
    Perform Wilcoxon rank-sum tests for each gene between MetS and Control groups.
    
    Args:
        expression_df: DataFrame with gene expression data (index: sample_id, columns: genes)
        phenotype_df: DataFrame with 'MetS_status' column
        genes: List of gene names to test
        
    Returns:
        DataFrame with columns: gene, statistic, p_value
    """
    logger.info(f"Running Wilcoxon tests for {len(genes)} genes")
    
    results = []
    
    for gene in genes:
        if gene not in expression_df.columns:
            logger.warning(f"Gene {gene} not found in expression data, skipping")
            continue
            
        # Split data by group
        met_s_mask = phenotype_df['MetS_status'] == 'MetS'
        control_mask = phenotype_df['MetS_status'] == 'Control'
        
        met_s_vals = expression_df.loc[met_s_mask, gene].dropna()
        control_vals = expression_df.loc[control_mask, gene].dropna()
        
        if len(met_s_vals) < 2 or len(control_vals) < 2:
            logger.warning(f"Insufficient samples for {gene}, skipping")
            continue
            
        # Perform Wilcoxon rank-sum test
        statistic, p_value = stats.ranksums(met_s_vals, control_vals)
        
        results.append({
            'gene': gene,
            'statistic': statistic,
            'p_value': p_value,
            'n_met_s': len(met_s_vals),
            'n_control': len(control_vals)
        })
        
    df_results = pd.DataFrame(results)
    logger.info(f"Wilcoxon tests complete. {len(df_results)} genes tested.")
    return df_results

def apply_fdr_correction(
    df_results: pd.DataFrame,
    p_column: str = 'p_value',
    method: str = 'benjamini_hochberg'
) -> pd.DataFrame:
    """
    Apply False Discovery Rate correction to p-values.
    
    Args:
        df_results: DataFrame with p-values
        p_column: Name of the column containing p-values
        method: Correction method (currently only 'benjamini_hochberg' supported)
        
    Returns:
        DataFrame with added 'p_adj' column
    """
    logger.info(f"Applying {method} FDR correction")
    
    if method != 'benjamini_hochberg':
        raise ValueError(f"Method {method} not implemented. Use 'benjamini_hochberg'.")
        
    p_values = df_results[p_column].values
    
    # Benjamini-Hochberg procedure
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate adjusted p-values
    adj_p = np.zeros(n)
    for i in range(n):
        adj_p[sorted_indices[i]] = sorted_p[i] * n / (i + 1)
    
    # Ensure monotonicity (cumulative min from largest to smallest)
    # Reverse, take cummin, reverse back
    adj_p = np.minimum.accumulate(adj_p[::-1])[::-1]
    adj_p = np.clip(adj_p, 0, 1)
    
    df_results = df_results.copy()
    df_results['p_adj'] = adj_p
    
    logger.info(f"FDR correction complete. {np.sum(adj_p < 0.05)} genes significant at FDR < 0.05")
    return df_results

def compute_effect_sizes(
    expression_df: pd.DataFrame,
    phenotype_df: pd.DataFrame,
    genes: List[str]
) -> pd.DataFrame:
    """
    Calculate Cohen's d effect sizes for each gene between MetS and Control groups.
    
    Cohen's d = (mean1 - mean2) / pooled_std
    where pooled_std = sqrt(((n1-1)*std1^2 + (n2-1)*std2^2) / (n1 + n2 - 2))
    
    Args:
        expression_df: DataFrame with gene expression data (index: sample_id, columns: genes)
        phenotype_df: DataFrame with 'MetS_status' column
        genes: List of gene names to calculate effect sizes for
        
    Returns:
        DataFrame with columns: gene, mean_met_s, mean_control, std_met_s, std_control, 
                               n_met_s, n_control, cohens_d
    """
    logger.info(f"Computing effect sizes for {len(genes)} genes")
    
    results = []
    
    for gene in genes:
        if gene not in expression_df.columns:
            logger.warning(f"Gene {gene} not found in expression data, skipping")
            continue
            
        # Split data by group
        met_s_mask = phenotype_df['MetS_status'] == 'MetS'
        control_mask = phenotype_df['MetS_status'] == 'Control'
        
        met_s_vals = expression_df.loc[met_s_mask, gene].dropna()
        control_vals = expression_df.loc[control_mask, gene].dropna()
        
        n_met_s = len(met_s_vals)
        n_control = len(control_vals)
        
        if n_met_s < 2 or n_control < 2:
            logger.warning(f"Insufficient samples for {gene}, skipping")
            continue
            
        mean_met_s = met_s_vals.mean()
        mean_control = control_vals.mean()
        std_met_s = met_s_vals.std(ddof=1)
        std_control = control_vals.std(ddof=1)
        
        # Calculate pooled standard deviation
        # pooled_std = sqrt(((n1-1)*s1^2 + (n2-1)*s2^2) / (n1 + n2 - 2))
        pooled_var = ((n_met_s - 1) * (std_met_s ** 2) + (n_control - 1) * (std_control ** 2)) / (n_met_s + n_control - 2)
        pooled_std = np.sqrt(pooled_var)
        
        # Calculate Cohen's d
        if pooled_std == 0:
            cohens_d = 0.0
        else:
            cohens_d = (mean_met_s - mean_control) / pooled_std
        
        results.append({
            'gene': gene,
            'mean_met_s': mean_met_s,
            'mean_control': mean_control,
            'std_met_s': std_met_s,
            'std_control': std_control,
            'n_met_s': n_met_s,
            'n_control': n_control,
            'cohens_d': cohens_d
        })
        
    df_results = pd.DataFrame(results)
    logger.info(f"Effect size computation complete. {len(df_results)} genes processed.")
    return df_results
