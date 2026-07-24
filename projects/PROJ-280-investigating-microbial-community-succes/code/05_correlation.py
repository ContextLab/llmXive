import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.model_selection import cross_val_score
from sklearn.linear_model import LinearRegression

# Import from project utils for VIF calculation and logging
from utils import calculate_vif, log_under_determined_flag

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
VIF_THRESHOLD = 5.0
CORRELATION_THRESHOLD = 0.5
P_VALUE_THRESHOLD = 0.05
MIN_SAMPLES = 10  # Minimum samples required for meaningful correlation analysis

def load_processed_taxon_data() -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Load processed taxon abundance data and metadata.
    
    Returns:
        Tuple of (feature_table_df, metadata_df, stage_mapping)
    """
    data_dir = Path("data/processed")
    
    # Load feature table
    feature_table_path = data_dir / "feature_table.csv"
    if not feature_table_path.exists():
        logger.error(f"Feature table not found at {feature_table_path}")
        sys.exit(1)
    
    feature_table = pd.read_csv(feature_table_path, index_col=0)
    
    # Load metadata
    metadata_path = data_dir / "sample_metadata.csv"
    if not metadata_path.exists():
        logger.error(f"Sample metadata not found at {metadata_path}")
        sys.exit(1)
    
    metadata = pd.read_csv(metadata_path)
    
    # Create stage mapping for filtering
    stage_mapping = {}
    if 'stage' in metadata.columns:
        stage_mapping = metadata.set_index('sample_id')['stage'].to_dict()
    
    logger.info(f"Loaded feature table with {feature_table.shape} shape")
    logger.info(f"Loaded metadata with {metadata.shape} shape")
    
    return feature_table, metadata, stage_mapping

def calculate_spearman_correlations(
    feature_table: pd.DataFrame, 
    metadata: pd.DataFrame,
    nutrient_col: str = 'n_removal_rate'
) -> pd.DataFrame:
    """
    Calculate Spearman correlations between taxon abundances and nutrient removal rates.
    
    Args:
        feature_table: DataFrame with taxa as rows and samples as columns
        metadata: DataFrame with sample metadata including nutrient removal rates
        nutrient_col: Column name for nutrient removal rate in metadata
        
    Returns:
        DataFrame with correlation coefficients and p-values
    """
    # Ensure we have matching samples
    common_samples = list(set(feature_table.columns) & set(metadata['sample_id']))
    
    if len(common_samples) < MIN_SAMPLES:
        logger.warning(f"Only {len(common_samples)} common samples found, below minimum {MIN_SAMPLES}")
        return pd.DataFrame()
    
    # Filter feature table to common samples
    feature_table_filtered = feature_table[common_samples]
    
    # Get nutrient removal rates for common samples
    nutrient_data = metadata[metadata['sample_id'].isin(common_samples)].set_index('sample_id')
    
    if nutrient_col not in nutrient_data.columns:
        logger.error(f"Nutrient column '{nutrient_col}' not found in metadata")
        return pd.DataFrame()
    
    nutrient_rates = nutrient_data[nutrient_col]
    
    # Calculate correlations for each taxon
    correlations = []
    p_values = []
    
    for taxon in feature_table_filtered.index:
        taxon_abundance = feature_table_filtered.loc[taxon]
        
        # Ensure alignment
        aligned_indices = taxon_abundance.index.intersection(nutrient_rates.index)
        
        if len(aligned_indices) < MIN_SAMPLES:
            continue
        
        corr, p_val = spearmanr(
            taxon_abundance.loc[aligned_indices],
            nutrient_rates.loc[aligned_indices]
        )
        
        correlations.append(corr)
        p_values.append(p_val)
    
    result_df = pd.DataFrame({
        'taxon': feature_table_filtered.index,
        'correlation': correlations,
        'p_value': p_values
    })
    
    return result_df

def calculate_vif_for_predictors(
    feature_table: pd.DataFrame,
    metadata: pd.DataFrame,
    target_col: str = 'n_removal_rate',
    vif_threshold: float = VIF_THRESHOLD
) -> Tuple[Dict[str, float], List[str]]:
    """
    Calculate Variance Inflation Factor (VIF) for predictor taxa to detect collinearity.
    
    FR-010: Flag predictor taxa with VIF > 5 for collinearity.
    
    Args:
        feature_table: DataFrame with taxa as rows and samples as columns
        metadata: DataFrame with sample metadata
        target_col: Column name for the target variable (nutrient removal rate)
        vif_threshold: Threshold above which taxa are flagged for collinearity
        
    Returns:
        Tuple of (vif_dict, flagged_taxa)
    """
    # Ensure we have matching samples
    common_samples = list(set(feature_table.columns) & set(metadata['sample_id']))
    
    if len(common_samples) < MIN_SAMPLES:
        logger.warning(f"Only {len(common_samples)} common samples found, VIF calculation may be unreliable")
        return {}, []
    
    # Prepare feature matrix (taxa as features)
    feature_table_filtered = feature_table[common_samples].T  # Samples x Taxa
    
    # Prepare target variable
    nutrient_data = metadata[metadata['sample_id'].isin(common_samples)].set_index('sample_id')
    
    if target_col not in nutrient_data.columns:
        logger.error(f"Target column '{target_col}' not found in metadata")
        return {}, []
    
    target = nutrient_data[target_col]
    
    # Ensure alignment
    aligned_indices = feature_table_filtered.index.intersection(target.index)
    X = feature_table_filtered.loc[aligned_indices]
    y = target.loc[aligned_indices]
    
    if X.shape[0] < X.shape[1] + 1:
        logger.warning(f"Under-determined: {X.shape[0]} samples < {X.shape[1]} features + intercept")
        log_under_determined_flag(f"VIF calculation: {X.shape[0]} samples < {X.shape[1]} features")
        return {}, []
    
    # Calculate VIF for each taxon
    vif_dict = {}
    flagged_taxa = []
    
    # Add intercept column for VIF calculation
    X_with_intercept = np.column_stack([np.ones(X.shape[0]), X.values])
    feature_names = ['intercept'] + list(X.columns)
    
    for i, col_name in enumerate(feature_names):
        if col_name == 'intercept':
            continue
        
        # Calculate VIF using the helper function from utils
        try:
            vif_value = calculate_vif(X_with_intercept, i)
            vif_dict[col_name] = vif_value
            
            if vif_value > vif_threshold:
                flagged_taxa.append(col_name)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col_name}: {e}")
            vif_dict[col_name] = np.nan
    
    logger.info(f"Calculated VIF for {len(vif_dict)} taxa")
    logger.info(f"Flagged {len(flagged_taxa)} taxa with VIF > {vif_threshold}")
    
    if flagged_taxa:
        logger.warning(f"Collinear taxa detected: {flagged_taxa}")
    
    return vif_dict, flagged_taxa

def perform_cross_validation(
    feature_table: pd.DataFrame,
    metadata: pd.DataFrame,
    target_col: str = 'n_removal_rate',
    k: int = 3
) -> Dict[str, float]:
    """
    Perform k-fold cross-validation on the taxa-nutrient correlation model.
    
    FR-012: Implement k=3 cross-validation.
    
    Args:
        feature_table: DataFrame with taxa as rows and samples as columns
        metadata: DataFrame with sample metadata
        target_col: Column name for the target variable
        k: Number of folds for cross-validation
        
    Returns:
        Dictionary with cross-validation metrics
    """
    # Ensure we have matching samples
    common_samples = list(set(feature_table.columns) & set(metadata['sample_id']))
    
    if len(common_samples) < MIN_SAMPLES:
        logger.warning(f"Only {len(common_samples)} common samples found, cross-validation may be unreliable")
        return {'mean_r2': np.nan, 'std_r2': np.nan, 'k': k, 'n_samples': len(common_samples)}
    
    # Prepare feature matrix (taxa as features)
    feature_table_filtered = feature_table[common_samples].T  # Samples x Taxa
    
    # Prepare target variable
    nutrient_data = metadata[metadata['sample_id'].isin(common_samples)].set_index('sample_id')
    
    if target_col not in nutrient_data.columns:
        logger.error(f"Target column '{target_col}' not found in metadata")
        return {'mean_r2': np.nan, 'std_r2': np.nan, 'k': k, 'n_samples': len(common_samples)}
    
    target = nutrient_data[target_col]
    
    # Ensure alignment
    aligned_indices = feature_table_filtered.index.intersection(target.index)
    X = feature_table_filtered.loc[aligned_indices].values
    y = target.loc[aligned_indices].values
    
    if len(X) < k:
        logger.warning(f"Sample size ({len(X)}) less than k ({k}), using available samples")
        k = max(1, len(X) - 1)
    
    # Perform cross-validation
    model = LinearRegression()
    scores = cross_val_score(model, X, y, cv=k, scoring='r2')
    
    results = {
        'mean_r2': float(np.mean(scores)),
        'std_r2': float(np.std(scores)),
        'k': k,
        'n_samples': len(X),
        'n_features': X.shape[1],
        'scores': scores.tolist()
    }
    
    logger.info(f"Cross-validation completed: mean R² = {results['mean_r2']:.4f}, std = {results['std_r2']:.4f}")
    
    return results

def save_correlation_results(
    correlation_df: pd.DataFrame,
    vif_dict: Dict[str, float],
    flagged_taxa: List[str],
    output_path: str
):
    """
    Save correlation results with VIF flags to JSON.
    
    Args:
        correlation_df: DataFrame with correlation coefficients and p-values
        vif_dict: Dictionary of VIF values for each taxon
        flagged_taxa: List of taxa with VIF > threshold
        output_path: Path to save the results
    """
    # Merge correlation data with VIF data
    results = []
    
    for _, row in correlation_df.iterrows():
        taxon = row['taxon']
        result_entry = {
            'taxon': taxon,
            'correlation': float(row['correlation']),
            'p_value': float(row['p_value']),
            'vif': float(vif_dict.get(taxon, np.nan)) if taxon in vif_dict else None,
            'is_flagged_collinear': taxon in flagged_taxa,
            'meets_significance_criteria': abs(row['correlation']) >= CORRELATION_THRESHOLD and row['p_value'] <= P_VALUE_THRESHOLD
        }
        results.append(result_entry)
    
    # Filter to significant correlations or include all if needed
    significant_results = [r for r in results if r['meets_significance_criteria']]
    
    output_data = {
        'summary': {
            'total_taxa_tested': len(results),
            'significant_correlations': len(significant_results),
            'collinear_taxa_flagged': len(flagged_taxa),
            'vif_threshold': VIF_THRESHOLD,
            'correlation_threshold': CORRELATION_THRESHOLD,
            'p_value_threshold': P_VALUE_THRESHOLD
        },
        'flagged_collinear_taxa': flagged_taxa,
        'all_results': results,
        'significant_results': significant_results
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved correlation results to {output_path}")
    logger.info(f"Found {len(significant_results)} taxa meeting significance criteria")
    logger.info(f"Flagged {len(flagged_taxa)} taxa for collinearity")

def save_cv_results(cv_results: Dict[str, Any], output_path: str):
    """
    Save cross-validation results to JSON.
    
    Args:
        cv_results: Dictionary with cross-validation metrics
        output_path: Path to save the results
    """
    with open(output_path, 'w') as f:
        json.dump(cv_results, f, indent=2)
    
    logger.info(f"Saved cross-validation results to {output_path}")

def main():
    """Main execution function for T033: VIF calculation and correlation analysis."""
    logger.info("Starting VIF calculation and correlation analysis (T033)")
    
    try:
        # Load data
        feature_table, metadata, stage_mapping = load_processed_taxon_data()
        
        if feature_table.empty or metadata.empty:
            logger.error("Empty data loaded, cannot proceed")
            sys.exit(1)
        
        # Calculate Spearman correlations
        correlation_df = calculate_spearman_correlations(feature_table, metadata)
        
        if correlation_df.empty:
            logger.warning("No correlations calculated, check data alignment")
        
        # Calculate VIF for collinearity detection (FR-010)
        vif_dict, flagged_taxa = calculate_vif_for_predictors(feature_table, metadata)
        
        # Perform cross-validation (FR-012)
        cv_results = perform_cross_validation(feature_table, metadata)
        
        # Save results
        output_dir = Path("data/processed")
        output_dir.mkdir(exist_ok=True)
        
        correlation_output_path = output_dir / "correlation_results.json"
        cv_output_path = output_dir / "correlation_cv_results.json"
        
        save_correlation_results(correlation_df, vif_dict, flagged_taxa, str(correlation_output_path))
        save_cv_results(cv_results, str(cv_output_path))
        
        logger.info("T033 completed successfully")
        
    except Exception as e:
        logger.error(f"Error during T033 execution: {e}")
        raise

if __name__ == "__main__":
    main()
