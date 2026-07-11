import os
import sys
import gc
import logging
import tracemalloc
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Configure logging to output to stdout and a file if needed
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_memory_usage_gb() -> float:
    """
    Returns the current memory usage of the process in Gigabytes.
    Uses tracemalloc if available, otherwise falls back to psutil if installed,
    or returns 0.0 if neither is available.
    """
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        return mem_info.rss / (1024 ** 3)
    except ImportError:
        logger.warning("psutil not installed. Using tracemalloc fallback.")
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            return current / (1024 ** 3)
        else:
            # tracemalloc not started, try to get a rough estimate or 0
            return 0.0
    except Exception as e:
        logger.error(f"Could not determine memory usage: {e}")
        return 0.0


def map_soc_codes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps MedDRA SOC codes to their textual names using an embedded mapping table.
    
    Args:
        df: DataFrame containing a 'SOC_CODE' column.
        
    Returns:
        DataFrame with an added 'SOC' column.
    """
    # Embedded mapping table for MedDRA SOC Codes to Names
    # Source: MedDRA Maintenance and Support Services Organization (MSSO)
    soc_mapping = {
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
        '10018000': 'Product issues',
        '10019000': 'Psychiatric disorders',
        '10020000': 'Renal and urinary disorders',
        '10021000': 'Reproductive system and breast disorders',
        '10022000': 'Respiratory, thoracic and mediastinal disorders',
        '10023000': 'Skin and subcutaneous tissue disorders',
        '10024000': 'Social circumstances',
        '10025000': 'Surgical and medical procedures',
        '10026000': 'Vascular disorders',
        # Add common codes if specific ones are missing in raw data, defaulting to 'Unspecified'
    }

    df = df.copy()
    # Map codes to names, filling unknown codes with 'Unknown SOC'
    df['SOC'] = df['SOC_CODE'].map(soc_mapping).fillna('Unknown SOC')
    return df


def process_data(input_path: str, output_dir: str) -> Dict[str, int]:
    """
    Processes the raw VAERS data:
    1. Loads data (with chunking if necessary for large files).
    2. Filters for COVID-19 and Non-COVID groups.
    3. Cleans data (removes rows with missing SOC or REPT_DATE).
    4. Maps SOC codes.
    5. Saves outputs (Parquet and CSV).
    6. Logs row counts and memory usage.

    Args:
        input_path: Path to the raw VAERS CSV file(s).
        output_dir: Directory to save processed files.
        
    Returns:
        Dictionary with row counts per group.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Start memory tracking
    tracemalloc.start()
    
    logger.info(f"Starting data processing for: {input_path}")
    initial_mem = get_memory_usage_gb()
    logger.info(f"Initial memory usage: {initial_mem:.2f} GB")

    # Determine if we need chunking (heuristic: if file > 1GB)
    file_size_gb = os.path.getsize(input_path) / (1024 ** 3)
    chunk_size = 500000 if file_size_gb > 1.0 else None
    
    logger.info(f"File size: {file_size_gb:.2f} GB. Using chunk size: {chunk_size}")

    # Read data
    chunks = []
    row_count = 0
    
    # Assuming input_path might be a single file or a glob pattern if extended later
    # For this implementation, we assume a single consolidated raw file or list of files
    # If multiple files, we'd iterate. Here we assume one file for simplicity based on T013.
    if chunk_size:
        for chunk in pd.read_csv(input_path, chunksize=chunk_size):
            chunks.append(chunk)
            row_count += len(chunk)
            # Periodic GC to manage memory
            if row_count % (chunk_size * 5) == 0:
                gc.collect()
                current_mem = get_memory_usage_gb()
                logger.info(f"Processed {row_count} rows. Current memory: {current_mem:.2f} GB")
    else:
        df_raw = pd.read_csv(input_path)
        row_count = len(df_raw)
        chunks = [df_raw]

    df = pd.concat(chunks, ignore_index=True)
    del chunks
    gc.collect()
    
    logger.info(f"Loaded {len(df)} total rows.")
    mem_after_load = get_memory_usage_gb()
    logger.info(f"Memory after load: {mem_after_load:.2f} GB")

    # --- T016 Logic: Filtering and Grouping ---
    
    # Filter for COVID-19 vaccine reports
    # T018 Requirement: Log row counts per group
    covid_mask = df['VAX_TYPE'].str.contains("COVID-19", na=False, case=True)
    df_covid = df[covid_mask].copy()
    logger.info(f"Row count for COVID-19 group: {len(df_covid)}")

    # Filter for Non-COVID baseline (all other vaccines)
    non_covid_mask = ~covid_mask & df['VAX_TYPE'].notna()
    df_non_covid = df[non_covid_mask].copy()
    logger.info(f"Row count for Non-COVID baseline group: {len(df_non_covid)}")

    # Filter for Non-COVID, Non-Flu sensitivity group
    non_flu_mask = ~df_non_covid['VAX_TYPE'].str.contains("Influenza|Flu", na=False, case=True)
    df_non_covid_non_flu = df_non_covid[non_flu_mask].copy()
    logger.info(f"Row count for Non-COVID, Non-Flu sensitivity group: {len(df_non_covid_non_flu)}")

    # Filter for Flu-only group
    flu_mask = df_non_covid['VAX_TYPE'].str.contains("Influenza|Flu", na=False, case=True)
    df_flu = df_non_covid[flu_mask].copy()
    logger.info(f"Row count for Flu-only group: {len(df_flu)}")

    # --- Cleaning ---
    # Exclude records with missing SOC or REPT_DATE
    # Note: We apply this to the main dataframe before splitting or to each subset?
    # Usually, cleaning is done on the raw data first, then split.
    # Let's clean the main dataframe first to ensure consistency.
    
    initial_clean_count = len(df)
    df = df.dropna(subset=['SOC_CODE', 'REPT_DATE'])
    # Re-apply filters on cleaned data to ensure accurate counts
    # Re-calculate masks on cleaned df
    covid_mask = df['VAX_TYPE'].str.contains("COVID-19", na=False, case=True)
    non_covid_mask = ~covid_mask & df['VAX_TYPE'].notna()
    
    df_covid = df[covid_mask].copy()
    df_non_covid = df[non_covid_mask].copy()
    df_non_covid_non_flu = df_non_covid[~df_non_covid['VAX_TYPE'].str.contains("Influenza|Flu", na=False, case=True)].copy()
    df_flu = df_non_covid[df_non_covid['VAX_TYPE'].str.contains("Influenza|Flu", na=False, case=True)].copy()

    cleaned_count = len(df)
    logger.info(f"Removed {initial_clean_count - cleaned_count} rows due to missing SOC_CODE or REPT_DATE.")
    logger.info(f"Total cleaned rows: {cleaned_count}")

    # Map SOC codes
    df_covid = map_soc_codes(df_covid)
    df_non_covid = map_soc_codes(df_non_covid)
    df_non_covid_non_flu = map_soc_codes(df_non_covid_non_flu)
    df_flu = map_soc_codes(df_flu)

    # Save outputs
    output_parquet = os.path.join(output_dir, 'cleaned_vaers.parquet')
    output_csv = os.path.join(output_dir, 'cleaned_vaers.csv')

    logger.info(f"Saving cleaned data to {output_parquet}...")
    df.to_parquet(output_parquet, index=False)
    
    logger.info(f"Saving cleaned data to {output_csv}...")
    df.to_csv(output_csv, index=False)

    # Final Memory Stats
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    final_mem_gb = current_mem / (1024 ** 3)
    peak_mem_gb = peak_mem / (1024 ** 3)
    
    logger.info(f"Processing complete.")
    logger.info(f"Final memory usage: {final_mem_gb:.2f} GB")
    logger.info(f"Peak memory usage: {peak_mem_gb:.2f} GB")
    
    # Log final row counts per group as required by T018
    logger.info(f"Final Group Counts:")
    logger.info(f"  - COVID-19: {len(df_covid)}")
    logger.info(f"  - Non-COVID (Baseline): {len(df_non_covid)}")
    logger.info(f"  - Non-COVID, Non-Flu (Sensitivity): {len(df_non_covid_non_flu)}")
    logger.info(f"  - Flu-only (Sensitivity): {len(df_flu)}")

    return {
        'total_cleaned': len(df),
        'covid': len(df_covid),
        'non_covid': len(df_non_covid),
        'non_covid_non_flu': len(df_non_covid_non_flu),
        'flu': len(df_flu)
    }


def main():
    """
    Main entry point for the data cleaning script.
    Expects input file path and output directory as arguments or defaults.
    """
    # Default paths based on project structure
    # If running from code/src/data/, adjust accordingly or pass args
    input_file = os.getenv('VAERS_RAW_FILE', 'data/raw/combined_vaers.csv')
    output_directory = os.getenv('VAERS_OUTPUT_DIR', 'data/processed')
    
    # Check if input file exists
    if not os.path.exists(input_file):
        # If not found, check relative to project root if running from subfolder
        # Or raise error
        logger.error(f"Input file not found: {input_file}")
        sys.exit(1)

    try:
        stats = process_data(input_file, output_directory)
        logger.info("Data cleaning completed successfully.")
    except Exception as e:
        logger.error(f"Data cleaning failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()