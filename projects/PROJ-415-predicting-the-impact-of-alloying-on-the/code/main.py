import os
import sys
import logging
import time
from pathlib import Path
import json

# Add project root to path if not already present
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories, set_global_seed
from utils.logging import get_logger
from utils.resource_monitor import monitor, log_resource_usage, save_resource_report
from data.acquisition import acquire_and_save_diffusion_data
from data.ingestion import load_and_filter
from data.curation import run_curation
from models.training import main as train_models
from validation.stats import main as run_validation_stats
from validation.sensitivity import main as run_sensitivity_analysis

logger = get_logger(__name__)

def main() -> None:
    """
    Orchestrates the full pipeline:
    Ingestion -> Features -> Training -> Validation
    Integrates Resource Monitoring at key stages.
    """
    logger.info("Starting Pipeline Execution")
    start_time = time.time()

    # 1. Setup
    ensure_directories()
    set_global_seed(42)
    log_resource_usage("Pipeline_Start")

    try:
        # 2. Data Acquisition
        logger.info("Phase: Data Acquisition")
        log_resource_usage("Acquisition_Start")
        acquire_and_save_diffusion_data()
        log_resource_usage("Acquisition_End")

        # 3. Data Ingestion
        logger.info("Phase: Data Ingestion")
        log_resource_usage("Ingestion_Start")
        load_and_filter()
        log_resource_usage("Ingestion_End")

        # 4. Data Curation
        logger.info("Phase: Data Curation")
        log_resource_usage("Curation_Start")
        run_curation()
        log_resource_usage("Curation_End")

        # 5. Model Training
        logger.info("Phase: Model Training")
        log_resource_usage("Training_Start")
        train_models()
        log_resource_usage("Training_End")

        # 6. Validation & Sensitivity
        logger.info("Phase: Validation")
        log_resource_usage("Validation_Start")
        run_validation_stats()
        run_sensitivity_analysis()
        log_resource_usage("Validation_End")

    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        raise
    finally:
        # Always save resource report
        end_time = time.time()
        logger.info(f"Pipeline Execution Time: {end_time - start_time:.2f} seconds")
        log_resource_usage("Pipeline_End")
        save_resource_report()
        logger.info("Resource usage report saved.")

if __name__ == "__main__":
    main()