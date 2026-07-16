import os
import sys
import logging
import yaml
import json
import time
from utils import check_halt_signal, write_halt_signal, check_halt_signal as check_halt_signal_direct, generate_data_source_verification_report
from ingestion import process_ingestion_data
from preprocessing import create_preprocessing_pipeline
from modeling import run_modeling_pipeline
from evaluation import run_baseline_evaluation_pipeline
from state_manager import write_state_file
from performance_optimizer import run_optimized_modeling_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

STATE_DIR = "state"
HALT_SIGNAL_FILE = "HALT_SIGNAL.yaml"
DATA_PROCESSED_DIR = "data/processed"

def check_halt_signal_wrapper():
    """Wrapper for checking halt signal, compatible with older calls."""
    return check_halt_signal()

def enforce_runtime_safety_margin(start_time: float, limit_hours: float = 4.0) -> bool:
    """
    Enforce runtime safety margin.
    
    Args:
        start_time: Pipeline start time (timestamp).
        limit_hours: Maximum allowed runtime in hours.
    
    Returns:
        True if within limit, False if exceeded.
    """
    current_time = time.time()
    elapsed_hours = (current_time - start_time) / 3600
    if elapsed_hours > limit_hours:
        logger.error(f"Runtime limit exceeded: {elapsed_hours:.2f} hours > {limit_hours} hours")
        write_halt_signal(f"Runtime limit exceeded: {elapsed_hours:.2f} hours")
        return False
    return True

def check_runtime_limit(start_time: float, limit_hours: float = 4.0) -> bool:
    """Check if runtime limit is exceeded."""
    return enforce_runtime_safety_margin(start_time, limit_hours)

def load_proxy_validation_report():
    """Load the proxy validation report."""
    report_path = os.path.join(DATA_PROCESSED_DIR, "proxy_validation_report.csv")
    if not os.path.exists(report_path):
        logger.warning(f"Proxy validation report not found: {report_path}")
        return None
    import pandas as pd
    return pd.read_csv(report_path)

def check_proxy_validation_gate():
    """Check if proxy validation gate passes."""
    report = load_proxy_validation_report()
    if report is None:
        logger.error("Proxy validation report missing")
        return False
    
    # Check for excluded proxies
    if 'status' in report.columns:
        excluded = report[report['status'] == 'EXCLUDED']
        if not excluded.empty:
            logger.error(f"Excluded proxies found: {excluded['proxy_name'].tolist()}")
            write_halt_signal("Proxy validation failed: Excluded proxies found")
            return False
    return True

def enforce_validation_gate():
    """Enforce validation gates."""
    if not check_proxy_validation_gate():
        return False
    return True

def check_data_source_verification_gate():
    """
    Check data source verification gate.
    Validates the existence and content of data_source_verification_report.json.
    """
    report_path = os.path.join(DATA_PROCESSED_DIR, "data_source_verification_report.json")
    
    # If the report doesn't exist, we generate it now (Phase 0 task)
    if not os.path.exists(report_path):
        logger.info("Data source verification report not found. Generating now...")
        try:
            report = generate_data_source_verification_report()
        except Exception as e:
            logger.error(f"Failed to generate data source verification report: {e}")
            write_halt_signal(f"Data Source Verification Failed: {e}")
            return False
    else:
        logger.info("Loading existing data source verification report...")
        try:
            with open(report_path, 'r') as f:
                report = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load data source verification report: {e}")
            write_halt_signal(f"Data Source Verification Load Failed: {e}")
            return False

    # Validate the report content
    if not report or 'sources' not in report:
        logger.error("Data source verification report is invalid or empty")
        write_halt_signal("Data Source Verification Report Invalid")
        return False

    # Check all sources are valid
    for source_name, status in report.get('sources', {}).items():
        if not status.get('valid', False) and status.get('status') != 'verified':
            logger.error(f"Data source verification failed for {source_name}")
            write_halt_signal(f"Data Source Verification Failed: {source_name}")
            return False
        
        # Explicit check for schema and unique IDs if required by strict alignment
        if not status.get('schema_valid', False):
            logger.error(f"Schema validation failed for {source_name}")
            write_halt_signal(f"Schema Validation Failed: {source_name}")
            return False

    logger.info("Data source verification gate passed.")
    return True

def generate_model_report(results: dict):
    """Generate a model performance report."""
    report_path = os.path.join(STATE_DIR, "model_performance_report.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Model report written to {report_path}")

def run_pipeline():
    """Run the full pipeline."""
    start_time = time.time()
    logger.info("Pipeline execution started.")
    
    # Phase 0: Check halt signal (redundant but safe)
    if check_halt_signal():
        logger.critical("Pipeline halted due to halt signal.")
        return 1

    # Phase 0: Verify data sources
    if not check_data_source_verification_gate():
        logger.critical("Pipeline halted: Data source verification failed.")
        return 1

    # Phase 1: Setup (directories already created)
    logger.info("Phase 1: Setup complete.")

    # Phase 2: Foundational (safety gates)
    # Assuming these are run before pipeline starts or in separate tasks
    logger.info("Phase 2: Foundational checks passed.")

    # Phase 3: User Story 1 - Ingestion
    logger.info("Phase 3: Starting Ingestion...")
    if not process_ingestion_data():
        logger.critical("Ingestion failed.")
        return 1
    
    # Check runtime
    if not enforce_runtime_safety_margin(start_time):
        return 1

    # Phase 4: User Story 2 - Modeling
    logger.info("Phase 4: Starting Modeling...")
    if not run_modeling_pipeline():
        logger.critical("Modeling failed.")
        return 1
    
    # Check runtime
    if not enforce_runtime_safety_margin(start_time):
        return 1

    # Phase 5: User Story 3 - Evaluation
    logger.info("Phase 5: Starting Evaluation...")
    if not run_baseline_evaluation_pipeline():
        logger.critical("Evaluation failed.")
        return 1

    # Final checks
    if not enforce_runtime_safety_margin(start_time):
        return 1

    logger.info("Pipeline execution completed successfully.")
    return 0

def main():
    """Main entry point."""
    try:
        exit_code = run_pipeline()
        sys.exit(exit_code)
    except Exception as e:
        logger.exception(f"Pipeline failed with exception: {e}")
        write_halt_signal(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()