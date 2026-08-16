import argparse
import csv
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
import zipfile
import io

try:
    from datasets import load_dataset
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    load_dataset = None

import pandas as pd

# Configure logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

logger = setup_logging()

def calculate_sha256(file_path):
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum(checksum, output_path):
    """Save checksum to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump({'checksum': checksum}, f, indent=2)
    logger.info(f"Checksum saved to {output_path}")

def verify_checksum(file_path, expected_checksum):
    """Verify file checksum."""
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def validate_columns(df, required_columns, required_properties):
    """
    Validate that the dataframe contains required columns and properties.
    
    Args:
        df: pandas DataFrame
        required_columns: list of required top-level column names
        required_properties: dict mapping column name to list of required nested keys
    
    Returns:
        tuple: (is_valid, missing_items)
    """
    missing_items = []
    
    # Check top-level columns
    for col in required_columns:
        if col not in df.columns:
            missing_items.append(f"Column: {col}")
    
    # Check nested properties
    for col, props in required_properties.items():
        if col in df.columns:
            # Check if it's an object/dict column
            if df[col].dtype == 'object':
                # Check a few rows to see if properties exist
                sample_valid = False
                for idx, val in df[col].dropna().head(5).items():
                    if isinstance(val, dict):
                        if all(p in val for p in props):
                            sample_valid = True
                            break
                if not sample_valid and len(df.dropna(subset=[col])) > 0:
                    missing_items.append(f"Column {col} missing properties: {props}")
            else:
                missing_items.append(f"Column {col} is not an object type")
        else:
            missing_items.append(f"Column: {col} (nested check skipped)")
    
    return len(missing_items) == 0, missing_items

def download_dataset(dataset_id, output_path):
    """
    Download dataset from Hugging Face Datasets.
    
    Args:
        dataset_id: Hugging Face dataset ID
        output_path: Path to save the parquet file
    
    Returns:
        pandas DataFrame or None
    """
    if not DATASETS_AVAILABLE:
        logger.error("datasets library not installed. Cannot download from Hugging Face.")
        return None
    
    try:
        logger.info(f"Attempting to load dataset: {dataset_id}")
        ds = load_dataset(dataset_id, split="train", streaming=False)
        df = ds.to_pandas()
        
        # Save to parquet
        df.to_parquet(output_path, index=False)
        logger.info(f"Dataset saved to {output_path}")
        logger.info(f"Dataset shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
        return df
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        return None

def download_from_local_archive(archive_path, output_path):
    """
    Download dataset from a local zip archive.
    
    Args:
        archive_path: Path to the local zip file
        output_path: Path to save the extracted parquet file
    
    Returns:
        pandas DataFrame or None
    """
    try:
        if not os.path.exists(archive_path):
            logger.error(f"Archive not found: {archive_path}")
            return None
        
        logger.info(f"Extracting dataset from local archive: {archive_path}")
        
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            # Find parquet files in the archive
            parquet_files = [f for f in zip_ref.namelist() if f.endswith('.parquet')]
            
            if not parquet_files:
                logger.error("No parquet files found in archive")
                return None
            
            # Extract first parquet file
            first_parquet = parquet_files[0]
            logger.info(f"Extracting: {first_parquet}")
            
            with zip_ref.open(first_parquet) as f:
                df = pd.read_parquet(f)
            
            # Save to output path
            df.to_parquet(output_path, index=False)
            logger.info(f"Dataset saved to {output_path}")
            logger.info(f"Dataset shape: {df.shape}")
            logger.info(f"Columns: {list(df.columns)}")
            
            return df
    except Exception as e:
        logger.error(f"Failed to extract dataset from archive: {e}")
        return None

def parse_args():
    parser = argparse.ArgumentParser(description="Download Z-Reward evaluation dataset")
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/raw',
        help='Output directory for downloaded dataset'
    )
    parser.add_argument(
        '--primary-id',
        type=str,
        default='z-reward/z-reward-v1',
        help='Primary Hugging Face dataset ID'
    )
    parser.add_argument(
        '--secondary-id',
        type=str,
        default='z-reward/z-reward-v2',
        help='Secondary Hugging Face dataset ID'
    )
    parser.add_argument(
        '--local-archive',
        type=str,
        default=None,
        help='Path to local zip archive (via Z_REWARD_ARCHIVE_PATH env var)'
    )
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    parquet_path = output_dir / 'z_reward.parquet'
    validation_log_path = output_dir / 'validation_log.json'
    
    validation_log = {
        'primary_id': args.primary_id,
        'secondary_id': args.secondary_id,
        'local_archive': args.local_archive,
        'attempts': [],
        'success': False,
        'error': None
    }
    
    # Required columns and properties based on schema
    required_columns = [
        'prompt', 
        'image_url', 
        'teacher_scores', 
        'student_scalar', 
        'human_annotations', 
        'primary_dimension'
    ]
    
    required_properties = {
        'teacher_scores': ['Alignment', 'Realism', 'Aesthetics', 'Plausibility'],
        'human_annotations': ['Alignment', 'Realism', 'Aesthetics', 'Plausibility']
    }
    
    # Try Primary Source
    logger.info(f"=== Attempt 1: Primary Dataset ID ===")
    df = download_dataset(args.primary_id, str(parquet_path))
    attempt_result = {
        'source': 'primary',
        'id': args.primary_id,
        'success': False,
        'error': None
    }
    
    if df is not None:
        is_valid, missing = validate_columns(df, required_columns, required_properties)
        attempt_result['valid'] = is_valid
        if not is_valid:
            attempt_result['missing'] = missing
            attempt_result['error'] = f"Schema validation failed: {missing}"
            # Remove file if invalid
            if parquet_path.exists():
                parquet_path.unlink()
            df = None
        else:
            attempt_result['success'] = True
            attempt_result['shape'] = list(df.shape)
            attempt_result['columns'] = list(df.columns)
            validation_log['success'] = True
    
    validation_log['attempts'].append(attempt_result)
    
    # Try Secondary Source if Primary failed
    if not validation_log['success']:
        logger.info(f"=== Attempt 2: Secondary Dataset ID ===")
        df = download_dataset(args.secondary_id, str(parquet_path))
        attempt_result = {
            'source': 'secondary',
            'id': args.secondary_id,
            'success': False,
            'error': None
        }
        
        if df is not None:
            is_valid, missing = validate_columns(df, required_columns, required_properties)
            attempt_result['valid'] = is_valid
            if not is_valid:
                attempt_result['missing'] = missing
                attempt_result['error'] = f"Schema validation failed: {missing}"
                if parquet_path.exists():
                    parquet_path.unlink()
                df = None
            else:
                attempt_result['success'] = True
                attempt_result['shape'] = list(df.shape)
                attempt_result['columns'] = list(df.columns)
                validation_log['success'] = True
        
        validation_log['attempts'].append(attempt_result)
    
    # Try Local Archive if both HF sources failed
    if not validation_log['success']:
        local_path = args.local_archive or os.environ.get('Z_REWARD_ARCHIVE_PATH')
        if local_path:
            logger.info(f"=== Attempt 3: Local Archive ===")
            df = download_from_local_archive(local_path, str(parquet_path))
            attempt_result = {
                'source': 'local_archive',
                'path': local_path,
                'success': False,
                'error': None
            }
            
            if df is not None:
                is_valid, missing = validate_columns(df, required_columns, required_properties)
                attempt_result['valid'] = is_valid
                if not is_valid:
                    attempt_result['missing'] = missing
                    attempt_result['error'] = f"Schema validation failed: {missing}"
                    if parquet_path.exists():
                        parquet_path.unlink()
                    df = None
                else:
                    attempt_result['success'] = True
                    attempt_result['shape'] = list(df.shape)
                    attempt_result['columns'] = list(df.columns)
                    validation_log['success'] = True
            
            validation_log['attempts'].append(attempt_result)
        else:
            validation_log['attempts'].append({
                'source': 'local_archive',
                'path': None,
                'success': False,
                'error': 'No local archive path provided'
            })
    
    # Final Check
    if not validation_log['success']:
        validation_log['error'] = "Real dataset not found. Pipeline cannot proceed without real data for reproducibility."
        logger.error(validation_log['error'])
        
        # Save validation log
        with open(validation_log_path, 'w') as f:
            json.dump(validation_log, f, indent=2)
        
        raise RuntimeError(validation_log['error'])
    
    # Save checksum
    checksum = calculate_sha256(str(parquet_path))
    checksum_path = output_dir / 'z_reward_checksum.json'
    save_checksum(checksum, str(checksum_path))
    
    # Final summary
    validation_log['final_shape'] = list(df.shape) if df is not None else None
    validation_log['final_columns'] = list(df.columns) if df is not None else None
    validation_log['checksum'] = checksum
    
    # Save validation log
    with open(validation_log_path, 'w') as f:
        json.dump(validation_log, f, indent=2)
    
    logger.info("=== Validation Complete ===")
    logger.info(f"Dataset successfully loaded and validated.")
    logger.info(f"Output saved to: {parquet_path}")
    logger.info(f"Validation log saved to: {validation_log_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
