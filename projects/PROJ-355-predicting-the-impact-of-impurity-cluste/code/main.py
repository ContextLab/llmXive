"""
Pipeline orchestration for predicting the impact of impurity clustering on grain boundary segregation.

This script defines the logical sequence of the research pipeline:
1. Download bulk configurations
2. Build GB supercells
3. Compute descriptors
4. Run simulation (segregation energy)

It handles errors gracefully, specifically catching [DATA_UNAVAILABLE] errors from the download step.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

# Import pipeline stages
# Note: These modules are expected to exist as per the project structure
from data.download import download_bulk_configs, main as download_main
from data.gb_builder import build_gb_supercell, main as gb_builder_main
from data.descriptors import run_descriptor_computation, main as descriptors_main
from data.simulate_energy import run_simulation, main as simulate_main
from config import get_project_root, get_data_paths

def run_pipeline():
    """
    Execute the full research pipeline with error handling.
    
    Logical Sequence:
    1. download_bulk_configs -> 2. build_gb_supercells -> 
    3. compute_descriptors -> 4. run_simulation
    """
    project_root = get_project_root()
    data_paths = get_data_paths()
    
    logger.info("Starting Impurity Clustering Segregation Pipeline")
    logger.info(f"Project Root: {project_root}")
    
    try:
        # Step 1: Download Bulk Configurations
        logger.info("Step 1: Downloading bulk configurations...")
        # The download module handles its own validation and retry logic.
        # We call the main entry point which returns the path to downloaded data or raises an error.
        # If [DATA_UNAVAILABLE] occurs, it raises ValueError which we catch here.
        try:
            # Assuming the download_main returns a path or modifies data/raw directly
            # We rely on the module's internal logic to handle the URL validation and fetching.
            download_main()
            logger.info("Step 1 completed: Bulk configurations downloaded.")
        except ValueError as e:
            if "[DATA_UNAVAILABLE]" in str(e):
                logger.error(f"Critical Error: {e}")
                logger.error("Pipeline aborted due to data unavailability.")
                return 1
            else:
                raise

        # Step 2: Build GB Supercells
        logger.info("Step 2: Building GB supercells...")
        # This step depends on Step 1 output
        gb_builder_main()
        logger.info("Step 2 completed: GB supercells constructed.")

        # Step 3: Compute Descriptors
        logger.info("Step 3: Computing clustering descriptors...")
        # This step depends on Step 2 output
        descriptors_main()
        logger.info("Step 3 completed: Descriptors computed.")

        # Step 4: Run Simulation (Segregation Energy)
        logger.info("Step 4: Running segregation energy simulation...")
        # This step depends on Step 2/3 output
        simulate_main()
        logger.info("Step 4 completed: Simulations finished.")

        logger.info("Pipeline completed successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Pipeline failed with unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_pipeline()
    sys.exit(exit_code)