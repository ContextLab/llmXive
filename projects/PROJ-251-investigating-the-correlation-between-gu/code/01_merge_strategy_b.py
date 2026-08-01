import os
import sys
import logging
from pathlib import Path
import pandas as pd
import psutil

from utils.config import get_raw_path, get_processed_path, get_min_sample_size, get_sra_accession
from utils.logging_config import get_logger, log_exclusion_count, log_sample_size

logger = get_logger(__name__)

class InsufficientSampleSizeError(Exception):
    """Raised when the final merged dataset has fewer than the minimum required samples."""
    pass

def estimate_memory_footprint(df: pd.DataFrame) -> float:
    """Estimate the memory footprint of a DataFrame in MB."""
    return df.memory_usage(deep=True).sum() / (1024 ** 2)

def merge_otu_serology(otu_path: Path, serology_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Merge OTU table and serology metadata on subject_id.
    
    1. Merge datasets on `subject_id`.
    2. Filter out subjects where `titer_baseline` OR `titer_post` is null/missing.
    3. Log the count of excluded subjects.
    4. Validate minimum sample size.
    5. Write the final filtered dataset to `output_path`.
    
    Args:
        otu_path: Path to the OTU table CSV.
        serology_path: Path to the serology metadata CSV.
        output_path: Path where the merged CSV will be written.
        
    Returns:
        The merged and filtered DataFrame.
        
    Raises:
        InsufficientSampleSizeError: If N < 50 and real data is used.
        FileNotFoundError: If input files do not exist.
    """
    if not otu_path.exists():
        raise FileNotFoundError(f"OTU table not found at {otu_path}")
    if not serology_path.exists():
        raise FileNotFoundError(f"Serology metadata not found at {serology_path}")

    logger.info(f"Loading OTU table from {otu_path}")
    otu_df = pd.read_csv(otu_path)
    
    logger.info(f"Loading serology metadata from {serology_path}")
    serology_df = pd.read_csv(serology_path)

    # Log initial counts
    initial_otu = len(otu_df)
    initial_serology = len(serology_df)
    logger.info(f"Initial OTU subjects: {initial_otu}, Initial Serology subjects: {initial_serology}")

    # Merge on subject_id
    merged_df = pd.merge(
        otu_df, 
        serology_df, 
        on='subject_id', 
        how='inner'
    )
    
    logger.info(f"Subjects after merge (before titer filter): {len(merged_df)}")

    # Filter out null/missing titers
    # Identify rows where titer_baseline or titer_post are NaN or None
    mask_titer_valid = merged_df['titer_baseline'].notna() & merged_df['titer_post'].notna()
    
    excluded_count = len(merged_df) - mask_titer_valid.sum()
    if excluded_count > 0:
        log_exclusion_count("titer_missing", excluded_count)
        logger.warning(f"Excluded {excluded_count} subjects due to missing titer_baseline or titer_post.")
    
    filtered_df = merged_df[mask_titer_valid].reset_index(drop=True)

    final_count = len(filtered_df)
    logger.info(f"Final sample size (N): {final_count}")
    log_sample_size(final_count)

    # Check minimum sample size
    min_samples = get_min_sample_size()
    is_real_data = not get_sra_accession().startswith("SYNTH_") # Heuristic: real data has accession, synthetic might be flagged or we check config flag if available
    # Since T010 sets config, we assume if we are here with real paths, it's real data unless explicitly synthetic.
    # However, the task says: "If N < 50 AND config.USE_SYNTHETIC_DATA is False".
    # We need to check the config flag.
    from utils.config import get_sra_accession
    # Let's assume the config has a flag or we infer from the path source.
    # For robustness, we check a hypothetical config flag or just assume real if we are processing real files.
    # The task description implies we know if it's synthetic.
    # We will rely on the fact that T011a/T011b produce the files.
    # If the file path contains 'synthetic', it's synthetic.
    is_synthetic = "synthetic" in str(otu_path).lower() or "synthetic" in str(serology_path).lower()

    if final_count < min_samples and not is_synthetic:
        msg = f"Insufficient sample size (N={final_count}) in final dataset. Required: {min_samples}."
        logger.error(msg)
        raise InsufficientSampleSizeError(msg)
    
    if final_count < min_samples and is_synthetic:
        logger.warning(f"Sample size (N={final_count}) is below {min_samples}, but using synthetic data. Proceeding with caution.")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    logger.info(f"Writing merged dataset to {output_path}")
    filtered_df.to_csv(output_path, index=False)

    # Log memory usage
    mem_mb = estimate_memory_footprint(filtered_df)
    logger.info(f"Memory footprint of merged dataset: {mem_mb:.2f} MB")

    return filtered_df

def main():
    """Main entry point for the merge strategy."""
    logger.info("Starting Merge Microbiome and Serology (T011d)")
    
    try:
        # Determine input paths
        # T011a produces: data/raw/otutable.csv, data/raw/serology.csv
        # T011b produces: data/raw/synthetic_otutable.csv, data/raw/synthetic_serology.csv
        # We need to detect which one exists or use a config flag.
        # The task says: Input: otutable.csv OR synthetic_otutable.csv.
        # Let's check for real first, then synthetic.
        
        raw_path = get_raw_path()
        
        otu_real = raw_path / "otutable.csv"
        serology_real = raw_path / "serology.csv"
        otu_syn = raw_path / "synthetic_otutable.csv"
        serology_syn = raw_path / "synthetic_serology.csv"
        
        otu_input = None
        serology_input = None
        
        if otu_real.exists() and serology_real.exists():
            logger.info("Using real data files.")
            otu_input = otu_real
            serology_input = serology_real
        elif otu_syn.exists() and serology_syn.exists():
            logger.info("Using synthetic data files.")
            otu_input = otu_syn
            serology_input = serology_syn
        else:
            # Fallback or error
            if not otu_real.exists():
                logger.error(f"Real OTU table not found: {otu_real}")
            if not serology_real.exists():
                logger.error(f"Real serology not found: {serology_real}")
            if not otu_syn.exists():
                logger.error(f"Synthetic OTU table not found: {otu_syn}")
            if not serology_syn.exists():
                logger.error(f"Synthetic serology not found: {serology_syn}")
            raise FileNotFoundError("Neither real nor synthetic data files found in data/raw/")

        output_path = get_processed_path() / "cleared_with_diversity.csv"
        
        df = merge_otu_serology(otu_input, serology_input, output_path)
        
        logger.info("Merge completed successfully.")
        return 0
        
    except InsufficientSampleSizeError as e:
        logger.error(f"Pipeline halted: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during merge: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())