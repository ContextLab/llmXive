import os
import sys
import logging
import argparse
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_paths, get_config, set_random_seed
from logger import get_logger
from download_data import main as download_main
from preprocessing import main as preprocess_main
from feature_extraction import main as features_main
from classification import main as classify_main
from collinearity_analysis import main as collinearity_main

class DataIntegrityError(Exception):
    """Raised when data source verification fails."""
    pass

def verify_data_source():
    """Verify that metadata.json exists and contains a valid data source URL."""
    paths = get_paths()
    metadata_path = paths["processed"] / "metadata.json"
    
    if not metadata_path.exists():
        # Allow execution to proceed if metadata doesn't exist yet (pre-download)
        return True
        
    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        if "data_source_url" not in metadata:
            raise DataIntegrityError("metadata.json exists but 'data_source_url' is missing.")
        
        source_url = metadata["data_source_url"]
        if "synthetic" in source_url.lower() or "mock" in source_url.lower():
            raise DataIntegrityError(f"Detected synthetic data source: {source_url}")
            
        return True
    except json.JSONDecodeError:
        raise DataIntegrityError("metadata.json is corrupted.")

def get_paths():
    return get_paths()

def run_download(args):
    """Run the download task."""
    set_random_seed(get_config()["SEED"])
    return download_main()

def run_preprocess(args):
    """Run the preprocessing task."""
    set_random_seed(get_config()["SEED"])
    return preprocess_main()

def run_features(args):
    """Run the feature extraction task."""
    set_random_seed(get_config()["SEED"])
    return features_main()

def run_classify(args):
    """Run the classification task."""
    set_random_seed(get_config()["SEED"])
    return classify_main()

def run_collinearity(args):
    """Run the collinearity analysis task (T024b)."""
    set_random_seed(get_config()["SEED"])
    return collinearity_main()

def main():
    parser = argparse.ArgumentParser(description="Neural Correlates Pipeline")
    parser.add_argument("--task", type=str, required=True,
                      choices=["download", "preprocess", "features", "classify", "collinearity", "all"],
                      help="Task to run")
    parser.add_argument("--dataset", type=str, default="ds0001171", help="OpenNeuro dataset ID")
    parser.add_argument("--timing", action="store_true", help="Print timing information")
    
    args = parser.parse_args()
    
    logger = get_logger("main")
    start_time = time.time()
    
    try:
        if args.task == "all":
            # Verify data source before proceeding
            verify_data_source()
            
            logger.info("Running full pipeline...")
            run_download(args)
            run_preprocess(args)
            run_features(args)
            run_collinearity(args)
            run_classify(args)
        else:
            if args.task == "download":
                run_download(args)
            elif args.task == "preprocess":
                verify_data_source()
                run_preprocess(args)
            elif args.task == "features":
                verify_data_source()
                run_features(args)
            elif args.task == "collinearity":
                verify_data_source()
                run_collinearity(args)
            elif args.task == "classify":
                verify_data_source()
                run_classify(args)
                
        elapsed = time.time() - start_time
        if args.timing:
            print(f"Total execution time: {elapsed:.2f} seconds")
            
        logger.info(f"Task '{args.task}' completed successfully in {elapsed:.2f}s")
        return 0
        
    except DataIntegrityError as e:
        logger.error(f"Data integrity check failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())