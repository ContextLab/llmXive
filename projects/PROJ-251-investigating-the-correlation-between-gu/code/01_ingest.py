import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd

from utils.config import get_hf_token, get_ncbi_api_key, get_random_seed, get_min_sample_size, get_pseudocount, get_output_path, get_processed_path, get_raw_path, ensure_directories
from utils.data_loader import load_csv_file, load_otu_table, filter_complete_records, validate_titer_values, ensure_minimum_sample_size, load_and_preprocess_data
from utils.logging_config import get_logger, log_exclusion_count, log_sample_size, log_error_context
from utils.sra_downloader import fetch_sra_data
from utils.validators import validate_dataset_schema

logger = get_logger(__name__)

def fetch_huggingface_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Strategy A: Fetch pre-processed OTU table and serology metadata from HuggingFace.
    Returns: (otutable_df, metadata_df)
    """
    logger.info("Attempting Strategy A: Fetching from HuggingFace...")
    try:
        from datasets import load_dataset
        dataset = load_dataset("biothings/srp053178_processed", split="train")
        df_otu = dataset["otutable"].to_pandas()
        df_meta = dataset["metadata"].to_pandas()
        logger.info(f"Successfully loaded {len(df_otu)} OTU samples and {len(df_meta)} metadata records.")
        return df_otu, df_meta
    except Exception as e:
        logger.error(f"Strategy A failed: {e}")
        raise

def run_strategy_b() -> Tuple[Path, Path]:
    """
    Strategy B: Download raw FASTQ files from NCBI SRA.
    Returns: Path to raw directory and list of FASTQ files (conceptually).
    Note: This task (T011b) only implements the download. The processing (T011c)
    and merging (T011d) are separate tasks. However, this function returns the
    state needed for the next steps.
    """
    logger.info("Initiating Strategy B: Downloading raw FASTQ from NCBI SRA...")
    try:
        run_ids, downloaded_files = fetch_sra_data("SRP053178")
        raw_dir = get_raw_path()
        logger.info(f"Strategy B complete. Downloaded {len(downloaded_files)} files to {raw_dir}")
        return raw_dir, downloaded_files[0] if downloaded_files else None
    except Exception as e:
        logger.error(f"Strategy B failed: {e}")
        raise

def merge_and_preprocess(otutable_df: pd.DataFrame, metadata_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge OTU table and metadata on subject_id.
    """
    # Assuming common key is 'subject_id' or similar. 
    # Based on typical SRA metadata, it might be 'Run' or 'Sample'.
    # We will assume 'subject_id' as per spec.
    if 'subject_id' not in otutable_df.columns or 'subject_id' not in metadata_df.columns:
        # Fallback or error handling
        raise ValueError("Missing 'subject_id' column for merging.")
    
    merged = pd.merge(otutable_df, metadata_df, on='subject_id', how='inner')
    logger.info(f"Merged dataset size: {len(merged)}")
    return merged

def run_ingestion(strategy: str = "auto") -> pd.DataFrame:
    """
    Orchestrate the ingestion process.
    If strategy is 'auto', try Strategy A first, then fall back to B.
    Returns the final filtered and preprocessed DataFrame.
    """
    ensure_directories()
    df_final = None

    try:
        if strategy == "A" or strategy == "auto":
            try:
                otu_df, meta_df = fetch_huggingface_data()
                df_final = merge_and_preprocess(otu_df, meta_df)
                logger.info("Ingestion via Strategy A successful.")
            except Exception as e:
                logger.warning(f"Strategy A failed ({e}), falling back to Strategy B.")
                if strategy == "A":
                    raise

        if df_final is None and (strategy == "B" or strategy == "auto"):
            # Strategy B involves downloading raw data, which is heavy.
            # For T011b, we implement the download. The actual merging requires
            # T011c (processing) and T011d (merging).
            # Since T011b is just the download, we return the path to raw data
            # and raise an exception to indicate that further processing is needed
            # before a DataFrame is returned.
            raw_dir, _ = run_strategy_b()
            log_error_context("Strategy B downloaded raw data. Further processing (QIIME2/DADA2) required.")
            # We cannot return a DataFrame yet because the OTU table doesn't exist in processed form.
            # We raise a specific exception or return a status object.
            # For the sake of the pipeline flow, we will raise a custom error indicating
            # that the raw data is ready but the processed table is not.
            raise RuntimeError("ERR_STRATEGY_B_INCOMPLETE: Raw data downloaded. Run T011c and T011d to process and merge.")

    except RuntimeError as e:
        if "ERR_STRATEGY_B_INCOMPLETE" in str(e):
            # This is expected for Strategy B at this stage
            logger.info(f"Expected interruption: {e}")
            return None # Or handle appropriately
        raise

    if df_final is not None:
        # Apply filtering
        df_filtered = filter_complete_records(df_final)
        df_validated = validate_titer_values(df_filtered)
        
        if not ensure_minimum_sample_size(df_validated):
            raise ValueError("ERR_NO_DATA: Insufficient Sample Size (N < 50)")
        
        log_sample_size(len(df_validated))
        validate_dataset_schema(df_validated)
        
        output_path = get_processed_path() / "filtered_data.csv"
        df_validated.to_csv(output_path, index=False)
        logger.info(f"Filtered data saved to {output_path}")
        return df_validated

    return None

if __name__ == "__main__":
    run_ingestion()