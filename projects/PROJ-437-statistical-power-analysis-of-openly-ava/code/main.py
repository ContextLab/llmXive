"""
Main entry point for the Statistical Power Analysis Pipeline.

This module orchestrates the end-to-end workflow:
1. Configuration loading and validation
2. Data download from OpenNeuro (if needed)
3. Preprocessing (ROI extraction, temporal smoothing)
4. Statistical modeling (GLM fitting, effect size estimation)
5. Validation (split-half replication, power curve generation)

Usage:
    python code/main.py --config config.yaml --dataset ds000030
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Local imports from project structure
from analysis.power_curve_generator import run_bootstrap_loop, generate_power_curve
from download.openneuro_fetcher import fetch_paradigm_data
from download.data_validator import validate_bids_structure, get_valid_subjects_list
from preprocess.roi_extractor import preprocess_and_extract
from preprocess.temporal_smoothing import apply_temporal_smoothing
from analysis.glm_fitter import fit_glm, estimate_effect_size
from analysis.split_half_validator import run_split_half_validation
from models.simulation_config import SimulationConfig
from utils.seed_manager import set_global_seed
from utils.memory_monitor import monitor_and_ensure_memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('results/pipeline_run.log')
    ]
)
logger = logging.getLogger(__name__)


def create_config(args: argparse.Namespace) -> SimulationConfig:
    """
    Create a SimulationConfig object from command-line arguments.

    Args:
        args (argparse.Namespace): Parsed command-line arguments containing
            dataset_id, sample_size, smoothing_kernel, random_seed, etc.

    Returns:
        SimulationConfig: A validated configuration object for the pipeline run.

    Raises:
        ValueError: If required arguments are missing or invalid.
    """
    if not args.dataset_id:
        raise ValueError("Dataset ID is required")

    if args.sample_size <= 0:
        raise ValueError("Sample size must be positive")

    if args.smoothing_kernel not in [4, 8]:
        raise ValueError("Smoothing kernel must be 4 or 8 mm")

    config = SimulationConfig(
        dataset_id=args.dataset_id,
        sample_size_target=args.sample_size,
        smoothing_kernel=args.smoothing_kernel,
        num_iterations=args.num_iterations,
        random_seed=args.random_seed,
        alpha_level=args.alpha_level,
        output_dir=Path(args.output_dir) if args.output_dir else Path("results")
    )

    logger.info(f"Created configuration: {config}")
    return config


def run_pipeline(config: SimulationConfig) -> dict:
    """
    Execute the full statistical power analysis pipeline.

    This function performs the following steps:
    1. Set random seed for reproducibility
    2. Monitor memory usage
    3. Download and validate dataset
    4. Preprocess data (ROI extraction, temporal smoothing)
    5. Fit GLM and estimate effect sizes
    6. Perform split-half validation
    7. Generate power curves if requested

    Args:
        config (SimulationConfig): The configuration object containing
            all parameters for the pipeline run.

    Returns:
        dict: A dictionary containing the results of the pipeline execution,
            including effect sizes, p-values, replication success flags,
            and power curve data if generated.

    Raises:
        RuntimeError: If any step in the pipeline fails unexpectedly.
    """
    logger.info("Starting pipeline execution")
    start_time = datetime.now()

    # Step 1: Set random seed
    set_global_seed(config.random_seed)
    logger.info(f"Random seed set to {config.random_seed}")

    # Step 2: Memory monitoring
    memory_status = monitor_and_ensure_memory(threshold_gb=6.0)
    logger.info(f"Memory status: {memory_status}")

    # Step 3: Download and validate dataset
    dataset_path = Path("data/raw") / config.dataset_id
    if not dataset_path.exists():
        logger.info(f"Downloading dataset {config.dataset_id}")
        fetch_paradigm_data(config.dataset_id, "data/raw")
    
    logger.info(f"Validating dataset structure at {dataset_path}")
    if not validate_bids_structure(dataset_path):
        raise RuntimeError("Dataset validation failed")

    valid_subjects = get_valid_subjects_list(dataset_path)
    logger.info(f"Found {len(valid_subjects)} valid subjects")

    if len(valid_subjects) < config.sample_size_target:
        logger.warning(f"Requested sample size {config.sample_size_target} exceeds available {len(valid_subjects)}")
        # Clamp to available data (handled by downstream components)

    # Step 4: Preprocessing
    logger.info("Starting preprocessing: ROI extraction")
    roi_data_path = preprocess_and_extract(
        bids_path=dataset_path,
        output_dir=Path("data/derived") / config.dataset_id / "roi"
    )

    logger.info(f"Applying temporal smoothing with kernel {config.smoothing_kernel}mm")
    smoothed_data_path = apply_temporal_smoothing(
        roi_data_path=roi_data_path,
        kernel_size=config.smoothing_kernel,
        output_dir=Path("data/derived") / config.dataset_id / "smoothed"
    )

    # Step 5: GLM fitting and effect size estimation
    logger.info("Fitting GLM models")
    glm_results = fit_glm(smoothed_data_path, config)
    effect_sizes = estimate_effect_size(glm_results)

    # Step 6: Split-half validation
    logger.info("Running split-half validation")
    validation_results = run_split_half_validation(
        smoothed_data_path=smoothed_data_path,
        config=config,
        effect_sizes=effect_sizes
    )

    # Step 7: Power curve generation (if requested)
    power_curve_results = None
    if config.num_iterations > 1:
        logger.info("Generating power curves")
        power_curve_results = generate_power_curve(
            smoothed_data_path=smoothed_data_path,
            config=config,
            validation_results=validation_results
        )

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    results = {
        "config": {
            "dataset_id": config.dataset_id,
            "sample_size": config.sample_size_target,
            "smoothing_kernel": config.smoothing_kernel,
            "random_seed": config.random_seed
        },
        "effect_sizes": effect_sizes,
        "validation": validation_results,
        "power_curve": power_curve_results,
        "execution_time_seconds": duration,
        "timestamp": end_time.isoformat()
    }

    # Save results
    output_file = config.output_dir / f"pipeline_run_{config.dataset_id}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Pipeline completed. Results saved to {output_file}")
    return results


def main():
    """
    Command-line entry point for the pipeline.

    Parses arguments, creates configuration, and runs the pipeline.
    """
    parser = argparse.ArgumentParser(
        description="Statistical Power Analysis Pipeline for fMRI Data"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML configuration file (optional, overrides CLI args)"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="OpenNeuro dataset ID (e.g., ds000030)"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=20,
        help="Target sample size (number of subjects)"
    )
    parser.add_argument(
        "--smoothing-kernel",
        type=int,
        default=4,
        choices=[4, 8],
        help="Temporal smoothing kernel size in mm (4 or 8)"
    )
    parser.add_argument(
        "--num-iterations",
        type=int,
        default=1,
        help="Number of bootstrap iterations for power curve generation"
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--alpha-level",
        type=float,
        default=0.05,
        help="Significance level for statistical tests"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory for output files"
    )

    args = parser.parse_args()

    try:
        config = create_config(args)
        results = run_pipeline(config)
        logger.info("Pipeline completed successfully")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
