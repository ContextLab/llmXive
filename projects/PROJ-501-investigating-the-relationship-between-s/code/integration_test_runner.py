"""
T036: Full Pipeline Integration Test Runner

Executes the complete research pipeline:
1. Data Ingestion (US1) -> data/processed/merged_filtered.csv
2. Physics Modeling (US2) -> data/processed/derived_physics.csv
3. Statistical Analysis (US3) -> data/results/correlation_results.json
4. Visualization (US3) -> data/results/flux_vs_retention.png

This script orchestrates the pipeline by calling the main functions
from data_ingestion, physics, analysis, and visualization modules.
"""

import logging
import sys
import time
from pathlib import Path

# Configure logging for the integration run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/integration_run.log')
    ]
)
logger = logging.getLogger('integration_test')

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import pipeline functions from existing modules
# These imports must match the API surface provided
from data_ingestion import run_ingestion_pipeline
from physics import run_physics_pipeline
from analysis import run_analysis_pipeline
from visualization import run_visualization_pipeline

def main():
    """Run the full pipeline integration test."""
    logger.info("=" * 80)
    logger.info("Starting Full Pipeline Integration Test (T036)")
    logger.info("=" * 80)
    
    start_time = time.time()
    success = True
    
    try:
        # Step 1: Data Ingestion (US1)
        logger.info("Step 1/4: Running Data Ingestion Pipeline...")
        ingestion_start = time.time()
        merged_path = run_ingestion_pipeline()
        ingestion_time = time.time() - ingestion_start
        logger.info(f"  -> Completed in {ingestion_time:.2f}s. Output: {merged_path}")
        
        if not merged_path or not merged_path.exists():
            raise FileNotFoundError(f"Ingestion pipeline failed to produce {merged_path}")
        
        # Step 2: Physics Modeling (US2)
        logger.info("Step 2/4: Running Physics Modeling Pipeline...")
        physics_start = time.time()
        physics_path = run_physics_pipeline()
        physics_time = time.time() - physics_start
        logger.info(f"  -> Completed in {physics_time:.2f}s. Output: {physics_path}")
        
        if not physics_path or not physics_path.exists():
            raise FileNotFoundError(f"Physics pipeline failed to produce {physics_path}")
        
        # Step 3: Statistical Analysis (US3)
        logger.info("Step 3/4: Running Statistical Analysis Pipeline...")
        analysis_start = time.time()
        results_path = run_analysis_pipeline()
        analysis_time = time.time() - analysis_start
        logger.info(f"  -> Completed in {analysis_time:.2f}s. Output: {results_path}")
        
        if not results_path or not results_path.exists():
            raise FileNotFoundError(f"Analysis pipeline failed to produce {results_path}")
        
        # Step 4: Visualization (US3)
        logger.info("Step 4/4: Running Visualization Pipeline...")
        viz_start = time.time()
        viz_path = run_visualization_pipeline()
        viz_time = time.time() - viz_start
        logger.info(f"  -> Completed in {viz_time:.2f}s. Output: {viz_path}")
        
        if not viz_path or not viz_path.exists():
            raise FileNotFoundError(f"Visualization pipeline failed to produce {viz_path}")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed with error: {e}", exc_info=True)
        success = False
    
    total_time = time.time() - start_time
    
    # Final Report
    logger.info("=" * 80)
    if success:
        logger.info("INTEGRATION TEST PASSED")
        logger.info(f"Total execution time: {total_time:.2f} seconds")
        logger.info("Artifacts generated:")
        logger.info(f"  1. {merged_path}")
        logger.info(f"  2. {physics_path}")
        logger.info(f"  3. {results_path}")
        logger.info(f"  4. {viz_path}")
    else:
        logger.error("INTEGRATION TEST FAILED")
        logger.error(f"Total execution time before failure: {total_time:.2f} seconds")
        sys.exit(1)
    
    logger.info("=" * 80)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())