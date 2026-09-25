import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

# Logging setup
def setup_logging(log_file=None):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    return logger

def setup_directories(base_dir):
    """Ensure required directories exist."""
    raw_dir = Path(base_dir) / 'data' / 'raw'
    processed_dir = Path(base_dir) / 'data' / 'processed'
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir, processed_dir

def load_and_align_data(input_path, output_path, exclusions_log_path, chunk_size=10000):
    """
    Load raw data in chunks to manage memory usage, validate columns,
    align data, and write to processed output.
    
    Args:
        input_path: Path to the input parquet file.
        output_path: Path to write the processed parquet file.
        exclusions_log_path: Path to write exclusions log.
        chunk_size: Number of rows per chunk for streaming.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting chunked ingestion from {input_path}")
    
    required_columns = [
        'image_path', 'species_id', 'prompt_text', 
        'teacher_scores', 'student_scalar', 'human_annotations', 'primary_dimension'
    ]
    
    excluded_samples = []
    processed_chunks = []
    total_rows = 0
    
    # Read in chunks using pyarrow for memory efficiency
    try:
        parquet_file = pq.ParquetFile(input_path)
    except Exception as e:
        logger.error(f"Failed to open parquet file: {e}")
        raise

    for i, batch in enumerate(parquet_file.iter_batches(batch_size=chunk_size)):
        logger.info(f"Processing chunk {i+1}")
        df_chunk = batch.to_pandas()
        total_rows += len(df_chunk)
        
        # Validate required columns exist
        missing_cols = set(required_columns) - set(df_chunk.columns)
        if missing_cols:
            logger.error(f"Missing required columns in chunk: {missing_cols}")
            # In a real scenario, we might handle this differently, but for now raise
            raise ValueError(f"Missing columns: {missing_cols}")
        
        # Align and filter: Check for missing student_scalar
        # Mark samples missing student_scalar
        mask_missing = df_chunk['student_scalar'].isna()
        if mask_missing.any():
            missing_indices = df_chunk[mask_missing].index.tolist()
            excluded_samples.extend([
                {'sample_id': idx, 'excluded_reason': 'missing_student_scalar'} 
                for idx in missing_indices
            ])
            logger.info(f"Excluded {mask_missing.sum()} samples in chunk {i+1} due to missing student_scalar")
        
        # Filter out rows with missing student_scalar for the output
        df_valid = df_chunk.dropna(subset=['student_scalar'])
        
        # Optional: Add other alignment checks if needed (e.g., primary_dimension validity)
        # For now, we assume primary_dimension is derived earlier or present
        
        processed_chunks.append(df_valid)
    
    if not processed_chunks:
        logger.warning("No valid data chunks found.")
        # Create empty dataframe with expected schema
        final_df = pd.DataFrame(columns=required_columns)
    else:
        final_df = pd.concat(processed_chunks, ignore_index=True)
    
    logger.info(f"Total rows processed: {total_rows}, Valid rows: {len(final_df)}")
    
    # Save exclusions log
    exclusions_log_dir = Path(exclusions_log_path).parent
    exclusions_log_dir.mkdir(parents=True, exist_ok=True)
    with open(exclusions_log_path, 'w') as f:
        json.dump(excluded_samples, f, indent=2)
    
    # Write output
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    final_df.to_parquet(output_path, index=False)
    logger.info(f"Saved aligned data to {output_path}")
    
    return final_df, excluded_samples

def print_summary(df, exclusions):
    """Print summary statistics."""
    logger = logging.getLogger(__name__)
    logger.info("=== Ingestion Summary ===")
    logger.info(f"Total samples loaded: {len(df)}")
    logger.info(f"Total exclusions: {len(exclusions)}")
    if 'primary_dimension' in df.columns:
        dim_counts = df['primary_dimension'].value_counts()
        logger.info("Primary dimension distribution:")
        for dim, count in dim_counts.items():
            logger.info(f"  Dimension {dim}: {count}")
    if 'teacher_scores' in df.columns:
        # teacher_scores is likely a list/array column, check non-null
        logger.info(f"Samples with teacher_scores: {df['teacher_scores'].notna().sum()}")
    if 'human_annotations' in df.columns:
        logger.info(f"Samples with human_annotations: {df['human_annotations'].notna().sum()}")

def parse_args():
    parser = argparse.ArgumentParser(description="Chunked Ingestion and Alignment Pipeline")
    parser.add_argument('--input', type=str, required=True, help='Path to input parquet file')
    parser.add_argument('--output', type=str, default='data/processed/raw_data.parquet', help='Path to output parquet file')
    parser.add_argument('--exclusions-log', type=str, default='data/processed/exclusions_log.json', help='Path to exclusions log')
    parser.add_argument('--chunk-size', type=int, default=10000, help='Number of rows per chunk')
    parser.add_argument('--log-file', type=str, default=None, help='Path to log file')
    return parser.parse_args()

def main():
    args = parse_args()
    logger = setup_logging(args.log_file)
    
    # Determine base directory (assuming project root is parent of code/)
    base_dir = Path(__file__).resolve().parent.parent
    
    raw_dir, processed_dir = setup_directories(base_dir)
    
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = base_dir / input_path
        
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = base_dir / output_path
        
    exclusions_log_path = Path(args.exclusions_log)
    if not exclusions_log_path.is_absolute():
        exclusions_log_path = base_dir / exclusions_log_path

    try:
        df, exclusions = load_and_align_data(
            str(input_path), 
            str(output_path), 
            str(exclusions_log_path), 
            chunk_size=args.chunk_size
        )
        print_summary(df, exclusions)
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()