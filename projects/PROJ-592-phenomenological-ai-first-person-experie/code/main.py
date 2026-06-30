"""
Main orchestration script for the Phenomenological AI pipeline.

This script coordinates the full research workflow:
1. Generation: Produces phenomenological reports using defined strategies.
2. Metrics: Computes Consistency, Stability, and Marker presence scores.
3. Stats: Performs statistical analysis (ANOVA/Kruskal-Wallis) and post-hoc tests.

Usage:
    python code/main.py --mode generation
    python code/main.py --mode analysis
    python code/main.py --mode full
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import setup_logging, get_logger, export_warning_log
from utils.io import safe_write_json, safe_write_csv, ensure_dir
from config import CONFIG

# Import Generation Pipeline
from generation.runner import run_generation_pipeline
from generation.control_corpus import generate_control_corpus

# Import Analysis Modules
from analysis.consistency import run_consistency_analysis
from analysis.stability import run_stability_analysis
from analysis.markers import run_marker_analysis
from analysis.stats import orchestrate_analysis
from analysis.sensitivity_analysis import run_sensitivity_analysis
from analysis.validity_justification import run_validity_justification

logger = None

def setup_environment():
    """Ensure directories exist and logging is configured."""
    global logger
    setup_logging(level=logging.INFO)
    logger = get_logger("main")
    
    # Create required directories
    ensure_dir(CONFIG["paths"]["raw"])
    ensure_dir(CONFIG["paths"]["processed"])
    ensure_dir(CONFIG["paths"]["qualitative"])
    ensure_dir(CONFIG["paths"]["figures"])
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Data root: {CONFIG['paths']['raw']}")

def run_generation_phase():
    """Execute the data generation phase (US1)."""
    logger.info("=" * 60)
    logger.info("PHASE 1: GENERATION")
    logger.info("=" * 60)

    # 1. Generate Phenomenological Reports
    logger.info("Starting phenomenological report generation...")
    try:
        run_generation_pipeline()
        logger.info("Phenomenological generation complete.")
    except Exception as e:
        logger.error(f"Generation pipeline failed: {e}", exc_info=True)
        raise

    # 2. Generate Control Corpus
    logger.info("Starting control corpus generation...")
    try:
        generate_control_corpus()
        logger.info("Control corpus generation complete.")
    except Exception as e:
        logger.error(f"Control corpus generation failed: {e}", exc_info=True)
        raise

    logger.info("Generation phase finished.")

def run_analysis_phase():
    """Execute the metrics and statistical analysis phase (US2)."""
    logger.info("=" * 60)
    logger.info("PHASE 2: ANALYSIS")
    logger.info("=" * 60)

    # 1. Consistency Metric
    logger.info("Computing Internal Consistency metrics...")
    try:
        run_consistency_analysis()
        logger.info("Consistency analysis complete.")
    except Exception as e:
        logger.error(f"Consistency analysis failed: {e}", exc_info=True)
        # Continue despite partial failure if possible, but log heavily
    
    # 2. Stability Metric
    logger.info("Computing Semantic Stability metrics...")
    try:
        run_stability_analysis()
        logger.info("Stability analysis complete.")
    except Exception as e:
        logger.error(f"Stability analysis failed: {e}", exc_info=True)

    # 3. Marker Presence Metric
    logger.info("Computing Phenomenological Marker scores...")
    try:
        run_marker_analysis()
        logger.info("Marker analysis complete.")
    except Exception as e:
        logger.error(f"Marker analysis failed: {e}", exc_info=True)

    # 4. Aggregate and Statistical Testing
    logger.info("Orchestrating statistical analysis...")
    try:
        orchestrate_analysis()
        logger.info("Statistical analysis complete.")
    except Exception as e:
        logger.error(f"Statistical orchestration failed: {e}", exc_info=True)
        raise

    # 5. Sensitivity Analysis
    logger.info("Running sensitivity analysis on weights...")
    try:
        run_sensitivity_analysis()
        logger.info("Sensitivity analysis complete.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}", exc_info=True)

    # 6. Validity Justification
    logger.info("Generating validity justification report...")
    try:
        run_validity_justification()
        logger.info("Validity justification complete.")
    except Exception as e:
        logger.error(f"Validity justification failed: {e}", exc_info=True)

    logger.info("Analysis phase finished.")

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Phenomenological AI Research Pipeline Orchestrator"
    )
    parser.add_argument(
        "--mode",
        choices=["generation", "analysis", "full"],
        default="full",
        help="Execution mode: generation only, analysis only, or full pipeline."
    )
    
    args = parser.parse_args()
    
    try:
        setup_environment()
        
        if args.mode in ["generation", "full"]:
            run_generation_phase()
        
        if args.mode in ["analysis", "full"]:
            run_analysis_phase()
        
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Export any captured warnings to a log file
        try:
            export_warning_log(project_root / "data" / "processing_warnings.log")
        except Exception:
            pass

if __name__ == "__main__":
    main()