"""
Main orchestration script for the augmentation impact study.

Coordinates the full pipeline: Download -> Subsample -> Baseline -> Augment -> Analyze -> Report.
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import project modules
# Note: These imports assume the modules are in the same directory
from download_data import main as download_main
from subsample import process_dataset
from simulation import run_full_simulation, save_results
from augment import augment_dataset
from analyze import analyze_baseline_results, generate_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT: Path = Path(__file__).parent.parent
DATA_RAW_DIR: Path = PROJECT_ROOT / "data" / "raw"
DATA_DERIVED_DIR: Path = PROJECT_ROOT / "data" / "derived"
RESULTS_DIR: Path = PROJECT_ROOT / "results"

# Ensure directories exist
DATA_DERIVED_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def run_pipeline(
    datasets: Optional[List[str]] = None,
    sample_sizes: Optional[List[int]] = None,
    n_iterations: int = 100,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Run the full analysis pipeline.

    Args:
        datasets: List of dataset names to process. Defaults to all available.
        sample_sizes: List of sample sizes to test. Defaults to [15, 25, 40].
        n_iterations: Number of Monte Carlo iterations per configuration.
        seed: Base random seed.

    Returns:
        Dictionary with pipeline execution summary.
    """
    logger.info("Starting full analysis pipeline...")

    if datasets is None:
        datasets = ['breast_cancer', 'ionosphere', 'heart_disease']

    if sample_sizes is None:
        sample_sizes = [15, 25, 40]

    results: List[Dict[str, Any]] = []
    execution_summary: Dict[str, Any] = {
        'datasets_processed': [],
        'configurations_run': 0,
        'errors': []
    }

    # Step 1: Download data (if not already done)
    logger.info("Step 1: Ensuring data is downloaded...")
    # Note: In a real run, we would check if data exists before downloading
    # For now, we assume download_data.py has been run or data exists

    # Step 2: Process each dataset
    for dataset_name in datasets:
        logger.info(f"Processing dataset: {dataset_name}")
        execution_summary['datasets_processed'].append(dataset_name)

        # Load dataset
        dataset_path: Path = DATA_RAW_DIR / f"{dataset_name}.csv"
        if not dataset_path.exists():
            error_msg: str = f"Dataset not found: {dataset_path}"
            logger.error(error_msg)
            execution_summary['errors'].append(error_msg)
            continue

        try:
            import pandas as pd
            df: pd.DataFrame = pd.read_csv(dataset_path)

            # Detect target column
            target_col: str = detect_target_column(df)

            # Step 3: Run baseline simulation for each sample size
            for n in sample_sizes:
                logger.info(
                    f"Running baseline simulation: {dataset_name}, n={n}, "
                    f"iterations={n_iterations}"
                )

                # Subsample
                from subsample import process_dataset as subsample_func
                subsample_df = subsample_func(df, dataset_name, n, seed)

                if subsample_df is None:
                    logger.warning(f"Skipping {dataset_name} at n={n}: subsampling failed")
                    continue

                # Run simulation (null condition)
                baseline_results = run_full_simulation(
                    subsample_df, target_col, n_iterations, 'null', seed
                )

                # Save results
                save_results(
                    baseline_results, dataset_name, n, 'null', 'baseline'
                )

                # Analyze
                analysis = analyze_baseline_results({
                    'p_values': [r['p_value'] for r in baseline_results],
                    'metadata': {'dataset': dataset_name, 'size': n}
                })

                results.append({
                    'dataset': dataset_name,
                    'size': n,
                    'method': 'baseline',
                    'condition': 'null',
                    **analysis
                })

                execution_summary['configurations_run'] += 1

        except Exception as e:
            error_msg: str = f"Error processing {dataset_name}: {str(e)}"
            logger.error(error_msg)
            execution_summary['errors'].append(error_msg)

    # Step 4: Generate final report
    logger.info("Generating final analysis report...")
    report_path: Path = generate_report(results)

    execution_summary['report_path'] = str(report_path)
    execution_summary['status'] = 'complete'

    logger.info(f"Pipeline complete. Processed {execution_summary['configurations_run']} configurations.")

    return execution_summary


def detect_target_column(df) -> str:
    """
    Detect target column in DataFrame.

    Args:
        df: Input DataFrame.

    Returns:
        Target column name.
    """
    priority = ['target', 'class', 'label']
    for col in priority:
        if col in df.columns:
            return col
    return df.columns[-1]


def main() -> int:
    """
    Main entry point for the pipeline.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Run the full augmentation impact analysis pipeline."
    )
    parser.add_argument(
        '--datasets',
        nargs='+',
        default=None,
        help='Datasets to process (default: all available)'
    )
    parser.add_argument(
        '--sizes',
        nargs='+',
        type=int,
        default=None,
        help='Sample sizes to test (default: 15 25 40)'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=100,
        help='Number of Monte Carlo iterations (default: 100)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed (default: 42)'
    )

    args: argparse.Namespace = parser.parse_args()

    try:
        summary: Dict[str, Any] = run_pipeline(
            datasets=args.datasets,
            sample_sizes=args.sizes,
            n_iterations=args.iterations,
            seed=args.seed
        )

        if summary.get('errors'):
            logger.error(f"Pipeline completed with {len(summary['errors'])} errors")
            return 1

        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit(main())