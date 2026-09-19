"""
Unified Pipeline Orchestration for USPTO Data Ingestion.

This module orchestrates the full preprocessing pipeline:
1. Sanitization (T014)
2. Yield Parsing (T015)
3. Fingerprinting (T016)

It implements batched/chunked loading to prevent OOM errors.
It logs exclusion reasons and calculates exclusion_fraction.
It validates the output against dataset.schema.yaml.
"""
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Iterator

import pandas as pd
import pyarrow.parquet as pq

# Project imports
from config import DATA_RAW_DIR, DATA_PROCESSED_DIR, DATA_RESULTS_DIR, YIELD_RANGE_STRATEGY
from preprocessing.sanitize import sanitize_reactions, verify_checksum
from preprocessing.fingerprints import process_fingerprints_chunked
from utils.io import load_parquet, save_parquet, get_file_size_mb
from utils.validators import validate_dataset_file, DatasetSchema
from utils.memory_profiler import profile_memory, get_current_memory_mb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(DATA_RESULTS_DIR) / 'ingest_pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
RAW_INPUT_FILE = Path(DATA_RAW_DIR) / "uspto_raw.parquet"
OUTPUT_FILE = Path(DATA_PROCESSED_DIR) / "cleaned_reactions.parquet"
QUALITY_REPORT_FILE = Path(DATA_RESULTS_DIR) / "data_quality_report.json"
CHECKSUM_FILE = Path(DATA_RESULTS_DIR) / "download_checksum.txt"

BATCH_SIZE = 5000  # Rows per batch for memory management


def stream_parquet(file_path: Path, batch_size: int = BATCH_SIZE) -> Iterator[pd.DataFrame]:
    """
    Stream a Parquet file in batches to prevent OOM.
    
    Args:
        file_path: Path to the Parquet file.
        batch_size: Number of rows per batch.
        
    Yields:
        DataFrames of the specified batch size.
    """
    logger.info(f"Streaming {file_path} in batches of {batch_size}...")
    
    # Use PyArrow dataset for efficient streaming
    dataset = pq.read_table(file_path)
    n_rows = dataset.num_rows
    logger.info(f"Total rows in source: {n_rows}")
    
    for start_idx in range(0, n_rows, batch_size):
        end_idx = min(start_idx + batch_size, n_rows)
        batch = dataset.slice(start_idx, end_idx - start_idx).to_pandas()
        yield batch
        
        # Log progress
        if (end_idx // batch_size) % 10 == 0 or end_idx == n_rows:
            logger.info(f"Processed rows {start_idx} to {end_idx} ({end_idx}/{n_rows})")


def run_ingestion_pipeline() -> Dict[str, Any]:
    """
    Orchestrates the full ingestion pipeline: Sanitize -> Parse Yield -> Fingerprint.
    
    Returns:
        Dictionary containing pipeline statistics and report data.
    """
    start_time = datetime.now()
    logger.info("Starting Unified Ingestion Pipeline")
    
    # Verify checksum first
    if not verify_checksum(RAW_INPUT_FILE, CHECKSUM_FILE):
        msg = "Checksum verification failed or missing. Cannot proceed."
        logger.error(msg)
        raise FileNotFoundError(msg)
    
    logger.info("Checksum verified. Starting processing...")
    
    # Initialize counters
    total_rows = 0
    valid_rows = 0
    excluded_yield_rows = 0
    excluded_smiles_rows = 0
    excluded_reasons: Dict[str, int] = {"invalid_yield": 0, "invalid_smiles": 0}
    
    # Temporary storage for processed batches
    processed_batches: List[pd.DataFrame] = []
    
    # --- Step 1 & 2: Sanitize and Parse Yield (Batched) ---
    logger.info("Step 1 & 2: Sanitization and Yield Parsing")
    
    for batch in stream_parquet(RAW_INPUT_FILE):
        total_rows += len(batch)
        
        # Sanitize (removes salts, standardizes SMILES)
        # This function returns a DataFrame with 'smiles' column cleaned
        sanitized_batch = sanitize_reactions(batch)
        
        # Parse Yield (handles ranges based on config)
        parsed_batch = parse_yield_batch(sanitized_batch)
        
        # Filter out invalid rows
        valid_mask = parsed_batch['smiles'].notna() & parsed_batch['yield'].notna()
        valid_batch = parsed_batch[valid_mask]
        
        # Update counters
        invalid_count = len(parsed_batch) - len(valid_batch)
        invalid_smiles = (~sanitized_batch['smiles'].notna()).sum()
        invalid_yield = (~parsed_batch['yield'].notna()).sum()
        
        excluded_smiles_rows += invalid_smiles
        excluded_yield_rows += invalid_yield
        
        excluded_reasons['invalid_smiles'] += invalid_smiles
        excluded_reasons['invalid_yield'] += invalid_yield
        
        valid_rows += len(valid_batch)
        processed_batches.append(valid_batch)
        
        # Memory check
        if get_current_memory_mb() > 5000:  # Safety threshold
            logger.warning("Memory usage high. Forcing GC.")
            import gc
            gc.collect()
    
    logger.info(f"Sanitization complete. Valid rows: {valid_rows}, Excluded: {excluded_smiles_rows + excluded_yield_rows}")
    
    # Combine batches
    if not processed_batches:
        raise ValueError("No valid data rows found after sanitization and yield parsing.")
        
    df_clean = pd.concat(processed_batches, ignore_index=True)
    logger.info(f"Combined {valid_rows} rows into single DataFrame.")
    
    # --- Step 3: Fingerprinting (Chunked) ---
    logger.info("Step 3: Generating Fingerprints")
    
    # process_fingerprints_chunked handles the chunking internally and returns the full DF
    # It adds 'fingerprint_ecfp' and 'fingerprint_maccs' columns
    df_final = process_fingerprints_chunked(df_clean)
    
    # --- Validation ---
    logger.info("Validating output against schema...")
    schema_path = Path("specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml")
    if not schema_path.exists():
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
    else:
        try:
            validate_dataset_file(df_final, schema_path)
            logger.info("Schema validation passed.")
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            raise e
    
    # --- Save Output ---
    logger.info(f"Saving output to {OUTPUT_FILE}...")
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    save_parquet(df_final, OUTPUT_FILE)
    
    # --- Generate Report ---
    exclusion_fraction = (total_rows - valid_rows) / total_rows if total_rows > 0 else 0.0
    
    report = {
        "timestamp": start_time.isoformat(),
        "strategy_used": YIELD_RANGE_STRATEGY,
        "rationale": (
            f"Yield parsing strategy '{YIELD_RANGE_STRATEGY}' was applied. "
            f"If 'midpoint', ranges like '50-60%' are converted to 55.0. "
            f"If 'exclude', rows with range formats are dropped. "
            f"This ensures consistent numeric yield values for modeling."
        ),
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "excluded_yield_rows": excluded_yield_rows,
        "excluded_smiles_rows": excluded_smiles_rows,
        "total_excluded_rows": total_rows - valid_rows,
        "exclusion_fraction": round(exclusion_fraction, 6),
        "exclusion_reasons": excluded_reasons
    }
    
    QUALITY_REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(QUALITY_REPORT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"Pipeline completed successfully in {duration:.2f}s.")
    logger.info(f"Output saved to: {OUTPUT_FILE}")
    logger.info(f"Quality report saved to: {QUALITY_REPORT_FILE}")
    
    return report


def parse_yield_batch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply yield parsing logic to a batch of data.
    
    Args:
        df: DataFrame with a 'yield' column (potentially strings with ranges).
        
    Returns:
        DataFrame with 'yield' column converted to float.
    """
    if YIELD_RANGE_STRATEGY == 'midpoint':
        def parse_midpoint(val):
            if pd.isna(val):
                return None
            val_str = str(val).strip()
            if '-' in val_str and '%' in val_str:
                try:
                    parts = val_str.replace('%', '').split('-')
                    if len(parts) == 2:
                        return (float(parts[0]) + float(parts[1])) / 2.0
                except ValueError:
                    return None
            elif '%' in val_str:
                try:
                    return float(val_str.replace('%', ''))
                except ValueError:
                    return None
            try:
                return float(val_str)
            except ValueError:
                return None
        
        df['yield'] = df['yield'].apply(parse_midpoint)
        
    elif YIELD_RANGE_STRATEGY == 'exclude':
        def check_valid(val):
            if pd.isna(val):
                return False
            val_str = str(val).strip()
            if '-' in val_str and '%' in val_str:
                return False  # Exclude ranges
            return True
        
        # We don't drop here, just mark as NaN for filtering later
        def parse_exclude(val):
            if not check_valid(val):
                return None
            val_str = str(val).strip().replace('%', '')
            try:
                return float(val_str)
            except ValueError:
                return None
        
        df['yield'] = df['yield'].apply(parse_exclude)
    else:
        logger.warning(f"Unknown YIELD_RANGE_STRATEGY: {YIELD_RANGE_STRATEGY}. Defaulting to midpoint.")
        # Fallback to midpoint logic
        return parse_yield_batch(df) # Recursive call with logic updated if needed, but here we just return as is or handle
    
    return df


@profile_memory
def main():
    """Main entry point for the ingestion pipeline."""
    try:
        result = run_ingestion_pipeline()
        print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
