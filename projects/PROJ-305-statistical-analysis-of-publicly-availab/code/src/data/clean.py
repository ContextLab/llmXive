import os
import sys
import gc
import logging
import tracemalloc
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

# Import config for paths if needed, though we use local logic mostly
# Assuming config exists based on completed tasks
try:
    from src.utils.config import ensure_dirs
except ImportError:
    ensure_dirs = None

# Constants
CHUNK_SIZE = 100000
MEMORY_LIMIT_GB = 5.0  # Threshold for chunked processing as per T039/T015
LOG_PATH = Path("logs")
DATA_PROCESSED_PATH = Path("data/processed")

def setup_logging() -> logging.Logger:
    """Setup logging configuration for the cleaning process."""
    LOG_PATH.mkdir(parents=True, exist_ok=True)
    log_file = LOG_PATH / "cleaning.log"
    
    # Configure root logger to avoid duplicate handlers if run multiple times
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("clean")

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB using tracemalloc."""
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 ** 3)

def check_memory_usage(logger: logging.Logger, limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """
    Check if current memory usage exceeds the limit.
    Returns True if limit exceeded (should halt), False otherwise.
    Logs to logs/memory.log as per T039/T040 requirements.
    """
    current_gb = get_memory_usage_gb()
    memory_log_path = LOG_PATH / "memory.log"
    
    with open(memory_log_path, "a") as f:
        f.write(f"{tracemalloc.get_traced_memory()[0]/(1024**3):.2f} GB current\n")
    
    if current_gb > limit_gb:
        msg = f"MEMORY_LIMIT_EXCEEDED: {current_gb:.2f} GB > {limit_gb} GB"
        logger.error(msg)
        with open(LOG_PATH / "memory.log", "a") as f:
            f.write(f"{msg} - HALTING\n")
        return True
    return False

def load_meddra_mapping(logger: logging.Logger) -> Dict[str, str]:
    """
    Load the MedDRA to SOC mapping from data/meddra_soc_mapping.csv.
    Fails loudly if file is missing.
    """
    mapping_path = Path("data/meddra_soc_mapping.csv")
    if not mapping_path.exists():
        logger.error(f"CRITICAL: MedDRA mapping file not found at {mapping_path}")
        raise FileNotFoundError(f"MedDRA mapping file missing: {mapping_path}")
    
    logger.info(f"Loading MedDRA mapping from {mapping_path}")
    df_map = pd.read_csv(mapping_path)
    # Assume columns: 'LLT_CODE' or 'SOC_CODE' and 'SOC_NAME'
    # We need to map whatever code column exists to SOC.
    # Based on T006, we expect SOC_CODE or LLT.
    # Let's assume the file has 'CODE' and 'SOC' columns for simplicity, 
    # or handle standard MedDRA CSV structure if known.
    # Since spec says "strictly using a mapping table", we load it.
    if 'SOC_CODE' in df_map.columns and 'SOC' in df_map.columns:
        mapping = df_map.set_index('SOC_CODE')['SOC'].to_dict()
    elif 'CODE' in df_map.columns and 'SOC' in df_map.columns:
        mapping = df_map.set_index('CODE')['SOC'].to_dict()
    else:
        # Fallback to first two columns if names are unknown but structure is simple
        mapping = dict(zip(df_map.iloc[:, 0], df_map.iloc[:, 1]))
    
    logger.info(f"Loaded {len(mapping)} mapping entries")
    return mapping

def map_soc_codes(df: pd.DataFrame, mapping: Dict[str, str], logger: logging.Logger) -> pd.DataFrame:
    """Map MedDRA codes to SOC names using the provided mapping."""
    # Identify the code column. T006 mentions SOC_CODE or LLT.
    code_col = None
    if 'SOC_CODE' in df.columns:
        code_col = 'SOC_CODE'
    elif 'LLT' in df.columns:
        code_col = 'LLT'
    elif 'CODE' in df.columns:
        code_col = 'CODE'
    
    if code_col is None:
        logger.warning("No standard code column found (SOC_CODE, LLT, CODE). Skipping SOC mapping.")
        return df
    
    logger.info(f"Mapping {code_col} to SOC using mapping table")
    df['SOC'] = df[code_col].map(mapping)
    
    # Count unmapped
    unmapped = df['SOC'].isna().sum()
    if unmapped > 0:
        logger.warning(f"Found {unmapped} records with unmapped codes. These will be excluded later if SOC is required.")
    
    return df

def process_chunk(chunk: pd.DataFrame, mapping: Dict[str, str], logger: logging.Logger) -> pd.DataFrame:
    """Process a single chunk of data."""
    # Filter by VAX_TYPE
    # COVID-19 Group
    covid_mask = chunk['VAX_TYPE'].str.contains("COVID-19", na=False)
    # Non-COVID Group (Primary Baseline)
    non_covid_mask = ~covid_mask
    
    # Subsets for baseline
    flu_mask = non_covid_mask & chunk['VAX_TYPE'].str.contains("Influenza", na=False)
    non_flu_mask = non_covid_mask & ~chunk['VAX_TYPE'].str.contains("Influenza", na=False)
    
    # Apply filters
    chunk['GROUP'] = 'Unknown'
    chunk.loc[covid_mask, 'GROUP'] = 'COVID-19'
    chunk.loc[flu_mask, 'GROUP'] = 'Flu-only'
    chunk.loc[non_flu_mask, 'GROUP'] = 'Non-COVID-Non-Flu'
    
    # Map SOC
    chunk = map_soc_codes(chunk, mapping, logger)
    
    # Filter: Exclude records with missing SOC or REPT_DATE
    chunk = chunk.dropna(subset=['SOC', 'REPT_DATE'])
    
    # Additional validation: Ensure VAX_TYPE is not empty
    chunk = chunk[chunk['VAX_TYPE'].notna()]
    
    return chunk

def process_data(logger: logging.Logger) -> pd.DataFrame:
    """
    Main data processing function.
    Reads raw VAERS data in chunks, processes, and aggregates.
    Implements memory optimization and logging of row counts per group.
    """
    raw_dir = Path("data/raw")
    output_dir = DATA_PROCESSED_PATH
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get list of raw CSV files
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        logger.error("No CSV files found in data/raw/")
        raise FileNotFoundError("No raw data files found.")
    
    logger.info(f"Found {len(csv_files)} raw files to process")
    
    # Load mapping
    mapping = load_meddra_mapping(logger)
    
    # Determine if we need chunking based on file size estimate
    total_size_gb = sum(f.stat().st_size for f in csv_files) / (1024 ** 3)
    use_chunking = total_size_gb > 5.0 or check_memory_usage(logger)
    
    if use_chunking:
        logger.info("Using chunked processing due to large data size or memory pressure")
    else:
        logger.info("Processing data in memory (size < 5GB and memory OK)")
    
    all_chunks = []
    total_rows = 0
    
    for file_path in csv_files:
        logger.info(f"Processing {file_path.name}")
        
        if use_chunking:
            for chunk in pd.read_csv(file_path, chunksize=CHUNK_SIZE):
                if check_memory_usage(logger):
                    # Force garbage collection before halting
                    gc.collect()
                    raise MemoryError("Memory limit exceeded during chunk processing")
                
                processed_chunk = process_chunk(chunk, mapping, logger)
                all_chunks.append(processed_chunk)
                total_rows += len(processed_chunk)
        else:
            df = pd.read_csv(file_path)
            if check_memory_usage(logger):
                gc.collect()
                raise MemoryError("Memory limit exceeded during file loading")
            
            processed_df = process_chunk(df, mapping, logger)
            all_chunks.append(processed_df)
            total_rows += len(processed_df)
        
        # Periodic memory check and cleanup
        if len(all_chunks) % 10 == 0:
            current_mem = get_memory_usage_gb()
            logger.info(f"Processed {len(all_chunks)} chunks. Current memory: {current_mem:.2f} GB")
            if check_memory_usage(logger):
                gc.collect()
                raise MemoryError("Memory limit exceeded")
    
    if not all_chunks:
        logger.error("No data processed. Check filters.")
        raise ValueError("No data processed.")
    
    # Concatenate all chunks
    logger.info(f"Concatenating {len(all_chunks)} chunks...")
    final_df = pd.concat(all_chunks, ignore_index=True)
    
    # Force cleanup
    del all_chunks
    gc.collect()
    
    # Final Memory Check
    final_mem = get_memory_usage_gb()
    logger.info(f"Final memory usage after concat: {final_mem:.2f} GB")
    
    # LOGGING: Report row counts per group
    logger.info("=" * 40)
    logger.info("DATA PROCESSING SUMMARY")
    logger.info("=" * 40)
    group_counts = final_df['GROUP'].value_counts()
    for group, count in group_counts.items():
        logger.info(f"Group '{group}': {count:,} rows")
    logger.info(f"Total valid rows: {len(final_df):,}")
    logger.info("=" * 40)
    
    # Save outputs
    parquet_path = output_dir / "cleaned_vaers.parquet"
    csv_path = output_dir / "cleaned_vaers.csv"
    
    logger.info(f"Saving to {parquet_path}")
    final_df.to_parquet(parquet_path, index=False)
    
    logger.info(f"Saving to {csv_path}")
    final_df.to_csv(csv_path, index=False)
    
    return final_df

def main():
    """Entry point for the cleaning script."""
    logger = setup_logging()
    logger.info("Starting data cleaning pipeline (T015 + T018)")
    
    # Start memory tracing
    tracemalloc.start()
    
    try:
        result = process_data(logger)
        logger.info("Data cleaning completed successfully.")
    except Exception as e:
        logger.error(f"Data cleaning failed: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        tracemalloc.stop()

if __name__ == "__main__":
    main()