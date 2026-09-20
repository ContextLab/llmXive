import os
import sys
import logging
import pandas as pd
import json
from pathlib import Path
import psutil

from utils.config import get_lod_value, get_use_synthetic_data, get_min_sample_size
from utils.logging_config import get_logger

class ConfigurationError(Exception):
    """Raised when configuration is missing or invalid."""
    pass

class InsufficientSampleSizeError(Exception):
    """Raised when the sample size is below the required minimum."""
    pass

def estimate_memory_footprint(df: pd.DataFrame) -> int:
    """Estimate memory footprint of a DataFrame in MB."""
    return df.memory_usage(deep=True).sum() / (1024 * 1024)

def handle_lod_titers(df: pd.DataFrame, lod_value: float) -> pd.DataFrame:
    """
    Handle Limit of Detection (LOD) for titer columns.
    Replaces 'ND', '', or NaN values with 0.5 * LOD_VALUE.
    Ensures titer columns are numeric.
    """
    titer_cols = ['titer_baseline', 'titer_post']
    if lod_value is None:
        raise ConfigurationError("LOD_VALUE must be explicitly set in config. No default allowed.")

    for col in titer_cols:
        if col not in df.columns:
            continue
        
        # Ensure column is numeric, coercing errors to NaN
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Identify missing or non-numeric values (NaN)
        # The task description implies 'ND' or '' might be present as strings before conversion
        # pd.to_numeric with errors='coerce' handles this by turning them into NaN
        
        # Impute missing values as 0.5 * LOD
        mask = df[col].isna()
        if mask.any():
            df.loc[mask, col] = 0.5 * lod_value
            logging.info(f"Imputed {mask.sum()} missing values in {col} with 0.5 * LOD ({0.5 * lod_value})")

    return df

def merge_otu_serology(otu_path: Path, serology_path: Path) -> pd.DataFrame:
    """Merge OTU table and serology metadata on subject_id."""
    if not otu_path.exists():
        raise FileNotFoundError(f"OTU table not found at {otu_path}")
    if not serology_path.exists():
        raise FileNotFoundError(f"Serology file not found at {serology_path}")

    otu_df = pd.read_csv(otu_path)
    sero_df = pd.read_csv(serology_path)

    if 'subject_id' not in otu_df.columns or 'subject_id' not in sero_df.columns:
        raise ValueError("Both datasets must contain 'subject_id' column for merging.")

    merged_df = pd.merge(otu_df, sero_df, on='subject_id', how='inner')
    logging.info(f"Merged dataset shape: {merged_df.shape}")
    return merged_df

def filter_complete_records(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out subjects where titer_baseline OR titer_post is truly missing (NaN).
    Microbiome columns: '0' abundance is valid, but actual NaNs in taxon columns are filtered.
    """
    titer_cols = ['titer_baseline', 'titer_post']
    
    # Filter rows where titer columns are not NaN
    df = df.dropna(subset=titer_cols)
    
    # Identify microbiome columns (exclude subject_id and titer columns)
    exclude_cols = ['subject_id'] + titer_cols
    taxon_cols = [c for c in df.columns if c not in exclude_cols]
    
    if taxon_cols:
        # Filter rows where any taxon column is NaN (actual missing data)
        # '0' is a valid abundance and should not be dropped
        df = df.dropna(subset=taxon_cols)
    
    logging.info(f"Filtered dataset shape: {df.shape}")
    return df

def validate_minimum_sample_size(df: pd.DataFrame, min_size: int, use_synthetic: bool) -> None:
    """
    Validate sample size against minimum requirement.
    If real data is insufficient, raise InsufficientSampleSizeError.
    If synthetic data is used, proceed regardless.
    """
    n = len(df)
    if n < min_size:
        if not use_synthetic:
            error_msg = f"Insufficient sample size (N={n} < {min_size}). Execution halted as per Spec Edge Cases."
            raise InsufficientSampleSizeError(error_msg)
        else:
            logging.warning(f"Sample size (N={n}) is below minimum ({min_size}), but proceeding because USE_SYNTHETIC_DATA is True.")
    else:
        logging.info(f"Sample size validation passed: N={n} >= {min_size}")

def write_assumptions(n: int, use_synthetic: bool, output_path: Path) -> None:
    """Write assumptions documentation to data/results/assumptions.md."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    content = f"""# Data Processing Assumptions

## LOD Handling
- Method: Imputation of missing/non-numeric values in titer columns.
- Value: 0.5 * LOD_VALUE (where LOD_VALUE is configured).
- Columns Affected: titer_baseline, titer_post.

## Sample Size Outcome
- Final Count: {n}
- Synthetic Data Used: {use_synthetic}
- Threshold: Minimum 50 subjects required for real data analysis.

## Methodology Note
- Data merging performed on 'subject_id'.
- Records with missing titer values or missing microbiome taxon data (NaN) were excluded.
- Zero abundance values in microbiome data were retained as valid observations.
"""
    
    with open(output_path, 'w') as f:
        f.write(content)
    logging.info(f"Assumptions written to {output_path}")

def write_error_report(error_type: str, count: int, message: str, results_dir: Path) -> None:
    """Write error report to data/results/sampling_error.json and error_log.txt."""
    results_dir.mkdir(parents=True, exist_ok=True)
    
    error_json = {
        "error_type": error_type,
        "count": count,
        "message": message
    }
    
    with open(results_dir / 'sampling_error.json', 'w') as f:
        json.dump(error_json, f, indent=2)
    
    with open(results_dir / 'error_log.txt', 'w') as f:
        f.write(message + '\n')
    
    logging.error(f"Error report written: {message}")

def main():
    """Main entry point for T011d: Merge Microbiome and Serology."""
    logger = get_logger(__name__)
    
    # Paths
    project_root = Path(__file__).resolve().parent.parent
    data_raw = project_root / 'data' / 'raw'
    data_processed = project_root / 'data' / 'processed'
    data_results = project_root / 'data' / 'results'
    
    # Determine input files based on config
    use_synthetic = get_use_synthetic_data()
    if use_synthetic:
        otu_file = data_raw / 'synthetic_otutable.csv'
        sero_file = data_raw / 'synthetic_serology.csv'
    else:
        otu_file = data_raw / 'otutable.csv'
        sero_file = data_raw / 'serology.csv'
    
    # Check if input files exist
    if not otu_file.exists():
        logger.error(f"Input OTU table not found: {otu_file}")
        sys.exit(1)
    if not sero_file.exists():
        logger.error(f"Input Serology file not found: {sero_file}")
        sys.exit(1)
    
    try:
        # 1. Merge
        df = merge_otu_serology(otu_file, sero_file)
        
        # 2. LOD Handling
        lod_value = get_lod_value()
        df = handle_lod_titers(df, lod_value)
        
        # 3. Filter Complete Records
        df = filter_complete_records(df)
        
        # 4. Validate Sample Size
        min_size = get_min_sample_size()
        validate_minimum_sample_size(df, min_size, use_synthetic)
        
        # 5. Write Output
        output_path = data_processed / 'cleared.csv'
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote filtered dataset to {output_path}")
        
        # 6. Document Assumptions
        write_assumptions(len(df), use_synthetic, data_results / 'assumptions.md')
        
    except InsufficientSampleSizeError as e:
        write_error_report("InsufficientSampleSize", len(df), str(e), data_results)
        sys.exit(1)
    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during merge process: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()