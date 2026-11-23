import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

import pandas as pd

# Import logging utilities from the project's existing logging module
from src.utils.logging import get_logger, log_info, log_warning, log_error, log_success

# Define expected columns based on the pipeline requirements
EXPECTED_COLUMNS = {'material_id', 'source', 'C11', 'C12', 'C44'}

def load_ingest_results(mp_path: Optional[Path], aflow_path: Optional[Path]) -> pd.DataFrame:
    """
    Load and merge ingestion results from Materials Project and AFLOW.
    
    Args:
        mp_path: Path to the Materials Project ingestion CSV
        aflow_path: Path to the AFLOW ingestion CSV
        
    Returns:
        Merged DataFrame with all valid entries
        
    Raises:
        FileNotFoundError: If specified input files do not exist
        ValueError: If required columns are missing
    """
    dfs = []
    sources_loaded = []
    
    if mp_path and mp_path.exists():
        log_info(f"Loading MP results from {mp_path}")
        try:
            df_mp = pd.read_csv(mp_path)
            if not EXPECTED_COLUMNS.issubset(df_mp.columns):
                missing = EXPECTED_COLUMNS - set(df_mp.columns)
                log_warning(f"MP file missing columns: {missing}. Attempting to proceed with available columns.")
            df_mp['source'] = 'MP'
            dfs.append(df_mp)
            sources_loaded.append('MP')
        except Exception as e:
            log_error(f"Failed to load MP file: {e}")
            raise
    elif mp_path:
        log_warning(f"MP file not found at {mp_path}, skipping MP source")
        
    if aflow_path and aflow_path.exists():
        log_info(f"Loading AFLOW results from {aflow_path}")
        try:
            df_aflow = pd.read_csv(aflow_path)
            if not EXPECTED_COLUMNS.issubset(df_aflow.columns):
                missing = EXPECTED_COLUMNS - set(df_aflow.columns)
                log_warning(f"AFLOW file missing columns: {missing}. Attempting to proceed with available columns.")
            df_aflow['source'] = 'AFLOW'
            dfs.append(df_aflow)
            sources_loaded.append('AFLOW')
        except Exception as e:
            log_error(f"Failed to load AFLOW file: {e}")
            raise
    elif aflow_path:
        log_warning(f"AFLOW file not found at {aflow_path}, skipping AFLOW source")
        
    if not dfs:
        log_error("No data sources were successfully loaded.")
        raise ValueError("No valid data sources found to merge.")
        
    merged_df = pd.concat(dfs, ignore_index=True)
    log_success(f"Merged {len(merged_df)} entries from sources: {sources_loaded}")
    return merged_df

def verify_entry_count(df: pd.DataFrame, min_entries: int = 1) -> bool:
    """
    Verify that the merged dataset contains at least the minimum required entries.
    
    Args:
        df: The merged DataFrame
        min_entries: Minimum number of entries required
        
    Returns:
        True if count meets threshold, False otherwise
    """
    count = len(df)
    if count < min_entries:
        log_error(f"Entry count {count} is below minimum threshold {min_entries}")
        return False
    log_info(f"Entry count verification passed: {count} >= {min_entries}")
    return True

def validate_ingest(input_mp: Optional[str] = None, 
                    input_aflow: Optional[str] = None, 
                    output_path: Optional[str] = None,
                    min_entries: int = 1) -> Tuple[bool, pd.DataFrame]:
    """
    Main validation function to merge, validate, and optionally save ingestion results.
    
    This function implements the core requirement to merge MP/AFLOW results,
    validate data integrity, and log skipped IDs (if any validation logic is added later).
    
    Args:
        input_mp: Path to MP ingestion CSV
        input_aflow: Path to AFLOW ingestion CSV
        output_path: Optional path to save the merged CSV
        min_entries: Minimum number of entries required to pass validation
        
    Returns:
        Tuple of (is_valid, merged_dataframe)
    """
    log_info("Starting ingestion validation and merge process")
    
    # Convert string paths to Path objects
    mp_path = Path(input_mp) if input_mp else None
    aflow_path = Path(input_aflow) if input_aflow else None
    
    # Load and merge data
    merged_df = load_ingest_results(mp_path, aflow_path)
    
    # Verify entry count
    is_valid = verify_entry_count(merged_df, min_entries)
    
    # Log basic statistics
    log_info(f"Total entries after merge: {len(merged_df)}")
    if 'source' in merged_df.columns:
        source_counts = merged_df['source'].value_counts().to_dict()
        log_info(f"Entries by source: {source_counts}")
    
    # Check for duplicate material IDs across sources
    if 'material_id' in merged_df.columns:
        duplicates = merged_df[merged_df.duplicated(subset=['material_id'], keep=False)]
        if not duplicates.empty:
            log_warning(f"Found {len(duplicates)} entries with duplicate material IDs across sources")
            # Log the duplicate IDs
            dup_ids = duplicates['material_id'].unique().tolist()
            log_info(f"Duplicate material IDs: {dup_ids[:10]}...") # Log first 10
        
    # Save output if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        merged_df.to_csv(output_file, index=False)
        log_success(f"Merged data saved to {output_file}")
        
    return is_valid, merged_df

def main():
    """CLI entry point for the validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate and merge elastic constant ingestion results")
    parser.add_argument("--mp-input", type=str, help="Path to MP ingestion CSV")
    parser.add_argument("--aflow-input", type=str, help="Path to AFLOW ingestion CSV")
    parser.add_argument("--output", type=str, help="Path to save merged CSV")
    parser.add_argument("--min-entries", type=int, default=1, help="Minimum required entries")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger("validate_ingest")
    
    try:
        is_valid, df = validate_ingest(
            input_mp=args.mp_input,
            input_aflow=args.aflow_input,
            output_path=args.output,
            min_entries=args.min_entries
        )
        
        if not is_valid:
            log_error("Validation failed due to insufficient entries")
            sys.exit(1)
            
        log_success("Ingestion validation completed successfully")
        sys.exit(0)
        
    except Exception as e:
        log_error(f"Validation process failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
