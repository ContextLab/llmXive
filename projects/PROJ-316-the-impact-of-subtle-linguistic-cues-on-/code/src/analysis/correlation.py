import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

def compute_correlations(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> pd.DataFrame:
    """
    Compute Pearson and Spearman correlations between linguistic features and authenticity scores.
    
    Args:
        df: DataFrame containing features and target column
        feature_cols: List of feature column names
        target_col: Name of the target column (authenticity_score)
        
    Returns:
        DataFrame with correlation results including method, coefficient, p-value
    """
    results = []
    
    for feature in feature_cols:
        if feature not in df.columns or target_col not in df.columns:
            logger.warning(f"Skipping {feature}: column not found")
            continue
        
        # Drop rows with NaN in either column
        valid_data = df[[feature, target_col]].dropna()
        
        if len(valid_data) < 3:
            logger.warning(f"Skipping {feature}: insufficient data points after NaN removal")
            continue
        
        # Pearson correlation
        pearson_corr, pearson_p = stats.pearsonr(valid_data[feature], valid_data[target_col])
        
        # Spearman correlation
        spearman_corr, spearman_p = stats.spearmanr(valid_data[feature], valid_data[target_col])
        
        results.append({
            'feature': feature,
            'method': 'pearson',
            'coefficient': pearson_corr,
            'p_value': pearson_p
        })
        
        results.append({
            'feature': feature,
            'method': 'spearman',
            'coefficient': spearman_corr,
            'p_value': spearman_p
        })
    
    return pd.DataFrame(results)

def apply_bh_correction(results_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """
    Apply Benjamini-Hochberg multiple-comparison correction to p-values.
    
    This controls the False Discovery Rate (FDR) across multiple hypothesis tests.
    
    Args:
        results_df: DataFrame with columns ['feature', 'method', 'coefficient', 'p_value']
        alpha: Significance level for FDR control (default 0.05)
        
    Returns:
        DataFrame with additional columns: 'p_value_bh', 'is_significant_bh'
        
    Raises:
        ValueError: If required columns are missing
    """
    if not {'p_value'}.issubset(results_df.columns):
        raise ValueError("Input DataFrame must contain 'p_value' column")
    
    # Make a copy to avoid modifying the original
    df = results_df.copy()
    
    # Sort by p-value
    df = df.sort_values('p_value').reset_index(drop=True)
    
    n = len(df)
    if n == 0:
        df['p_value_bh'] = np.nan
        df['is_significant_bh'] = False
        return df
    
    # Calculate BH adjusted p-values
    # For each p-value at rank i (1-indexed), adjusted p = p * n / i
    # Then ensure monotonicity by taking cumulative minimum from bottom up
    
    ranks = np.arange(1, n + 1)
    raw_p_values = df['p_value'].values
    
    # Calculate BH adjusted p-values
    bh_p_values = raw_p_values * n / ranks
    
    # Enforce monotonicity: adjusted p-value at rank i should be <= adjusted p-value at rank i+1
    # We do this by taking cumulative minimum from the end
    bh_p_values = np.minimum.accumulate(bh_p_values[::-1])[::-1]
    
    # Ensure no adjusted p-value exceeds 1.0
    bh_p_values = np.minimum(bh_p_values, 1.0)
    
    df['p_value_bh'] = bh_p_values
    df['is_significant_bh'] = df['p_value_bh'] <= alpha
    
    # Reset index to match original order (optional, but cleaner)
    # df = df.sort_index().reset_index(drop=True)
    
    logger.info(f"Applied Benjamini-Hochberg correction: {df['is_significant_bh'].sum()} of {n} tests significant at alpha={alpha}")
    
    return df

def calculate_effect_size(df: pd.DataFrame, feature_cols: List[str], target_col: str) -> pd.DataFrame:
    """
    Calculate effect sizes (Cohen's r) for correlations.
    
    Cohen's r is simply the absolute value of the correlation coefficient.
    Interpretation: 0.1 = small, 0.3 = medium, 0.5 = large.
    
    Args:
        df: DataFrame containing features and target
        feature_cols: List of feature column names
        target_col: Name of the target column
        
    Returns:
        DataFrame with effect sizes merged into correlation results
    """
    # This assumes correlation results are already computed
    # Effect size for correlation is |r|
    effect_sizes = []
    
    for feature in feature_cols:
        if feature not in df.columns or target_col not in df.columns:
            continue
        
        valid_data = df[[feature, target_col]].dropna()
        if len(valid_data) < 3:
            continue
        
        # Use Pearson r as the effect size
        r, _ = stats.pearsonr(valid_data[feature], valid_data[target_col])
        effect_sizes.append({
            'feature': feature,
            'cohen_r': abs(r),
            'interpretation': interpret_cohen_r(abs(r))
        })
    
    return pd.DataFrame(effect_sizes)

def interpret_cohen_r(r: float) -> str:
    """
    Interpret Cohen's r effect size.
    
    Args:
        r: Absolute value of correlation coefficient
        
    Returns:
        String interpretation of effect size
    """
    if r < 0.1:
        return "negligible"
    elif r < 0.3:
        return "small"
    elif r < 0.5:
        return "medium"
    else:
        return "large"

def run_correlation_analysis(
    features_path: str,
    ratings_path: str,
    output_path: str,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run full correlation analysis pipeline with BH correction.
    
    Args:
        features_path: Path to features CSV
        ratings_path: Path to ratings CSV
        output_path: Path to save correlation results
        alpha: Significance level for BH correction
        
    Returns:
        Dictionary with analysis summary
    """
    logger.info(f"Loading features from {features_path}")
    features_df = pd.read_csv(features_path)
    
    logger.info(f"Loading ratings from {ratings_path}")
    ratings_df = pd.read_csv(ratings_path)
    
    # Merge on conversation_id
    merged_df = pd.merge(features_df, ratings_df, on='conversation_id', how='inner')
    logger.info(f"Merged dataset has {len(merged_df)} conversations")
    
    # Define feature columns (exclude non-feature columns)
    feature_cols = ['pronoun_rate', 'hedge_density', 'valence_score']
    feature_cols = [col for col in feature_cols if col in merged_df.columns]
    
    if not feature_cols:
        raise ValueError("No valid feature columns found in merged dataset")
    
    # Compute correlations
    corr_results = compute_correlations(merged_df, feature_cols, 'authenticity_score')
    
    # Apply BH correction
    corr_results_corrected = apply_bh_correction(corr_results, alpha)
    
    # Calculate effect sizes
    effect_sizes = calculate_effect_size(merged_df, feature_cols, 'authenticity_score')
    
    # Save results
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    corr_results_corrected.to_csv(output_path, index=False)
    logger.info(f"Saved correlation results to {output_path}")
    
    # Create summary
    summary = {
        'total_tests': len(corr_results),
        'significant_uncorrected': int((corr_results['p_value'] < alpha).sum()),
        'significant_bh_corrected': int(corr_results_corrected['is_significant_bh'].sum()),
        'alpha': alpha,
        'features_analyzed': feature_cols,
        'output_file': str(output_path)
    }
    
    return summary