import sys
import argparse
import logging
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.loader import (
    DataFetchError,
    fetch_dataset_from_hf,
    fetch_dataset_from_url,
    process_and_validate,
    compute_sha256
)
from data.dataset_registry import update_registry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    parser = argparse.ArgumentParser(description="CLI for data loading and validation")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset identifier (name or URL)")
    parser.add_argument("--mode", type=str, choices=["download", "validate", "full"], default="download", help="Mode of operation")
    parser.add_argument("--source_type", type=str, default="hf", choices=["hf", "url"], help="Source type (HuggingFace or URL)")
    parser.add_argument("--output_dir", type=str, default="data/raw", help="Directory to save raw data")
    parser.add_argument("--registry", type=str, default="data/dataset_registry.yaml", help="Path to dataset registry")
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    try:
        if args.mode == "download":
            logger.info(f"Starting download for dataset: {args.dataset}")
            
            # Dispatch to correct fetcher based on source_type
            if args.source_type == "hf":
                file_path = fetch_dataset_from_hf(args.dataset, args.output_dir)
            elif args.source_type == "url":
                file_path = fetch_dataset_from_url(args.dataset, args.output_dir)
            else:
                raise ValueError(f"Unknown source_type: {args.source_type}")
            
            if file_path is None:
                raise DataFetchError(f"Failed to download dataset: {args.dataset}")
            
            # Validate the downloaded file
            logger.info("Validating downloaded file...")
            df = process_and_validate(file_path)
            
            # Compute checksum
            checksum = compute_sha256(file_path)
            logger.info(f"Checksum: {checksum}")
            
            # Update registry
            update_registry(args.registry, args.dataset, str(file_path), checksum, args.source_type)
            
            logger.info(f"Download and validation successful: {file_path}")
            
        elif args.mode == "validate":
            if not Path(args.dataset).exists():
                logger.error(f"File not found: {args.dataset}")
                sys.exit(1)
            df = process_and_validate(args.dataset)
            logger.info("Validation successful.")
        
        elif args.mode == "full":
            # Load all from registry
            from data.loader import load_all_datasets
            datasets = load_all_datasets(args.registry, args.output_dir)
            logger.info(f"Successfully loaded {len(datasets)} datasets.")

    except DataFetchError as e:
        logger.error(f"DataFetchError: {e}")
        # Re-raise so the orchestrator (main.py) can catch and skip
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
