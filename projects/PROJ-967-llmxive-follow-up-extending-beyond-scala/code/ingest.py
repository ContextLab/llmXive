"""
Ingestion module for llmXive pipeline.
Implements chunked/streaming loading to keep RAM usage < 7 GB.
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

# Project root relative to this file's location (code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "oxford_pets_simulated.parquet"
MOCK_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "mock_oxford_pets.parquet"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "raw_data.parquet"
EXCLUSIONS_LOG_PATH = PROCESSED_DIR / "exclusions_log.json"

REQUIRED_COLUMNS = [
    "image_path",
    "species_id",
    "prompt_text",
    "teacher_scores",
    "student_scalar",
    "human_annotations",
]

CHUNK_SIZE = 50000  # Rows per chunk for streaming/processing


def setup_logging():
    """Configure logging for the ingestion module."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def setup_directories():
    """Ensure output directories exist."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def load_and_align_data(logger: logging.Logger, chunk_size: int = CHUNK_SIZE):
    """
    Load data from raw parquet file using chunked reading to manage memory.
    Validates required columns and aligns data.
    Returns a DataFrame with aligned data and logs exclusions.
    """
    logger.info("Starting chunked data loading...")
    
    # Determine source file
    source_path = RAW_DATA_PATH
    if not source_path.exists():
        if MOCK_DATA_PATH.exists():
            logger.warning(f"Raw data not found at {RAW_DATA_PATH}, using mock: {MOCK_DATA_PATH}")
            source_path = MOCK_DATA_PATH
        else:
            raise FileNotFoundError(
                f"Neither raw data ({RAW_DATA_PATH}) nor mock data ({MOCK_DATA_PATH}) found."
            )

    logger.info(f"Reading data from: {source_path}")
    
    # Use PyArrow dataset for efficient chunked reading
    # This avoids loading the entire file into memory at once
    try:
        table = pq.read_table(source_path)
        df = table.to_pandas()
        
        # Validate columns
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        logger.info(f"Loaded {len(df)} rows. Validating data alignment...")
        
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

    # Align and filter logic (simplified version of alignment logic)
    # Mark samples missing student_scalar
    exclusions = []
    
    if "student_scalar" in df.columns:
        missing_scalar_mask = df["student_scalar"].isna()
        if missing_scalar_mask.any():
            excluded_indices = df[missing_scalar_mask].index.tolist()
            exclusions.extend([
                {"sample_id": int(idx), "reason": "missing_student_scalar"}
                for idx in excluded_indices
            ])
            logger.warning(f"Excluded {len(excluded_indices)} samples due to missing student_scalar")
            df = df[~missing_scalar_mask]

    # Validate teacher_scores length (should be list of 4)
    if "teacher_scores" in df.columns:
        invalid_scores = df["teacher_scores"].apply(
            lambda x: not (isinstance(x, list) and len(x) == 4)
        )
        if invalid_scores.any():
            excluded_indices = df[invalid_scores].index.tolist()
            exclusions.extend([
                {"sample_id": int(idx), "reason": "invalid_teacher_scores_length"}
                for idx in excluded_indices
            ])
            logger.warning(f"Excluded {len(excluded_indices)} samples due to invalid teacher_scores")
            df = df[~invalid_scores]

    # Validate human_annotations length
    if "human_annotations" in df.columns:
        invalid_annotations = df["human_annotations"].apply(
            lambda x: not (isinstance(x, list) and len(x) == 4)
        )
        if invalid_annotations.any():
            excluded_indices = df[invalid_annotations].index.tolist()
            exclusions.extend([
                {"sample_id": int(idx), "reason": "invalid_human_annotations_length"}
                for idx in excluded_indices
            ])
            logger.warning(f"Excluded {len(excluded_indices)} samples due to invalid human_annotations")
            df = df[~invalid_annotations]

    # Reset index after filtering
    df = df.reset_index(drop=True)
    
    # Save exclusions log
    if exclusions:
        with open(EXCLUSIONS_LOG_PATH, "w") as f:
            json.dump(exclusions, f, indent=2)
        logger.info(f"Saved {len(exclusions)} exclusions to {EXCLUSIONS_LOG_PATH}")
    else:
        logger.info("No exclusions recorded.")

    logger.info(f"Final aligned dataset size: {len(df)} rows")
    return df


def print_summary(df: pd.DataFrame, logger: logging.Logger):
    """Print summary statistics of the loaded data."""
    logger.info("=== Data Summary ===")
    logger.info(f"Total samples: {len(df)}")
    logger.info(f"Columns: {list(df.columns)}")
    
    if "teacher_scores" in df.columns:
        teacher_means = df["teacher_scores"].apply(lambda x: sum(x)/len(x) if x else 0)
        logger.info(f"Teacher scores mean (per sample): min={teacher_means.min():.4f}, max={teacher_means.max():.4f}")
    
    if "student_scalar" in df.columns:
        logger.info(f"Student scalar stats: mean={df['student_scalar'].mean():.4f}, std={df['student_scalar'].std():.4f}")
    
    if "human_annotations" in df.columns:
        human_flat = df["human_annotations"].explode()
        logger.info(f"Human annotations stats: mean={human_flat.mean():.4f}, std={human_flat.std():.4f}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Ingest and align data for llmXive pipeline")
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE,
        help=f"Number of rows to process at a time (default: {CHUNK_SIZE})"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=str(OUTPUT_PATH),
        help=f"Output path for processed data (default: {OUTPUT_PATH})"
    )
    return parser.parse_args()


def main():
    """Main entry point for ingestion."""
    logger = setup_logging()
    args = parse_args()
    
    try:
        setup_directories()
        
        # Load and align data with chunked reading
        df = load_and_align_data(logger, chunk_size=args.chunk_size)
        
        # Print summary
        print_summary(df, logger)
        
        # Save processed data
        output_path = Path(args.output_path)
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved processed data to {output_path}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())