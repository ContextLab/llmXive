"""
Exclusion logic for low-reliability EBSD samples.

Implements the logic to flag and exclude samples where >50% of points
are filtered out during preprocessing, marking them as "low reliability".
"""
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging import get_logger

logger = get_logger(__name__)

RELIABILITY_THRESHOLD = 0.5  # Exclude if >50% points filtered

def calculate_reliability_metrics(
    original_count: int, 
    filtered_count: int, 
    sample_id: str
) -> Dict[str, Any]:
    """
    Calculate reliability metrics for a single sample.
    
    Args:
        original_count: Number of points before filtering
        filtered_count: Number of points after filtering
        sample_id: Identifier for the sample
        
    Returns:
        Dictionary containing reliability metrics
    """
    if original_count == 0:
        reliability_score = 0.0
        points_filtered_ratio = 1.0
    else:
        points_remaining_ratio = filtered_count / original_count
        points_filtered_ratio = 1.0 - points_remaining_ratio
        reliability_score = points_remaining_ratio
    
    is_low_reliability = points_filtered_ratio > RELIABILITY_THRESHOLD
    
    return {
        'sample_id': sample_id,
        'original_point_count': original_count,
        'filtered_point_count': filtered_count,
        'points_remaining_ratio': points_remaining_ratio,
        'points_filtered_ratio': points_filtered_ratio,
        'is_low_reliability': is_low_reliability,
        'reliability_status': 'low_reliability' if is_low_reliability else 'acceptable'
    }

def apply_exclusion_logic(
    data_path: Path,
    output_path: Path,
    metadata_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Apply exclusion logic to filtered EBSD data.
    
    Reads the filtered data, calculates reliability metrics per sample,
    flags low-reliability samples, and produces a clean dataset excluding
    them.
    
    Args:
        data_path: Path to the filtered EBSD data (Parquet/CSV)
        output_path: Path to write the clean dataset
        metadata_path: Optional path to write detailed metadata about excluded samples
        
    Returns:
        Dictionary containing summary statistics
    """
    logger.info(f"Loading filtered data from {data_path}")
    
    if not data_path.exists():
        raise FileNotFoundError(f"Input data file not found: {data_path}")
    
    # Load data
    if data_path.suffix == '.parquet':
        df = pd.read_parquet(data_path)
    elif data_path.suffix == '.csv':
        df = pd.read_csv(data_path)
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")
    
    if df.empty:
        logger.warning("Input data is empty. Creating empty output.")
        df_clean = pd.DataFrame()
        summary = {
            'total_samples': 0,
            'low_reliability_samples': 0,
            'kept_samples': 0,
            'excluded_samples': 0
        }
    else:
        # Ensure sample_id column exists
        if 'sample_id' not in df.columns:
            raise ValueError("Input data must contain 'sample_id' column")
        
        # Calculate point counts per sample
        original_counts = df.groupby('sample_id').size()
        
        # We need the original count before filtering. 
        # Assuming the input to this stage is the result of T012 (filtering),
        # we need to track the original counts. 
        # If the input data contains a 'original_count' column (from T012), use it.
        # Otherwise, we assume the current df represents the kept points,
        # and we need to know how many were dropped.
        
        # Strategy: We look for a metadata column or infer from context.
        # However, T012 (preprocess.py) should ideally pass the original count.
        # If not present, we must rely on a separate metadata file or assume
        # the input to T012 was the "original" and we are comparing.
        # Since T012 is the filter step, the data passed to T014 is the *filtered* result.
        # We need the *original* count to calculate the ratio.
        
        # If the dataframe has 'original_point_count' (added by T012), use it.
        if 'original_point_count' in df.columns:
            # Group by sample_id and aggregate
            sample_stats = df.groupby('sample_id').agg(
                filtered_point_count=('sample_id', 'size'),
                original_point_count=('original_point_count', 'first')
            ).reset_index()
        else:
            # Fallback: If original count is not in the data, we cannot calculate
            # the ratio accurately without external metadata. 
            # However, per T013, we handle missing info by logging warnings.
            # For this implementation, we assume the caller (T015 or main) 
            # ensures the 'original_point_count' is present in the input data
            # from T012. If missing, we raise an error as we cannot proceed.
            raise ValueError(
                "Input data missing 'original_point_count' column. "
                "Preprocessing step (T012) must include original point counts."
            )
        
        # Calculate metrics
        metrics = []
        for _, row in sample_stats.iterrows():
            metrics.append(calculate_reliability_metrics(
                original_count=row['original_point_count'],
                filtered_count=row['filtered_point_count'],
                sample_id=row['sample_id']
            ))
        
        metrics_df = pd.DataFrame(metrics)
        
        # Identify low reliability samples
        low_reliability_ids = metrics_df[metrics_df['is_low_reliability']]['sample_id'].tolist()
        kept_ids = metrics_df[~metrics_df['is_low_reliability']]['sample_id'].tolist()
        
        logger.info(f"Identified {len(low_reliability_ids)} low-reliability samples to exclude.")
        logger.info(f"Keeping {len(kept_ids)} acceptable samples.")
        
        # Filter the main dataframe
        df_clean = df[~df['sample_id'].isin(low_reliability_ids)].copy()
        
        # Add reliability status to the clean dataframe (optional, for debugging)
        # But the output should ideally just be the clean data.
        
        # Prepare metadata for excluded samples
        excluded_metadata = metrics_df[metrics_df['is_low_reliability']].copy()
        
        # Summary
        summary = {
            'total_samples': len(metrics_df),
            'low_reliability_samples': len(low_reliability_ids),
            'kept_samples': len(kept_ids),
            'excluded_samples': len(low_reliability_ids),
            'excluded_sample_ids': low_reliability_ids
        }
        
        # Write metadata if requested
        if metadata_path:
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            excluded_metadata.to_csv(metadata_path, index=False)
            logger.info(f"Wrote exclusion metadata to {metadata_path}")
    
    # Write clean data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix == '.parquet':
        df_clean.to_parquet(output_path, index=False)
    elif output_path.suffix == '.csv':
        df_clean.to_csv(output_path, index=False)
    else:
        # Default to parquet
        output_path = output_path.with_suffix('.parquet')
        df_clean.to_parquet(output_path, index=False)
    
    logger.info(f"Wrote clean dataset to {output_path}")
    
    return summary

def main():
    """
    Main entry point for exclusion logic.
    Reads configuration, runs exclusion, and prints summary.
    """
    import json
    from config import get_reductions
    
    # Default paths (can be overridden by CLI args or config in a full implementation)
    # Assuming the pipeline runs T012 -> T014 -> T015
    # T012 outputs to data/processed/filtered_ebsd.parquet (or similar)
    # T014 reads that and outputs data/processed/cleaned_ebsd.parquet
    
    input_path = Path("data/processed/filtered_ebsd.parquet")
    output_path = Path("data/processed/cleaned_ebsd.parquet")
    metadata_path = Path("data/processed/exclusion_metadata.csv")
    
    if not input_path.exists():
        # Check if CSV fallback exists
        csv_input = Path("data/processed/filtered_ebsd.csv")
        if csv_input.exists():
            input_path = csv_input
        else:
            logger.error(f"Input file not found: {input_path} or {csv_input}")
            return
    
    try:
        summary = apply_exclusion_logic(input_path, output_path, metadata_path)
        print(json.dumps(summary, indent=2))
    except Exception as e:
        logger.error(f"Exclusion logic failed: {e}")
        raise
