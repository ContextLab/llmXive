import os
import sys
import gc
import logging
import tracemalloc
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/cleaning.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants for memory thresholds (from T039/T040 context)
MEMORY_THRESHOLD_CLEANING_GB = 5.0
MEMORY_THRESHOLD_ANALYSIS_GB = 7.0

# Embedded MedDRA to SOC mapping (simplified for implementation, real data would have full mapping)
# In a real scenario, this would be loaded from a file or database
MEDDRA_TO_SOC_MAP = {
    '10000001': 'Blood and lymphatic system disorders',
    '10000002': 'Cardiac disorders',
    '10000003': 'Congenital, familial and genetic disorders',
    '10000004': 'Ear and labyrinth disorders',
    '10000005': 'Endocrine disorders',
    '10000006': 'Eye disorders',
    '10000007': 'Gastrointestinal disorders',
    '10000008': 'General disorders and administration site conditions',
    '10000009': 'Hepatobiliary disorders',
    '10000010': 'Immune system disorders',
    '10000011': 'Infections and infestations',
    '10000012': 'Injury, poisoning and procedural complications',
    '10000013': 'Investigations',
    '10000014': 'Metabolism and nutrition disorders',
    '10000015': 'Musculoskeletal and connective tissue disorders',
    '10000016': 'Neoplasms benign, malignant and unspecified',
    '10000017': 'Nervous system disorders',
    '10000018': 'Pregnancy, puerperium and perinatal conditions',
    '10000019': 'Psychiatric disorders',
    '10000020': 'Renal and urinary disorders',
    '10000021': 'Reproductive system and breast disorders',
    '10000022': 'Respiratory, thoracic and mediastinal disorders',
    '10000023': 'Skin and subcutaneous tissue disorders',
    '10000024': 'Social circumstances',
    '10000025': 'Surgical and medical procedures',
    '10000026': 'Vascular disorders',
}

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    if sys.platform == 'win32':
        # Windows specific memory usage
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)
    else:
        # Unix/Linux/macOS
        import resource
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        return rusage.ru_maxrss / (1024 * 1024)  # Convert KB to GB

def map_soc_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map MedDRA codes to System Organ Classes (SOC).
    
    Args:
        df: DataFrame with 'LLT' or 'SOC_CODE' column containing MedDRA codes
        
    Returns:
        DataFrame with added 'SOC' column
    """
    logger.info("Mapping MedDRA codes to SOC...")
    
    # Try to map from LLT column first, then SOC_CODE
    if 'LLT' in df.columns:
        source_col = 'LLT'
    elif 'SOC_CODE' in df.columns:
        source_col = 'SOC_CODE'
    else:
        logger.warning("No LLT or SOC_CODE column found for SOC mapping")
        df['SOC'] = 'Unknown'
        return df
    
    # Map codes to SOC names
    df['SOC'] = df[source_col].map(MEDDRA_TO_SOC_MAP)
    
    # Fill unknown codes with 'Unknown'
    unknown_count = df['SOC'].isna().sum()
    if unknown_count > 0:
        logger.warning(f"Found {unknown_count} MedDRA codes that could not be mapped to SOC")
        df['SOC'].fillna('Unknown', inplace=True)
    
    return df

def process_data(
    input_path: str,
    output_csv_path: str,
    output_parquet_path: str,
    chunk_size: int = 100000
) -> Dict[str, int]:
    """
    Process VAERS data with memory optimization and logging.
    
    This function:
    1. Reads data in chunks to manage memory
    2. Filters for COVID-19 and Non-COVID groups
    3. Maps MedDRA codes to SOCs
    4. Excludes records with missing critical fields
    5. Logs row counts per group and memory usage stats
    
    Args:
        input_path: Path to input CSV file
        output_csv_path: Path for output CSV file
        output_parquet_path: Path for output Parquet file
        chunk_size: Number of rows to process at a time
        
    Returns:
        Dictionary with row counts per group
    """
    logger.info(f"Starting data processing for {input_path}")
    logger.info(f"Memory threshold for cleaning: {MEMORY_THRESHOLD_CLEANING_GB} GB")
    
    # Initialize memory tracking
    tracemalloc.start()
    initial_memory = get_memory_usage_gb()
    logger.info(f"Initial memory usage: {initial_memory:.2f} GB")
    
    # Initialize counters
    group_counts = {
        'total_input': 0,
        'covid_19': 0,
        'non_covid': 0,
        'non_covid_non_flu': 0,
        'flu_only': 0,
        'excluded_missing_soc': 0,
        'excluded_missing_date': 0,
        'final_cleaned': 0
    }
    
    # Process data in chunks
    chunks = []
    total_processed = 0
    
    for chunk in pd.read_csv(input_path, chunksize=chunk_size):
        total_processed += len(chunk)
        if total_processed % 1000000 == 0:
            current_memory = get_memory_usage_gb()
            logger.info(f"Processed {total_processed:,} rows. Current memory: {current_memory:.2f} GB")
            
            # Check memory usage
            if current_memory > MEMORY_THRESHOLD_CLEANING_GB:
                logger.warning(f"Memory usage ({current_memory:.2f} GB) exceeds threshold ({MEMORY_THRESHOLD_CLEANING_GB} GB)")
                logger.info("Attempting to clear memory...")
                gc.collect()
                current_memory = get_memory_usage_gb()
                logger.info(f"Memory after GC: {current_memory:.2f} GB")
        
        # Filter for COVID-19 vaccine type
        covid_mask = chunk['VAX_TYPE'].str.contains('COVID-19', na=False, case=False)
        non_covid_mask = ~covid_mask
        
        # Further classify Non-COVID group
        flu_mask = non_covid_mask & chunk['VAX_TYPE'].str.contains('Influenza|Flu', na=False, case=False)
        non_covid_non_flu_mask = non_covid_mask & ~flu_mask
        
        # Update group counts
        group_counts['covid_19'] += covid_mask.sum()
        group_counts['non_covid'] += non_covid_mask.sum()
        group_counts['flu_only'] += flu_mask.sum()
        group_counts['non_covid_non_flu'] += non_covid_non_flu_mask.sum()
        
        # Filter out records with missing SOC or REPT_DATE
        has_soc = chunk['SOC_CODE'].notna() | chunk['LLT'].notna()
        has_date = chunk['REPT_DATE'].notna()
        
        valid_mask = has_soc & has_date
        
        excluded_soc = (~has_soc).sum()
        excluded_date = (~has_date).sum()
        
        group_counts['excluded_missing_soc'] += excluded_soc
        group_counts['excluded_missing_date'] += excluded_date
        
        # Keep only valid records
        valid_chunk = chunk[valid_mask].copy()
        
        # Map SOC codes
        valid_chunk = map_soc_codes(valid_chunk)
        
        # Add group labels
        valid_chunk['GROUP'] = 'COVID-19'
        valid_chunk.loc[non_covid_mask[valid_mask], 'GROUP'] = 'Non-COVID'
        valid_chunk.loc[flu_mask[valid_mask], 'GROUP'] = 'Flu-only'
        valid_chunk.loc[non_covid_non_flu_mask[valid_mask], 'GROUP'] = 'Non-COVID, Non-Flu'
        
        chunks.append(valid_chunk)
    
    # Combine all chunks
    logger.info(f"Combining {len(chunks)} chunks...")
    df_cleaned = pd.concat(chunks, ignore_index=True)
    
    # Final memory check
    final_memory = get_memory_usage_gb()
    logger.info(f"Final memory usage after processing: {final_memory:.2f} GB")
    
    # Update final counts
    group_counts['total_input'] = total_processed
    group_counts['final_cleaned'] = len(df_cleaned)
    
    # Log summary statistics
    logger.info("=" * 60)
    logger.info("PROCESSING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total input rows: {group_counts['total_input']:,}")
    logger.info(f"Final cleaned rows: {group_counts['final_cleaned']:,}")
    logger.info(f"Rows excluded (missing SOC): {group_counts['excluded_missing_soc']:,}")
    logger.info(f"Rows excluded (missing date): {group_counts['excluded_missing_date']:,}")
    logger.info(f"COVID-19 group: {group_counts['covid_19']:,}")
    logger.info(f"Non-COVID group: {group_counts['non_covid']:,}")
    logger.info(f"  - Flu-only subset: {group_counts['flu_only']:,}")
    logger.info(f"  - Non-COVID, Non-Flu subset: {group_counts['non_covid_non_flu']:,}")
    logger.info(f"Memory usage: Initial={initial_memory:.2f} GB, Final={final_memory:.2f} GB")
    logger.info("=" * 60)
    
    # Ensure output directories exist
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_parquet_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save outputs
    logger.info(f"Saving cleaned data to {output_csv_path}")
    df_cleaned.to_csv(output_csv_path, index=False)
    
    logger.info(f"Saving cleaned data to {output_parquet_path}")
    df_cleaned.to_parquet(output_parquet_path, index=False)
    
    # Stop memory tracking
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    logger.info(f"Peak memory usage during processing: {peak / (1024**3):.2f} GB")
    
    return group_counts

def main():
    """Main entry point for data cleaning."""
    logger.info("Starting VAERS data cleaning pipeline")
    
    # Define paths
    input_path = "data/raw/VAERSDATA.csv"  # Default, could be parameterized
    output_csv_path = "data/processed/cleaned_vaers.csv"
    output_parquet_path = "data/processed/cleaned_vaers.parquet"
    
    # Check if input file exists
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run download.py first to fetch VAERS data")
        sys.exit(1)
    
    try:
        # Process data
        group_counts = process_data(input_path, output_csv_path, output_parquet_path)
        
        logger.info("Data cleaning completed successfully")
        logger.info(f"Output files saved to:")
        logger.info(f"  - {output_csv_path}")
        logger.info(f"  - {output_parquet_path}")
        
        return group_counts
        
    except Exception as e:
        logger.error(f"Error during data cleaning: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()