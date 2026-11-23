import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from config import get_output_dir, get_repo_list, get_depth_limit
from utils.logging_utils import configure_logging, get_logger
from utils.memory_utils import (
    get_current_memory_mb, 
    check_memory_limit, 
    clear_memory,
    memory_limit_guard,
    MEMORY_LIMIT_MB
)
from data_collection import clone_repositories, process_all_repos
from metrics_calc import main as run_metrics_calculation
from statistical_analysis import main as run_statistical_analysis
from visualizations import main as run_visualizations
from state_manager import main as run_state_manager
from validate_quickstart import main as run_validation
from verify_associational_framing import main as verify_framing

logger = get_logger(__name__)


def setup_logging():
    """Configure logging for the entire pipeline."""
    configure_logging()
    logger.info("Logging system initialized")


def run_data_collection():
    """Execute the data collection phase."""
    logger.info("=" * 60)
    logger.info("PHASE 1: DATA COLLECTION")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    with memory_limit_guard(MEMORY_LIMIT_MB):
        repo_list = get_repo_list()
        logger.info(f"Processing {len(repo_list)} repositories")
        
        # Clone and process repositories
        process_all_repos()
        
        # Clear memory after data collection
        clear_memory()
    
    elapsed = time.time() - start_time
    logger.info(f"Data collection completed in {elapsed:.2f} seconds")
    logger.info(f"Current memory usage: {get_current_memory_mb():.2f} MB")
    
    return True


def run_metrics_calculation():
    """Execute the metrics calculation phase."""
    logger.info("=" * 60)
    logger.info("PHASE 2: METRICS CALCULATION")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    with memory_limit_guard(MEMORY_LIMIT_MB):
        run_metrics_calculation()
        
        # Clear memory after metrics calculation
        clear_memory()
    
    elapsed = time.time() - start_time
    logger.info(f"Metrics calculation completed in {elapsed:.2f} seconds")
    logger.info(f"Current memory usage: {get_current_memory_mb():.2f} MB")
    
    return True


def run_statistical_analysis():
    """Execute the statistical analysis phase."""
    logger.info("=" * 60)
    logger.info("PHASE 3: STATISTICAL ANALYSIS")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    with memory_limit_guard(MEMORY_LIMIT_MB):
        run_statistical_analysis()
        
        # Clear memory after analysis
        clear_memory()
    
    elapsed = time.time() - start_time
    logger.info(f"Statistical analysis completed in {elapsed:.2f} seconds")
    logger.info(f"Current memory usage: {get_current_memory_mb():.2f} MB")
    
    return True


def run_visualizations():
    """Execute the visualization generation phase."""
    logger.info("=" * 60)
    logger.info("PHASE 4: VISUALIZATIONS")
    logger.info("=" * 60)
    
    start_time = time.time()
    
    with memory_limit_guard(MEMORY_LIMIT_MB):
        run_visualizations()
        
        # Clear memory after visualization
        clear_memory()
    
    elapsed = time.time() - start_time
    logger.info(f"Visualizations completed in {elapsed:.2f} seconds")
    logger.info(f"Current memory usage: {get_current_memory_mb():.2f} MB")
    
    return True


def generate_final_report():
    """Generate the final report with associational framing."""
    logger.info("=" * 60)
    logger.info("PHASE 5: FINAL REPORT GENERATION")
    logger.info("=" * 60)
    
    output_dir = get_output_dir()
    report_path = Path(output_dir) / "final_report.json"
    
    # Verify associational framing
    framing_ok = verify_framing()
    
    report = {
        "metadata": {
            "project": "PROJ-062-quantifying-the-impact-of-code-ownership",
            "phase": "completed",
            "memory_limit_mb": MEMORY_LIMIT_MB,
            "framing": "associational rather than causal" if framing_ok else "WARNING: Framing verification failed",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "performance": {
            "memory_limit_enforced": True,
            "runtime_limit_hours": 6
        }
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Final report written to {report_path}")
    return True


def main():
    """
    Main entry point for the pipeline.
    Orchestrates all phases with memory and time monitoring.
    """
    start_total = time.time()
    
    try:
        setup_logging()
        logger.info("Starting full pipeline execution...")
        logger.info(f"Memory limit: {MEMORY_LIMIT_MB} MB")
        logger.info(f"Runtime limit: 6 hours (21600 seconds)")
        
        # Phase 1: Data Collection
        if not run_data_collection():
            logger.error("Data collection failed")
            return False
        
        # Phase 2: Metrics Calculation
        if not run_metrics_calculation():
            logger.error("Metrics calculation failed")
            return False
        
        # Phase 3: Statistical Analysis
        if not run_statistical_analysis():
            logger.error("Statistical analysis failed")
            return False
        
        # Phase 4: Visualizations
        if not run_visualizations():
            logger.error("Visualization generation failed")
            return False
        
        # Phase 5: State Management
        logger.info("Running state manager...")
        run_state_manager()
        
        # Phase 6: Final Report
        if not generate_final_report():
            logger.error("Final report generation failed")
            return False
        
        # Validation
        logger.info("Running quickstart validation...")
        run_validation()
        
        total_elapsed = time.time() - start_total
        total_hours = total_elapsed / 3600
        
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"Total runtime: {total_elapsed:.2f} seconds ({total_hours:.2f} hours)")
        logger.info(f"Final memory usage: {get_current_memory_mb():.2f} MB")
        logger.info("=" * 60)
        
        if total_hours > 6:
            logger.warning("WARNING: Pipeline exceeded 6 hour runtime limit")
            return False
        
        return True
        
    except MemoryError as e:
        logger.error(f"CRITICAL: Memory limit exceeded: {e}")
        return False
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
