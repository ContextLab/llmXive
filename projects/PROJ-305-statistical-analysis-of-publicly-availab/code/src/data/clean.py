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
        logging.FileHandler('data/processing.log')
    ]
)
logger = logging.getLogger(__name__)

# Embedded MedDRA to SOC mapping (simplified for demonstration)
# In a real implementation, this would be a comprehensive mapping table
MEDDRA_TO_SOC = {
    '10000000': 'Blood and lymphatic system disorders',
    '10001000': 'Cardiac disorders',
    '10002000': 'Congenital, familial and genetic disorders',
    '10003000': 'Ear and labyrinth disorders',
    '10004000': 'Endocrine disorders',
    '10005000': 'Eye disorders',
    '10006000': 'Gastrointestinal disorders',
    '10007000': 'General disorders and administration site conditions',
    '10008000': 'Hepatobiliary disorders',
    '10009000': 'Immune system disorders',
    '10010000': 'Infections and infestations',
    '10011000': 'Injury, poisoning and procedural complications',
    '10012000': 'Investigations',
    '10013000': 'Metabolism and nutrition disorders',
    '10014000': 'Musculoskeletal and connective tissue disorders',
    '10015000': 'Neoplasms benign, malignant and unspecified',
    '10016000': 'Nervous system disorders',
    '10017000': 'Pregnancy, puerperium and perinatal conditions',
    '10018000': 'Psychiatric disorders',
    '10019000': 'Renal and urinary disorders',
    '10020000': 'Reproductive system and breast disorders',
    '10021000': 'Respiratory, thoracic and mediastinal disorders',
    '10022000': 'Skin and subcutaneous tissue disorders',
    '10023000': 'Social circumstances',
    '10024000': 'Surgical and medical procedures',
    '10025000': 'Vascular disorders',
}

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    if sys.platform == 'win32':
        # Windows: use psutil if available, else estimate
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 ** 3)
        except ImportError:
            return 0.0
    else:
        # Unix-like: use tracemalloc or /proc
        try:
            with open('/proc/self/status', 'r') as f:
                for line in f:
                    if line.startswith('VmRSS:'):
                        # VmRSS is in kB
                        rss_kb = int(line.split()[1])
                        return rss_kb / (1024 ** 2)
        except Exception:
            pass
        return 0.0

def map_soc_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Map MedDRA codes to System Organ Classes (SOC)."""
    logger.info("Mapping MedDRA codes to SOC...")
    
    # Create a copy to avoid SettingWithCopyWarning
    df_mapped = df.copy()
    
    # Map SOC codes using the embedded dictionary
    df_mapped['SOC'] = df_mapped['SOC_CODE'].map(MEDDRA_TO_SOC)
    
    # Log mapping statistics
    total_rows = len(df_mapped)
    mapped_rows = df_mapped['SOC'].notna().sum()
    unmapped_rows = total_rows - mapped_rows
    
    logger.info(f"Mapping complete: {mapped_rows}/{total_rows} rows mapped ({mapped_rows/total_rows:.2%})")
    if unmapped_rows > 0:
        logger.warning(f"{unmapped_rows} rows have unmapped SOC codes")
    
    return df_mapped

def process_data(
    input_path: str,
    output_csv_path: str,
    output_parquet_path: str,
    chunk_size: int = 100000
) -> Dict[str, int]:
    """
    Process VAERS data with memory optimization and logging.
    
    Args:
        input_path: Path to raw VAERS data
        output_csv_path: Path for cleaned CSV output
        output_parquet_path: Path for cleaned Parquet output
        chunk_size: Number of rows to process at a time
        
    Returns:
        Dictionary with row counts per group
    """
    logger.info(f"Starting data processing for {input_path}")
    logger.info(f"Input file size: {os.path.getsize(input_path) / (1024**2):.2f} MB")
    
    # Start memory tracking
    tracemalloc.start()
    initial_memory = get_memory_usage_gb()
    logger.info(f"Initial memory usage: {initial_memory:.2f} GB")
    
    # Initialize counters
    group_counts = {
        'COVID-19': 0,
        'Non-COVID': 0,
        'Non-COVID, Non-Flu': 0,
        'Flu-only': 0,
        'Total': 0,
        'Excluded (missing SOC or REPT_DATE)': 0
    }
    
    # Process in chunks to manage memory
    chunks = []
    processed_rows = 0
    
    for chunk in pd.read_csv(input_path, chunksize=chunk_size):
        processed_rows += len(chunk)
        logger.debug(f"Processed chunk: {processed_rows} rows")
        
        # Filter for required columns
        required_cols = ['VAX_TYPE', 'SOC_CODE', 'REPT_DATE', 'AGE']
        available_cols = [col for col in required_cols if col in chunk.columns]
        if len(available_cols) < len(required_cols):
            logger.warning(f"Missing columns in chunk: {set(required_cols) - set(available_cols)}")
            continue
        
        # Filter out rows with missing SOC_CODE or REPT_DATE
        valid_chunk = chunk.dropna(subset=['SOC_CODE', 'REPT_DATE'])
        excluded_count = len(chunk) - len(valid_chunk)
        group_counts['Excluded (missing SOC or REPT_DATE)'] += excluded_count
        
        # Map SOC codes
        valid_chunk = map_soc_codes(valid_chunk)
        
        # Remove rows where SOC mapping failed
        valid_chunk = valid_chunk.dropna(subset=['SOC'])
        
        # Classify vaccine types
        # COVID-19 group
        covid_mask = valid_chunk['VAX_TYPE'].str.contains('COVID-19', case=False, na=False)
        covid_count = covid_mask.sum()
        group_counts['COVID-19'] += covid_count
        
        # Non-COVID group (all other vaccines)
        non_covid_mask = ~covid_mask
        non_covid_count = non_covid_mask.sum()
        group_counts['Non-COVID'] += non_covid_count
        
        # Non-COVID, Non-Flu group (subset of Non-COVID)
        non_flu_mask = ~valid_chunk.loc[non_covid_mask, 'VAX_TYPE'].str.contains('Influenza', case=False, na=False)
        non_covid_non_flu_count = non_flu_mask.sum()
        group_counts['Non-COVID, Non-Flu'] += non_covid_non_flu_count
        
        # Flu-only group
        flu_mask = valid_chunk['VAX_TYPE'].str.contains('Influenza', case=False, na=False)
        flu_count = flu_mask.sum()
        group_counts['Flu-only'] += flu_count
        
        # Store processed chunk
        chunks.append(valid_chunk)
        
        # Periodic memory check
        if processed_rows % (chunk_size * 10) == 0:
            current_memory = get_memory_usage_gb()
            logger.info(f"Memory usage at {processed_rows} rows: {current_memory:.2f} GB")
            if current_memory > 7.0:
                logger.error("Memory usage exceeded 7 GB limit!")
                gc.collect()
                tracemalloc.clear_traces()
                raise MemoryError("Memory usage exceeded 7 GB limit")
    
    # Combine all chunks
    logger.info(f"Combining {len(chunks)} chunks...")
    if chunks:
        final_df = pd.concat(chunks, ignore_index=True)
    else:
        logger.warning("No valid data chunks found!")
        final_df = pd.DataFrame(columns=['VAX_TYPE', 'SOC_CODE', 'REPT_DATE', 'AGE', 'SOC'])
    
    group_counts['Total'] = len(final_df)
    
    # Final memory stats
    current_memory = get_memory_usage_gb()
    current_snapshot = tracemalloc.take_snapshot()
    top_stats = current_snapshot.statistics('lineno')
    
    logger.info("=" * 50)
    logger.info("PROCESSING COMPLETE - MEMORY AND ROW COUNT STATISTICS")
    logger.info("=" * 50)
    logger.info(f"Final memory usage: {current_memory:.2f} GB")
    logger.info(f"Memory increase: {current_memory - initial_memory:.2f} GB")
    logger.info(f"Total rows processed: {processed_rows}")
    logger.info(f"Final dataset size: {len(final_df)} rows")
    logger.info(f"Excluded rows: {group_counts['Excluded (missing SOC or REPT_DATE)']}")
    logger.info("-" * 50)
    logger.info("ROW COUNTS PER GROUP:")
    logger.info(f"  COVID-19: {group_counts['COVID-19']}")
    logger.info(f"  Non-COVID: {group_counts['Non-COVID']}")
    logger.info(f"  Non-COVID, Non-Flu: {group_counts['Non-COVID, Non-Flu']}")
    logger.info(f"  Flu-only: {group_counts['Flu-only']}")
    logger.info(f"  Total: {group_counts['Total']}")
    logger.info("=" * 50)
    
    # Log top memory consumers
    if top_stats:
        logger.info("Top 5 memory consumers:")
        for stat in top_stats[:5]:
            logger.info(f"  {stat}")
    
    # Stop memory tracking
    tracemalloc.stop()
    
    # Save outputs
    logger.info(f"Saving cleaned data to {output_csv_path}")
    final_df.to_csv(output_csv_path, index=False)
    
    logger.info(f"Saving cleaned data to {output_parquet_path}")
    final_df.to_parquet(output_parquet_path, index=False)
    
    logger.info("Data processing completed successfully")
    
    return group_counts

def main():
    """Main entry point for data cleaning pipeline."""
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    input_path = base_dir / "data" / "raw" / "vaers_2020_2023.csv"
    output_csv_path = base_dir / "data" / "processed" / "cleaned_vaers.csv"
    output_parquet_path = base_dir / "data" / "processed" / "cleaned_vaers.parquet"
    
    # Ensure output directory exists
    output_dir = output_csv_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if input file exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Run processing
    try:
        group_counts = process_data(
            input_path=str(input_path),
            output_csv_path=str(output_csv_path),
            output_parquet_path=str(output_parquet_path)
        )
        logger.info("Pipeline completed successfully")
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()