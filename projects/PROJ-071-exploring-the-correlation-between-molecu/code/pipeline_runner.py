"""
Full pipeline execution script for T041.
Executes the entire research pipeline end-to-end and measures execution time.
"""
import os
import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path if not already present
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.ingest import main as ingest_main
from code.descriptors import main as descriptors_main
from code.standardize import main as standardize_main
from code.analysis import main as analysis_main
from code.viz import main as viz_main
from code.report import main as report_main
from code.logging_config import setup_logging, get_logger
from code.config import get_config, ensure_directories

def run_pipeline():
    """Execute the full pipeline and return timing metrics."""
    logger = get_logger("pipeline_runner")
    logger.info("Starting full pipeline execution for T041")
    
    start_time = time.time()
    stages = []
    
    try:
        # Stage 1: Ingestion
        stage_start = time.time()
        logger.info("Stage 1: Data Ingestion (T012-T017)")
        ingest_main()
        stages.append({
            "stage": "Ingestion",
            "duration_seconds": time.time() - stage_start,
            "status": "completed"
        })
        
        # Stage 2: Descriptor Calculation
        stage_start = time.time()
        logger.info("Stage 2: Descriptor Calculation (T014-T015)")
        descriptors_main()
        stages.append({
            "stage": "Descriptors",
            "duration_seconds": time.time() - stage_start,
            "status": "completed"
        })
        
        # Stage 3: Standardization
        stage_start = time.time()
        logger.info("Stage 3: Data Standardization (T020-T021)")
        standardize_main()
        stages.append({
            "stage": "Standardization",
            "duration_seconds": time.time() - stage_start,
            "status": "completed"
        })
        
        # Stage 4: Analysis
        stage_start = time.time()
        logger.info("Stage 4: Correlation & Regression Analysis (T022-T026)")
        analysis_main()
        stages.append({
            "stage": "Analysis",
            "duration_seconds": time.time() - stage_start,
            "status": "completed"
        })
        
        # Stage 5: Visualization
        stage_start = time.time()
        logger.info("Stage 5: Visualization (T032-T033)")
        viz_main()
        stages.append({
            "stage": "Visualization",
            "duration_seconds": time.time() - stage_start,
            "status": "completed"
        })
        
        # Stage 6: Reporting
        stage_start = time.time()
        logger.info("Stage 6: Report Generation (T034-T036)")
        report_main()
        stages.append({
            "stage": "Reporting",
            "duration_seconds": time.time() - stage_start,
            "status": "completed"
        })
        
        total_time = time.time() - start_time
        
        # Save timing results
        results = {
            "execution_timestamp": datetime.now().isoformat(),
            "total_duration_seconds": total_time,
            "stages": stages
        }
        
        output_path = project_root / "data" / "processed" / "pipeline_timing.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Pipeline completed successfully in {total_time:.2f} seconds")
        logger.info(f"Timing results saved to {output_path}")
        
        return results
        
    except Exception as e:
        logger.error(f"Pipeline failed at stage {len(stages) + 1}: {str(e)}", exc_info=True)
        total_time = time.time() - start_time
        
        failure_results = {
            "execution_timestamp": datetime.now().isoformat(),
            "total_duration_seconds": total_time,
            "status": "failed",
            "error": str(e),
            "completed_stages": stages
        }
        
        output_path = project_root / "data" / "processed" / "pipeline_timing.json"
        with open(output_path, 'w') as f:
            json.dump(failure_results, f, indent=2)
        
        raise

def main():
    """Entry point for pipeline execution."""
    # Initialize logging
    log_dir = project_root / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file=str(log_dir / "pipeline_run.log"))
    
    logger = get_logger("pipeline_runner")
    
    # Ensure directories exist
    config = get_config()
    ensure_directories(config)
    
    logger.info("="*60)
    logger.info("LLMXive Pipeline Execution - Task T041")
    logger.info("="*60)
    
    try:
        results = run_pipeline()
        print(f"\n✅ Pipeline execution completed successfully.")
        print(f"   Total time: {results['total_duration_seconds']:.2f} seconds")
        print(f"   Details saved to: data/processed/pipeline_timing.json")
        return 0
    except Exception as e:
        print(f"\n❌ Pipeline execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
