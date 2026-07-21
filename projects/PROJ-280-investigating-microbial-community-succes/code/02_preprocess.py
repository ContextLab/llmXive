"""
Preprocessing pipeline for microbial community data in constructed wetlands.

This module handles:
- Loading and validating sample metadata
- Filtering for constructed wetlands with nutrient removal metrics
- Subsampling to uniform depth
- Sensitivity analysis for subsampling depth
- Logging exclusion reasons for transparency
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import shannon_entropy

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import log_data_gap_flag, generate_checksum
from data_models import Sample, FeatureTable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_READ_DEPTH = 1000  # Conservative minimum for exclusion
NUTRIENT_FIELDS = ['n_removal_rate', 'p_removal_rate']

def load_sample_metadata(metadata_path: Path) -> pd.DataFrame:
    """Load sample metadata from a CSV or JSON file."""
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    if metadata_path.suffix == '.csv':
        return pd.read_csv(metadata_path)
    elif metadata_path.suffix == '.json':
        return pd.read_json(metadata_path)
    else:
        raise ValueError(f"Unsupported metadata format: {metadata_path.suffix}")

def load_feature_table(table_path: Path) -> pd.DataFrame:
    """Load feature table from a CSV or BIOM-like format."""
    if not table_path.exists():
        raise FileNotFoundError(f"Feature table not found: {table_path}")
    
    if table_path.suffix == '.csv':
        return pd.read_csv(table_path, index_col=0)
    else:
        raise ValueError(f"Unsupported feature table format: {table_path.suffix}")

def filter_constructed_wetlands(metadata: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Filter samples to only include constructed wetlands."""
    initial_count = len(metadata)
    
    # Assuming 'wetland_type' column exists and 'constructed' is a valid value
    if 'wetland_type' in metadata.columns:
        filtered = metadata[metadata['wetland_type'].str.lower() == 'constructed']
    else:
        # If column doesn't exist, assume all are constructed wetlands for now
        # In a real scenario, this would be a data gap
        filtered = metadata
        logger.warning("Column 'wetland_type' not found in metadata. Assuming all samples are constructed wetlands.")
    
    excluded_count = initial_count - len(filtered)
    logger.info(f"Filtered constructed wetlands: {initial_count} -> {len(filtered)} (excluded {excluded_count})")
    return filtered, excluded_count

def validate_metadata_fields(metadata: pd.DataFrame, required_fields: List[str]) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Validate that required metadata fields exist and are populated.
    
    Returns:
        Tuple of (filtered_metadata, exclusion_counts_by_field)
    """
    exclusion_counts = {}
    current_metadata = metadata.copy()
    
    for field in required_fields:
        if field not in current_metadata.columns:
            exclusion_counts[field] = len(current_metadata)
            logger.warning(f"Required field '{field}' not found in metadata. All samples excluded.")
            return pd.DataFrame(), exclusion_counts
        
        # Count missing values (NaN, None, empty string)
        missing_mask = current_metadata[field].isna() | (current_metadata[field] == '')
        missing_count = missing_mask.sum()
        
        if missing_count > 0:
            exclusion_counts[field] = missing_count
            logger.info(f"Field '{field}' has {missing_count} missing values. Excluding these samples.")
            current_metadata = current_metadata[~missing_mask]
    
    return current_metadata, exclusion_counts

def filter_nutrient_removal_metrics(metadata: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Filter samples that have nutrient removal metrics (N/P rates).
    
    Returns:
        Tuple of (filtered_metadata, exclusion_count)
    """
    initial_count = len(metadata)
    
    # Check for nutrient removal columns
    has_n = 'n_removal_rate' in metadata.columns
    has_p = 'p_removal_rate' in metadata.columns
    
    if not has_n and not has_p:
        logger.error("Neither 'n_removal_rate' nor 'p_removal_rate' columns found in metadata.")
        log_data_gap_flag("No nutrient removal rate columns found in metadata")
        return pd.DataFrame(), initial_count
    
    # Filter for samples that have at least one nutrient metric
    if has_n and has_p:
        valid_mask = metadata['n_removal_rate'].notna() & metadata['p_removal_rate'].notna()
    elif has_n:
        valid_mask = metadata['n_removal_rate'].notna()
    else:
        valid_mask = metadata['p_removal_rate'].notna()
    
    filtered = metadata[valid_mask]
    excluded_count = initial_count - len(filtered)
    
    logger.info(f"Filtered nutrient removal metrics: {initial_count} -> {len(filtered)} (excluded {excluded_count})")
    return filtered, excluded_count

def subsample_minimum_depth(feature_table: pd.DataFrame, min_depth: int = MIN_READ_DEPTH) -> Tuple[pd.DataFrame, int]:
    """
    Exclude samples with read depth below the minimum threshold.
    
    Args:
        feature_table: DataFrame with samples as rows and taxa as columns
        min_depth: Minimum read depth required
    
    Returns:
        Tuple of (filtered_feature_table, exclusion_count)
    """
    initial_count = len(feature_table)
    
    # Calculate read depth for each sample
    sample_depths = feature_table.sum(axis=1)
    
    # Filter samples
    valid_mask = sample_depths >= min_depth
    filtered = feature_table[valid_mask]
    excluded_count = initial_count - len(filtered)
    
    logger.info(f"Subsampled to minimum depth {min_depth}: {initial_count} -> {len(filtered)} (excluded {excluded_count})")
    return filtered, excluded_count

def subsample_to_depth(feature_table: pd.DataFrame, target_depth: int) -> pd.DataFrame:
    """
    Subsample all samples to a uniform read depth.
    
    Args:
        feature_table: DataFrame with samples as rows and taxa as columns
        target_depth: Target read depth for all samples
    
    Returns:
        Subsampled feature table
    """
    subsampled = pd.DataFrame()
    
    for sample_id, sample_data in feature_table.iterrows():
        current_depth = sample_data.sum()
        if current_depth < target_depth:
            logger.warning(f"Sample {sample_id} has depth {current_depth} < {target_depth}, skipping")
            continue
        
        # Perform subsampling
        counts = sample_data.values
        total = counts.sum()
        
        # Use multinomial sampling for subsampling
        probs = counts / total
        subsampled_counts = np.random.multinomial(target_depth, probs)
        
        subsampled_row = pd.Series(subsampled_counts, index=sample_data.index, name=sample_id)
        subsampled = pd.concat([subsampled, subsampled_row.to_frame().T])
    
    return subsampled

def calculate_alpha_diversity(feature_table: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate alpha diversity metrics (Shannon, Simpson) for each sample.
    
    Args:
        feature_table: DataFrame with samples as rows and taxa as columns
    
    Returns:
        DataFrame with alpha diversity metrics
    """
    diversity_metrics = pd.DataFrame(index=feature_table.index)
    
    for sample_id, sample_data in feature_table.iterrows():
        # Shannon entropy
        shannon = shannon_entropy(sample_data.values)
        
        # Simpson index
        total = sample_data.sum()
        if total > 0:
            probs = sample_data.values / total
            simpson = 1 - np.sum(probs ** 2)
        else:
            simpson = 0
        
        diversity_metrics.loc[sample_id, 'shannon'] = shannon
        diversity_metrics.loc[sample_id, 'simpson'] = simpson
    
    return diversity_metrics

def run_sensitivity_sweep(feature_table: pd.DataFrame, depths: List[int]) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by subsampling at different depths.
    
    Args:
        feature_table: Filtered feature table
        depths: List of target depths to test
    
    Returns:
        Dictionary with results for each depth and correlation metrics
    """
    results = {}
    diversity_by_depth = {}
    
    for depth in depths:
        logger.info(f"Running sensitivity sweep at depth {depth}")
        
        # Subsample
        subsampled = subsample_to_depth(feature_table, depth)
        
        # Calculate alpha diversity
        diversity = calculate_alpha_diversity(subsampled)
        diversity_by_depth[depth] = diversity
        
        # Save intermediate results
        result_file = Path(f"data/processed/low_depth_results.json" if depth == depths[0] else 
                         "data/processed/medium_depth_results.json" if depth == depths[1] else 
                         "data/processed/high_depth_results.json")
        
        results[depth] = {
            'sample_count': len(subsampled),
            'diversity_summary': {
                'shannon_mean': float(diversity['shannon'].mean()),
                'shannon_std': float(diversity['shannon'].std()),
                'simpson_mean': float(diversity['simpson'].mean()),
                'simpson_std': float(diversity['simpson'].std())
            }
        }
        
        # Save subsampled data (as summary for now)
        with open(result_file, 'w') as f:
            json.dump(results[depth], f, indent=2)
    
    # Calculate Spearman rank correlation between depths
    if len(depths) >= 2:
        # Compare rankings of alpha diversity across depths
        first_depth = depths[0]
        second_depth = depths[1]
        
        # Ensure same samples are compared
        common_samples = set(diversity_by_depth[first_depth].index) & set(diversity_by_depth[second_depth].index)
        
        if len(common_samples) > 1:
            shannon_first = diversity_by_depth[first_depth].loc[common_samples, 'shannon']
            shannon_second = diversity_by_depth[second_depth].loc[common_samples, 'shannon']
            
            from scipy.stats import spearmanr
            correlation, p_value = spearmanr(shannon_first, shannon_second)
            
            results['sensitivity_summary'] = {
                'spearman_rank_correlation': float(correlation),
                'p_value': float(p_value),
                'robustness_pass': correlation > 0.9
            }
            
            logger.info(f"Spearman correlation between depths {first_depth} and {second_depth}: {correlation:.3f}")
    
    return results

def save_exclusion_log(exclusion_data: Dict[str, Any], output_path: Path) -> None:
    """
    Save exclusion log to JSON file.
    
    Args:
        exclusion_data: Dictionary containing exclusion counts and reasons
        output_path: Path to save the exclusion log
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(exclusion_data, f, indent=2)
    
    logger.info(f"Exclusion log saved to {output_path}")

def preprocess_data(
    raw_metadata_path: Path,
    raw_feature_table_path: Path,
    processed_dir: Path,
    sensitivity_depths: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Main preprocessing pipeline.
    
    Args:
        raw_metadata_path: Path to raw metadata file
        raw_feature_table_path: Path to raw feature table
        processed_dir: Directory to save processed data
        sensitivity_depths: List of depths for sensitivity analysis (optional)
    
    Returns:
        Dictionary with processing results and exclusion counts
    """
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    logger.info("Loading metadata and feature table...")
    metadata = load_sample_metadata(raw_metadata_path)
    feature_table = load_feature_table(raw_feature_table_path)
    
    # Filter for constructed wetlands
    logger.info("Filtering for constructed wetlands...")
    metadata, cw_excluded = filter_constructed_wetlands(metadata)
    
    # Validate metadata fields
    logger.info("Validating metadata fields...")
    required_fields = ['wetland_type'] + NUTRIENT_FIELDS
    metadata, field_exclusions = validate_metadata_fields(metadata, required_fields)
    
    # Filter for nutrient removal metrics
    logger.info("Filtering for nutrient removal metrics...")
    metadata, nutrient_excluded = filter_nutrient_removal_metrics(metadata)
    
    # Subsample to minimum depth
    logger.info("Subsampling to minimum depth...")
    feature_table = feature_table.loc[metadata.index]  # Align feature table with filtered metadata
    feature_table, depth_excluded = subsample_minimum_depth(feature_table)
    
    # Prepare exclusion log
    exclusion_log = {
        'total_initial_samples': len(metadata) + cw_excluded + sum(field_exclusions.values()) + nutrient_excluded + depth_excluded,
        'exclusions': {
            'constructed_wetlands_filter': cw_excluded,
            'missing_metadata_fields': field_exclusions,
            'missing_nutrient_metrics': nutrient_excluded,
            'insufficient_read_depth': depth_excluded
        },
        'final_sample_count': len(metadata)
    }
    
    # Save exclusion log
    exclusion_log_path = processed_dir / 'exclusion_log.json'
    save_exclusion_log(exclusion_log, exclusion_log_path)
    
    # Run sensitivity analysis if requested
    if sensitivity_depths:
        logger.info("Running sensitivity analysis...")
        sensitivity_results = run_sensitivity_sweep(feature_table, sensitivity_depths)
        
        # Save sensitivity sweep results
        sensitivity_path = processed_dir / 'sensitivity_sweep_results.json'
        with open(sensitivity_path, 'w') as f:
            json.dump(sensitivity_results, f, indent=2)
        
        exclusion_log['sensitivity_analysis'] = sensitivity_results.get('sensitivity_summary', {})
        
        # Update exclusion log
        save_exclusion_log(exclusion_log, exclusion_log_path)
    
    # Calculate final alpha diversity
    logger.info("Calculating final alpha diversity...")
    final_diversity = calculate_alpha_diversity(feature_table)
    
    # Save processed data
    diversity_path = processed_dir / 'diversity_metrics.json'
    final_diversity.to_json(diversity_path, orient='index', indent=2)
    
    feature_table_path = processed_dir / 'feature_table.csv'
    feature_table.to_csv(feature_table_path)
    
    return exclusion_log

def main():
    """Main entry point for preprocessing."""
    # Define paths
    project_root = Path(__file__).parent.parent
    raw_metadata_path = project_root / 'data' / 'raw' / 'metadata.csv'
    raw_feature_table_path = project_root / 'data' / 'raw' / 'feature_table.csv'
    processed_dir = project_root / 'data' / 'processed'
    
    # Check if files exist
    if not raw_metadata_path.exists():
        logger.error(f"Metadata file not found: {raw_metadata_path}")
        log_data_gap_flag("Metadata file not found in data/raw/")
        sys.exit(1)
    
    if not raw_feature_table_path.exists():
        logger.error(f"Feature table not found: {raw_feature_table_path}")
        log_data_gap_flag("Feature table not found in data/raw/")
        sys.exit(1)
    
    # Define sensitivity depths (low, medium, high)
    # These should be determined based on the data distribution
    sensitivity_depths = [5000, 10000, 15000]  # Example values, should be optimized
    
    # Run preprocessing
    logger.info("Starting preprocessing pipeline...")
    results = preprocess_data(
        raw_metadata_path,
        raw_feature_table_path,
        processed_dir,
        sensitivity_depths
    )
    
    logger.info(f"Preprocessing complete. Final sample count: {results['final_sample_count']}")
    logger.info(f"Exclusion log saved to {processed_dir / 'exclusion_log.json'}")

if __name__ == '__main__':
    main()