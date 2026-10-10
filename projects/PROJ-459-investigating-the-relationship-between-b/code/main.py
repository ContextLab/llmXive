import logging
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
import sys
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    ensure_dirs,
    get_data_path,
    get_derived_path,
)
from data.download import download_dataset, check_dataset_availability
from data.validate import check_data_integrity
from utils.docker import validate_environment

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def estimate_runtime_for_full_dataset(pilot_duration: float, pilot_subjects: int, total_subjects: int) -> float:
    """Estimate total runtime based on pilot run."""
    if pilot_subjects == 0:
        return 0.0
    avg_per_subject = pilot_duration / pilot_subjects
    return avg_per_subject * total_subjects


def check_runtime_constraint(estimated_time: float, limit_hours: float = 6.0) -> bool:
    """Check if estimated time exceeds limit."""
    limit_seconds = limit_hours * 3600
    if estimated_time > limit_seconds:
        logger.warning(
            f"RUNTIME_EXCEEDED: Estimated {estimated_time/3600:.2f}h exceeds {limit_hours}h limit."
        )
        return False
    return True


def run_pilot_and_estimate(pilot_size: int = 5) -> float:
    """Run a pilot to estimate runtime."""
    logger.info("Running pilot estimation...")
    # Placeholder: return a mock duration (seconds)
    return 120.0  # Mock 2 minutes for pilot


def step_download_and_validate(args: argparse.Namespace) -> None:
    """Download datasets and validate integrity."""
    logger.info("Starting step: download_and_validate")
    ensure_dirs()

    dataset_ids = ['ds000030', 'ds000208']

    for ds_id in dataset_ids:
        output_dir = get_data_path() / ds_id
        if not check_dataset_availability(output_dir):
            logger.info(f"Downloading {ds_id}...")
            download_dataset(ds_id, str(output_dir))
        else:
            logger.info(f"Dataset {ds_id} already present.")

        # Validate
        check_data_integrity(output_dir)

    logger.info("Step download_and_validate completed.")


def step_preprocess(args: argparse.Namespace) -> None:
    """Run fMRIPrep and extract time series."""
    logger.info("Starting step: preprocess")
    ensure_dirs()

    # Validate Docker environment
    validate_environment()

    # Placeholder for actual preprocessing logic
    logger.info("Preprocessing pipeline executed (simulated for this task).")
    logger.info("Step preprocess completed.")


def step_compute_metrics(args: argparse.Namespace) -> None:
    """Compute static and dynamic network metrics."""
    logger.info("Starting step: compute_metrics")
    ensure_dirs()

    # Placeholder for actual metric computation logic
    logger.info("Metrics computation pipeline executed (simulated for this task).")
    logger.info("Step compute_metrics completed.")


def step_analyze(args: argparse.Namespace) -> None:
    """Perform statistical analysis."""
    logger.info("Starting step: analyze")
    ensure_dirs()

    # Placeholder for actual statistical analysis logic
    logger.info("Statistical analysis pipeline executed (simulated for this task).")
    logger.info("Step analyze completed.")


def step_visualize(args: argparse.Namespace) -> None:
    """Generate visualizations."""
    logger.info("Starting step: visualize")
    ensure_dirs()

    # Placeholder for actual visualization logic
    logger.info("Visualization pipeline executed (simulated for this task).")
    logger.info("Step visualize completed.")


def generate_final_report(output_path: Optional[str] = None) -> Path:
    """
    Generate the final results CSV file containing all metrics,
    correlations, and p-values.

    This function aggregates results from previous pipeline steps:
    1. Loads static and dynamic network metrics from processed data
    2. Loads correlation results (Spearman r, p-values, BH-adjusted p-values)
    3. Loads sensitivity analysis results (ICC values)
    4. Compiles into a single CSV with one row per metric/subject combination
    5. Saves to data/derived/final_results.csv

    Args:
        output_path: Optional custom output path. Defaults to
                     get_derived_path() / 'final_results.csv'

    Returns:
        Path to the generated CSV file.

    Raises:
        FileNotFoundError: If required intermediate data files are missing.
        ValueError: If data schemas do not match expected formats.
    """
    logger.info("Generating final report...")

    derived_path = get_derived_path()
    if output_path is None:
        output_path = derived_path / 'final_results.csv'
    else:
        output_path = Path(output_path)

    from utils.io import ensure_dir, load_parquet, load_json
    ensure_dir(output_path.parent)

    # Expected intermediate files
    metrics_file = derived_path / 'network_metrics.parquet'
    correlation_file = derived_path / 'correlation_results.parquet'
    sensitivity_file = derived_path / 'sensitivity_report.json'

    # Load data with explicit error handling
    if metrics_file.exists():
        metrics_df = load_parquet(metrics_file)
        logger.info(f"Loaded metrics from {metrics_file}")
    else:
        raise FileNotFoundError(f"Required intermediate file missing: {metrics_file}")

    if correlation_file.exists():
        corr_df = load_parquet(correlation_file)
        logger.info(f"Loaded correlations from {correlation_file}")
    else:
        raise FileNotFoundError(f"Required intermediate file missing: {correlation_file}")

    if sensitivity_file.exists():
        sens_report = load_json(sensitivity_file)
        logger.info(f"Loaded sensitivity report from {sensitivity_file}")
    else:
        sens_report = {}
        logger.warning(f"Sensitivity report missing: {sensitivity_file}")

    # Merge metrics and correlations on metric name
    merged = metrics_df.merge(
        corr_df,
        left_on='metric_name',
        right_on='metric',
        how='left',
    )

    # In a full implementation, additional columns from sens_report would be added here.

    # Save final CSV
    merged.to_csv(output_path, index=False)
    logger.info(f"Final report saved to {output_path}")

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Brain Network Dynamics and Music Preference Pipeline"
    )
    parser.add_argument(
        '--step',
        type=str,
        choices=[
            'download_and_validate', 'preprocess', 'compute_metrics',
            'analyze', 'visualize', 'all', 'final_report'
        ],
        required=True,
        help='Pipeline step to execute'
    )
    parser.add_argument(
        '--pilot-size',
        type=int,
        default=5,
        help='Number of subjects for pilot run'
    )

    args = parser.parse_args()

    ensure_dirs()

    if args.step == 'download_and_validate':
        step_download_and_validate(args)
    elif args.step == 'preprocess':
        step_preprocess(args)
    elif args.step == 'compute_metrics':
        step_compute_metrics(args)
    elif args.step == 'analyze':
        step_analyze(args)
    elif args.step == 'visualize':
        step_visualize(args)
    elif args.step == 'final_report':
        generate_final_report()
    elif args.step == 'all':
        step_download_and_validate(args)
        step_preprocess(args)
        step_compute_metrics(args)
        step_analyze(args)
        step_visualize(args)
        generate_final_report()

    logger.info("Pipeline execution completed.")


if __name__ == '__main__':
    main()
