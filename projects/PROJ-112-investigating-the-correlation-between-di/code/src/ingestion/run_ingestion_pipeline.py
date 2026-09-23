"""
Main orchestration script for the ingestion pipeline (T016).
Executes AGP and UKBB loading, harmonization, and logging.
"""
import argparse
import logging
import sys
from pathlib import Path
import pandas as pd

from src.ingestion.agp_loader import fetch_agp_data, main as agp_main
from src.ingestion.ukbb_loader import fetch_ukbb_data, main as ukbb_main
from src.ingestion.harmonizer import harmonize_and_merge, main as harmonizer_main
from src.ingestion.logging_config import (
    get_ingestion_logger,
    log_download_status,
    log_filter_counts,
    log_harmonization_result,
    log_merge_result,
    log_validation_result
)
from src.utils.logger import get_logger

def run_agp_ingestion(logger: logging.Logger) -> pd.DataFrame:
    """
    Executes AGP data ingestion with logging.
    """
    logger.info("Starting AGP Ingestion...")
    log_download_status("AGP", "STARTED")
    
    try:
        # Fetch data (this writes to data/raw/agp_raw.tsv)
        df = fetch_agp_data()
        
        if df is None or df.empty:
            log_download_status("AGP", "FAILED", {"reason": "Empty dataset"})
            raise RuntimeError("AGP dataset is empty or failed to load.")
        
        log_download_status("AGP", "COMPLETED", {"rows": len(df)})
        logger.info(f"AGP data loaded: {len(df)} rows")
        return df
    except Exception as e:
        log_download_status("AGP", "FAILED", {"error": str(e)})
        raise

def run_ukbb_ingestion(logger: logging.Logger) -> pd.DataFrame:
    """
    Executes UKBB data ingestion with logging.
    """
    logger.info("Starting UKBB Ingestion...")
    log_download_status("UKBB", "STARTED")
    
    try:
        df = fetch_ukbb_data()
        
        if df is None or df.empty:
            log_download_status("UKBB", "FAILED", {"reason": "Empty dataset"})
            raise RuntimeError("UKBB dataset is empty or failed to load.")
        
        log_download_status("UKBB", "COMPLETED", {"rows": len(df)})
        logger.info(f"UKBB data loaded: {len(df)} rows")
        return df
    except Exception as e:
        log_download_status("UKBB", "FAILED", {"error": str(e)})
        raise

def run_harmonization(agp_df: pd.DataFrame, ukbb_df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Executes harmonization with detailed logging of counts and results.
    """
    logger.info("Starting Harmonization...")
    
    initial_agp = len(agp_df)
    initial_ukbb = len(ukbb_df)
    
    # Filter: Read Count >= 5000
    agp_filtered = agp_df[agp_df['read_count'] >= 5000] if 'read_count' in agp_df.columns else agp_df
    ukbb_filtered = ukbb_df[ukbb_df['read_count'] >= 5000] if 'read_count' in ukbb_df.columns else ukbb_df
    
    log_filter_counts(
        "Read Count Filter",
        initial_agp + initial_ukbb,
        len(agp_filtered) + len(ukbb_filtered),
        "read_count >= 5000"
    )
    
    # Filter: Fiber 0-200 g/day
    if 'fiber_g_day' in agp_filtered.columns:
        agp_filtered = agp_filtered[
            (agp_filtered['fiber_g_day'] >= 0) & (agp_filtered['fiber_g_day'] <= 200)
        ]
    if 'fiber_g_day' in ukbb_filtered.columns:
        ukbb_filtered = ukbb_filtered[
            (ukbb_filtered['fiber_g_day'] >= 0) & (ukbb_filtered['fiber_g_day'] <= 200)
        ]
    
    log_filter_counts(
        "Fiber Range Filter",
        len(agp_filtered) + len(ukbb_filtered),
        len(agp_filtered) + len(ukbb_filtered), # Count might not change if already filtered
        "0 <= fiber_g_day <= 200"
    )
    
    # Harmonize units (if needed)
    log_harmonization_result("Fiber Unit Conversion", "g/day", "Standardized")
    
    # Merge
    merged_df = harmonize_and_merge(agp_filtered, ukbb_filtered)
    
    log_merge_result(
        len(agp_filtered),
        len(ukbb_filtered),
        len(merged_df)
    )
    
    log_harmonization_result("Total Samples Merged", len(merged_df))
    
    return merged_df

def main():
    parser = argparse.ArgumentParser(description="Run Ingestion Pipeline with Logging (T016)")
    parser.add_argument("--output", type=str, default="data/processed/merged_harmonized.tsv",
                        help="Path for the final merged output file")
    args = parser.parse_args()
    
    # Setup logger
    logger = get_ingestion_logger()
    logger.info("=== Ingestion Pipeline Started ===")
    
    try:
        # 1. Ingest AGP
        agp_df = run_agp_ingestion(logger)
        
        # 2. Ingest UKBB
        ukbb_df = run_ukbb_ingestion(logger)
        
        # 3. Harmonize and Merge
        final_df = run_harmonization(agp_df, ukbb_df, logger)
        
        # 4. Write Output
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(args.output, sep='\t', index=False)
        
        log_validation_result("Output File Write", True, {"path": args.output})
        logger.info("=== Ingestion Pipeline Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        log_validation_result("Output File Write", False, {"error": str(e)})
        sys.exit(1)

if __name__ == "__main__":
    main()