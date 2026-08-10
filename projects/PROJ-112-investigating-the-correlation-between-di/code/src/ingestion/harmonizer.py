import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import pandas as pd

from src.utils.logger import get_logger
from src.ingestion.logging_config import (
    log_download_status,
    log_filter_counts,
    log_harmonization_result,
    log_merge_result,
    log_validation_result
)

def load_agp_data(file_path: str) -> pd.DataFrame:
    """
    Load AGP data from file.
    
    Args:
        file_path: Path to AGP data file
        
    Returns:
        DataFrame with AGP data
    """
    logger = get_logger(LOG_HARMONIZE)
    logger.info(f"Loading AGP data from {file_path}")
    
    try:
        df = pd.read_csv(file_path, sep='\t' if file_path.endswith('.tsv') else ',')
        log_validation_result(logger, "AGP load", True, f"Loaded {len(df)} samples")
        return df
    except Exception as e:
        log_validation_result(logger, "AGP load", False, str(e))
        raise

def load_ukbb_data(file_path: str) -> pd.DataFrame:
    """
    Load UKBB data from file.
    
    Args:
        file_path: Path to UKBB data file
        
    Returns:
        DataFrame with UKBB data
    """
    logger = get_logger(LOG_HARMONIZE)
    logger.info(f"Loading UKBB data from {file_path}")
    
    try:
        df = pd.read_csv(file_path, sep='\t' if file_path.endswith('.tsv') else ',')
        log_validation_result(logger, "UKBB load", True, f"Loaded {len(df)} samples")
        return df
    except Exception as e:
        log_validation_result(logger, "UKBB load", False, str(e))
        raise

def harmonize_fiber_units(df: pd.DataFrame, 
                          fiber_col: str, 
                          unit_col: Optional[str] = None) -> pd.DataFrame:
    """
    Harmonize fiber units to g/day.
    
    Args:
        df: DataFrame with fiber data
        fiber_col: Column name containing fiber values
        unit_col: Column name containing units (optional)
        
    Returns:
        DataFrame with harmonized fiber values
    """
    logger = get_logger(LOG_HARMONIZE)
    original_count = len(df)
    
    # If unit column exists, convert units
    if unit_col and unit_col in df.columns:
        logger.info(f"Converting fiber units from {unit_col} to g/day")
        
        # Example conversions (would need actual data-specific logic)
        def convert_to_g_per_day(row):
            value = row[fiber_col]
            unit = row[unit_col]
            
            if pd.isna(value):
                return value
            
            if unit == 'mg/day':
                return value / 1000.0
            elif unit == 'g/week':
                return value / 7.0
            elif unit == 'g/month':
                return value / 30.0
            else:
                return value  # Assume already g/day
        
        df[fiber_col] = df.apply(convert_to_g_per_day, axis=1)
        
        log_harmonization_result(
            logger,
            "fiber_units",
            {fiber_col: f"{fiber_col}_g_per_day"},
            {fiber_col: "mg/day, g/week, g/month -> g/day"}
        )
    
    return df

def filter_samples(df: pd.DataFrame, 
                  min_reads: int = 5000,
                  min_fiber: float = 0.0,
                  max_fiber: float = 200.0,
                  reads_col: str = 'sequence_reads',
                  fiber_col: str = 'fiber_g_per_day') -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filter samples based on read depth and fiber intake.
    
    Args:
        df: DataFrame with sample data
        min_reads: Minimum sequence reads required
        min_fiber: Minimum fiber intake (g/day)
        max_fiber: Maximum fiber intake (g/day)
        reads_col: Column name for sequence reads
        fiber_col: Column name for fiber intake
        
    Returns:
        Tuple of (filtered DataFrame, filter counts)
    """
    logger = get_logger(LOG_FILTER)
    filter_counts = {}
    
    initial_count = len(df)
    
    # Filter by read depth
    if reads_col in df.columns:
        df = df[df[reads_col] >= min_reads]
        filtered_count = len(df)
        filter_counts['read_depth'] = {
            'initial': initial_count,
            'final': filtered_count,
            'excluded': initial_count - filtered_count,
            'reason': f'Read depth < {min_reads}'
        }
        log_filter_counts(
            logger,
            'read_depth',
            initial_count,
            filtered_count,
            initial_count - filtered_count,
            f'Read depth < {min_reads}'
        )
        initial_count = filtered_count
    
    # Filter by fiber range
    if fiber_col in df.columns:
        df = df[(df[fiber_col] >= min_fiber) & (df[fiber_col] <= max_fiber)]
        filtered_count = len(df)
        filter_counts['fiber_range'] = {
            'initial': initial_count,
            'final': filtered_count,
            'excluded': initial_count - filtered_count,
            'reason': f'Fiber outside {min_fiber}-{max_fiber} g/day'
        }
        log_filter_counts(
            logger,
            'fiber_range',
            initial_count,
            filtered_count,
            initial_count - filtered_count,
            f'Fiber outside {min_fiber}-{max_fiber} g/day'
        )
    
    # Exclude samples with missing fiber data
    if fiber_col in df.columns:
        initial_count = len(df)
        df = df.dropna(subset=[fiber_col])
        filtered_count = len(df)
        filter_counts['missing_fiber'] = {
            'initial': initial_count,
            'final': filtered_count,
            'excluded': initial_count - filtered_count,
            'reason': 'Missing fiber data'
        }
        log_filter_counts(
            logger,
            'missing_fiber',
            initial_count,
            filtered_count,
            initial_count - filtered_count,
            'Missing fiber data'
        )
    
    return df, filter_counts

def merge_datasets(agp_df: pd.DataFrame, ukbb_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge AGP and UKBB datasets.
    
    Args:
        agp_df: AGP DataFrame
        ukbb_df: UKBB DataFrame
        
    Returns:
        Merged DataFrame
    """
    logger = get_logger(LOG_HARMONIZE)
    
    # Add cohort identifier
    agp_df['cohort'] = 'AGP'
    ukbb_df['cohort'] = 'UKBB'
    
    # Standardize column names if needed
    # This would be more complex in production with actual column mapping
    merged_df = pd.concat([agp_df, ukbb_df], ignore_index=True)
    
    log_merge_result(
        logger,
        len(agp_df),
        len(ukbb_df),
        len(merged_df)
    )
    
    return merged_df

def harmonize_and_merge(agp_path: str, ukbb_path: str, output_path: str) -> pd.DataFrame:
    """
    Full harmonization and merge pipeline.
    
    Args:
        agp_path: Path to AGP data file
        ukbb_path: Path to UKBB data file
        output_path: Path to save merged output
        
    Returns:
        Merged and harmonized DataFrame
    """
    logger = get_logger(LOG_HARMONIZE)
    logger.info("Starting harmonization and merge pipeline")
    
    # Load data
    agp_df = load_agp_data(agp_path)
    ukbb_df = load_ukbb_data(ukbb_path)
    
    # Harmonize fiber units
    agp_df = harmonize_fiber_units(agp_df, 'fiber_g_per_day')
    ukbb_df = harmonize_fiber_units(ukbb_df, 'fiber_g_per_day')
    
    # Filter samples
    agp_df, agp_filters = filter_samples(agp_df)
    ukbb_df, ukbb_filters = filter_samples(ukbb_df)
    
    # Merge datasets
    merged_df = merge_datasets(agp_df, ukbb_df)
    
    # Save output
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, sep='\t', index=False)
    
    log_validation_result(
        logger,
        "harmonization_complete",
        True,
        f"Output saved to {output_path}"
    )
    
    return merged_df

def build_arg_parser() -> argparse.ArgumentParser:
    """Build argument parser for harmonizer."""
    parser = argparse.ArgumentParser(description="Harmonize and merge AGP and UKBB data")
    parser.add_argument(
        "--agp-path",
        type=str,
        default="data/raw/agp/agp_sample_mapping.tsv",
        help="Path to AGP data file"
    )
    parser.add_argument(
        "--ukbb-path",
        type=str,
        default="data/raw/ukbb/ukbb_processed.tsv",
        help="Path to UKBB data file"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/processed/merged_harmonized.tsv",
        help="Path to save merged output"
    )
    return parser

def main():
    """Main entry point for harmonizer."""
    parser = build_arg_parser()
    args = parser.parse_args()
    
    logger = get_logger(LOG_HARMONIZE)
    logger.info("Starting harmonization pipeline")
    
    try:
        merged_df = harmonize_and_merge(args.agp_path, args.ukbb_path, args.output_path)
        print(f"Successfully harmonized and merged data: {len(merged_df)} samples")
    except Exception as e:
        logger.error(f"Failed to harmonize data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
