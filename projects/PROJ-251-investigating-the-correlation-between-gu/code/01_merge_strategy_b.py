import os
import sys
import logging
import pandas as pd
from pathlib import Path
import psutil
from typing import Tuple, Optional

from utils.config import get_lod_handling_methods, get_impute_lod, get_min_sample_size, get_use_synthetic_data
from utils.logging_config import get_logger, log_exclusion_count, log_sample_size, log_error_context

class InsufficientSampleSizeError(Exception):
    """Raised when the filtered dataset has fewer subjects than the minimum required."""
    pass

def estimate_memory_footprint(df: pd.DataFrame) -> float:
    """Estimate memory footprint of a DataFrame in MB."""
    return df.memory_usage(deep=True).sum() / (1024 * 1024)

def merge_otu_serology(
    otu_path: Path,
    serology_path: Path,
    output_path: Path,
    logger: logging.Logger
) -> pd.DataFrame:
    """
    Merge microbiome OTU table and serology metadata.
    
    Steps:
    1. Load both datasets.
    2. Merge on subject_id (inner join).
    3. Filter out subjects with missing (NaN) titer_baseline or titer_post.
    4. Handle LOD values ('ND', '0') by imputing with config.LOD_VALUE or 0.5 * LOD.
    5. Verify microbiome columns are not NaN for retained subjects (0 is valid).
    6. Validate minimum sample size.
    7. Write output.
    """
    logger.info(f"Loading OTU table from {otu_path}")
    otu_df = pd.read_csv(otu_path)
    
    logger.info(f"Loading serology metadata from {serology_path}")
    sero_df = pd.read_csv(serology_path)
    
    # Ensure subject_id is string for consistent merging
    otu_df['subject_id'] = otu_df['subject_id'].astype(str)
    sero_df['subject_id'] = sero_df['subject_id'].astype(str)
    
    # Merge on subject_id
    merged_df = pd.merge(otu_df, sero_df, on='subject_id', how='inner')
    initial_count = len(merged_df)
    logger.info(f"Initial merged count: {initial_count}")
    
    # Filter out subjects with truly missing (NaN) titers
    required_titer_cols = ['titer_baseline', 'titer_post']
    for col in required_titer_cols:
        if col not in merged_df.columns:
            raise ValueError(f"Required column {col} not found in serology data.")
    
    # Count nulls before filtering
    null_titer_count = merged_df[required_titer_cols].isnull().any(axis=1).sum()
    if null_titer_count > 0:
        log_exclusion_count(logger, "Missing titer values", null_titer_count)
    
    merged_df = merged_df.dropna(subset=required_titer_cols)
    after_null_filter_count = len(merged_df)
    logger.info(f"After null titer filter: {after_null_filter_count}")
    
    # LOD Handling: Impute 'ND', '0' (if string) or numeric 0 if specified
    # Check for string 'ND' or 'Not Detected' first, then numeric 0
    lod_methods = get_lod_handling_methods()
    lod_value = get_impute_lod()
    
    for col in required_titer_cols:
        # Ensure column is numeric, coercing errors to NaN first
        merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
        
        # Handle 'ND' or similar if they were strings (already coerced to NaN above)
        # If the original data had 'ND' as string, to_numeric made it NaN.
        # We need to check if there are any non-numeric strings left or handle them before to_numeric.
        # Assuming input is clean or handled by to_numeric.
        # The task says: "For any titer value marked as 'ND' (Not Detected) or '0', impute..."
        # If '0' is present as a number, we might want to impute it if it's below LOD.
        # But the spec says "impute as a fraction of the limit of detection".
        # Let's assume '0' in the raw data is a placeholder for <LOD.
        
        # Re-read: "For any titer value marked as 'ND' ... or '0', impute as a fraction..."
        # If the column is now numeric, '0' is 0.0.
        # We need to impute 0.0 and NaN (if they came from 'ND')?
        # The step "Filter out subjects where ... is truly missing (NaN)" already removed NaNs from 'ND' if they were strings.
        # So we need to handle '0' (numeric) and maybe re-handle NaN if 'ND' was passed as a string that didn't convert?
        # Let's assume 'ND' was converted to NaN and removed.
        # Now we handle 0.0.
        
        # If the original data had 'ND' as string, to_numeric -> NaN -> dropped.
        # If the original data had '0' as string -> to_numeric -> 0.0.
        # If the original data had 0 as int -> 0.0.
        
        # Logic: Impute 0.0 values with lod_value * 0.5 (default).
        # Also, if there are any remaining NaNs (from 'ND' that somehow survived or were not dropped?), impute them too?
        # The task says: "Filter out subjects where ... is truly missing (NaN/Null)".
        # So we should NOT impute NaNs, we should have dropped them.
        # So we only impute 0.0.
        
        # However, the task also says: "For any titer value marked as 'ND' ... or '0', impute..."
        # If 'ND' was in the data as a string, to_numeric makes it NaN.
        # If we drop NaNs, we lose 'ND' subjects.
        # The task says: "Filter out ... truly missing". 'ND' might not be "truly missing" but a specific value.
        # So we should impute 'ND' BEFORE dropping NaNs?
        # Let's adjust:
        # 1. Load data.
        # 2. Identify 'ND'/'Not Detected' strings and replace with a placeholder or directly impute.
        # 3. Convert to numeric.
        # 4. Drop NaNs (which are truly missing, not 'ND').
        
        # Revised LOD Handling:
        # Check for 'ND' in original string column before conversion?
        # Or, if to_numeric made 'ND' -> NaN, we can't distinguish from truly missing.
        # Assumption: The input CSV has 'ND' as a string.
        # We should replace 'ND' with lod_value * 0.5 BEFORE to_numeric?
        # Or replace 'ND' with NaN, then impute NaNs?
        # The task says: "impute as a fraction of the limit of detection".
        # So 'ND' -> imputed value.
        # '0' -> imputed value.
        # Truly missing (empty cell) -> drop.
        
        # Let's do:
        # 1. Replace 'ND', 'Not Detected' (case insensitive) with a special marker or directly with impute value?
        # Better: Replace with NaN, then impute NaNs that came from 'ND'?
        # How to distinguish 'ND' from truly missing?
        # If the CSV has 'ND', it's a string. If empty, it's NaN.
        # So:
        # - Replace 'ND', 'Not Detected' with NaN? No, we want to impute them.
        # - Replace 'ND', 'Not Detected' with a placeholder like -1?
        # - Or, replace 'ND', 'Not Detected' with the imputed value directly.
        # - Replace '0' (string or int) with the imputed value.
        # - Then convert to numeric.
        # - Then drop NaNs (truly missing).
        
        # Let's implement:
        # 1. If column is object, replace 'ND', 'Not Detected' (case insensitive) with lod_value * 0.5.
        # 2. Replace '0' (string) with lod_value * 0.5.
        # 3. Convert to numeric.
        # 4. Drop NaNs.
        
        if merged_df[col].dtype == 'object':
            # Replace 'ND', 'Not Detected' (case insensitive)
            merged_df[col] = merged_df[col].str.upper().replace({'ND': lod_value * 0.5, 'NOT DETECTED': lod_value * 0.5})
            # Replace '0' string
            merged_df[col] = merged_df[col].replace('0', lod_value * 0.5)
            # Convert to numeric
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
        else:
            # Numeric column
            # Replace 0.0 with lod_value * 0.5
            merged_df[col] = merged_df[col].replace(0.0, lod_value * 0.5)
            # Ensure numeric
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
        
        # Now drop NaNs (truly missing)
        merged_df = merged_df.dropna(subset=[col])
    
    # Microbiome Completeness: Verify taxon columns are not NaN for retained subjects.
    # Taxon columns are all columns except subject_id, titer_baseline, titer_post.
    taxon_cols = [col for col in merged_df.columns if col not in ['subject_id', 'titer_baseline', 'titer_post']]
    if not taxon_cols:
        raise ValueError("No taxon columns found in OTU table.")
    
    # Check for NaN in taxon columns
    null_taxa_count = merged_df[taxon_cols].isnull().any(axis=1).sum()
    if null_taxa_count > 0:
        log_exclusion_count(logger, "Missing microbiome data", null_taxa_count)
        merged_df = merged_df.dropna(subset=taxon_cols)
    
    final_count = len(merged_df)
    log_sample_size(logger, final_count)
    
    min_sample_size = get_min_sample_size()
    use_synthetic = get_use_synthetic_data()
    
    if final_count < min_sample_size and not use_synthetic:
        error_msg = f"Insufficient sample size (N < {min_sample_size}) in final dataset."
        log_error_context(logger, error_msg)
        raise InsufficientSampleSizeError(error_msg)
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Written merged dataset to {output_path} with {final_count} subjects.")
    
    return merged_df

def main():
    """Main entry point for merging strategy B."""
    logger = get_logger(__name__)
    
    # Determine input paths based on synthetic flag
    use_synthetic = get_use_synthetic_data()
    if use_synthetic:
        otu_path = Path("data/raw/synthetic_otutable.csv")
        sero_path = Path("data/raw/synthetic_serology.csv")
    else:
        otu_path = Path("data/raw/otutable.csv")
        sero_path = Path("data/raw/serology.csv")
    
    output_path = Path("data/processed/data_merged.csv")
    
    try:
        merge_otu_serology(otu_path, sero_path, output_path, logger)
        print(f"Successfully merged data to {output_path}")
    except InsufficientSampleSizeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        log_error_context(logger, f"Unexpected error during merge: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()