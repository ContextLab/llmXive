import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants for paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / 'data' / 'raw'
DATA_PROCESSED = PROJECT_ROOT / 'data' / 'processed'
CONFIG_DIR = PROJECT_ROOT / 'data' / 'config'

# Ensure processed directory exists
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

def load_sample_metadata(metadata_path: Path) -> pd.DataFrame:
    """Load sample metadata from a JSON or CSV file."""
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    if metadata_path.suffix == '.json':
        with open(metadata_path, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    elif metadata_path.suffix == '.csv':
        return pd.read_csv(metadata_path)
    else:
        raise ValueError(f"Unsupported metadata format: {metadata_path.suffix}")

def load_feature_table(table_path: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load feature table and sample metadata.
    Returns: (feature_table_df, sample_metadata_df)
    Feature table: rows=samples, cols=taxa, values=counts.
    """
    if not table_path.exists():
        raise FileNotFoundError(f"Feature table not found: {table_path}")
    
    # Try to load as CSV (common format for feature tables)
    try:
        feature_df = pd.read_csv(table_path, index_col=0)
    except Exception as e:
        logger.error(f"Failed to load feature table: {e}")
        raise

    # Assume sample metadata is in the same directory with a standard name
    sample_meta_path = table_path.parent / 'sample_metadata.csv'
    if not sample_meta_path.exists():
        sample_meta_path = table_path.parent / 'sample_metadata.json'
    
    if sample_meta_path.exists():
        sample_meta_df = load_sample_metadata(sample_meta_path)
    else:
        # Fallback: create empty metadata if not found (might cause issues downstream)
        logger.warning(f"Sample metadata not found at {sample_meta_path}, creating empty DataFrame.")
        sample_meta_df = pd.DataFrame(index=feature_df.index)

    return feature_df, sample_meta_df

def filter_constructed_wetlands(metadata_df: pd.DataFrame) -> pd.DataFrame:
    """Filter samples to only include those from constructed wetlands."""
    # Assuming a column 'system_type' or similar exists
    # If column name differs, adjust here. Common names: 'system_type', 'environment'
    col_candidates = ['system_type', 'environment', 'wetland_type', 'type']
    target_value = 'constructed_wetland'
    
    found_col = None
    for col in col_candidates:
        if col in metadata_df.columns:
            found_col = col
            break
    
    if not found_col:
        logger.warning("Could not identify system type column. Returning all samples.")
        return metadata_df
    
    # Filter for constructed wetlands (case-insensitive match if string)
    mask = metadata_df[found_col].str.lower().str.contains('constructed', na=False)
    filtered_df = metadata_df[mask]
    excluded_count = len(metadata_df) - len(filtered_df)
    logger.info(f"Filtered constructed wetlands: excluded {excluded_count} samples.")
    return filtered_df

def filter_nutrient_removal_metrics(metadata_df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Filter samples that have N/P removal metrics."""
    # Look for columns like 'n_removal', 'p_removal', 'nitrogen_removal', etc.
    n_cols = [c for c in metadata_df.columns if 'n' in c.lower() and 'removal' in c.lower()]
    p_cols = [c for c in metadata_df.columns if 'p' in c.lower() and 'removal' in c.lower()]
    
    if not n_cols and not p_cols:
        logger.warning("No N/P removal columns found. Returning all samples.")
        return metadata_df, 0
    
    # Create a mask for samples that have at least one N or P removal value
    # Assuming numeric values; NaN indicates missing
    n_mask = metadata_df[n_cols].notna().any(axis=1) if n_cols else pd.Series([True]*len(metadata_df))
    p_mask = metadata_df[p_cols].notna().any(axis=1) if p_cols else pd.Series([True]*len(metadata_df))
    
    combined_mask = n_mask | p_mask
    filtered_df = metadata_df[combined_mask]
    excluded_count = len(metadata_df) - len(filtered_df)
    logger.info(f"Filtered nutrient removal metrics: excluded {excluded_count} samples.")
    return filtered_df, excluded_count

def subsample_minimum_depth(feature_df: pd.DataFrame, min_depth: int = 5000) -> Tuple[pd.DataFrame, int]:
    """
    Exclude samples with fewer than min_depth reads.
    Returns: (filtered_feature_df, excluded_count)
    """
    # Calculate total reads per sample (row sum)
    read_counts = feature_df.sum(axis=1)
    valid_mask = read_counts >= min_depth
    filtered_df = feature_df[valid_mask]
    excluded_count = len(feature_df) - len(filtered_df)
    logger.info(f"Subsampled minimum depth ({min_depth}): excluded {excluded_count} samples.")
    return filtered_df, excluded_count

def validate_metadata_fields(metadata_df: pd.DataFrame) -> Dict[str, int]:
    """Validate presence of required metadata fields (N/P rates)."""
    required_fields = ['n_removal', 'p_removal'] # Adjust based on actual schema
    missing_counts = {}
    for field in required_fields:
        if field not in metadata_df.columns:
            missing_counts[field] = len(metadata_df)
        else:
            missing_counts[field] = metadata_df[field].isna().sum()
    return missing_counts

def save_exclusion_log(exclusion_data: Dict[str, Any], output_path: Path):
    """Save exclusion log to JSON."""
    with open(output_path, 'w') as f:
        json.dump(exclusion_data, f, indent=2)
    logger.info(f"Exclusion log saved to {output_path}")

def validate_sample_pool_size(metadata_df: pd.DataFrame, min_total: int = 30, min_per_stage: int = 10) -> Tuple[bool, Dict[str, int]]:
    """
    Validate sample pool size after filtering.
    Returns: (is_valid, stage_counts)
    """
    stage_counts = {}
    # Assume 'stage' column exists with values: 'early', 'intermediate', 'mature'
    stage_col = 'stage'
    if stage_col not in metadata_df.columns:
        logger.warning("Stage column not found. Assuming single stage.")
        stage_counts['unknown'] = len(metadata_df)
        total = len(metadata_df)
    else:
        stage_counts = metadata_df[stage_col].value_counts().to_dict()
        total = len(metadata_df)
    
    logger.info(f"Sample pool validation: Total={total}, Per stage={stage_counts}")
    
    is_valid = total >= min_total
    for stage, count in stage_counts.items():
        if count < min_per_stage:
            is_valid = False
            break
    
    if not is_valid:
        logger.error(f"CRITICAL DATA GAP: Insufficient samples after filtering. Total={total}, Stage counts={stage_counts}")
        sys.exit(1)
    
    return is_valid, stage_counts

def perform_sensitivity_analysis(feature_df: pd.DataFrame, metadata_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform FR-015 Sensitivity Analysis: subsampling depth sweep.
    Generates intermediate artifacts and final robustness report.
    """
    logger.info("Starting Sensitivity Analysis (FR-015)...")
    
    # Define depth levels (low, medium, high)
    # Heuristic: use 10th, 50th, 90th percentiles of read counts, or fixed values if data is sparse
    read_counts = feature_df.sum(axis=1)
    min_depth = read_counts.min()
    max_depth = read_counts.max()
    
    # Avoid depths that are too low to be meaningful or too high to be feasible
    low_depth = max(int(np.percentile(read_counts, 10)), 1000)
    medium_depth = max(int(np.percentile(read_counts, 50)), 2000)
    high_depth = max(int(np.percentile(read_counts, 90)), 3000)
    
    # Ensure depths are within valid range [min_depth, max_depth]
    low_depth = min(low_depth, max_depth)
    medium_depth = min(medium_depth, max_depth)
    high_depth = min(high_depth, max_depth)
    
    depths = {
        'low': low_depth,
        'medium': medium_depth,
        'high': high_depth
    }
    
    logger.info(f"Subsampling depths: Low={low_depth}, Medium={medium_depth}, High={high_depth}")
    
    # Function to subsample a single feature table to a target depth
    def subsample_to_depth(df: pd.DataFrame, target_depth: int, seed: int = 42) -> pd.DataFrame:
        np.random.seed(seed)
        result_dfs = []
        for idx, row in df.iterrows():
            total_reads = row.sum()
            if total_reads < target_depth:
                # Cannot subsample this sample; skip or pad? Spec says exclude <5000 initially, but here we might have less after filtering?
                # We assume all samples in df have >= min_depth (from T013), so this should be rare or impossible if depths are chosen carefully.
                # If impossible, we skip the sample.
                continue
            
            # Subsample counts to target depth
            # Simple approach: multinomial sampling based on proportions
            proportions = row / total_reads
            subsampled_counts = np.random.multinomial(target_depth, proportions)
            result_dfs.append(pd.Series(subsampled_counts, index=row.index, name=idx))
        
        return pd.DataFrame(result_dfs)
    
    # Calculate Alpha Diversity (Shannon) for a feature table
    def calculate_shannon_diversity(df: pd.DataFrame) -> pd.Series:
        # Shannon index: H = -sum(p * ln(p))
        # p = count / total_count
        total_counts = df.sum(axis=1)
        shannon = pd.Series(index=df.index, dtype=float)
        for idx, row in df.iterrows():
            total = total_counts[idx]
            if total == 0:
                shannon[idx] = 0.0
                continue
            p = row / total
            # Avoid log(0)
            p = p[p > 0]
            h = -np.sum(p * np.log(p))
            shannon[idx] = h
        return shannon
    
    results = {}
    alpha_diversity_rankings = {}
    
    for level, depth in depths.items():
        logger.info(f"Processing {level} depth ({depth})...")
        try:
            subsampled_df = subsample_to_depth(feature_df, depth)
            
            # Calculate Shannon diversity
            shannon_indices = calculate_shannon_diversity(subsampled_df)
            
            # Rank the diversity indices (1 = highest diversity)
            # Higher Shannon = more diverse. Rank descending.
            rankings = shannon_indices.rank(ascending=False).astype(int)
            alpha_diversity_rankings[level] = rankings
            
            # Save intermediate artifact: subsampled feature table stats
            # We save a summary (mean, std of counts, total samples) to avoid huge JSON
            summary_stats = {
                'level': level,
                'depth': depth,
                'num_samples': len(subsampled_df),
                'mean_reads_per_sample': subsampled_df.sum(axis=1).mean(),
                'shannon_mean': shannon_indices.mean(),
                'shannon_std': shannon_indices.std(),
                'shannon_median': shannon_indices.median()
            }
            
            output_file = DATA_PROCESSED / f'{level}_depth_results.json'
            with open(output_file, 'w') as f:
                json.dump(summary_stats, f, indent=2)
            logger.info(f"Saved {level} depth results to {output_file}")
            
            results[level] = {
                'subsampled_table_stats': summary_stats,
                'shannon_indices': shannon_indices.to_dict(),
                'rankings': rankings.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error processing {level} depth: {e}")
            results[level] = {'error': str(e)}
    
    # Aggregate results into robustness verification report
    logger.info("Calculating Spearman correlations between depth levels...")
    
    correlation_results = {}
    robustness_category = 'unknown'
    
    # Get ranking series for each level
    ranking_series = {}
    for level in depths.keys():
        if level in results and 'rankings' in results[level]:
            # Convert to Series for correlation
            rankings = pd.Series(results[level]['rankings'])
            ranking_series[level] = rankings
    
    if len(ranking_series) < 2:
        logger.error("Not enough depth levels with valid rankings to compute correlations.")
        robustness_category = 'insufficient_data'
    else:
        levels = list(ranking_series.keys())
        pairs = []
        correlations = []
        
        for i in range(len(levels)):
            for j in range(i + 1, len(levels)):
                level_a, level_b = levels[i], levels[j]
                s_a, s_b = ranking_series[level_a], ranking_series[level_b]
                
                # Align indices
                common_idx = s_a.index.intersection(s_b.index)
                if len(common_idx) < 5:
                    logger.warning(f"Too few common samples between {level_a} and {level_b} for correlation.")
                    continue
                
                s_a_common = s_a.loc[common_idx]
                s_b_common = s_b.loc[common_idx]
                
                corr, p_val = spearmanr(s_a_common, s_b_common)
                pairs.append(f"{level_a} vs {level_b}")
                correlations.append(corr)
                
                correlation_results[f"{level_a}_vs_{level_b}"] = {
                    'spearman_correlation': corr,
                    'p_value': p_val
                }
        
        if correlations:
            avg_corr = np.mean(correlations)
            correlation_results['average_correlation'] = avg_corr
            
            # Qualitative assessment
            if avg_corr > 0.85:
                robustness_category = 'robust'
            elif avg_corr >= 0.7:
                robustness_category = 'moderate'
            else:
                robustness_category = 'weak'
        else:
            robustness_category = 'no_correlations_computed'
    
    # Construct final report
    robustness_report = {
        'analysis_type': 'FR-015 Sensitivity Analysis - Subsampling Depth Sweep',
        'depth_levels': depths,
        'alpha_diversity_rankings': {
            level: results[level]['rankings'] if level in results else None
            for level in depths.keys()
        },
        'spearman_correlations': correlation_results,
        'qualitative_assessment': {
            'category': robustness_category,
            'description': f"Robustness categorized as '{robustness_category}' based on average Spearman correlation of alpha diversity rankings."
        },
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    report_path = DATA_PROCESSED / 'robustness_verification_report.json'
    with open(report_path, 'w') as f:
        json.dump(robustness_report, f, indent=2)
    
    logger.info(f"Robustness verification report saved to {report_path}")
    logger.info(f"Sensitivity Analysis Complete. Robustness: {robustness_category}")
    
    return robustness_report

def preprocess_data():
    """Main preprocessing pipeline: Load, Filter, Subsample, Sensitivity Analysis."""
    logger.info("Starting Preprocessing Pipeline...")
    
    # 1. Load data (Assuming T011/T012/T013 have produced data in data/raw/)
    # We expect a feature table and metadata in data/raw/
    feature_table_path = DATA_RAW / 'feature_table.csv' # Or .tsv, .json
    if not feature_table_path.exists():
        # Try other common names
        possible_names = ['feature_table.csv', 'feature_table.tsv', 'otu_table.csv', 'feature-table.csv']
        found = False
        for name in possible_names:
            p = DATA_RAW / name
            if p.exists():
                feature_table_path = p
                found = True
                break
        if not found:
            logger.error("CRITICAL DATA GAP: No feature table found in data/raw/")
            sys.exit(1)
    
    logger.info(f"Loading feature table from {feature_table_path}")
    feature_df, metadata_df = load_feature_table(feature_table_path)
    
    # 2. Filter for constructed wetlands
    metadata_df = filter_constructed_wetlands(metadata_df)
    
    # 3. Filter for nutrient removal metrics
    metadata_df, n_excluded = filter_nutrient_removal_metrics(metadata_df)
    
    # 4. Validate metadata fields
    missing_fields = validate_metadata_fields(metadata_df)
    if missing_fields:
        logger.warning(f"Missing metadata fields: {missing_fields}")
    
    # 5. Save exclusion log
    exclusion_log = {
        'constructed_wetland_filter': 'N/A', # Count not explicitly tracked in filter function above, but can be added
        'nutrient_removal_filter': n_excluded,
        'missing_metadata_fields': missing_fields
    }
    save_exclusion_log(exclusion_log, DATA_PROCESSED / 'exclusion_log.json')
    
    # 6. Subsample minimum depth (T013)
    feature_df, min_depth_excluded = subsample_minimum_depth(feature_df, min_depth=5000)
    exclusion_log['minimum_depth_filter'] = min_depth_excluded
    save_exclusion_log(exclusion_log, DATA_PROCESSED / 'exclusion_log.json')
    
    # 7. Validate sample pool size (T013b)
    validate_sample_pool_size(metadata_df)
    
    # 8. Perform Sensitivity Analysis (T014)
    robustness_report = perform_sensitivity_analysis(feature_df, metadata_df)
    
    logger.info("Preprocessing Pipeline Complete.")
    return robustness_report

def main():
    """Entry point for the script."""
    try:
        preprocess_data()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()