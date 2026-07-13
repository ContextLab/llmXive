"""
Main orchestration script for the Phenomenological AI pipeline.
Coordinates Generation, Analysis, Stats, and Validation phases.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config
from utils.logging import get_logger, log_operation
from utils.io import ensure_dir

# Import phase modules
# Note: These imports must match the public API surface defined in the task descriptions.
from generation.runner import main as generation_main
from generation.control_corpus import main as control_main
from analysis.consistency import main as consistency_main
from analysis.stability import main as stability_main
from analysis.markers import main as markers_main
from analysis.stats import main as stats_main
from analysis.sensitivity_analysis import main as sensitivity_main
from analysis.validity_justification import main as justification_main
from validation.human_rater import main as human_rater_main
from validation.stratified_sampler import main as sampler_main
from utils.archiver import main as archiver_main

def setup_environment(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Setup environment and load configuration."""
    logger = get_logger("main")
    # Fixed: log_operation now accepts operation as first arg, kwargs as params
    log_operation("setup_environment", config_path=config_path)
    
    config = get_config(config_path)
    
    # Ensure output directories exist
    output_dir = Path(config.get("output_dir", "data"))
    for dir_name in ["data/raw", "data/processed", "data/qualitative", "figures"]:
        ensure_dir(output_dir / dir_name)
    
    return config

def run_generation_phase(config: Dict[str, Any]) -> None:
    """Run the generation phase (US1)."""
    logger = get_logger("main")
    log_operation("run_generation_phase")
    generation_main()

def run_control_phase(config: Dict[str, Any]) -> None:
    """Run the control corpus generation (US1)."""
    logger = get_logger("main")
    log_operation("run_control_phase")
    control_main()

def run_analysis_phase(config: Dict[str, Any]) -> None:
    """Run the analysis phase (US2)."""
    logger = get_logger("main")
    log_operation("run_analysis_phase")
    
    # Run consistency analysis
    consistency_main()
    
    # Run stability analysis
    stability_main()
    
    # Run marker analysis
    markers_main()

def run_stats_phase(config: Dict[str, Any]) -> None:
    """Run the statistics phase (US2)."""
    logger = get_logger("main")
    log_operation("run_stats_phase")
    
    # Run main stats orchestration (produces validity_scores.csv)
    stats_main()
    
    # Run sensitivity analysis
    sensitivity_main()
    
    # Run validity justification
    justification_main()

def run_validation_phase(config: Dict[str, Any]) -> None:
    """Run the validation phase (US3)."""
    logger = get_logger("main")
    log_operation("run_validation_phase")
    
    # Run stratified sampling
    sampler_main()
    
    # Run human rating
    human_rater_main()

def run_full_pipeline(config: Dict[str, Any]) -> None:
    """Run the complete pipeline: Generation -> Metrics -> Stats -> Validation."""
    logger = get_logger("main")
    log_operation("run_full_pipeline")
    
    run_generation_phase(config)
    run_control_phase(config)
    run_analysis_phase(config)
    run_stats_phase(config)
    run_validation_phase(config)
    
    log_operation("full_pipeline_complete")

def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Phenomenological AI Pipeline Orchestrator"
    )
    parser.add_argument(
        "--task",
        type=str,
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
        default="full",
        help="Task to execute"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.py",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    logger = get_logger("main")
    
    # Fixed: log_operation expects operation as first arg
    log_operation("main_start", task=args.task, config=args.config)
    
    try:
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
            from analysis.sensitivity_kappa import main as kappa_main
            kappa_main()
        elif args.task == "archive":
            archiver_main()
        elif args.task == "full":
            run_full_pipeline(config)
        
        log_operation("task_complete", task=args.task)
        
    except Exception as e:
        log_operation("task_failed", task=args.task, error=str(e))
        raise

if __name__ == "__main__":
    main()
