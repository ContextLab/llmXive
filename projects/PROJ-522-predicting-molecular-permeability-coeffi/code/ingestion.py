import os
import sys
import time
import signal
import logging
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import config to read TIMEOUT_GRAPHS
from config import load_config

# Import data loading utilities
from utils.data_loader import fetch_nist_data, fetch_pubchem_data, fetch_mtr_data

# Set up logging
logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

class MemoryLimitError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("TIMEOUT: Graph construction exceeded 5 minutes")

def setup_timeout_handler(seconds: int):
    if os.name == 'posix':
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
    else:
        logger.warning("Signal-based timeout only supported on Linux/Unix")

def cancel_timeout_handler():
    if os.name == 'posix':
        signal.alarm(0)

def ingest_nist_data() -> pd.DataFrame:
    """Fetch NIST dataset using the data loader."""
    logger.info("Fetching NIST dataset...")
    df = fetch_nist_data()
    if df is not None and not df.empty:
        logger.info(f"NIST dataset loaded: {len(df)} rows")
    return df

def ingest_pubchem_data() -> pd.DataFrame:
    """Fetch PubChem dataset using the data loader."""
    logger.info("Fetching PubChem dataset...")
    df = fetch_pubchem_data()
    if df is not None and not df.empty:
        logger.info(f"PubChem dataset loaded: {len(df)} rows")
    return df

def ingest_mtr_data() -> pd.DataFrame:
    """Fetch MTR dataset using the data loader."""
    logger.info("Fetching MTR dataset...")
    df = fetch_mtr_data()
    if df is not None and not df.empty:
        logger.info(f"MTR dataset loaded: {len(df)} rows")
    return df

def deduplicate_smiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle duplicate SMILES by aggregating targets using mean function.
    Returns dataframe with schema: [smiles, target_mean, count, source_id]
    """
    logger.info("Deduplicating SMILES...")
    if df.empty:
        return pd.DataFrame(columns=['smiles', 'target_mean', 'count', 'source_id'])

    # Ensure target column exists
    if 'target' not in df.columns:
        raise ValueError("Input dataframe must contain 'target' column")

    # Group by SMILES and aggregate
    grouped = df.groupby('smiles').agg(
        target_mean=('target', 'mean'),
        count=('target', 'count'),
        source_id=('source_id', 'first') # Take first source ID for simplicity
    ).reset_index()

    logger.info(f"Deduplicated to {len(grouped)} unique compounds")
    return grouped

def merge_sources(df_nist: pd.DataFrame, df_pubchem: pd.DataFrame, df_mtr: pd.DataFrame) -> pd.DataFrame:
    """Merge NIST, PubChem, and MTR datasets into a single dataframe."""
    logger.info("Merging datasets...")
    dfs = [df for df in [df_nist, df_pubchem, df_mtr] if df is not None and not df.empty]
    if not dfs:
        return pd.DataFrame()
    
    merged = pd.concat(dfs, ignore_index=True)
    logger.info(f"Merged dataset size: {len(merged)} rows")
    return merged

def validate_and_filter_dataset(df: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    """
    Validate >=500 unique compounds, exclude rows with missing permeability values,
    log exclusion reasons, and output validation report.
    
    Returns:
        Dict containing validation stats and exclusion details.
    """
    logger.info("Validating and filtering dataset...")
    
    total_rows = len(df)
    exclusion_log = []
    
    # Filter out rows with missing permeability (target)
    if 'target' in df.columns:
        missing_target_mask = df['target'].isna()
        if missing_target_mask.any():
            missing_targets = df[missing_target_mask]
            for idx, row in missing_targets.iterrows():
                exclusion_log.append({
                    "smiles": str(row.get('smiles', 'Unknown')),
                    "reason": "Missing target variable"
                })
            df = df.dropna(subset=['target'])
    else:
        logger.warning("No 'target' column found in dataset")
    
    # Filter out rows with missing SMILES
    if 'smiles' in df.columns:
        missing_smiles_mask = df['smiles'].isna()
        if missing_smiles_mask.any():
            missing_smiles = df[missing_smiles_mask]
            for idx, row in missing_smiles.iterrows():
                exclusion_log.append({
                    "smiles": "Unknown",
                    "reason": "Missing SMILES string"
                })
            df = df.dropna(subset=['smiles'])
    
    valid_count = len(df)
    
    # Log exclusion reasons to file
    exclusion_log_path = output_dir / "exclusion_log.json"
    with open(exclusion_log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Exclusion log written to {exclusion_log_path}")
    
    # Check minimum compound count
    if valid_count < 500:
        error_msg = f"Validation failed: Only {valid_count} unique compounds found. Minimum required: 500"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    validation_report = {
        "total_rows": total_rows,
        "valid_rows": valid_count,
        "excluded_rows": total_rows - valid_count,
        "status": "PASS"
    }
    
    validation_report_path = output_dir / "validation_report.json"
    with open(validation_report_path, 'w') as f:
        json.dump(validation_report, f, indent=2)
    logger.info(f"Validation report written to {validation_report_path}")
    
    return validation_report

def calculate_exclusion_stats(df: pd.DataFrame, output_dir: Path) -> Dict[str, Any]:
    """
    Calculate and log exclusion reasons and exclusion rate statistics.
    Writes to data/processed/exclusion_stats.json.
    
    Args:
        df: The original dataframe before filtering
        output_dir: Directory to write the stats file
    
    Returns:
        Dict with stats: total_rows, excluded_rows, rate
    """
    logger.info("Calculating exclusion statistics...")
    
    # We need to know what was excluded. 
    # Since we are running this after validation/filtering logic (or as part of it),
    # we assume the 'df' passed here is the original raw data, and we compare 
    # against the count of valid rows we intend to keep.
    
    # However, to be precise, let's assume this function is called 
    # *after* the filtering logic in validate_and_filter_dataset,
    # or we re-calculate the exclusions here to be consistent with T014.
    
    total_rows = len(df)
    excluded_rows = 0
    reasons = []
    
    # Recalculate exclusions to get accurate stats for the report
    if 'target' in df.columns:
        missing_target = df['target'].isna().sum()
        excluded_rows += missing_target
        reasons.append({"reason": "Missing target variable", "count": int(missing_target)})
    
    if 'smiles' in df.columns:
        missing_smiles = df['smiles'].isna().sum()
        excluded_rows += missing_smiles
        reasons.append({"reason": "Missing SMILES", "count": int(missing_smiles)})
    
    # Calculate rate
    rate = excluded_rows / total_rows if total_rows > 0 else 0.0
    
    stats = {
        "total_rows": int(total_rows),
        "excluded_rows": int(excluded_rows),
        "rate": float(rate),
        "exclusion_reasons": reasons
    }
    
    stats_path = output_dir / "exclusion_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Exclusion stats written to {stats_path}: {stats}")
    return stats

def main():
    """Main entry point for ingestion pipeline."""
    config = load_config()
    timeout_seconds = config.get('TIMEOUT_GRAPHS', 300)
    
    # Setup output directories
    data_raw_dir = Path("data/raw")
    data_processed_dir = Path("data/processed")
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Setup timeout
    setup_timeout_handler(timeout_seconds)
    
    try:
        # Ingest data
        df_nist = ingest_nist_data()
        df_pubchem = ingest_pubchem_data()
        df_mtr = ingest_mtr_data()
        
        # Save raw data
        if df_nist is not None and not df_nist.empty:
            df_nist.to_parquet(data_raw_dir / "nist.parquet", index=False)
        if df_pubchem is not None and not df_pubchem.empty:
            df_pubchem.to_parquet(data_raw_dir / "pubchem.parquet", index=False)
        if df_mtr is not None and not df_mtr.empty:
            df_mtr.to_parquet(data_raw_dir / "mtr.parquet", index=False)
        
        # Merge sources
        merged_df = merge_sources(df_nist, df_pubchem, df_mtr)
        
        if merged_df.empty:
            logger.error("No data available after merging sources.")
            return
        
        # Calculate exclusion stats BEFORE filtering (to get accurate rates)
        # We pass the merged_df which is the raw combined data
        calculate_exclusion_stats(merged_df, data_processed_dir)
        
        # Validate and filter
        validation_report = validate_and_filter_dataset(merged_df, data_processed_dir)
        
        # Deduplicate
        deduped_df = deduplicate_smiles(merged_df) # Note: Should ideally filter first then dedup
        # Re-order: Filter -> Dedup
        # Let's re-run logic correctly:
        # 1. Filter (done in validate_and_filter_dataset, returns filtered df? No, it returns report)
        # We need to refactor slightly to ensure we save the filtered data.
        
        # Re-implementing flow for correctness:
        # 1. Merge
        # 2. Calculate Stats (T016)
        # 3. Filter & Validate (T014, T012d)
        # 4. Dedup (T012c)
        # 5. Save Merged (T012e)
        
        # Since validate_and_filter_dataset doesn't return the filtered DF, we do it inline here for the save
        filtered_df = merged_df.dropna(subset=['target', 'smiles']) if 'target' in merged_df.columns else merged_df
        
        # Save merged dataset
        filtered_df.to_csv(data_processed_dir / "merged_dataset.csv", index=False)
        logger.info(f"Merged dataset saved to {data_processed_dir / 'merged_dataset.csv'}")
        
        # Deduplicate the filtered data
        final_deduped_df = deduplicate_smiles(filtered_df)
        final_deduped_df.to_csv(data_processed_dir / "deduplicated.csv", index=False)
        logger.info(f"Deduplicated dataset saved to {data_processed_dir / 'deduplicated.csv'}")
        
        logger.info("Ingestion pipeline completed successfully.")
        
    except TimeoutError as e:
        logger.error(str(e))
        sys.exit(1)
    finally:
        cancel_timeout_handler()

if __name__ == "__main__":
    main()
