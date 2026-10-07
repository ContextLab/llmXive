import os
import sys
import gc
import logging
import tracemalloc
import psutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd

# Constants for error codes
E_MAPPINGS_INVALID = "E_MAPPINGS_INVALID"
E_MEMORY_LIMIT = "E_MEMORY_LIMIT"
E_SCHEMA_MISSING = "E_SCHEMA_MISSING"

def setup_logging() -> logging.Logger:
    """Configure logging for the cleaning process."""
    logger = logging.getLogger("clean")
    logger.setLevel(logging.INFO)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # File handler
    fh = logging.FileHandler(logs_dir / "clean.log")
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def get_memory_usage_gb() -> float:
    """Get current memory usage in GB."""
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def check_memory_usage(logger: logging.Logger, limit_gb: float = 7.0) -> bool:
    """Check if memory usage exceeds limit. Returns True if limit exceeded."""
    current_mb = get_memory_usage_gb()
    if current_mb > limit_gb:
        logger.error(f"MEMORY_LIMIT_EXCEEDED: {current_mb:.2f} GB > {limit_gb} GB")
        return True
    return False

def estimate_file_size_gb(file_path: Path) -> float:
    """Estimate file size in GB."""
    if not file_path.exists():
        return 0.0
    size_bytes = file_path.stat().st_size
    return size_bytes / (1024 ** 3)

def load_meddra_mapping(mapping_path: Path, logger: logging.Logger) -> pd.DataFrame:
    """Load MedDRA to SOC mapping table."""
    logger.info(f"Loading MedDRA mapping from {mapping_path}")
    
    if not mapping_path.exists():
        logger.error(f"MedDRA mapping file not found: {mapping_path}")
        raise FileNotFoundError(f"MedDRA mapping file not found: {mapping_path}")
    
    try:
        mapping_df = pd.read_csv(mapping_path)
        
        # Validate required columns
        required_cols = ['LLT_CODE', 'SOC_CODE', 'SOC_NAME']
        missing_cols = [col for col in required_cols if col not in mapping_df.columns]
        
        if missing_cols:
            logger.error(f"MedDRA mapping missing required columns: {missing_cols}")
            raise ValueError(f"MedDRA mapping missing columns: {missing_cols}")
        
        logger.info(f"Loaded {len(mapping_df)} MedDRA mappings")
        return mapping_df
        
    except Exception as e:
        logger.error(f"Failed to load MedDRA mapping: {str(e)}")
        raise

def map_soc_to_code(row: pd.Series, mapping_df: pd.DataFrame, logger: logging.Logger) -> str:
    """Map LLT or SOC_CODE to SOC_NAME using the mapping table."""
    llt_code = row.get('LLT', '')
    soc_code = row.get('SOC_CODE', '')
    
    # If we have an LLT code, try to map it
    if pd.notna(llt_code) and llt_code != '':
        match = mapping_df[mapping_df['LLT_CODE'] == str(llt_code)]
        if not match.empty:
            return match.iloc[0]['SOC_NAME']
    
    # If we have an SOC_CODE, try to map it directly
    if pd.notna(soc_code) and soc_code != '':
        match = mapping_df[mapping_df['SOC_CODE'] == str(soc_code)]
        if not match.empty:
            return match.iloc[0]['SOC_NAME']
    
    return 'UNKNOWN'

def process_chunk(chunk: pd.DataFrame, mapping_df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Process a single chunk of data."""
    # Filter out null/empty VAX_TYPE
    chunk = chunk[chunk['VAX_TYPE'].notna() & (chunk['VAX_TYPE'] != '')]
    chunk = chunk[chunk['VAX_TYPE'].apply(lambda x: isinstance(x, str))]
    
    # Filter out missing REPT_DATE
    chunk = chunk[chunk['REPT_DATE'].notna()]
    
    # Map SOC codes
    chunk['SOC'] = chunk.apply(lambda row: map_soc_to_code(row, mapping_df, logger), axis=1)
    
    return chunk

def process_data(
    input_files: List[Path],
    mapping_df: pd.DataFrame,
    output_dir: Path,
    logger: logging.Logger,
    chunk_size: int = 100000
) -> Dict[str, pd.DataFrame]:
    """Process all input files with memory-aware chunked processing."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_data = []
    total_rows = 0
    
    for file_path in input_files:
        logger.info(f"Processing file: {file_path}")
        
        # Estimate file size and decide on chunked processing
        file_size_gb = estimate_file_size_gb(file_path)
        use_chunked = file_size_gb > 5.0 or check_memory_usage(logger)
        
        if use_chunked:
            logger.info(f"Using chunked processing for {file_path} (size: {file_size_gb:.2f} GB)")
            
            # Track memory during chunked processing
            tracemalloc.start()
            
            for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                if check_memory_usage(logger):
                    tracemalloc.stop()
                    raise MemoryError(f"Memory limit exceeded while processing {file_path}")
                
                processed_chunk = process_chunk(chunk, mapping_df, logger)
                all_data.append(processed_chunk)
                total_rows += len(processed_chunk)
                
                # Log progress
                if total_rows % 1000000 == 0:
                    logger.info(f"Processed {total_rows:,} rows")
                    current, peak = tracemalloc.get_traced_memory()
                    logger.info(f"Current memory: {current / 1024 / 1024:.2f} MB, Peak: {peak / 1024 / 1024:.2f} MB")
            
            tracemalloc.stop()
            gc.collect()
        else:
            logger.info(f"Loading full file into memory: {file_path}")
            df = pd.read_csv(file_path)
            processed_df = process_chunk(df, mapping_df, logger)
            all_data.append(processed_df)
            total_rows += len(processed_df)
    
    # Combine all processed data
    logger.info(f"Combining {len(all_data)} processed chunks")
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Log memory usage before grouping
    mem_before = get_memory_usage_gb()
    logger.info(f"Memory usage before grouping: {mem_before:.2f} GB")
    
    # Create groups as per T015 specification
    # COVID-19 Group: VAX_TYPE contains "COVID-19"
    covid_mask = combined_df['VAX_TYPE'].str.contains('COVID-19', case=False, na=False)
    covid_df = combined_df[covid_mask].copy()
    
    # Full Non-COVID Group: VAX_TYPE does NOT contain "COVID-19"
    non_covid_mask = ~covid_mask
    full_non_covid_df = combined_df[non_covid_mask].copy()
    
    # Flu-only Group: Full Non-COVID where VAX_TYPE contains "Influenza"
    flu_mask = full_non_covid_df['VAX_TYPE'].str.contains('Influenza', case=False, na=False)
    flu_only_df = full_non_covid_df[flu_mask].copy()
    
    # Non-COVID, Non-Flu Group: Full Non-COVID where VAX_TYPE does NOT contain "Influenza"
    non_flu_mask = ~flu_mask
    non_covid_non_flu_df = full_non_covid_df[non_flu_mask].copy()
    
    # Log memory usage after grouping
    mem_after = get_memory_usage_gb()
    logger.info(f"Memory usage after grouping: {mem_after:.2f} GB")
    logger.info(f"Memory delta for grouping: {mem_after - mem_before:.2f} GB")
    
    # Log row counts per group
    logger.info("=" * 60)
    logger.info("ROW COUNTS PER GROUP:")
    logger.info(f"  Total cleaned records: {len(combined_df):,}")
    logger.info(f"  COVID-19 Group: {len(covid_df):,}")
    logger.info(f"  Full Non-COVID Group (includes Flu): {len(full_non_covid_df):,}")
    logger.info(f"  Flu-only Group: {len(flu_only_df):,}")
    logger.info(f"  Non-COVID, Non-Flu Group: {len(non_covid_non_flu_df):,}")
    logger.info("=" * 60)
    
    # Verify all groups have valid SOC fields
    for group_name, group_df in [
        ('Combined', combined_df),
        ('COVID-19', covid_df),
        ('Full Non-COVID', full_non_covid_df),
        ('Flu-only', flu_only_df),
        ('Non-COVID Non-Flu', non_covid_non_flu_df)
    ]:
        valid_soc = group_df['SOC'].notna() & (group_df['SOC'] != '')
        invalid_count = (~valid_soc).sum()
        logger.info(f"  {group_name} - Valid SOC count: {valid_soc.sum():,}, Invalid/Empty: {invalid_count}")
    
    return {
        'combined': combined_df,
        'covid': covid_df,
        'full_non_covid': full_non_covid_df,
        'flu_only': flu_only_df,
        'non_covid_non_flu': non_covid_non_flu_df
    }

def save_outputs(data: Dict[str, pd.DataFrame], output_dir: Path, logger: logging.Logger):
    """Save processed data to output files."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save Full Non-COVID (Primary input for T022)
    full_non_covid_path = output_dir / "cleaned_vaers_full_non_covid.parquet"
    logger.info(f"Saving Full Non-COVID group to {full_non_covid_path}")
    data['full_non_covid'].to_parquet(full_non_covid_path, index=False)
    
    # Save all groups (General)
    all_path = output_dir / "cleaned_vaers.parquet"
    logger.info(f"Saving all groups to {all_path}")
    # Create a combined dataframe with group labels
    all_combined = pd.concat([
        data['covid'].assign(group='COVID-19'),
        data['full_non_covid'].assign(group='Full Non-COVID'),
        data['flu_only'].assign(group='Flu-only'),
        data['non_covid_non_flu'].assign(group='Non-COVID Non-Flu')
    ], ignore_index=True)
    all_combined.to_parquet(all_path, index=False)
    
    # Save human-readable CSV
    csv_path = output_dir / "cleaned_vaers.csv"
    logger.info(f"Saving human-readable CSV to {csv_path}")
    all_combined.to_csv(csv_path, index=False)
    
    logger.info("All output files saved successfully")

def main():
    """Main entry point for data cleaning."""
    logger = setup_logging()
    logger.info("Starting data cleaning process")
    
    # Start memory tracking
    tracemalloc.start()
    
    try:
        # Define paths
        base_dir = Path(__file__).parent.parent.parent
        data_dir = base_dir / "data"
        raw_dir = data_dir / "raw"
        processed_dir = data_dir / "processed"
        mapping_path = data_dir / "meddra_soc_mapping.csv"
        
        # Ensure output directory exists
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Find input files (VAERS 2020-2023)
        input_files = list(raw_dir.glob("vaers_*.csv"))
        
        if not input_files:
            logger.error(f"No VAERS CSV files found in {raw_dir}")
            sys.exit(1)
        
        logger.info(f"Found {len(input_files)} input files: {[f.name for f in input_files]}")
        
        # Load MedDRA mapping
        mapping_df = load_meddra_mapping(mapping_path, logger)
        
        # Process data
        data = process_data(input_files, mapping_df, processed_dir, logger)
        
        # Save outputs
        save_outputs(data, processed_dir, logger)
        
        # Final memory stats
        current, peak = tracemalloc.get_traced_memory()
        logger.info(f"Final memory usage: Current {current / 1024 / 1024:.2f} MB, Peak {peak / 1024 / 1024:.2f} MB")
        logger.info(f"Peak memory usage: {peak / 1024 / 1024 / 1024:.2f} GB")
        
        logger.info("Data cleaning completed successfully")
        
    except Exception as e:
        logger.error(f"Data cleaning failed: {str(e)}")
        raise
    finally:
        tracemalloc.stop()

if __name__ == "__main__":
    main()