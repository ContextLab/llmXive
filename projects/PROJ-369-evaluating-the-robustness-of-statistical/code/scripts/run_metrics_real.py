"""
Script to compute ACF, Hurst exponent, and Spectral Density for real preprocessed datasets.

This script implements task T010a:
- Reads preprocessed datasets from data/processed/
- Computes ACF, Hurst (via DFA), and Spectral Peak Ratio for each series
- Stores results in data/processed/metrics_real.json

Constraint: Must run BEFORE T019a to ensure metrics exist before shuffling.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from src.data.metrics import compute_all_metrics, MetricsError
from src.data.preprocessing import PreprocessingError
from src.utils.logging import setup_logger, log_info, log_error, log_warning
from src.utils.config import get_path

logger = logging.getLogger(__name__)

def find_preprocessed_datasets(
    processed_dir: Path,
    min_points: int = 25
) -> List[Path]:
    """
    Find all preprocessed dataset files in the processed directory.

    Args:
        processed_dir: Path to the data/processed directory
        min_points: Minimum number of points required (edge case handling)

    Returns:
        List of paths to valid preprocessed CSV files
    """
    if not processed_dir.exists():
        log_error(f"Processed directory does not exist: {processed_dir}")
        return []

    valid_extensions = {'.csv', '.parquet'}
    datasets = []

    for file_path in processed_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            # Skip manifest files and metric files
            if 'manifest' in file_path.name or 'metrics' in file_path.name:
                continue
            datasets.append(file_path)

    log_info(f"Found {len(datasets)} preprocessed dataset files")
    return datasets

def compute_metrics_for_real_datasets(
    datasets: List[Path],
    output_path: Path,
    min_points: int = 25
) -> Dict[str, Any]:
    """
    Compute ACF, Hurst, and Spectral Density for all real preprocessed datasets.

    Args:
        datasets: List of paths to preprocessed dataset files
        output_path: Path to write the metrics JSON file
        min_points: Minimum number of points required (edge case handling)

    Returns:
        Dictionary containing metrics for all processed datasets
    """
    results = {
        "metadata": {
            "script": "run_metrics_real.py",
            "task_id": "T010a",
            "description": "ACF, Hurst, and Spectral Density for real series",
        },
        "datasets": {},
        "summary": {
            "total_datasets": 0,
            "successful": 0,
            "skipped_too_short": 0,
            "errors": 0
        }
    }

    for dataset_path in datasets:
        dataset_name = dataset_path.stem
        log_info(f"Processing dataset: {dataset_name}")

        try:
            # Load the preprocessed dataset
            import pandas as pd
            df = pd.read_csv(dataset_path, index_col=0, parse_dates=True)

            # Check for minimum length (Edge Case 1)
            if len(df) < min_points:
                log_warning(f"Skipping {dataset_name}: only {len(df)} points (min: {min_points})")
                results["datasets"][dataset_name] = {
                    "status": "skipped",
                    "reason": "too_short",
                    "points": len(df)
                }
                results["summary"]["skipped_too_short"] += 1
                continue

            # Extract the time series value (assuming single column or first column)
            if df.shape[1] > 1:
                # Try to find a numeric column that looks like the target variable
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    series = df[numeric_cols[0]].values
                    column_used = numeric_cols[0]
                else:
                    series = df.iloc[:, 0].values
                    column_used = df.columns[0]
            else:
                series = df.iloc[:, 0].values
                column_used = df.columns[0]

            # Compute metrics
            metrics = compute_all_metrics(series)

            results["datasets"][dataset_name] = {
                "status": "success",
                "source_file": str(dataset_path),
                "column_used": column_used,
                "n_points": len(series),
                "metrics": metrics
            }
            results["summary"]["successful"] += 1

        except PreprocessingError as e:
            log_error(f"Preprocessing error for {dataset_name}: {e}")
            results["datasets"][dataset_name] = {
                "status": "error",
                "reason": "preprocessing_error",
                "message": str(e)
            }
            results["summary"]["errors"] += 1
        except MetricsError as e:
            log_error(f"Metrics computation error for {dataset_name}: {e}")
            results["datasets"][dataset_name] = {
                "status": "error",
                "reason": "metrics_error",
                "message": str(e)
            }
            results["summary"]["errors"] += 1
        except Exception as e:
            log_error(f"Unexpected error for {dataset_name}: {e}")
            results["datasets"][dataset_name] = {
                "status": "error",
                "reason": "unexpected_error",
                "message": str(e)
            }
            results["summary"]["errors"] += 1

    results["summary"]["total_datasets"] = len(datasets)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write results to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    log_info(f"Metrics written to {output_path}")
    log_info(f"Summary: {results['summary']}")

    return results

def main():
    """Main entry point for the metrics computation script."""
    setup_logger("run_metrics_real", level=logging.INFO)

    # Get paths
    processed_dir = get_path("data_processed")
    output_path = get_path("data_processed") / "metrics_real.json"

    log_info(f"Looking for preprocessed datasets in: {processed_dir}")
    log_info(f"Output path: {output_path}")

    # Find datasets
    datasets = find_preprocessed_datasets(processed_dir)

    if not datasets:
        log_error("No preprocessed datasets found. Ensure T016 has completed successfully.")
        sys.exit(1)

    # Compute metrics
    results = compute_metrics_for_real_datasets(datasets, output_path)

    # Exit with error if all failed
    if results["summary"]["successful"] == 0:
        log_error("No datasets were successfully processed.")
        sys.exit(1)

    log_info("T010a completed successfully")
    sys.exit(0)

if __name__ == "__main__":
    main()
