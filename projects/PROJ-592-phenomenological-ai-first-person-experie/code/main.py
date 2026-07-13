"""Main orchestration script for the Phenomenological AI pipeline."""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger, setup_logging, retry_on_failure
from generation.runner import run_generation_pipeline, main as generation_main
from generation.control_corpus import generate_control_corpus, main as control_main
from analysis.consistency import run_consistency_analysis, main as consistency_main
from analysis.stability import run_stability_analysis, main as stability_main
from analysis.markers import run_marker_analysis, main as markers_main
from analysis.stats import orchestrate_analysis, main as stats_main
from validation.stratified_sampler import run_stratified_sampling, main as sampler_main
from validation.human_rater import run_rating_pipeline, main as rater_main
from validation.turing_simulation import run_turing_simulation, main as turing_main
from utils.io import safe_write_csv

logger = setup_logging()


def setup_environment(config_path: str) -> dict:
    """Load configuration and setup environment."""
    import json
    if not os.path.exists(config_path):
        # Fallback for CI if config.json is missing, use defaults
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {
            "seeds": [42, 123, 456],
            "paths": {
                "raw": "data/raw",
                "processed": "data/processed",
                "qualitative": "data/qualitative"
            },
            "models": {
                "primary": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
            }
        }
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    logger.log("config_loaded", path=config_path)
    return config


def run_generation_phase(config: dict) -> None:
    """Execute the generation phase."""
    logger.log("phase_start", phase="generation")
    # Calls runner.py main which handles its own logging
    generation_main()
    logger.log("phase_complete", phase="generation")


def run_analysis_phase(config: dict) -> None:
    """Execute the analysis (metrics) phase."""
    logger.log("phase_start", phase="analysis")

    # Run consistency analysis
    logger.log("subphase_start", subphase="consistency")
    consistency_main()

    # Run stability analysis
    logger.log("subphase_start", subphase="stability")
    stability_main()

    # Run marker analysis
    logger.log("subphase_start", subphase="markers")
    markers_main()

    logger.log("phase_complete", phase="analysis")


def run_stats_phase(config: dict) -> None:
    """Execute the statistical analysis phase."""
    logger.log("phase_start", phase="stats")
    stats_main()
    logger.log("phase_complete", phase="stats")


def run_validation_phase(config: dict) -> None:
    """Execute the validation phase."""
    logger.log("phase_start", phase="validation")

    # Select validation sample
    logger.log("subphase_start", subphase="sampling")
    sampler_main()

    # Run human rating (if data available)
    logger.log("subphase_start", subphase="rating")
    rater_main()

    logger.log("phase_complete", phase="validation")


def run_full_pipeline(config: dict) -> None:
    """Run the complete pipeline: Generation → Metrics → Stats → Validation."""
    logger.log("pipeline_start")
    run_generation_phase(config)
    run_analysis_phase(config)
    run_stats_phase(config)
    run_validation_phase(config)
    logger.log("pipeline_complete")


def main():
    """Entry point for CLI."""
    parser = argparse.ArgumentParser(description="Phenomenological AI Pipeline")
    parser.add_argument("--task", type=str, required=True,
                      choices=["generate", "generate_control", "analyze", "stats",
                              "select_validation_sample", "validate_human", "turing_sim", "full"],
                      help="Task to execute")
    parser.add_argument("--config", type=str, default="code/config.json",
                      help="Path to configuration file")

    args = parser.parse_args()
    config = setup_environment(args.config)

    if args.task == "generate":
        run_generation_phase(config)
    elif args.task == "generate_control":
        control_main()
    elif args.task == "analyze":
        run_analysis_phase(config)
    elif args.task == "stats":
        run_stats_phase(config)
    elif args.task == "select_validation_sample":
        sampler_main()
    elif args.task == "validate_human":
        rater_main()
    elif args.task == "turing_sim":
        turing_main()
    elif args.task == "full":
        run_full_pipeline(config)

    logger.log("task_complete", task=args.task)


if __name__ == "__main__":
    main()