import os
import sys
import gc
import logging
import tracemalloc
from pathlib import Path
from typing import Dict, Optional, List
import pandas as pd
import numpy as np

# Import config for paths if needed, though we use relative logic here
# Assuming project root is parent of 'code' or we are running from project root
# The task requires logging to logs/memory.log
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MEDDRA_MAPPING_PATH = PROJECT_ROOT / "data" / "meddra_soc_mapping.csv"

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging():
    """Configure logging to file and console."""
    log_file = LOGS_DIR / "clean.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB using tracemalloc."""
    if not tracemalloc.is_tracing():
        return 0.0
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 ** 3)

def check_memory_usage(limit_gb: float = 5.0) -> bool:
    """Check if current memory usage exceeds limit. Returns True if safe."""
    usage = get_memory_usage_gb()
    if usage > limit_gb:
        logger.error(f"MEMORY_LIMIT_EXCEEDED: {usage:.2f} GB > {limit_gb} GB")
        # Log to specific memory log as per T039/T040 requirements
        mem_log_file = LOGS_DIR / "memory.log"
        with open(mem_log_file, 'a') as f:
            f.write(f"MEMORY_LIMIT_EXCEEDED: {usage:.2f} GB > {limit_gb} GB\n")
        return False
    return True

def load_meddra_mapping() -> pd.DataFrame:
    """Load the MedDRA to SOC mapping table."""
    if not MEDDRA_MAPPING_PATH.exists():
        logger.error(f"MedDRA mapping file not found: {MEDDRA_MAPPING_PATH}")
        raise FileNotFoundError(f"MedDRA mapping file missing: {MEDDRA_MAPPING_PATH}")
    
    logger.info(f"Loading MedDRA mapping from {MEDDRA_MAPPING_PATH}")
    df = pd.read_csv(MEDDRA_MAPPING_PATH)
    # Ensure required columns exist
    required_cols = ['LLT_CODE', 'SOC_CODE']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column '{col}' in MedDRA mapping")
    return df

def map_soc_codes(df: pd.DataFrame, mapping_df: pd.DataFrame) -> pd.DataFrame:
    """Map MedDRA codes in the dataframe to SOC codes."""
    logger.info("Mapping MedDRA codes to SOCs...")
    
    # Create a mapping series
    soc_map = mapping_df.set_index('LLT_CODE')['SOC_CODE']
    
    # Map the LLT column (assuming 'LLT' is the column name in raw data)
    # If the column is named differently, adjust accordingly. 
    # Based on T006 schema, 'LLT' is expected.
    if 'LLT' not in df.columns:
        # Try 'LLT_CODE' if 'LLT' is missing
        if 'LLT_CODE' in df.columns:
            df['SOC'] = df['LLT_CODE'].map(soc_map)
        else:
            logger.warning("No LLT or LLT_CODE column found. Skipping SOC mapping.")
            return df
    else:
        df['SOC'] = df['LLT'].map(soc_map)
    
    logger.info(f"Mapping complete. Unique SOCs found: {df['SOC'].nunique()}")
    return df

def process_chunk(chunk: pd.DataFrame, mapping_df: pd.DataFrame) -> pd.DataFrame:
    """Process a single chunk of data: filter, map, clean."""
    # 1. Filter records with missing SOC or REPT_DATE (will be done after mapping)
    # 2. Map SOC codes
    chunk = map_soc_codes(chunk, mapping_df)
    
    # 3. Filter records with missing SOC or REPT_DATE
    initial_count = len(chunk)
    chunk = chunk.dropna(subset=['SOC', 'REPT_DATE'])
    dropped_count = initial_count - len(chunk)
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} rows due to missing SOC or REPT_DATE in chunk.")
    
    return chunk

def process_data() -> pd.DataFrame:
    """Main processing function: read, filter, map, and aggregate groups."""
    logger.info("Starting data cleaning and processing...")
    
    # Start memory tracing
    tracemalloc.start()
    
    # Load MedDRA Mapping
    try:
        mapping_df = load_meddra_mapping()
    except FileNotFoundError as e:
        logger.critical(str(e))
        raise e

    # Find all raw CSV files
    raw_files = list(DATA_RAW_DIR.glob("*.csv"))
    if not raw_files:
        # Check for zips if download.py didn't extract yet, but T015 assumes raw CSVs exist
        logger.error(f"No CSV files found in {DATA_RAW_DIR}")
        raise FileNotFoundError(f"No raw data found in {DATA_RAW_DIR}")
    
    # Combine all raw files
    logger.info(f"Found {len(raw_files)} raw files to process.")
    
    # We need to process in chunks if memory is a concern, but for simplicity
    # and to ensure we can filter groups correctly across years, we might need
    # to load in chunks and aggregate counts, or load if size permits.
    # Per T015, use chunksize if file size > 5GB or memory check fails.
    
    all_data = []
    estimated_size_gb = 0
    
    for f in raw_files:
        try:
            size = f.stat().st_size / (1024 ** 3)
            estimated_size_gb += size
        except:
            pass

    chunk_size = 100000
    use_chunked = estimated_size_gb > 5.0
    
    if use_chunked:
        logger.info(f"Estimated size {estimated_size_gb:.2f}GB > 5GB. Using chunked processing.")
    else:
        logger.info(f"Estimated size {estimated_size_gb:.2f}GB. Attempting full load.")
        # Check memory before full load
        if not check_memory_usage(5.0):
            logger.error("Memory limit exceeded before full load. Switching to chunked.")
            use_chunked = True

    if use_chunked:
        logger.info("Processing data in chunks...")
        for file_path in raw_files:
            logger.info(f"Reading chunked file: {file_path}")
            reader = pd.read_csv(file_path, chunksize=chunk_size)
            for i, chunk in enumerate(reader):
                if not check_memory_usage(5.0):
                    logger.critical("Memory limit exceeded during chunked processing. Aborting.")
                    raise MemoryError("Memory limit exceeded during chunked processing")
                
                processed_chunk = process_chunk(chunk, mapping_df)
                all_data.append(processed_chunk)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i+1} chunks from {file_path.name}")
    else:
        logger.info("Loading full files...")
        for file_path in raw_files:
            if not check_memory_usage(5.0):
                logger.critical("Memory limit exceeded before loading file. Aborting.")
                raise MemoryError("Memory limit exceeded")
            
            df = pd.read_csv(file_path)
            processed_df = process_chunk(df, mapping_df)
            all_data.append(processed_df)
            del df
            gc.collect()

    # Concatenate all processed chunks
    logger.info("Concatenating processed data...")
    if not all_data:
        raise ValueError("No data was processed. Check input files and filtering logic.")
    
    final_df = pd.concat(all_data, ignore_index=True)
    
    # Define Groups
    # 1. COVID-19 Group: VAX_TYPE contains "COVID-19"
    # 2. Primary Baseline (Non-COVID): VAX_TYPE does NOT contain "COVID-19"
    # 3. Flu-only: Primary Baseline AND VAX_TYPE contains "Influenza"
    # 4. Primary Baseline (Non-COVID, Non-Flu): Primary Baseline AND VAX_TYPE does NOT contain "Influenza"
    
    logger.info("Defining analysis groups...")
    
    # Ensure VAX_TYPE is string
    final_df['VAX_TYPE'] = final_df['VAX_TYPE'].astype(str)
    
    mask_covid = final_df['VAX_TYPE'].str.contains("COVID-19", na=False)
    mask_non_covid = ~mask_covid
    mask_influenza = final_df['VAX_TYPE'].str.contains("Influenza", na=False)
    
    df_covid = final_df[mask_covid].copy()
    df_non_covid = final_df[mask_non_covid].copy()
    df_flu = df_non_covid[mask_influenza].copy()
    df_non_covid_non_flu = df_non_covid[~mask_influenza].copy()
    
    # Log Row Counts per Group
    logger.info("=" * 50)
    logger.info("ROW COUNTS PER GROUP")
    logger.info("=" * 50)
    logger.info(f"Total Cleaned Records: {len(final_df)}")
    logger.info(f"COVID-19 Group: {len(df_covid)}")
    logger.info(f"Primary Baseline (Non-COVID): {len(df_non_covid)}")
    logger.info(f"Flu-only Group: {len(df_flu)}")
    logger.info(f"Primary Baseline (Non-COVID, Non-Flu): {len(df_non_covid_non_flu)}")
    logger.info("=" * 50)
    
    # Memory Stats
    current, peak = tracemalloc.get_traced_memory()
    logger.info(f"Current Memory Usage: {current / 1024**3:.2f} GB")
    logger.info(f"Peak Memory Usage: {peak / 1024**3:.2f} GB")
    
    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Output Artifacts
    output_parquet = DATA_PROCESSED_DIR / "cleaned_vaers.parquet"
    output_csv = DATA_PROCESSED_DIR / "cleaned_vaers.csv"
    
    logger.info(f"Saving cleaned data to {output_parquet} and {output_csv}")
    
    # Save to Parquet
    final_df.to_parquet(output_parquet, index=False)
    
    # Save to CSV
    final_df.to_csv(output_csv, index=False)
    
    logger.info("Data cleaning and processing complete.")
    
    tracemalloc.stop()
    return final_df

def main():
    """Entry point for the cleaning script."""
    try:
        process_data()
        logger.info("Script completed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Script failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()