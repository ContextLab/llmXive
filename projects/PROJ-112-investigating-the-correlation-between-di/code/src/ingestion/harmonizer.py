import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import pandas as pd
import numpy as np

# Import from existing project modules
from src.utils.logger import get_logger
from src.ingestion.logging_config import log_filter_counts, log_harmonization_result, log_merge_result
from src.preprocessing.id_generator import generate_sample_id

# Constants
MIN_READ_COUNT = 5000
MAX_FIBER_G_DAY = 200
MIN_FIBER_G_DAY = 0
PSEUDOCOUNT_FOR_ZERO = 1e-6  # Small value to avoid log(0) if needed later, though filtering handles it

def get_project_root() -> Path:
    """Determine the project root directory."""
    # Assume structure: code/src/ingestion/harmonizer.py
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent.parent

def load_agp_data(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load AGP data from the raw TSV file.
    Expected columns: sample_id, fiber_g_day, read_count, ... (plus taxon/covariate cols)
    """
    if path is None:
        path = get_project_root() / "data" / "raw" / "agp_raw.tsv"
    
    if not path.exists():
        raise FileNotFoundError(f"AGP raw data file not found at {path}")
    
    logger = get_logger("harmonizer")
    logger.info(f"Loading AGP data from {path}")
    
    # Read TSV. AGP data usually has sample metadata and OTU table merged or separate.
    # Assuming the loader T012 produced a unified TSV with metadata + abundances.
    # We need to handle potential column name variations.
    df = pd.read_csv(path, sep='\t')
    
    # Ensure standard column names exist (T012 should have handled this, but safe guard)
    # Expected: sample_id, fiber_g_day, read_count, cohort_id (maybe not yet), taxon columns
    if 'sample_id' not in df.columns:
        # Try to find an ID column
        id_cols = [c for c in df.columns if 'id' in c.lower()]
        if id_cols:
            df.rename(columns={id_cols[0]: 'sample_id'}, inplace=True)
        else:
            df['sample_id'] = df.index.astype(str)
    
    if 'fiber_g_day' not in df.columns:
        # Try common variations
        for col in ['fiber', 'dietary_fiber', 'fiber_intake']:
            if col in df.columns:
                df['fiber_g_day'] = df[col]
                break
        if 'fiber_g_day' not in df.columns:
            raise ValueError("AGP data missing fiber intake column")
    
    if 'read_count' not in df.columns:
        for col in ['reads', 'read_depth', 'sequencing_depth']:
            if col in df.columns:
                df['read_count'] = df[col]
                break
        if 'read_count' not in df.columns:
            # Try to infer from OTU sum if present, but for now assume missing means fail
            # Or assume a default if the schema allows, but task says filter < 5000
            raise ValueError("AGP data missing read count column")

    return df

def load_ukbb_data(path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load UKBB data from the raw TSV file.
    """
    if path is None:
        path = get_project_root() / "data" / "raw" / "ukbb_raw.tsv"
    
    if not path.exists():
        raise FileNotFoundError(f"UKBB raw data file not found at {path}")
    
    logger = get_logger("harmonizer")
    logger.info(f"Loading UKBB data from {path}")
    
    df = pd.read_csv(path, sep='\t')
    
    # Standardize column names similar to AGP
    if 'sample_id' not in df.columns:
        id_cols = [c for c in df.columns if 'id' in c.lower()]
        if id_cols:
            df.rename(columns={id_cols[0]: 'sample_id'}, inplace=True)
        else:
            df['sample_id'] = df.index.astype(str)
    
    if 'fiber_g_day' not in df.columns:
        for col in ['fiber', 'dietary_fiber', 'fiber_intake']:
            if col in df.columns:
                df['fiber_g_day'] = df[col]
                break
        if 'fiber_g_day' not in df.columns:
            raise ValueError("UKBB data missing fiber intake column")
    
    if 'read_count' not in df.columns:
        for col in ['reads', 'read_depth', 'sequencing_depth']:
            if col in df.columns:
                df['read_count'] = df[col]
                break
        if 'read_count' not in df.columns:
            raise ValueError("UKBB data missing read count column")
    
    return df

def harmonize_fiber_units(df: pd.DataFrame, source: str = "unknown") -> pd.DataFrame:
    """
    Ensure fiber is in g/day. 
    If the loader T012/T013 already did this, this is a pass-through.
    If units are different (e.g., mg/day), convert here.
    For this implementation, we assume input is already in g/day as per T012/T013 contracts,
    but we enforce numeric type and bounds checking later.
    """
    logger = get_logger("harmonizer")
    logger.info(f"Harmonizing fiber units for {source}")
    
    # Ensure numeric
    df['fiber_g_day'] = pd.to_numeric(df['fiber_g_day'], errors='coerce')
    
    # Check for negative values or extreme outliers before filtering
    # (Filtering happens in filter_samples)
    
    return df

def filter_samples(df: pd.DataFrame, source: str = "unknown") -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filter samples based on:
    1. Read count >= 5000
    2. Fiber intake >= 0 and <= 200 g/day
    3. Missing fiber data (NaN)
    
    Returns: (filtered_df, stats_dict)
    """
    logger = get_logger("harmonizer")
    initial_count = len(df)
    stats = {
        "source": source,
        "initial_count": initial_count,
        "excluded_read_count": 0,
        "excluded_fiber_range": 0,
        "excluded_missing_fiber": 0,
        "final_count": 0
    }
    
    # 1. Filter missing fiber
    before_fiber = len(df)
    df = df.dropna(subset=['fiber_g_day'])
    stats["excluded_missing_fiber"] = before_fiber - len(df)
    
    # 2. Filter read count < 5000
    before_reads = len(df)
    df = df[df['read_count'] >= MIN_READ_COUNT]
    stats["excluded_read_count"] = before_reads - len(df)
    
    # 3. Filter fiber range [0, 200]
    before_fiber_range = len(df)
    df = df[(df['fiber_g_day'] >= MIN_FIBER_G_DAY) & (df['fiber_g_day'] <= MAX_FIBER_G_DAY)]
    stats["excluded_fiber_range"] = before_fiber_range - len(df)
    
    stats["final_count"] = len(df)
    
    logger.info(f"Filtering {source}: {initial_count} -> {stats['final_count']} samples")
    log_filter_counts(logger, stats)
    
    return df, stats

def merge_datasets(agp_df: pd.DataFrame, ukbb_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge AGP and UKBB datasets.
    Adds 'cohort_id' column.
    Ensures consistent column ordering.
    """
    logger = get_logger("harmonizer")
    logger.info("Merging AGP and UKBB datasets")
    
    agp_df = agp_df.copy()
    ukbb_df = ukbb_df.copy()
    
    agp_df['cohort_id'] = "AGP"
    ukbb_df['cohort_id'] = "UKBB"
    
    # Combine
    combined = pd.concat([agp_df, ukbb_df], ignore_index=True)
    
    # Sort columns: sample_id, cohort_id, fiber_g_day, read_count, then others
    # Identify taxon columns (usually start with 'OTU' or taxon names, or specific suffix)
    # For now, keep order: sample_id, cohort_id, fiber_g_day, read_count, then rest
    primary_cols = ['sample_id', 'cohort_id', 'fiber_g_day', 'read_count']
    other_cols = [c for c in combined.columns if c not in primary_cols]
    combined = combined[primary_cols + other_cols]
    
    log_merge_result(logger, len(agp_df), len(ukbb_df), len(combined))
    
    return combined

def write_exclusion_log(stats_list: List[Dict[str, Any]], output_path: Optional[Path] = None):
    """
    Write a log of exclusion counts to a file.
    """
    if output_path is None:
        output_path = get_project_root() / "data" / "processed" / "results" / "harmonization_exclusion_log.txt"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write("Harmonization Exclusion Log\n")
        f.write("=" * 30 + "\n")
        for stats in stats_list:
            f.write(f"Cohort: {stats['source']}\n")
            f.write(f"  Initial: {stats['initial_count']}\n")
            f.write(f"  Excluded (Missing Fiber): {stats['excluded_missing_fiber']}\n")
            f.write(f"  Excluded (Read Count < {MIN_READ_COUNT}): {stats['excluded_read_count']}\n")
            f.write(f"  Excluded (Fiber Range [{MIN_FIBER_G_DAY}-{MAX_FIBER_G_DAY}]): {stats['excluded_fiber_range']}\n")
            f.write(f"  Final Count: {stats['final_count']}\n")
            f.write("-" * 30 + "\n")
    
    logger = get_logger("harmonizer")
    logger.info(f"Exclusion log written to {output_path}")

def harmonize_and_merge(
    agp_path: Optional[Path] = None,
    ukbb_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    exclusion_log_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Main orchestration function for T014.
    1. Load AGP and UKBB data.
    2. Harmonize units (ensure g/day).
    3. Filter samples (reads, fiber range, missing).
    4. Merge with cohort_id.
    5. Write outputs.
    """
    logger = get_logger("harmonizer")
    logger.info("Starting harmonization pipeline")
    
    # Load
    agp_df = load_agp_data(agp_path)
    ukbb_df = load_ukbb_data(ukbb_path)
    
    # Harmonize
    agp_df = harmonize_fiber_units(agp_df, "AGP")
    ukbb_df = harmonize_fiber_units(ukbb_df, "UKBB")
    
    # Filter
    agp_filtered, agp_stats = filter_samples(agp_df, "AGP")
    ukbb_filtered, ukbb_stats = filter_samples(ukbb_df, "UKBB")
    
    # Merge
    merged_df = merge_datasets(agp_filtered, ukbb_filtered)
    
    # Write exclusion log
    write_exclusion_log([agp_stats, ukbb_stats], exclusion_log_path)
    
    # Write merged data
    if output_path is None:
        output_path = get_project_root() / "data" / "processed" / "merged_harmonized.tsv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, sep='\t', index=False)
    
    logger.info(f"Harmonization complete. Output: {output_path}")
    log_harmonization_result(logger, len(merged_df))
    
    return merged_df

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harmonize and merge AGP and UKBB datasets.")
    parser.add_argument("--agp-path", type=Path, help="Path to AGP raw TSV")
    parser.add_argument("--ukbb-path", type=Path, help="Path to UKBB raw TSV")
    parser.add_argument("--output", type=Path, help="Output path for merged TSV")
    parser.add_argument("--log-path", type=Path, help="Output path for exclusion log")
    return parser

def main():
    parser = build_arg_parser()
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger("harmonizer")
    
    try:
        harmonize_and_merge(
            agp_path=args.agp_path,
            ukbb_path=args.ukbb_path,
            output_path=args.output,
            exclusion_log_path=args.log_path
        )
    except Exception as e:
        logger.error(f"Harmonization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
