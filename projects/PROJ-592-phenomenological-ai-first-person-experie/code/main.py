import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Ensure code/ is in path for imports
code_root = Path(__file__).parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from utils.logging import setup_logging, get_logger
from utils.io import safe_write_csv, safe_write_json, ensure_dir
from generation.runner import run_generation_pipeline
from generation.control_corpus import generate_control_corpus
from analysis.consistency import run_consistency_analysis
from analysis.stability import run_stability_analysis
from analysis.markers import run_marker_analysis
from analysis.stats import orchestrate_analysis
from analysis.sensitivity_analysis import run_sensitivity_analysis
from analysis.validity_justification import run_validity_justification
from analysis.sensitivity_kappa import run_sensitivity_kappa_analysis
from validation.stratified_sampler import run_stratified_sampling
from validation.human_rater import run_rating_pipeline

logger = get_logger(__name__)

def setup_environment(config_path: Optional[Path] = None):
    """Initialize logging and validate paths."""
    setup_logging()
    if config_path:
        logger.info(f"Using config from {config_path}")
    else:
        logger.info("No config provided, using defaults")
    
    # Ensure required directories exist
    for dir_path in ["data/raw", "data/processed", "data/qualitative", "figures"]:
        ensure_dir(dir_path)
    
    logger.info("Environment setup complete")

def run_generation_phase(config_path: Optional[Path] = None):
    """Execute the generation pipeline (US1)."""
    logger.info("Starting generation phase...")
    try:
        # Run main generation
        run_generation_pipeline()
        logger.info("Main generation complete")
        
        # Run control corpus generation
        generate_control_corpus()
        logger.info("Control corpus generation complete")
    except Exception as e:
        logger.error(f"Generation phase failed: {e}")
        raise

def run_analysis_phase(config_path: Optional[Path] = None):
    """Execute the analysis pipeline (US2)."""
    logger.info("Starting analysis phase...")
    try:
        # 1. Consistency
        run_consistency_analysis()
        logger.info("Consistency analysis complete")
        
        # 2. Stability
        run_stability_analysis()
        logger.info("Stability analysis complete")
        
        # 3. Markers
        run_marker_analysis()
        logger.info("Marker analysis complete")
        
        # 4. Stats & Aggregation (Produces validity_scores.csv)
        orchestrate_analysis()
        logger.info("Statistical orchestration complete")
        
        # 5. Sensitivity & Justification
        run_sensitivity_analysis()
        logger.info("Sensitivity analysis complete")
        
        run_validity_justification()
        logger.info("Validity justification complete")
        
        # 6. Kappa Sensitivity
        run_sensitivity_kappa_analysis()
        logger.info("Kappa sensitivity analysis complete")
        
    except Exception as e:
        logger.error(f"Analysis phase failed: {e}")
        raise

def run_validation_phase(config_path: Optional[Path] = None):
    """Execute the validation pipeline (US3)."""
    logger.info("Starting validation phase...")
    try:
        # 1. Stratified Sampling
        run_stratified_sampling()
        logger.info("Stratified sampling complete")
        
        # 2. Human Rating
        run_rating_pipeline()
        logger.info("Human rating pipeline complete")
    except Exception as e:
        logger.error(f"Validation phase failed: {e}")
        raise

def run_full_pipeline(config_path: Optional[Path] = None):
    """Run Generation -> Analysis -> Validation."""
    logger.info("Starting full pipeline...")
    run_generation_phase(config_path)
    run_analysis_phase(config_path)
    run_validation_phase(config_path)
    logger.info("Full pipeline complete")

def main():
    parser = argparse.ArgumentParser(description="Phenomenological AI Research Pipeline")
    parser.add_argument(
        "--task", 
        type=str, 
        choices=["generate", "generate_control", "select_validation_sample", "analyze", "validate_human", "stats", "sensitivity-kappa", "full"],
        help="Task to execute"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default="code/config.py",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    config_path = Path(args.config) if args.config else None
    
    if args.task == "generate":
        setup_environment(config_path)
        run_generation_phase(config_path)
    elif args.task == "generate_control":
        setup_environment(config_path)
        generate_control_corpus()
    elif args.task == "select_validation_sample":
        setup_environment(config_path)
        run_stratified_sampling()
    elif args.task == "analyze":
        setup_environment(config_path)
        run_analysis_phase(config_path)
    elif args.task == "validate_human":
        setup_environment(config_path)
        run_validation_phase(config_path)
    elif args.task == "stats":
        setup_environment(config_path)
        orchestrate_analysis()
    elif args.task == "sensitivity-kappa":
        setup_environment(config_path)
        run_sensitivity_kappa_analysis()
    elif args.task == "full":
        setup_environment(config_path)
        run_full_pipeline(config_path)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
