"""Main entry point for the Phenomenological AI pipeline."""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import get_config
from utils.logging import log_operation, get_logger, setup_logging
from generation.runner import run_generation_pipeline
from generation.control_corpus import generate_control_corpus
from analysis.consistency import run_consistency_analysis
from analysis.stability import run_stability_analysis
from analysis.markers import run_marker_analysis
from analysis.stats import orchestrate_analysis
from validation.stratified_sampler import run_stratified_sampling
from validation.human_rater import run_rating_pipeline
from utils.archiver import run_archiver


def setup_environment(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Initialize environment and load configuration."""
    logger = get_logger()
    log_operation("setup_environment", config_path=config_path)
    
    config = get_config(config_path)
    logger.info("Environment setup complete")
    return config


def run_generation_phase(config: Dict[str, Any]) -> None:
    """Run the generation phase for phenomenological reports."""
    log_operation("run_generation_phase")
    run_generation_pipeline(config)


def run_control_phase(config: Dict[str, Any]) -> None:
    """Run the control corpus generation phase."""
    log_operation("run_control_phase")
    generate_control_corpus(config)


def run_analysis_phase(config: Dict[str, Any]) -> None:
    """Run the analysis phase (consistency, stability, markers)."""
    log_operation("run_analysis_phase")
    run_consistency_analysis(config)
    run_stability_analysis(config)
    run_marker_analysis(config)


def run_stats_phase(config: Dict[str, Any]) -> None:
    """Run the statistical analysis phase."""
    log_operation("run_stats_phase")
    orchestrate_analysis(config)


def run_validation_phase(config: Dict[str, Any]) -> None:
    """Run the validation phase (sample selection and human rating)."""
    log_operation("run_validation_phase")
    run_stratified_sampling(config)
    run_rating_pipeline(config)


def run_full_pipeline(config: Dict[str, Any]) -> None:
    """Run the complete pipeline."""
    log_operation("run_full_pipeline")
    run_generation_phase(config)
    run_control_phase(config)
    run_analysis_phase(config)
    run_stats_phase(config)
    run_validation_phase(config)
    log_operation("full_pipeline_complete")


def main() -> None:
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(description="Phenomenological AI Pipeline")
    parser.add_argument(
        "--task",
        choices=[
            "generate",
            "generate_control",
            "analyze",
            "stats",
            "validate_human",
            "sensitivity-kappa",
            "archive",
            "full"
        ],
        required=True,
        help="Task to execute"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.py",
        help="Path to configuration file"
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging("data/logs/pipeline.log")
    
    try:
        log_operation("main_start", task=args.task, config=args.config)
        
        config = setup_environment(args.config)
        
        if args.task == "generate":
            run_generation_phase(config)
        elif args.task == "generate_control":
            run_control_phase(config)
        elif args.task == "analyze":
            run_analysis_phase(config)
        elif args.task == "stats":
            run_stats_phase(config)
        elif args.task == "validate_human":
            run_validation_phase(config)
        elif args.task == "sensitivity-kappa":
            from analysis.sensitivity_kappa import run_sensitivity_kappa_analysis
            run_sensitivity_kappa_analysis(config)
        elif args.task == "archive":
            run_archiver(config)
        elif args.task == "full":
            run_full_pipeline(config)
        
        log_operation("task_complete", task=args.task)
        
    except Exception as e:
        log_operation("task_failed", task=args.task, error=str(e))
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()