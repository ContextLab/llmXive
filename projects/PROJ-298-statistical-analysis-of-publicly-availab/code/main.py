"""
Main orchestration script for the Statistical Analysis of Stack Overflow Tags pipeline.

This script executes the full pipeline as defined in tasks.md, ensuring dependencies
are respected and artifacts are generated.

Execution Order:
1. Data Download (T012)
2. Preprocessing (T013)
3. External Metrics (T039)
4. Trend Analysis (T014b, T014c)
5. Mapping (T015)
6. Correlation (T040)
7. Bootstrapping (T016b)
8. Generate Trend Results (T018)
9. Decomposition (T021a, T021b, T022)
10. Generate Decomposition Results (T025)
11. Clustering (T028, T029, T030)
12. Generate Cluster Results (T032)
"""
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR.parent))

# Configure logging
LOG_FILE = ROOT_DIR.parent / "data" / "processed" / "pipeline_execution.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PipelineOrchestrator")

def run_module(module_name: str, func_name: str = "main"):
    """
    Dynamically imports and runs a module's main function.
    
    Args:
        module_name: The module path relative to 'code' (e.g., 'data.download')
        func_name: The function to call (default: 'main')
    """
    start_time = time.time()
    logger.info(f"--- Starting {module_name}.{func_name} ---")
    
    try:
        # Import the module
        module = __import__(module_name, fromlist=[func_name])
        func = getattr(module, func_name)
        
        # Execute
        result = func()
        
        elapsed = time.time() - start_time
        if result == 0:
            logger.info(f"--- Finished {module_name}.{func_name} successfully in {elapsed:.2f}s ---")
            return True
        else:
            logger.error(f"--- {module_name}.{func_name} returned non-zero exit code: {result} ---")
            return False
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"--- FAILED {module_name}.{func_name} after {elapsed:.2f}s: {e} ---")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """
    Orchestrates the full pipeline execution.
    """
    logger.info("Starting Statistical Analysis Pipeline...")
    pipeline_start = time.time()

    # Define execution steps (Task ID -> (module, func))
    # Note: Modules are imported from 'code' directory
    steps = [
        # Phase 1: Data Ingestion
        ("T012: Download", "data.download"),
        ("T013: Preprocess", "data.preprocess"),
        
        # Phase 2: External Data
        ("T039: External Metrics", "data.external"),
        
        # Phase 3: Trend Analysis (US1)
        ("T014b: Trends", "analysis.trends"),
        ("T014c: Power Analysis", "analysis.trends"), # Often part of same script or called sequentially
        ("T015: Mapping", "analysis.mapping"),
        ("T040: Correlation", "analysis.correlation"),
        ("T016b: Bootstrapping", "analysis.bootstrapping"),
        
        # Phase 4: Generate US1 Final Results
        ("T018: Finalize Trends", "analysis.generate_trend_results"),
        
        # Phase 5: Decomposition (US2)
        ("T021a/b: Decomposition", "analysis.decomposition"),
        ("T022: Residual/Event Check", "analysis.decomposition"), # Often combined in same run
        ("T025: Finalize Decomposition", "analysis.generate_decomposition_results"),
        
        # Phase 6: Clustering (US3)
        ("T028/29/30: Clustering", "analysis.clustering"),
        ("T032: Finalize Clusters", "analysis.generate_cluster_results"),
    ]

    failed_steps = []
    
    for step_name, module_path in steps:
        logger.info(f"Executing Step: {step_name}")
        success = run_module(module_path)
        if not success:
            failed_steps.append(step_name)
            # Halt on failure as per "Fail Loudly" principle for pipeline
            logger.critical(f"Pipeline halted due to failure in {step_name}")
            break

    total_time = time.time() - pipeline_start
    logger.info(f"Pipeline execution completed in {total_time:.2f} seconds.")
    
    # Write timing to log
    with open(LOG_FILE, 'a') as f:
        f.write(f"Total Pipeline Time: {total_time:.2f}s\n")
    
    if failed_steps:
        logger.error(f"Pipeline failed. Failed steps: {', '.join(failed_steps)}")
        sys.exit(1)
    else:
        logger.info("Pipeline completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()