"""
Preprocessing pipeline for constructed wetlands microbial community data.

This module handles:
1. Loading sample metadata and feature tables
2. Filtering for constructed wetlands with nutrient removal metrics
3. Subsampling to uniform depth
4. Calculating diversity metrics
5. Running sensitivity analysis on subsampling depth
6. Validation and error handling for missing metadata fields
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from scipy.stats import entropy

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_READS_THRESHOLD = 1000
SUBSAMPLE_DEPTHS = {
    'low': 1000,
    'medium': 5000,
    'high': 10000
}

# Required metadata fields for nutrient removal analysis
REQUIRED_METADATA_FIELDS = ['nutrient_removal_rate_N', 'nutrient_removal_rate_P', 'wetland_stage']

def load_sample_metadata(metadata_path: Path) -> pd.DataFrame:
    """Load sample metadata from JSON or CSV file."""
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    if metadata_path.suffix == '.json':
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
    elif metadata_path.suffix == '.csv':
        df = pd.read_csv(metadata_path)
    else:
        raise ValueError(f"Unsupported metadata format: {metadata_path.suffix}")
    
    logger.info(f"Loaded {len(df)} samples from {metadata_path}")
    return df

def load_feature_table(table_path: Path) -> pd.DataFrame:
    """Load feature table (OTU/ASV counts) from CSV or TSV."""
    if not table_path.exists():
        raise FileNotFoundError(f"Feature table not found: {table_path}")
    
    if table_path.suffix == '.tsv':
        df = pd.read_csv(table_path, sep='\t', index_col=0)
    elif table_path.suffix == '.csv':
        df = pd.read_csv(table_path, index_col=0)
    else:
        raise ValueError(f"Unsupported feature table format: {table_path.suffix}")
    
    logger.info(f"Loaded feature table with {df.shape[0]} taxa and {df.shape[1]} samples")
    return df

def filter_constructed_wetlands(metadata_df: pd.DataFrame) -> pd.DataFrame:
    """Filter samples to only include constructed wetlands."""
    if 'wetland_type' not in metadata_df.columns:
        logger.warning("Column 'wetland_type' not found in metadata. Skipping wetland type filter.")
        return metadata_df
    
    # Filter for constructed wetlands (case-insensitive)
    constructed_mask = metadata_df['wetland_type'].str.lower().str.contains('constructed', na=False)
    filtered_df = metadata_df[constructed_mask].copy()
    
    excluded_count = len(metadata_df) - len(filtered_df)
    logger.info(f"Filtered for constructed wetlands: {excluded_count} samples excluded, {len(filtered_df)} retained")
    
    return filtered_df

def validate_metadata_fields(metadata_df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate that required metadata fields exist and are not missing.
    
    Returns:
        Tuple of (filtered DataFrame with valid rows, list of excluded sample IDs)
    """
    missing_fields = []
    for field in REQUIRED_METADATA_FIELDS:
        if field not in metadata_df.columns:
            missing_fields.append(field)
    
    if missing_fields:
        logger.error(f"Missing required metadata fields: {missing_fields}")
        raise ValueError(f"Missing required metadata fields: {missing_fields}")
    
    # Check for missing values in required fields
    excluded_samples = []
    valid_mask = pd.Series([True] * len(metadata_df), index=metadata_df.index)
    
    for field in REQUIRED_METADATA_FIELDS:
        null_mask = metadata_df[field].isna()
        if null_mask.any():
            excluded_samples.extend(metadata_df.index[null_mask].tolist())
            valid_mask = valid_mask & ~null_mask
            logger.warning(f"Found {null_mask.sum()} samples with missing '{field}' values")
    
    filtered_df = metadata_df[valid_mask].copy()
    
    if len(excluded_samples) > 0:
        logger.info(f"Excluded {len(excluded_samples)} samples due to missing metadata fields")
    
    return filtered_df, excluded_samples

def filter_nutrient_removal_metrics(metadata_df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter samples to only include those with valid nutrient removal metrics.
    
    This function validates that N/P removal rate fields exist and contain
    numeric values, excluding samples with missing or invalid data.
    
    Returns:
        Tuple of (filtered DataFrame, list of excluded sample IDs)
    """
    # First validate metadata fields exist
    filtered_df, excluded_samples = validate_metadata_fields(metadata_df)
    
    # Ensure nutrient removal rates are numeric
    for field in ['nutrient_removal_rate_N', 'nutrient_removal_rate_P']:
        filtered_df[field] = pd.to_numeric(filtered_df[field], errors='coerce')
        null_count = filtered_df[field].isna().sum()
        if null_count > 0:
            # Re-validate after coercion
            new_null_mask = filtered_df[field].isna()
            new_excluded = filtered_df.index[new_null_mask].tolist()
            excluded_samples.extend(new_excluded)
            filtered_df = filtered_df[~new_null_mask].copy()
            logger.warning(f"After numeric conversion, {null_count} samples still missing '{field}'")
    
    logger.info(f"Final nutrient metric validation: {len(excluded_samples)} total samples excluded")
    return filtered_df, excluded_samples

def subsample_minimum_depth(feature_df: pd.DataFrame, min_depth: int = MIN_READS_THRESHOLD) -> pd.DataFrame:
    """
    Exclude samples with read depth below the minimum threshold.
    
    Args:
        feature_df: Feature table with samples as columns
        min_depth: Minimum read depth threshold (default: 1000)
    
    Returns:
        Filtered feature table with only samples meeting minimum depth
    """
    sample_sums = feature_df.sum(axis=0)
    valid_samples = sample_sums[sample_sums >= min_depth].index.tolist()
    excluded_count = len(feature_df.columns) - len(valid_samples)
    
    logger.info(f"Subsampled to minimum depth {min_depth}: {excluded_count} samples excluded, {len(valid_samples)} retained")
    
    return feature_df[valid_samples]

def subsample_to_depth(feature_df: pd.DataFrame, target_depth: int, random_state: int = 42) -> pd.DataFrame:
    """
    Subsample all samples to a uniform sequencing depth.
    
    Args:
        feature_df: Feature table with samples as columns
        target_depth: Target sequencing depth
        random_state: Random seed for reproducibility
    
    Returns:
        Subsampled feature table
    """
    np.random.seed(random_state)
    subsampled_data = {}
    
    for sample in feature_df.columns:
        counts = feature_df[sample].values
        total = counts.sum()
        
        if total < target_depth:
            logger.warning(f"Sample {sample} has {total} reads, less than target {target_depth}. Skipping.")
            continue
        
        # Multinomial subsampling
        proportions = counts / total
        subsampled_counts = np.random.multinomial(target_depth, proportions)
        subsampled_data[sample] = subsampled_counts
    
    result_df = pd.DataFrame(subsampled_data, index=feature_df.index)
    logger.info(f"Subsampled to depth {target_depth}: {len(result_df.columns)} samples retained")
    
    return result_df

def calculate_alpha_diversity(feature_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate alpha diversity metrics (Shannon, Simpson) for each sample.
    
    Args:
        feature_df: Feature table with samples as columns
    
    Returns:
        DataFrame with alpha diversity metrics
    """
    results = {}
    
    for sample in feature_df.columns:
        counts = feature_df[sample].values
        total = counts.sum()
        
        if total == 0:
            results[sample] = {'shannon': np.nan, 'simpson': np.nan}
            continue
        
        # Relative abundances
        probs = counts / total
        probs = probs[probs > 0]  # Remove zeros for log calculation
        
        # Shannon index
        shannon = -np.sum(probs * np.log(probs))
        
        # Simpson index (1 - D)
        simpson = 1 - np.sum(probs ** 2)
        
        results[sample] = {'shannon': shannon, 'simpson': simpson}
    
    return pd.DataFrame(results).T

def run_sensitivity_sweep(
    feature_df: pd.DataFrame,
    metadata_df: pd.DataFrame,
    depths: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across multiple subsampling depths.
    
    Args:
        feature_df: Filtered feature table
        metadata_df: Filtered metadata with nutrient rates
        depths: Dictionary of depth labels to values (default: SUBSAMPLE_DEPTHS)
    
    Returns:
        Dictionary containing sensitivity analysis results
    """
    if depths is None:
        depths = SUBSAMPLE_DEPTHS
    
    results = {}
    alpha_diversities = {}
    
    for label, depth in depths.items():
        logger.info(f"Running sensitivity sweep at depth: {label} ({depth})")
        
        # Subsample to target depth
        subsampled_features = subsample_to_depth(feature_df, depth)
        
        # Calculate alpha diversity
        alpha_div = calculate_alpha_diversity(subsampled_features)
        alpha_diversities[label] = alpha_div
        
        # Correlate with nutrient removal rates (only samples present in both)
        common_samples = set(alpha_div.index) & set(metadata_df.index)
        
        if len(common_samples) < 3:
            logger.warning(f"Not enough common samples for correlation at depth {label}")
            results[label] = {
                'n_samples': len(common_samples),
                'n_taxa': len(subsampled_features),
                'correlation_with_N': None,
                'correlation_with_P': None
            }
            continue
        
        # Merge with metadata
        merged = alpha_div.loc[common_samples].join(metadata_df.loc[common_samples, ['nutrient_removal_rate_N', 'nutrient_removal_rate_P']])
        
        # Calculate correlations
        corr_N = merged['shannon'].corr(merged['nutrient_removal_rate_N'])
        corr_P = merged['shannon'].corr(merged['nutrient_removal_rate_P'])
        
        results[label] = {
            'n_samples': len(common_samples),
            'n_taxa': len(subsampled_features),
            'correlation_with_N': corr_N,
            'correlation_with_P': corr_P,
            'alpha_diversity_stats': {
                'shannon_mean': float(merged['shannon'].mean()),
                'shannon_std': float(merged['shannon'].std()),
                'simpson_mean': float(merged['simpson'].mean()),
                'simpson_std': float(merged['simpson'].std())
            }
        }
    
    # Calculate rank correlation between depths for robustness check
    if len(alpha_diversities) >= 2:
        labels = list(alpha_diversities.keys())
        first_label = labels[0]
        rank_correlations = {}
        
        for i in range(1, len(labels)):
            second_label = labels[i]
            common = set(alpha_diversities[first_label].index) & set(alpha_diversities[second_label].index)
            
            if len(common) > 0:
                ranks1 = alpha_diversities[first_label].loc[common]['shannon'].rank()
                ranks2 = alpha_diversities[second_label].loc[common]['shannon'].rank()
                
                spearman_corr, _ = entropy(ranks1, ranks2), 0  # Placeholder, using scipy
                from scipy.stats import spearmanr
                spearman_corr, _ = spearmanr(ranks1, ranks2)
                
                rank_correlations[f"{first_label}_vs_{second_label}"] = float(spearman_corr)
        
        results['spearman_rank_correlation'] = rank_correlations
    
    return results

def save_exclusion_log(excluded_samples: List[str], output_path: Path):
    """Save exclusion log to JSON file."""
    log_data = {
        'excluded_samples': excluded_samples,
        'count': len(excluded_samples),
        'reason': 'Missing N/P metadata fields'
    }
    
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    logger.info(f"Exclusion log saved to {output_path}")

def preprocess_data(
    raw_data_dir: Path,
    processed_data_dir: Path,
    config_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main preprocessing pipeline.
    
    Args:
        raw_data_dir: Directory containing raw data files
        processed_data_dir: Directory for processed output
        config_path: Optional path to configuration file
    
    Returns:
        Dictionary containing processing summary
    """
    # Ensure output directories exist
    processed_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    metadata_path = raw_data_dir / 'sample_metadata.json'
    feature_table_path = raw_data_dir / 'feature_table.csv'
    
    logger.info("Loading metadata and feature table...")
    metadata_df = load_sample_metadata(metadata_path)
    feature_df = load_feature_table(feature_table_path)
    
    # Filter for constructed wetlands
    logger.info("Filtering for constructed wetlands...")
    filtered_metadata = filter_constructed_wetlands(metadata_df)
    
    # Filter and validate nutrient removal metrics
    logger.info("Validating and filtering nutrient removal metrics...")
    valid_metadata, excluded_samples = filter_nutrient_removal_metrics(filtered_metadata)
    
    # Save exclusion log
    exclusion_log_path = processed_data_dir / 'exclusion_log.json'
    save_exclusion_log(excluded_samples, exclusion_log_path)
    
    # Filter feature table to match valid samples
    valid_sample_ids = set(valid_metadata.index)
    feature_df = feature_df[feature_df.columns.intersection(valid_sample_ids)]
    
    logger.info(f"Feature table filtered to {feature_df.shape[1]} samples matching valid metadata")
    
    # Subsample to minimum depth
    logger.info("Subsampling to minimum depth...")
    feature_df = subsample_minimum_depth(feature_df, MIN_READS_THRESHOLD)
    
    # Run sensitivity sweep
    logger.info("Running sensitivity analysis...")
    sensitivity_results = run_sensitivity_sweep(feature_df, valid_metadata)
    
    # Save results
    results = {
        'preprocessing_summary': {
            'initial_samples': len(metadata_df),
            'constructed_wetland_samples': len(filtered_metadata),
            'valid_nutrient_samples': len(valid_metadata),
            'excluded_due_to_missing_metadata': len(excluded_samples),
            'final_samples_after_min_depth': feature_df.shape[1],
            'final_taxa_count': feature_df.shape[0]
        },
        'sensitivity_analysis': sensitivity_results
    }
    
    # Save intermediate depth results
    for label, depth in SUBSAMPLE_DEPTHS.items():
        if label in sensitivity_results:
            depth_result_path = processed_data_dir / f'{label}_depth_results.json'
            with open(depth_result_path, 'w') as f:
                json.dump({
                    'depth': depth,
                    'n_samples': sensitivity_results[label]['n_samples'],
                    'n_taxa': sensitivity_results[label]['n_taxa'],
                    'correlation_with_N': sensitivity_results[label]['correlation_with_N'],
                    'correlation_with_P': sensitivity_results[label]['correlation_with_P']
                }, f, indent=2)
    
    # Save sensitivity sweep results
    sweep_path = processed_data_dir / 'sensitivity_sweep_results.json'
    with open(sweep_path, 'w') as f:
        json.dump(sensitivity_results, f, indent=2)
    
    # Save final processed data
    feature_df.to_csv(processed_data_dir / 'processed_feature_table.csv')
    valid_metadata.to_csv(processed_data_dir / 'processed_metadata.csv')
    
    logger.info(f"Preprocessing complete. Results saved to {processed_data_dir}")
    
    return results

def main():
    """Main entry point for preprocessing script."""
    # Default paths
    raw_data_dir = Path('data/raw')
    processed_data_dir = Path('data/processed')
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        raw_data_dir = Path(sys.argv[1])
    if len(sys.argv) > 2:
        processed_data_dir = Path(sys.argv[2])
    
    logger.info(f"Starting preprocessing pipeline")
    logger.info(f"Raw data directory: {raw_data_dir}")
    logger.info(f"Processed data directory: {processed_data_dir}")
    
    try:
        results = preprocess_data(raw_data_dir, processed_data_dir)
        logger.info("Pipeline completed successfully")
        return results
    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}")
        raise

if __name__ == '__main__':
    main()