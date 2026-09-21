"""
Multi-Paradigm Runner for Statistical Power Analysis.

This module orchestrates the power curve generation loop across the 5 distinct
cognitive paradigms (Motor, Working Memory, etc.) defined in the research plan.
It depends on T022 (power_curve_generator) to perform the actual calculations.

Usage:
    python code/analysis/multi_paradigm_runner.py
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Import from local project structure
# T022 dependency: power_curve_generator
from analysis.power_curve_generator import generate_power_curve, save_power_curves
from utils.seed_manager import set_global_seed
from utils.memory_monitor import monitor_and_ensure_memory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("results/paper/multi_paradigm_run.log")
    ]
)
logger = logging.getLogger(__name__)

# Define the 5 distinct cognitive paradigms as per research.md/specs
# These correspond to OpenNeuro dataset IDs typically used in power analysis
PARADIGM_CONFIG = {
    "motor": {
        "dataset_id": "ds000030",
        "label": "Motor Task",
        "description": "Simple motor response task (finger tapping)"
    },
    "working_memory": {
        "dataset_id": "ds000205",
        "label": "Working Memory Task",
        "description": "N-back working memory paradigm"
    },
    "emotion_processing": {
        "dataset_id": "ds000105",
        "label": "Emotion Processing Task",
        "description": "Facial emotion recognition task"
    },
    "reward_processing": {
        "dataset_id": "ds000227",
        "label": "Reward Processing Task",
        "description": "Monetary incentive delay task"
    },
    "language_processing": {
        "dataset_id": "ds000212",
        "label": "Language Processing Task",
        "description": "Sentence comprehension task"
    }
}

def run_paradigm_analysis(
    paradigm_key: str,
    config: Dict[str, Any],
    sample_sizes: List[int],
    smoothing_kernels: List[float],
    num_iterations: int,
    output_dir: Path
) -> Dict[str, Any]:
    """
    Run power curve generation for a single paradigm.

    Args:
        paradigm_key: Unique identifier for the paradigm
        config: Configuration dictionary for the paradigm
        sample_sizes: List of sample sizes to test (e.g., [10, 20, 30, 40])
        smoothing_kernels: List of temporal smoothing kernels (e.g., [4.0, 8.0])
        num_iterations: Number of bootstrap iterations per sample size
        output_dir: Directory to save results

    Returns:
        Dictionary containing results for this paradigm
    """
    logger.info(f"Starting analysis for paradigm: {paradigm_key} ({config['label']})")
    
    dataset_id = config["dataset_id"]
    logger.info(f"Using dataset: {dataset_id}")

    # Ensure memory safety before heavy computation
    monitor_and_ensure_memory(threshold_gb=6.0)

    try:
        # Generate power curves using T022 implementation
        power_results = generate_power_curve(
            dataset_id=dataset_id,
            sample_sizes=sample_sizes,
            smoothing_kernels=smoothing_kernels,
            num_iterations=num_iterations,
            output_dir=output_dir / paradigm_key
        )

        # Save results
        save_power_curves(power_results, output_dir / paradigm_key / "power_curves.json")

        logger.info(f"Successfully completed analysis for {paradigm_key}")
        return {
            "paradigm_key": paradigm_key,
            "dataset_id": dataset_id,
            "status": "success",
            "results_summary": {
                "sample_sizes_tested": power_results.get("sample_sizes_tested", []),
                "num_iterations": num_iterations,
                "kernels_used": power_results.get("kernels_used", [])
            }
        }

    except Exception as e:
        logger.error(f"Failed to process paradigm {paradigm_key}: {str(e)}", exc_info=True)
        return {
            "paradigm_key": paradigm_key,
            "dataset_id": dataset_id,
            "status": "failed",
            "error_message": str(e)
        }

def run_multi_paradigm_loop(
    sample_sizes: List[int],
    smoothing_kernels: List[float],
    num_iterations: int,
    output_dir: Path,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Orchestrate power curve generation across all 5 paradigms.

    This is the main entry point for T029.

    Args:
        sample_sizes: List of sample sizes to test
        smoothing_kernels: List of temporal smoothing kernels
        num_iterations: Number of bootstrap iterations per sample size
        output_dir: Root directory for all outputs
        seed: Random seed for reproducibility

    Returns:
        Aggregated results dictionary
    """
    # Set global seed for reproducibility
    set_global_seed(seed)
    logger.info(f"Global random seed set to: {seed}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")

    start_time = datetime.now()
    logger.info(f"Multi-paradigm run started at {start_time}")

    all_results = {
        "run_metadata": {
            "start_time": start_time.isoformat(),
            "seed": seed,
            "sample_sizes": sample_sizes,
            "smoothing_kernels": smoothing_kernels,
            "num_iterations": num_iterations,
            "paradigms_total": len(PARADIGM_CONFIG)
        },
        "paradigm_results": []
    }

    successful_count = 0
    failed_count = 0

    # Iterate through all 5 paradigms
    for paradigm_key, config in PARADIGM_CONFIG.items():
        logger.info(f"Processing paradigm {paradigm_key} ({failed_count + successful_count + 1}/{len(PARADIGM_CONFIG)})")
        
        result = run_paradigm_analysis(
            paradigm_key=paradigm_key,
            config=config,
            sample_sizes=sample_sizes,
            smoothing_kernels=smoothing_kernels,
            num_iterations=num_iterations,
            output_dir=output_dir
        )

        all_results["paradigm_results"].append(result)

        if result["status"] == "success":
            successful_count += 1
        else:
            failed_count += 1

    end_time = datetime.now()
    duration = end_time - start_time

    all_results["run_metadata"]["end_time"] = end_time.isoformat()
    all_results["run_metadata"]["duration_seconds"] = duration.total_seconds()
    all_results["summary"] = {
        "total_paradigms": len(PARADIGM_CONFIG),
        "successful": successful_count,
        "failed": failed_count,
        "success_rate": successful_count / len(PARADIGM_CONFIG) if len(PARADIGM_CONFIG) > 0 else 0.0
    }

    # Save aggregated results
    aggregated_path = output_dir / "multi_paradigm_aggregated.json"
    with open(aggregated_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    logger.info(f"Aggregated results saved to: {aggregated_path}")
    logger.info(f"Multi-paradigm run completed in {duration} with {successful_count}/{len(PARADIGM_CONFIG)} successes")

    return all_results

def main():
    """CLI entry point for multi-paradigm runner."""
    parser = argparse.ArgumentParser(
        description="Run power curve analysis across multiple cognitive paradigms"
    )
    parser.add_argument(
        "--sample-sizes",
        type=int,
        nargs="+",
        default=[10, 20, 30, 40],
        help="Sample sizes to test (default: 10 20 30 40)"
    )
    parser.add_argument(
        "--kernels",
        type=float,
        nargs="+",
        default=[4.0],
        help="Temporal smoothing kernels in mm (default: 4.0)"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of bootstrap iterations per sample size (default: 100)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/aggregated",
        help="Output directory for results (default: data/aggregated)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )

    args = parser.parse_args()

    try:
        results = run_multi_paradigm_loop(
            sample_sizes=args.sample_sizes,
            smoothing_kernels=args.kernels,
            num_iterations=args.iterations,
            output_dir=Path(args.output_dir),
            seed=args.seed
        )

        # Exit with error code if any paradigm failed
        if results["summary"]["failed"] > 0:
            logger.warning(f"Completed with {results['summary']['failed']} failures")
            sys.exit(1)
        
        sys.exit(0)

    except Exception as e:
        logger.error(f"Critical error in multi-paradigm runner: {str(e)}", exc_info=True)
        sys.exit(2)

if __name__ == "__main__":
    main()