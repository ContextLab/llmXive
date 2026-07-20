"""
Orchestration script for the Zero-Shot Drift Detection pipeline.

This script runs the full scoring pipeline:
1. Validates data integrity.
2. Builds taxonomy centroids (if not present or forced).
3. Runs batch drift scoring on logs.
4. Exports results to CSV.

Usage:
    python code/main.py
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to path to ensure imports work when running from root
# or if this script is executed directly from the code directory.
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import set_seed, ensure_directories, get_path, get_config
from taxonomy_builder import main as build_taxonomy
from drift_scoring import main as run_drift_scoring
from data_loader import validate_data_integrity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("main")

def run_pipeline():
    """
    Executes the full drift detection pipeline.
    """
    logger.info("Starting Zero-Shot Drift Detection Pipeline...")
    
    # Load configuration
    config = get_config()
    logger.info(f"Loaded configuration: {config.get('summary', 'N/A')}")

    # 1. Initialize paths and ensure directories exist
    ensure_directories()
    logger.info("Ensured required directories exist.")

    # 2. Set random seeds for reproducibility
    set_seed(config.get('random_seed', 42))
    logger.info("Random seeds set.")

    # 3. Validate raw data integrity
    # This ensures that AdvBench, HF4, and Taxonomy files are present and valid
    # before proceeding to heavy computation.
    logger.info("Validating raw data integrity...")
    try:
        validate_data_integrity()
        logger.info("Data integrity check passed.")
    except Exception as e:
        logger.error(f"Data integrity check failed: {e}")
        logger.error("Pipeline aborted. Please ensure raw data is downloaded and checksums match.")
        return False

    # 4. Build Taxonomy Centroids
    # This step generates the reference embeddings for the taxonomy categories.
    # It checks for existing centroids and regenerates if necessary or if forced.
    logger.info("Running Taxonomy Builder...")
    try:
        build_taxonomy()
        logger.info("Taxonomy centroids built successfully.")
    except Exception as e:
        logger.error(f"Taxonomy building failed: {e}")
        logger.error("Pipeline aborted. Centroids are required for scoring.")
        return False

    # 5. Run Drift Scoring
    # This is the core step: loading logs, computing cosine distances, and exporting results.
    logger.info("Running Drift Scoring...")
    try:
        run_drift_scoring()
        logger.info("Drift scoring completed successfully.")
    except Exception as e:
        logger.error(f"Drift scoring failed: {e}")
        logger.error("Pipeline aborted. Check logs for details.")
        return False

    logger.info("Pipeline completed successfully.")
    return True

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)