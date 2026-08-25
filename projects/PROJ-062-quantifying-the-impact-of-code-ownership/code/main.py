"""
Main orchestration script for the Code Ownership Impact Analysis Pipeline.

This script coordinates the full research pipeline:
1. Data Collection (US1)
2. Metrics Calculation (US2)
3. Statistical Analysis (US3)
4. Visualization (US3)

It ensures temporal separation (T vs T+1) and maintains an associational
framing as required by FR-010.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Import project modules
from config import get_cutoff_date, get_depth_limit, get_repo_list, get_output_dir
from utils.logging_utils import configure_logging, get_logger
from data_collection import process_all_repos, main as data_collection_main
from metrics_calc import main as metrics_calc_main
from statistical_analysis import run_full_analysis
from visualizations import main as visualizations_main
from state_manager import generate_latest_snapshot, save_state_snapshot

def setup_logging():
    """Configure logging for the pipeline."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "pipeline_execution.log"
    configure_logging(log_file=str(log_file), level=logging.INFO)
    return get_logger(__name__)

def run_data_collection(logger):
    """Execute User Story 1: Data Collection."""
    logger.info("Starting Data Collection (US1)...")
    start_time = time.time()
    
    # Process all repositories
    success = process_all_repos()
    
    elapsed = time.time() - start_time
    logger.info(f"Data Collection completed in {elapsed:.2f} seconds. Success: {success}")
    return success

def run_metrics_calculation(logger):
    """Execute User Story 2: Metrics Calculation."""
    logger.info("Starting Metrics Calculation (US2)...")
    start_time = time.time()
    
    # Calculate all metrics
    success = metrics_calc_main()
    
    elapsed = time.time() - start_time
    logger.info(f"Metrics Calculation completed in {elapsed:.2f} seconds. Success: {success}")
    return success

def run_statistical_analysis(logger):
    """Execute User Story 3: Statistical Analysis."""
    logger.info("Starting Statistical Analysis (US3)...")
    start_time = time.time()
    
    # Run full analysis suite
    success = run_full_analysis()
    
    elapsed = time.time() - start_time
    logger.info(f"Statistical Analysis completed in {elapsed:.2f} seconds. Success: {success}")
    return success

def run_visualizations(logger):
    """Execute Visualization tasks."""
    logger.info("Starting Visualizations...")
    start_time = time.time()
    
    # Generate plots
    success = visualizations_main()
    
    elapsed = time.time() - start_time
    logger.info(f"Visualizations completed in {elapsed:.2f} seconds. Success: {success}")
    return success

def generate_final_report(logger, execution_metadata: Dict[str, Any]) -> bool:
    """
    Generate the final report JSON with associational framing.
    
    FR-010: The report MUST explicitly state that findings are 
    "associational rather than causal".
    """
    logger.info("Generating final report...")
    
    output_dir = get_output_dir()
    output_path = Path(output_dir) / "results" / "final_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cutoff_date = get_cutoff_date()
    
    report = {
        "metadata": {
            "project_name": "Quantifying the Impact of Code Ownership on Software Quality",
            "project_id": "PROJ-062",
            "execution_timestamp": datetime.now().isoformat(),
            "cutoff_date": cutoff_date.isoformat() if hasattr(cutoff_date, 'isoformat') else str(cutoff_date),
            "temporal_framing": {
                "ownership_period": f"Up to {cutoff_date}",
                "quality_period": f"After {cutoff_date} (T+1)",
                "note": "Temporal separation ensures ownership metrics precede quality outcomes"
            },
            "causal_framing": {
                "statement": "associational rather than causal",
                "rationale": "This study identifies statistical correlations between code ownership metrics and software quality indicators. Due to the observational nature of the data and potential confounding variables (e.g., team experience, project complexity, development processes), findings should be interpreted as associations, not causal relationships.",
                "confounders_acknowledged": [
                    "Team experience and expertise",
                    "Project complexity and domain",
                    "Development processes and practices",
                    "Organizational factors"
                ]
            }
        },
        "execution_summary": execution_metadata,
        "findings": {
            "ownership_quality_correlation": {
                "status": "computed",
                "description": "Spearman correlation between Gini coefficient and bug density",
                "note": "See data/results/statistical_results.json for detailed coefficients"
            },
            "non_linearity_test": {
                "status": "computed",
                "description": "Quadratic model comparison for Gini effects",
                "note": "See data/results/statistical_results.json for p-values"
            },
            "sensitivity_analysis": {
                "pvalue_sweep": "data/results/sensitivity_pvalue.csv",
                "rho_sweep": "data/results/sensitivity_rho.csv"
            }
        },
        "artifacts": {
            "raw_data": "data/raw/",
            "intermediate_data": "data/intermediate/",
            "ownership_metrics": "data/ownership_metrics/",
            "bug_metrics": "data/bug_metrics/",
            "calculated_metrics": "data/results/metrics/",
            "visualizations": "figures/",
            "state_snapshot": "state/"
        },
        "limitations": [
            "Observational study design limits causal inference",
            "Path-based bug attribution may miss implicit fixes",
            "Shallow git history (depth=1000) may miss long-term trends",
            "GitHub API rate limits may affect issue completeness"
        ]
    }
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Final report written to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write final report: {e}")
        return False

def main():
    """
    Main entry point for the pipeline.
    
    Orchestrates all phases in sequence and generates the final report.
    """
    logger = setup_logging()
    logger.info("=" * 80)
    logger.info("Starting Code Ownership Impact Analysis Pipeline")
    logger.info("=" * 80)
    
    start_time = time.time()
    execution_metadata = {
        "status": "running",
        "phases": {}
    }
    
    try:
        # Phase 1: Data Collection (US1)
        logger.info("\n--- Phase 1: Data Collection ---")
        us1_success = run_data_collection(logger)
        execution_metadata["phases"]["data_collection"] = {
            "status": "success" if us1_success else "failed",
            "timestamp": datetime.now().isoformat()
        }
        if not us1_success:
            logger.error("Data Collection failed. Aborting pipeline.")
            execution_metadata["status"] = "failed"
            return 1
        
        # Phase 2: Metrics Calculation (US2)
        logger.info("\n--- Phase 2: Metrics Calculation ---")
        us2_success = run_metrics_calculation(logger)
        execution_metadata["phases"]["metrics_calculation"] = {
            "status": "success" if us2_success else "failed",
            "timestamp": datetime.now().isoformat()
        }
        if not us2_success:
            logger.error("Metrics Calculation failed. Aborting pipeline.")
            execution_metadata["status"] = "failed"
            return 1
        
        # Phase 3: Statistical Analysis (US3)
        logger.info("\n--- Phase 3: Statistical Analysis ---")
        us3_success = run_statistical_analysis(logger)
        execution_metadata["phases"]["statistical_analysis"] = {
            "status": "success" if us3_success else "failed",
            "timestamp": datetime.now().isoformat()
        }
        if not us3_success:
            logger.error("Statistical Analysis failed. Aborting pipeline.")
            execution_metadata["status"] = "failed"
            return 1
        
        # Phase 4: Visualizations
        logger.info("\n--- Phase 4: Visualizations ---")
        viz_success = run_visualizations(logger)
        execution_metadata["phases"]["visualizations"] = {
            "status": "success" if viz_success else "failed",
            "timestamp": datetime.now().isoformat()
        }
        if not viz_success:
            logger.warning("Visualizations failed, but continuing to report generation.")
        
        # Update execution status
        execution_metadata["status"] = "success"
        execution_metadata["total_duration_seconds"] = time.time() - start_time
        execution_metadata["completion_timestamp"] = datetime.now().isoformat()
        
        # Generate final report with associational framing
        logger.info("\n--- Final Report Generation ---")
        report_success = generate_final_report(logger, execution_metadata)
        
        if not report_success:
            logger.error("Failed to generate final report.")
            return 1
        
        # Generate state snapshot
        logger.info("Generating state snapshot...")
        try:
            generate_latest_snapshot()
        except Exception as e:
            logger.warning(f"State snapshot generation failed: {e}")
        
        logger.info("\n" + "=" * 80)
        logger.info("Pipeline completed successfully!")
        logger.info(f"Total execution time: {execution_metadata['total_duration_seconds']:.2f} seconds")
        logger.info("Final report: data/results/final_report.json")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}", exc_info=True)
        execution_metadata["status"] = "failed"
        execution_metadata["error"] = str(e)
        return 1

if __name__ == "__main__":
    sys.exit(main())
