"""
Main entry point for the llmXive research pipeline: The Impact of Musical Training on Functional Connectivity.

This script orchestrates the entire research workflow, supporting two distinct modes:
1. Synthetic verification mode (`--mode synthetic`): runs the pipeline on synthetic data to validate code correctness,
   data flow, and memory constraints without requiring real biological data.
2. Real-data mode (`--mode real`): runs the pipeline on real, verified neuroimaging data (e.g., ABCD, HCP)
   to produce scientifically valid results.

Usage:
    python code/main.py --mode synthetic --n-subjects 100 --seed 42
    python code/main.py --mode real --data-path /path/to/verified/dataset
"""

import argparse
import sys
import os
from pathlib import Path
import logging
import traceback
import time

import numpy as np
import pandas as pd

# Project root is the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

# Ensure the code directory is on the import path
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

# ----------------------------------------------------------------------
# Local imports – these must match the existing API surface
# ----------------------------------------------------------------------
from utils.logging import configure_logger, get_logger
from utils.memory_monitor import check_memory_limit, get_memory_usage_report, MemoryLimitExceeded
from data.preprocess import preprocess_subjects
from data.output_cleaned_subjects import write_cleaned_subjects
from analysis.connectivity import generate_group_connectivity_results
from analysis.stats import process_connectivity_statistics
from analysis.output_connectivity_results import write_connectivity_results
from analysis.run_nbs import run_nbs_analysis
from analysis.output_nbs_results import write_nbs_results
from analysis.correlation import process_correlation_analysis
from analysis.sensitivity import process_sensitivity_analysis
from analysis.output_correlation_results import process_correlation_output
from analysis.download_atlas import main as download_atlas_main

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions for synthetic data generation (verification mode)
# ----------------------------------------------------------------------
def _generate_synthetic_subjects(num_subjects: int = 100, seed: int = 0) -> pd.DataFrame:
    """
    Generate a deterministic synthetic behavioural table for verification.

    Parameters
    ----------
    num_subjects : int
        Total number of subjects (will be split evenly between musician and non‑musician).
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        Synthetic subject metadata with required columns.
    """
    np.random.seed(seed)
    per_group = num_subjects // 2
    total = per_group * 2
    subject_ids = [f"SYNTH_{i:04d}" for i in range(total)]

    groups = (["musician"] * per_group) + (["non_musician"] * per_group)
    years_of_training = (
        np.random.randint(1, 11, size=per_group).tolist() +  # musicians: >=1 yr
        [0] * per_group                                      # non‑musicians: 0 yr
    )
    ages = np.random.randint(12, 19, size=total).tolist()
    sexes = np.random.choice(["M", "F"], size=total).tolist()
    motion_score = np.random.uniform(0.0, 0.5, size=total).round(3).tolist()
    ses_score = np.random.uniform(0.0, 1.0, size=total).round(3).tolist()

    df = pd.DataFrame({
        "subject_id": subject_ids,
        "group": groups,
        "years_of_training": years_of_training,
        "age": ages,
        "sex": sexes,
        "motion_score": motion_score,
        "ses_score": ses_score,
    })
    return df

def _generate_synthetic_time_series(num_subjects: int, n_timepoints: int = 200, n_rois: int = 400, seed: int = 0):
    """
    Produce a deterministic list of dictionaries suitable for
    ``generate_group_connectivity_results`` in verification mode.
    """
    np.random.seed(seed)
    subjects_data = []
    for i in range(num_subjects):
        subject_id = f"SYNTH_{i:04d}"
        ts = np.random.randn(n_timepoints, n_rois) * 0.5
        subjects_data.append({"subject_id": subject_id, "time_series": ts})
    return subjects_data

# ----------------------------------------------------------------------
# Verification (synthetic) mode implementation
# ----------------------------------------------------------------------
def run_verification_mode(output_dir: str, n_subjects: int, seed: int) -> bool:
    """
    Execute the pipeline using synthetic data for verification.

    Parameters
    ----------
    output_dir : str
        Directory where all processed outputs will be written.
    n_subjects : int
        Total number of synthetic subjects (even number; split evenly between groups).
    seed : int
        Random seed for reproducibility.

    Returns
    -------
    bool
        True if the pipeline completes without error, False otherwise.
    """
    logger.info("Starting VERIFICATION MODE pipeline.")
    start_time = time.time()

    try:
        # 1. Generate synthetic subject metadata
        logger.info("Generating synthetic subject metadata...")
        df_subjects = _generate_synthetic_subjects(num_subjects=n_subjects, seed=seed)
        check_memory_limit()

        # 2. Preprocess – creates subjects_cleaned.csv,
        #    dataset_validity_report.csv, matching_balance_report.csv
        logger.info("Preprocessing synthetic subjects...")
        cleaned_df = preprocess_subjects(
            df=df_subjects,
            mode="verification",
            synthetic_count=len(df_subjects),
            output_dir=output_dir,
        )
        check_memory_limit()

        cleaned_path = Path(output_dir) / "subjects_cleaned.csv"
        logger.info(f"Writing cleaned subjects to {cleaned_path}")
        write_cleaned_subjects(cleaned_df, cleaned_path)
        check_memory_limit()

        # 3. Ensure the Schaefer atlas is available (bundled stub)
        logger.info("Ensuring Schaefer atlas is present...")
        download_atlas_main()
        atlas_path = Path("data/atlas/schaefer_400.csv")
        if not atlas_path.is_file():
            raise FileNotFoundError("Atlas download failed – expected file not found.")

        # 4. Generate synthetic functional time‑series and compute connectivity
        logger.info("Generating synthetic functional time‑series for connectivity...")
        subjects_data = _generate_synthetic_time_series(
            num_subjects=len(cleaned_df),
            n_timepoints=200,
            n_rois=400,
            seed=seed,
        )

        logger.info("Computing connectivity matrices...")
        matrices, subject_ids = generate_group_connectivity_results(
            subjects_data=subjects_data,
            atlas_path=atlas_path,
            output_dir=Path(output_dir),
            chunk_size=50,
        )
        check_memory_limit()

        # 5. Statistical analysis (Welch's t‑test, FDR, Cohen's d)
        logger.info("Running statistical analysis (Welch's t-test, FDR, Cohen's d)...")
        stats_results = process_connectivity_statistics(matrices)
        check_memory_limit()

        # 6. Write connectivity statistics
        stats_path = Path(output_dir) / "connectivity_results.csv"
        write_connectivity_results(stats_results, str(stats_path))
        logger.info(f"Connectivity statistics written to {stats_path}")

        # 7. Network‑Based Statistic (placeholder implementation)
        logger.info("Running Network Based Statistic (NBS) placeholder...")
        nbs_results = run_nbs_analysis(str(cleaned_path))
        check_memory_limit()

        nbs_path = Path(output_dir) / "nbs_results.csv"
        write_nbs_results(nbs_results, str(nbs_path))
        logger.info(f"NBS results written to {nbs_path}")

        # 8. Correlation analysis (musician‑only)
        logger.info("Running correlation analysis (Years of Training vs Connectivity)...")
        corr_results = process_correlation_analysis(str(cleaned_path))
        check_memory_limit()

        # 9. Sensitivity analysis over FDR thresholds
        logger.info("Running sensitivity analysis...")
        sens_results = process_sensitivity_analysis(corr_results)
        check_memory_limit()

        # 10. Write correlation & sensitivity outputs
        corr_out_path = Path(output_dir) / "correlation_results.csv"
        sens_out_path = Path(output_dir) / "sensitivity_analysis.csv"
        process_correlation_output(
            corr_results,
            sens_results,
            str(corr_out_path),
            str(sens_out_path),
        )
        logger.info(f"Correlation results written to {corr_out_path}")
        logger.info(f"Sensitivity results written to {sens_out_path}")

        elapsed = time.time() - start_time
        logger.info(f"Verification Mode completed successfully in {elapsed:.2f} seconds.")
        logger.info(f"Memory Report: {get_memory_usage_report()}")
        return True

    except MemoryLimitExceeded as e:
        logger.error(f"Memory limit exceeded during verification: {e}")
        logger.error(get_memory_usage_report())
        return False
    except Exception as e:
        logger.error(f"Verification Mode failed with unexpected error: {e}")
        logger.error(traceback.format_exc())
        return False

# ----------------------------------------------------------------------
# Real‑data mode implementation (graceful stub when no dataset is available)
# ----------------------------------------------------------------------
def run_real_mode(data_path: str, output_dir: str) -> bool:
    """
    Execute the pipeline using real neuroimaging data.

    This implementation follows the specification's edge‑case: if no
    verified dataset is supplied, the real‑data ingestion script will
    report unavailability and exit 0 with a status JSON. The pipeline
    therefore aborts early with a clear message rather than raising an
    unhandled exception.

    Parameters
    ----------
    data_path : str
        Path to the real data directory or manifest.
    output_dir : str
        Directory for processed outputs.

    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    logger.info("Starting REAL‑DATA MODE pipeline.")
    logger.warning("Real‑data mode is currently a graceful stub pending a verified dataset.")
    start_time = time.time()

    try:
        # 1. Attempt to ingest real data – this will invoke the stub
        #    which writes a JSON status file and returns a DataFrame
        #    placeholder if the dataset is unavailable.
        from data.real_ingest import main as real_ingest_main

        exit_code = real_ingest_main()
        if exit_code != 0:
            logger.error("Real‑data ingestion failed (see status JSON).")
            return False

        # Since no real data is present, we stop here. In a future
        # iteration, the code below would mirror the verification
        # workflow but using the loaded real subjects and time‑series.
        logger.info("Real‑data ingestion reported no dataset; pipeline ends gracefully.")
        return True

    except Exception as e:
        logger.error(f"Real‑data mode failed with unexpected error: {e}")
        logger.error(traceback.format_exc())
        return False

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Main pipeline for Musical Training Connectivity Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
          python code/main.py --mode synthetic --n-subjects 100 --seed 42
          python code/main.py --mode real --data-path ./data/raw
        """,
    )
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["synthetic", "real"],
        help="Mode of operation: 'synthetic' (verification) or 'real' (real data).",
    )
    parser.add_argument(
        "--n-subjects",
        type=int,
        default=100,
        help="Total number of synthetic subjects (even number). Ignored in real mode.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for synthetic data generation.",
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=1000,
        help="Number of permutations for statistical tests (placeholder).",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="./data/raw",
        help="Path to data directory (required for real mode).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data/processed",
        help="Directory for output files.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )

    args = parser.parse_args()

    # Configure logging
    configure_logger(level=args.log_level)
    logger.info(f"Pipeline initialized. Mode: {args.mode}, Data: {args.data_path}")

    # Ensure output directory exists
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Execute pipeline
    if args.mode == "synthetic":
        success = run_verification_mode(args.output_dir, args.n_subjects, args.seed)
    elif args.mode == "real":
        success = run_real_mode(args.data_path, args.output_dir)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)

    if success:
        logger.info("Pipeline execution finished successfully.")
        sys.exit(0)
    else:
        logger.error("Pipeline execution failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
