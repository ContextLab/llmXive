import os
import sys
import logging
import argparse
import time
import json
from pathlib import Path

from config import get_config, set_random_seed, ensure_directories
from logger import get_logger
from preprocessing import download_dataset, preprocess_pipeline, EventSourceError, SampleSizeError
from feature_extraction import run_extraction
from classification import run_classification
from verify_dataset import run_verification

logger = get_logger(__name__)

class DataIntegrityError(Exception):
    """Raised when data source verification fails."""
    pass

def verify_data_source(metadata_path: str = None) -> bool:
    """Verify that metadata.json exists and contains valid data source info."""
    cfg = get_config()
    paths = get_paths()
    metadata_path = metadata_path or str(paths.processed / 'metadata.json')
    
    if not os.path.exists(metadata_path):
        logger.warning("metadata.json not found. Skipping data source verification.")
        return True  # Allow execution to proceed to download
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Check for required fields
    if 'data_source_url' not in metadata:
        raise DataIntegrityError("data_source_url missing in metadata.json")
    
    if 'fetch_method' not in metadata:
        raise DataIntegrityError("fetch_method missing in metadata.json")
    
    # Check for synthetic indicators
    source_url = metadata.get('data_source_url', '')
    if 'synthetic' in source_url.lower() or 'fake' in source_url.lower():
        raise DataIntegrityError(f"Synthetic data source detected: {source_url}")
    
    logger.info(f"Data source verified: {metadata['data_source_url']}")
    return True

def get_paths():
    """Get resolved Path objects."""
    cfg = get_config()
    return {
        'raw': Path(cfg['DATA_PATH']),
        'processed': Path(cfg['OUTPUT_PATH']),
        'figures': Path(cfg['OUTPUT_PATH']) / 'figures',
        'logs': Path('logs')
    }

def run_download(args):
    """Run dataset download task."""
    logger.info("=== Download Task ===")
    set_random_seed()
    ensure_directories()
    
    dataset_id = args.dataset or get_config().get('OPENNEURO_DATASET', 'ds0001171')
    data_path = download_dataset(dataset_id)
    logger.info(f"Download complete: {data_path}")

def run_preprocess(args):
    """Run preprocessing task."""
    logger.info("=== Preprocessing Task ===")
    set_random_seed()
    ensure_directories()
    
    # Verify data source before preprocessing
    verify_data_source()
    
    cfg = get_config()
    dataset_id = args.dataset or cfg.get('OPENNEURO_DATASET', 'ds0001171')
    
    # Check if dataset exists
    paths = get_paths()
    dataset_dir = paths.raw / dataset_id
    if not dataset_dir.exists():
        logger.info("Dataset not found, downloading...")
        download_dataset(dataset_id)
    
    metadata = preprocess_pipeline(str(dataset_dir), cfg['OUTPUT_PATH'])
    logger.info(f"Preprocessing complete. Epochs: {metadata.get('epoch_count', 0)}")

def run_features(args):
    """Run feature extraction task."""
    logger.info("=== Feature Extraction Task ===")
    set_random_seed()
    ensure_directories()
    
    # Verify data source
    verify_data_source()
    
    run_extraction()

def run_classify(args):
    """Run classification task."""
    logger.info("=== Classification Task ===")
    set_random_seed()
    ensure_directories()
    
    # Verify data source
    verify_data_source()
    
    run_classification()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Neural Correlates Pipeline")
    parser.add_argument('--task', choices=['download', 'preprocess', 'features', 'classify', 'all'],
                      default='all', help='Task to run')
    parser.add_argument('--dataset', type=str, help='OpenNeuro dataset ID')
    parser.add_argument('--timing', action='store_true', help='Print timing information')
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    try:
        if args.task == 'download':
            run_download(args)
        elif args.task == 'preprocess':
            run_preprocess(args)
        elif args.task == 'features':
            run_features(args)
        elif args.task == 'classify':
            run_classify(args)
        elif args.task == 'all':
            run_download(args)
            run_preprocess(args)
            run_features(args)
            run_classify(args)
        
        elapsed = time.time() - start_time
        if args.timing:
            print(f"Total execution time: {elapsed:.2f} seconds")
        
        logger.info("Pipeline completed successfully")
        
    except DataIntegrityError as e:
        logger.error(f"Data integrity error: {e}")
        sys.exit(1)
    except EventSourceError as e:
        logger.error(f"Event source error: {e}")
        sys.exit(1)
    except SampleSizeError as e:
        logger.error(f"Sample size error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()