import argparse
import json
import logging
import os
import sys
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def setup_directories(logger):
    base_dir = Path(__file__).resolve().parent.parent
    data_raw_dir = base_dir / "data" / "raw"
    data_processed_dir = base_dir / "data" / "processed"
    
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    data_processed_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Directories ready: {data_raw_dir}, {data_processed_dir}")
    return data_raw_dir, data_processed_dir

def load_and_align_data(logger, input_path, output_path, chunk_size=10000):
    """
    Load data using chunked/streaming reading to keep RAM usage < 7GB.
    Validates required columns and writes aligned data to output_path.
    
    Args:
        logger: Logger instance
        input_path: Path to input parquet file
        output_path: Path to write processed parquet file
        chunk_size: Number of rows to process at a time
    
    Returns:
        tuple: (total_samples, valid_samples, excluded_count)
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    required_columns = [
        'image_path', 'species_id', 'teacher_scores', 'student_scalar', 
        'human_annotations', 'primary_dimension'
    ]
    
    total_samples = 0
    valid_samples = 0
    excluded_count = 0
    excluded_reasons = []
    
    logger.info(f"Starting chunked load from {input_path} with chunk_size={chunk_size}")
    
    # Use PyArrow's parquet file reader for efficient chunked reading
    parquet_file = pq.ParquetFile(input_path)
    
    writer = None
    
    for batch in parquet_file.iter_batches(batch_size=chunk_size):
        batch_df = batch.to_pandas()
        total_samples += len(batch_df)
        logger.info(f"Processing batch of {len(batch_df)} rows (Total: {total_samples})")
        
        # Validate required columns exist
        missing_cols = set(required_columns) - set(batch_df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns in batch: {missing_cols}")
        
        # Filter out rows with missing student_scalar (alignment check)
        valid_mask = batch_df['student_scalar'].notna()
        batch_valid = batch_df[valid_mask]
        batch_excluded = batch_df[~valid_mask]
        
        valid_samples += len(batch_valid)
        excluded_count += len(batch_excluded)
        
        if len(batch_excluded) > 0:
            for idx in batch_excluded.index:
                excluded_reasons.append({
                    'sample_id': int(batch_excluded.loc[idx, 'image_path'].split('/')[-1].split('.')[0]) if isinstance(batch_excluded.loc[idx, 'image_path'], str) else idx,
                    'reason': 'missing_student_scalar'
                })
        
        # Write valid batch to output
        if writer is None:
            # Initialize writer with schema from first valid batch
            if len(batch_valid) > 0:
                writer = pq.ParquetWriter(output_path, batch_valid.to_pyarrow_table().schema)
        
        if len(batch_valid) > 0:
            writer.write_table(batch_valid.to_pyarrow_table())
    
    if writer is not None:
        writer.close()
    
    logger.info(f"Chunked loading complete: {total_samples} total, {valid_samples} valid, {excluded_count} excluded")
    
    # Save exclusions log if any
    if excluded_reasons:
        exclusions_path = output_path.parent / 'exclusions_log.json'
        with open(exclusions_path, 'w') as f:
            json.dump(excluded_reasons, f, indent=2)
        logger.info(f"Exclusions log written to {exclusions_path}")
    
    return total_samples, valid_samples, excluded_count

def print_summary(logger, total, valid, excluded):
    logger.info("=" * 60)
    logger.info("INGESTION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total samples processed: {total}")
    logger.info(f"Valid samples (aligned): {valid}")
    logger.info(f"Excluded samples: {excluded}")
    if total > 0:
        logger.info(f"Valid rate: {valid/total:.2%}")
    logger.info("=" * 60)

def parse_args():
    parser = argparse.ArgumentParser(description="Chunked data ingestion with alignment")
    parser.add_argument(
        "--input",
        type=str,
        default="data/raw/oxford_pets_simulated.parquet",
        help="Path to input parquet file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/raw_data.parquet",
        help="Path to output processed parquet file"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=10000,
        help="Number of rows to process per chunk"
    )
    return parser.parse_args()

def main():
    logger = setup_logging()
    args = parse_args()
    
    base_dir = Path(__file__).resolve().parent.parent
    input_path = base_dir / args.input
    output_path = base_dir / args.output
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    total, valid, excluded = load_and_align_data(
        logger, 
        str(input_path), 
        str(output_path), 
        args.chunk_size
    )
    
    print_summary(logger, total, valid, excluded)
    
    # Save sample count metadata
    metadata = {
        "total_samples": total,
        "valid_samples": valid,
        "excluded_count": excluded,
        "input_file": str(input_path),
        "output_file": str(output_path),
        "chunk_size": args.chunk_size
    }
    
    metadata_path = base_dir / "data" / "processed" / "valid_sample_count.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata written to {metadata_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())