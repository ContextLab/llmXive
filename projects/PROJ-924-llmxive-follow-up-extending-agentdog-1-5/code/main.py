"""
Main orchestration script for the Zero-Shot Drift Detection pipeline.

This script orchestrates the full scoring pipeline:
1. Validates data integrity
2. Loads taxonomy centroids
3. Processes logs to compute drift scores
4. Exports results to CSV
"""
import sys
import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import project modules
from config import set_seed, get_config, get_path, ensure_directories, get_batch_size
from data_loader import (
    LoudFailureError,
    validate_data_integrity,
    fetch_advbench,
    fetch_hf4,
    fetch_taxonomy
)
from taxonomy_builder import main as build_taxonomy_main
from drift_scoring import (
    load_centroids,
    batch_process_logs,
    export_results
)
from utils import load_json_file, save_json_file

def run_data_validation(config: Dict[str, Any]) -> bool:
    """
    Validate that all required data files exist and have correct checksums.
    
    Returns:
        bool: True if validation passes, False otherwise
    """
    logger.info("Running data integrity validation...")
    try:
        validate_data_integrity()
        logger.info("Data integrity validation passed.")
        return True
    except LoudFailureError as e:
        logger.error(f"Data validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during data validation: {e}")
        return False

def run_taxonomy_building(config: Dict[str, Any]) -> bool:
    """
    Build taxonomy centroids if they don't exist or are outdated.
    
    Returns:
        bool: True if taxonomy building passes, False otherwise
    """
    logger.info("Checking taxonomy centroids...")
    centroid_path = get_path("centroid_file")
    
    if not centroid_path.exists():
        logger.info(f"Centroid file not found at {centroid_path}. Building taxonomy...")
        try:
            build_taxonomy_main()
            logger.info("Taxonomy building completed successfully.")
            return True
        except LoudFailureError as e:
            logger.error(f"Taxonomy building failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during taxonomy building: {e}")
            return False
    else:
        logger.info(f"Centroid file exists at {centroid_path}. Skipping taxonomy building.")
        return True

def run_drift_scoring(config: Dict[str, Any]) -> bool:
    """
    Run the full drift scoring pipeline.
    
    Returns:
        bool: True if scoring completes successfully, False otherwise
    """
    logger.info("Starting drift scoring pipeline...")
    
    try:
        # Load centroids
        logger.info("Loading taxonomy centroids...")
        centroids = load_centroids()
        if not centroids:
            logger.error("Failed to load centroids. Aborting.")
            return False
        logger.info(f"Loaded {len(centroids)} centroids.")
        
        # Fetch and process logs
        logger.info("Fetching and processing logs...")
        all_logs = []
        
        # Fetch AdvBench data
        try:
            advbench_logs = fetch_advbench()
            logger.info(f"Fetched {len(advbench_logs)} logs from AdvBench.")
            all_logs.extend(advbench_logs)
        except Exception as e:
            logger.warning(f"Failed to fetch AdvBench data: {e}. Continuing without it.")
        
        # Fetch HF4 data
        try:
            hf4_logs = fetch_hf4()
            logger.info(f"Fetched {len(hf4_logs)} logs from HF4.")
            all_logs.extend(hf4_logs)
        except Exception as e:
            logger.warning(f"Failed to fetch HF4 data: {e}. Continuing without it.")
        
        if not all_logs:
            logger.error("No logs available for processing. Aborting.")
            return False
        
        logger.info(f"Total logs to process: {len(all_logs)}")
        
        # Process logs in batches
        logger.info("Processing logs in batches...")
        batch_size = get_batch_size()
        results = batch_process_logs(all_logs, centroids, batch_size)
        
        if not results:
            logger.error("Drift scoring produced no results. Aborting.")
            return False
        
        logger.info(f"Processed {len(results)} logs.")
        
        # Export results
        logger.info("Exporting results to CSV...")
        output_path = get_path("drift_scores_csv")
        export_results(results, output_path)
        
        logger.info(f"Results exported to {output_path}")
        return True
        
    except LoudFailureError as e:
        logger.error(f"Drift scoring failed with LoudFailure: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during drift scoring: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False

def main() -> int:
    """
    Main entry point for the orchestration script.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("=" * 60)
    logger.info("Starting Zero-Shot Drift Detection Pipeline")
    logger.info("=" * 60)
    
    try:
        # Initialize configuration
        config = get_config()
        set_seed(config.get('random_seed', 42))
        
        # Ensure required directories exist
        ensure_directories()
        logger.info("Directories ensured.")
        
        # Step 1: Data Validation
        if not run_data_validation(config):
            logger.error("Data validation failed. Aborting pipeline.")
            return 1
        
        # Step 2: Taxonomy Building (if needed)
        if not run_taxonomy_building(config):
            logger.error("Taxonomy building failed. Aborting pipeline.")
            return 1
        
        # Step 3: Drift Scoring
        if not run_drift_scoring(config):
            logger.error("Drift scoring failed. Aborting pipeline.")
            return 1
        
        logger.info("=" * 60)
        logger.info("Pipeline completed successfully!")
        logger.info("=" * 60)
        return 0
        
    except KeyboardInterrupt:
        logger.error("Pipeline interrupted by user.")
        return 130
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())