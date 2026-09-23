"""
Harmonizer module for merging and filtering AGP and UKBB datasets.

This module handles:
- Loading raw AGP and UKBB data
- Converting fiber units to g/day
- Filtering samples based on read count and fiber intake
- Merging datasets with cohort identification
- Logging exclusion reasons and counts
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

import pandas as pd
import numpy as np

# Import logger from project utils
from src.utils.logger import get_logger
from src.ingestion.logging_config import get_ingestion_logger, log_filter_counts, log_harmonization_result, log_merge_result

# Constants
MIN_READ_COUNT = 5000
MIN_FIBER = 0.0
MAX_FIBER = 200.0
OUTPUT_FILE = "data/processed/merged_harmonized.tsv"
LOG_FILE = "data/processed/results/harmonization_log.txt"

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent.parent

def load_agp_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load AGP raw data from TSV file.
    
    Args:
        filepath: Path to AGP raw TSV file. If None, uses default path.
        
    Returns:
        DataFrame with AGP data.
        
    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If required columns are missing.
    """
    if filepath is None:
        filepath = get_project_root() / "data" / "raw" / "agp_raw.tsv"
    
    if not filepath.exists():
        raise FileNotFoundError(f"AGP raw data file not found: {filepath}")
    
    logger = get_ingestion_logger("harmonizer")
    logger.info(f"Loading AGP data from {filepath}")
    
    df = pd.read_csv(filepath, sep='\t', low_memory=False)
    
    # Expected columns based on AGP loader output
    required_cols = ['sample_id', 'fiber_g_day', 'read_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"AGP data missing required columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} AGP samples")
    return df.copy()

def load_ukbb_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """
    Load UKBB raw data from TSV file.
    
    Args:
        filepath: Path to UKBB raw TSV file. If None, uses default path.
        
    Returns:
        DataFrame with UKBB data.
        
    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If required columns are missing.
    """
    if filepath is None:
        filepath = get_project_root() / "data" / "raw" / "ukbb_raw.tsv"
    
    if not filepath.exists():
        raise FileNotFoundError(f"UKBB raw data file not found: {filepath}")
    
    logger = get_ingestion_logger("harmonizer")
    logger.info(f"Loading UKBB data from {filepath}")
    
    df = pd.read_csv(filepath, sep='\t', low_memory=False)
    
    # Expected columns based on UKBB loader output
    required_cols = ['sample_id', 'fiber_g_day', 'read_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"UKBB data missing required columns: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} UKBB samples")
    return df.copy()

def harmonize_fiber_units(df: pd.DataFrame, source: str) -> pd.DataFrame:
    """
    Ensure fiber units are in g/day.
    
    Args:
        df: Input DataFrame with fiber data.
        source: Source identifier ('AGP' or 'UKBB') for logging.
        
    Returns:
        DataFrame with harmonized fiber units.
    """
    logger = get_ingestion_logger("harmonizer")
    logger.info(f"Harmonizing fiber units for {source} data")
    
    # Assuming data is already in g/day from loaders
    # If conversion is needed, it would happen here
    df = df.copy()
    
    # Ensure numeric type
    df['fiber_g_day'] = pd.to_numeric(df['fiber_g_day'], errors='coerce')
    
    return df

def filter_samples(df: pd.DataFrame, source: str, exclusion_log: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Filter samples based on read count and fiber intake criteria.
    
    Criteria:
    - Read count >= 5000
    - Fiber intake between 0 and 200 g/day
    - No missing fiber data
    
    Args:
        df: Input DataFrame.
        source: Source identifier ('AGP' or 'UKBB').
        exclusion_log: List to append exclusion records to.
        
    Returns:
        Filtered DataFrame.
    """
    logger = get_ingestion_logger("harmonizer")
    initial_count = len(df)
    
    # Filter 1: Missing fiber data
    missing_fiber = df['fiber_g_day'].isna()
    if missing_fiber.any():
        excluded_count = missing_fiber.sum()
        exclusion_log.append({
            'source': source,
            'reason': 'missing_fiber_data',
            'count': int(excluded_count)
        })
        logger.warning(f"{source}: Excluded {excluded_count} samples with missing fiber data")
        df = df[~missing_fiber]
    
    # Filter 2: Read count < 5000
    low_reads = df['read_count'] < MIN_READ_COUNT
    if low_reads.any():
        excluded_count = low_reads.sum()
        exclusion_log.append({
            'source': source,
            'reason': f'read_count_below_{MIN_READ_COUNT}',
            'count': int(excluded_count)
        })
        logger.warning(f"{source}: Excluded {excluded_count} samples with read_count < {MIN_READ_COUNT}")
        df = df[~low_reads]
    
    # Filter 3: Fiber < 0 or > 200 g/day
    invalid_fiber = (df['fiber_g_day'] < MIN_FIBER) | (df['fiber_g_day'] > MAX_FIBER)
    if invalid_fiber.any():
        excluded_count = invalid_fiber.sum()
        exclusion_log.append({
            'source': source,
            'reason': f'fiber_outside_{MIN_FIBER}_{MAX_FIBER}g_day',
            'count': int(excluded_count)
        })
        logger.warning(f"{source}: Excluded {excluded_count} samples with fiber outside [{MIN_FIBER}, {MAX_FIBER}] g/day")
        df = df[~invalid_fiber]
    
    final_count = len(df)
    log_filter_counts(
        logger=logger,
        source=source,
        initial=initial_count,
        final=final_count,
        excluded=initial_count - final_count
    )
    
    return df.reset_index(drop=True)

def merge_datasets(agp_df: pd.DataFrame, ukbb_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge AGP and UKBB datasets with cohort identification.
    
    Args:
        agp_df: Filtered AGP DataFrame.
        ukbb_df: Filtered UKBB DataFrame.
        
    Returns:
        Merged DataFrame with cohort_id column.
    """
    logger = get_ingestion_logger("harmonizer")
    logger.info("Merging AGP and UKBB datasets")
    
    # Add cohort_id column
    agp_df = agp_df.copy()
    ukbb_df = ukbb_df.copy()
    
    agp_df['cohort_id'] = 'AGP'
    ukbb_df['cohort_id'] = 'UKBB'
    
    # Concatenate
    merged = pd.concat([agp_df, ukbb_df], ignore_index=True)
    
    # Ensure column order: sample_id, cohort_id, fiber_g_day, read_count, then others
    # Get all columns
    base_cols = ['sample_id', 'cohort_id', 'fiber_g_day', 'read_count']
    other_cols = [col for col in merged.columns if col not in base_cols]
    final_cols = base_cols + sorted(other_cols)
    
    merged = merged[final_cols]
    
    log_merge_result(
        logger=logger,
        agp_count=len(agp_df),
        ukbb_count=len(ukbb_df),
        total_count=len(merged)
    )
    
    return merged

def write_exclusion_log(exclusion_log: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write exclusion log to file.
    
    Args:
        exclusion_log: List of exclusion records.
        output_path: Path to write the log file.
    """
    logger = get_ingestion_logger("harmonizer")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("Harmonization Exclusion Log\n")
        f.write("=" * 50 + "\n\n")
        
        total_excluded = 0
        for record in exclusion_log:
            source = record['source']
            reason = record['reason']
            count = record['count']
            total_excluded += count
            f.write(f"Source: {source}\n")
            f.write(f"Reason: {reason}\n")
            f.write(f"Count: {count}\n")
            f.write("-" * 30 + "\n")
        
        f.write(f"\nTotal samples excluded: {total_excluded}\n")
    
    logger.info(f"Wrote exclusion log to {output_path}")

def harmonize_and_merge(
    agp_path: Optional[Path] = None,
    ukbb_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    log_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Main orchestration function for harmonization and merging.
    
    Args:
        agp_path: Path to AGP raw data.
        ukbb_path: Path to UKBB raw data.
        output_path: Path for merged output.
        log_path: Path for exclusion log.
        
    Returns:
        Merged and harmonized DataFrame.
    """
    logger = get_ingestion_logger("harmonizer")
    logger.info("Starting harmonization and merge process")
    
    # Load data
    agp_df = load_agp_data(agp_path)
    ukbb_df = load_ukbb_data(ukbb_path)
    
    # Harmonize units
    agp_df = harmonize_fiber_units(agp_df, "AGP")
    ukbb_df = harmonize_fiber_units(ukbb_df, "UKBB")
    
    # Track exclusions
    exclusion_log: List[Dict[str, Any]] = []
    
    # Filter samples
    agp_df = filter_samples(agp_df, "AGP", exclusion_log)
    ukbb_df = filter_samples(ukbb_df, "UKBB", exclusion_log)
    
    # Merge datasets
    merged_df = merge_datasets(agp_df, ukbb_df)
    
    # Write exclusion log
    if log_path is None:
        log_path = get_project_root() / LOG_FILE
    write_exclusion_log(exclusion_log, log_path)
    
    # Write merged data
    if output_path is None:
        output_path = get_project_root() / OUTPUT_FILE
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, sep='\t', index=False)
    
    log_harmonization_result(
        logger=logger,
        output_file=str(output_path),
        final_count=len(merged_df)
    )
    
    logger.info(f"Harmonization complete. Output: {output_path}")
    
    return merged_df

def build_arg_parser() -> argparse.ArgumentParser:
    """Build argument parser for command-line execution."""
    parser = argparse.ArgumentParser(
        description="Harmonize and merge AGP and UKBB datasets"
    )
    parser.add_argument(
        "--agp-path",
        type=Path,
        default=None,
        help="Path to AGP raw TSV file"
    )
    parser.add_argument(
        "--ukbb-path",
        type=Path,
        default=None,
        help="Path to UKBB raw TSV file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path for merged output TSV file"
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=None,
        help="Path for exclusion log file"
    )
    return parser

def main(args: Optional[List[str]] = None) -> None:
    """Main entry point for command-line execution."""
    parser = build_arg_parser()
    parsed_args = parser.parse_args(args)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        harmonize_and_merge(
            agp_path=parsed_args.agp_path,
            ukbb_path=parsed_args.ukbb_path,
            output_path=parsed_args.output,
            log_path=parsed_args.log
        )
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logging.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
