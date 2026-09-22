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
        logging.FileHandler('logs/clean.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Embedded MedDRA to SOC mapping (subset of common codes for demonstration)
# In a production environment, this would be loaded from a full MedDRA dictionary file
SOC_MAPPING = {
    # Cardiac disorders
    '10007541': 'Cardiac disorders',
    # Gastrointestinal disorders
    '10017947': 'Gastrointestinal disorders',
    # General disorders and administration site conditions
    '10018065': 'General disorders and administration site conditions',
    # Immune system disorders
    '10021459': 'Immune system disorders',
    # Infections and infestations
    '10021881': 'Infections and infestations',
    # Injury, poisoning and procedural complications
    '10022423': 'Injury, poisoning and procedural complications',
    # Investigations
    '10022449': 'Investigations',
    # Metabolism and nutrition disorders
    '10027433': 'Metabolism and nutrition disorders',
    # Musculoskeletal and connective tissue disorders
    '10028395': 'Musculoskeletal and connective tissue disorders',
    # Neoplasms benign, malignant and unspecified
    '10029104': 'Neoplasms benign, malignant and unspecified',
    # Nervous system disorders
    '10029285': 'Nervous system disorders',
    # Pregnancy, puerperium and perinatal conditions
    '10036169': 'Pregnancy, puerperium and perinatal conditions',
    # Psychiatric disorders
    '10037175': 'Psychiatric disorders',
    # Renal and urinary disorders
    '10037777': 'Renal and urinary disorders',
    # Reproductive system and breast disorders
    '10038738': 'Reproductive system and breast disorders',
    # Respiratory, thoracic and mediastinal disorders
    '10038738': 'Respiratory, thoracic and mediastinal disorders',
    # Skin and subcutaneous tissue disorders
    '10040785': 'Skin and subcutaneous tissue disorders',
    # Vascular disorders
    '10047065': 'Vascular disorders',
}

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    if sys.platform == 'win32':
        # Windows implementation
        import psutil
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 ** 3)
    else:
        # Unix/Linux implementation
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on macOS
        if sys.platform == 'darwin':
            return usage.ru_maxrss / (1024 ** 3)
        else:
            return usage.ru_maxrss / (1024 ** 2)

def check_memory_usage(threshold_gb: float = 7.0) -> bool:
    """Check if memory usage exceeds threshold. Returns True if safe."""
    current_usage = get_memory_usage_gb()
    logger.info(f"Current memory usage: {current_usage:.2f} GB (Threshold: {threshold_gb} GB)")
    if current_usage > threshold_gb:
        logger.warning(f"Memory usage ({current_usage:.2f} GB) exceeds threshold ({threshold_gb} GB)")
        return False
    return True

def map_soc_codes(df: pd.DataFrame) -> pd.DataFrame:
    """Map MedDRA codes to System Organ Classes (SOC)."""
    logger.info("Mapping MedDRA codes to SOC...")
    
    # Create a mapping series
    def map_code(code):
        if pd.isna(code):
            return None
        code_str = str(code)
        # Try direct mapping first
        if code_str in SOC_MAPPING:
            return SOC_MAPPING[code_str]
        # Try partial match for codes that might be formatted differently
        for meddra_code, soc_name in SOC_MAPPING.items():
            if meddra_code in code_str:
                return soc_name
        return None

    df['SOC'] = df['SOC_CODE'].apply(map_code)
    
    # Log mapping statistics
    total_codes = len(df)
    mapped_codes = df['SOC'].notna().sum()
    unmapped_codes = total_codes - mapped_codes
    
    logger.info(f"MedDRA to SOC mapping: {mapped_codes}/{total_codes} ({100*mapped_codes/total_codes:.1f}%) mapped")
    if unmapped_codes > 0:
        logger.warning(f"{unmapped_codes} records could not be mapped to SOC")
    
    return df

def process_data(input_path: str, output_csv_path: str, output_parquet_path: str) -> Dict[str, Any]:
    """
    Process VAERS data: filter, clean, map SOC, and save.
    
    Args:
        input_path: Path to raw VAERS data (CSV or Parquet)
        output_csv_path: Path to save cleaned CSV
        output_parquet_path: Path to save cleaned Parquet
    
    Returns:
        Dictionary with processing statistics
    """
    logger.info(f"Starting data processing from {input_path}")
    tracemalloc.start()
    
    # Start memory tracking
    start_mem = get_memory_usage_gb()
    logger.info(f"Initial memory usage: {start_mem:.2f} GB")
    
    # Read data in chunks if file is large
    chunk_size = 100000
    chunks = []
    total_rows = 0
    processed_rows = 0
    
    logger.info("Reading and processing data in chunks...")
    
    # Determine file type and read accordingly
    if input_path.endswith('.parquet'):
        df = pd.read_parquet(input_path)
        total_rows = len(df)
        chunks = [df]
    elif input_path.endswith('.csv'):
        # Read in chunks for large CSV files
        for chunk in pd.read_csv(input_path, chunksize=chunk_size):
            total_rows += len(chunk)
            chunks.append(chunk)
    else:
        raise ValueError(f"Unsupported file format: {input_path}")
    
    logger.info(f"Total rows to process: {total_rows:,}")
    
    # Process each chunk
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk):,} rows)")
        
        # Check memory before processing chunk
        if not check_memory_usage(threshold_gb=5.0):
            logger.error("Memory threshold exceeded during chunk processing")
            raise MemoryError("Memory usage exceeded threshold during chunk processing")
        
        # Filter for COVID-19 and Non-COVID vaccines
        # Create a copy to avoid SettingWithCopyWarning
        chunk = chunk.copy()
        
        # Filter records where VAX_TYPE contains "COVID-19"
        covid_mask = chunk['VAX_TYPE'].str.contains('COVID-19', na=False, case=True)
        non_covid_mask = ~covid_mask
        
        # Further filter Non-COVID to exclude Influenza for sensitivity analysis
        flu_mask = chunk['VAX_TYPE'].str.contains('Influenza|Flu', na=False, case=True, flags=re.IGNORECASE)
        
        # Create group labels
        chunk['VAX_GROUP'] = pd.Series(
            index=chunk.index,
            data=['COVID-19' if covid_mask.iloc[i] else 
                  ('Non-COVID-Non-Flu' if non_covid_mask.iloc[i] and not flu_mask.iloc[i] else 
                   ('Flu-only' if non_covid_mask.iloc[i] and flu_mask.iloc[i] else 'Other'))
                  for i in range(len(chunk))]
        )
        
        # Filter out records with missing critical fields
        chunk = chunk.dropna(subset=['SOC_CODE', 'REPT_DATE'])
        
        # Map SOC codes
        chunk = map_soc_codes(chunk)
        
        # Filter out records where SOC mapping failed
        chunk = chunk.dropna(subset=['SOC'])
        
        # Log chunk statistics
        chunk_stats = {
            'total': len(chunk),
            'COVID-19': (chunk['VAX_GROUP'] == 'COVID-19').sum(),
            'Non-COVID-Non-Flu': (chunk['VAX_GROUP'] == 'Non-COVID-Non-Flu').sum(),
            'Flu-only': (chunk['VAX_GROUP'] == 'Flu-only').sum(),
            'Other': (chunk['VAX_GROUP'] == 'Other').sum()
        }
        logger.info(f"Chunk {i+1} stats: {chunk_stats}")
        
        processed_chunks.append(chunk)
        processed_rows += len(chunk)
        
        # Force garbage collection every 5 chunks
        if i % 5 == 0:
            gc.collect()
            current_mem = get_memory_usage_gb()
            logger.info(f"Memory after chunk {i+1}: {current_mem:.2f} GB")
    
    # Combine all processed chunks
    logger.info(f"Combining {len(processed_chunks)} processed chunks...")
    combined_df = pd.concat(processed_chunks, ignore_index=True)
    
    # Final filtering and cleanup
    combined_df = combined_df[combined_df['VAX_GROUP'].isin(['COVID-19', 'Non-COVID-Non-Flu', 'Flu-only'])]
    
    # Final memory check
    final_mem = get_memory_usage_gb()
    logger.info(f"Final memory usage: {final_mem:.2f} GB")
    
    # Calculate final statistics
    final_stats = {
        'total_processed_rows': processed_rows,
        'final_row_count': len(combined_df),
        'COVID-19': (combined_df['VAX_GROUP'] == 'COVID-19').sum(),
        'Non-COVID-Non-Flu': (combined_df['VAX_GROUP'] == 'Non-COVID-Non-Flu').sum(),
        'Flu-only': (combined_df['VAX_GROUP'] == 'Flu-only').sum(),
        'memory_start_gb': start_mem,
        'memory_end_gb': final_mem,
        'memory_peak_gb': tracemalloc.get_traced_memory()[1] / (1024 ** 3)
    }
    
    # Log final statistics
    logger.info("=" * 50)
    logger.info("FINAL PROCESSING STATISTICS")
    logger.info("=" * 50)
    logger.info(f"Total rows processed: {final_stats['total_processed_rows']:,}")
    logger.info(f"Final row count: {final_stats['final_row_count']:,}")
    logger.info(f"  COVID-19 group: {final_stats['COVID-19']:,}")
    logger.info(f"  Non-COVID-Non-Flu group: {final_stats['Non-COVID-Non-Flu']:,}")
    logger.info(f"  Flu-only group: {final_stats['Flu-only']:,}")
    logger.info(f"Memory start: {final_stats['memory_start_gb']:.2f} GB")
    logger.info(f"Memory end: {final_stats['memory_end_gb']:.2f} GB")
    logger.info(f"Memory peak: {final_stats['memory_peak_gb']:.2f} GB")
    logger.info("=" * 50)
    
    # Save outputs
    logger.info(f"Saving cleaned data to {output_csv_path}")
    combined_df.to_csv(output_csv_path, index=False)
    
    logger.info(f"Saving cleaned data to {output_parquet_path}")
    combined_df.to_parquet(output_parquet_path, index=False)
    
    tracemalloc.stop()
    
    return final_stats

def main():
    """Main entry point for data cleaning."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clean and process VAERS data')
    parser.add_argument('--input', required=True, help='Path to input VAERS data')
    parser.add_argument('--output-csv', default='data/processed/cleaned_vaers.csv', 
                      help='Path to output CSV file')
    parser.add_argument('--output-parquet', default='data/processed/cleaned_vaers.parquet',
                      help='Path to output Parquet file')
    args = parser.parse_args()
    
    # Ensure output directories exist
    Path(args.output_csv).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_parquet).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        stats = process_data(args.input, args.output_csv, args.output_parquet)
        logger.info("Data processing completed successfully")
        logger.info(f"Output files saved to {args.output_csv} and {args.output_parquet}")
        return 0
    except Exception as e:
        logger.error(f"Data processing failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == '__main__':
    sys.exit(main())