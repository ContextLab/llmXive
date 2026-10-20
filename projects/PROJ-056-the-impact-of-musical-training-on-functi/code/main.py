"""
Main entry point for the llmXive research pipeline: The Impact of Musical Training on Functional Connectivity.

This script orchestrates the entire workflow, supporting two modes:
1. Synthetic verification mode (`--mode synthetic`): runs the pipeline on synthetic data.
2. Real‑data mode (`--mode real`): reports unavailability and writes a status JSON.
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

# Ensure the project root is the working directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_ROOT)

# Make sure the code directory is importable
if str(PROJECT_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

# Project utilities
from utils.logging import configure_logger, get_logger
from utils.memory_monitor import (
    check_memory_limit,
    get_memory_usage_report,
    MemoryLimitExceeded,
)
from data.preprocess import preprocess_subjects
from data.output_cleaned_subjects import write_cleaned_subjects
from analysis.connectivity import (
    generate_group_connectivity_results,
)
from analysis.run_nbs import run_nbs_analysis
from analysis.correlation import process_correlation_analysis
from analysis.sensitivity import process_sensitivity_analysis
from analysis.output_correlation_results import process_correlation_output
from analysis.download_atlas import main as download_atlas_main

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions for the synthetic verification pipeline
# ----------------------------------------------------------------------
def _generate_synthetic_subjects(num_subjects: int = 100, seed: int = 0) -> pd.DataFrame:
    """Create a simple synthetic subject table used by the verification pipeline."""
    np.random.seed(seed)
    per_group = num_subjects // 2
    total = per_group * 2
    subject_ids = [f"SYNTH_{i:04d}" for i in range(total)]
    groups = (["musician"] * per_group) + (["non_musician"] * per_group)

    years_of_training = (
        np.random.randint(1, 11, size=per_group).tolist() + [0] * per_group
    )
    ages = np.random.randint(12, 19, size=total).tolist()
    sexes = np.random.choice(["M", "F"], size=total).tolist()
    motion_score = np.random.uniform(0.0, 0.5, size=total).round(3).tolist()
    ses_score = np.random.uniform(0.0, 1.0, size=total).round(3).tolist()

    return pd.DataFrame({
        "subject_id": subject_ids,
        "group": groups,
        "years_of_training": years_of_training,
        "age": ages,
        "sex": sexes,
        "motion_score": motion_score,
        "ses_score": ses_score,
    })

def _generate_synthetic_time_series(num_subjects: int, n_timepoints: int = 200,
                                    n_rois: int = 400, seed: int = 0):
    """Create random Gaussian time‑series for each synthetic subject."""
    np.random.seed(seed)
    subjects_data = []
    for i in range(num_subjects):
        subject_id = f"SYNTH_{i:04d}"
        ts = np.random.randn(n_timepoints, n_rois) * 0.5
        subjects_data.append({"subject_id": subject_id, "time_series": ts})
    return subjects_data

# ----------------------------------------------------------------------
# Minimal placeholder implementations for downstream analysis steps
# ----------------------------------------------------------------------
def _write_placeholder_csv(path: Path, columns: list):
    """Write an empty CSV with the requested column headers."""
    df = pd.DataFrame(columns=columns)
    df.to_csv(path, index=False)

# ----------------------------------------------------------------------
# Pipeline runners
# ----------------------------------------------------------------------
def run_verification_mode(output_dir: str, n_subjects: int, seed: int) -> bool:
    """Execute the full synthetic verification pipeline."""
    logger.info("Starting VERIFICATION MODE pipeline.")
    start_time = time.time()
    try:
        # 1️⃣ Synthetic subject table
        df_subjects = _generate_synthetic_subjects(num_subjects=n_subjects, seed=seed)
        check_memory_limit()

        subjects_parquet_path = Path(output_dir) / "subjects.parquet"
        df_subjects.to_parquet(subjects_parquet_path, index=False)
        check_memory_limit()

        # 2️⃣ Pre‑process / matching (synthetic mode uses a simple pass‑through)
        cleaned_df = preprocess_subjects(
            df=df_subjects,
            mode="verification",
            synthetic_count=len(df_subjects),
            output_dir=output_dir,
        )
        check_memory_limit()

        # 3️⃣ Write cleaned subject CSV and also a Parquet version (required by downstream)
        cleaned_csv_path = Path(output_dir) / "subjects_cleaned.csv"
        write_cleaned_subjects(cleaned_df, cleaned_csv_path)
        cleaned_parquet_path = Path(output_dir) / "subjects_cleaned.parquet"
        cleaned_df.to_parquet(cleaned_parquet_path, index=False)
        check_memory_limit()

        # 4️⃣ Balance report (simple aggregate)
        balance_report_path = Path(output_dir) / "matching_balance_report.csv"
        balance_df = (
            cleaned_df.groupby("group")
            .agg(
                mean_age=("age", "mean"),
                mean_motion=("motion_score", "mean"),
                mean_ses=("ses_score", "mean"),
                n_subjects=("subject_id", "count"),
            )
            .reset_index()
        )
        balance_df.to_csv(balance_report_path, index=False)
        check_memory_limit()

        # 5️⃣ Download / generate a minimal atlas
        download_atlas_main()
        atlas_path = Path("data/atlas/schaefer_400.csv")
        if not atlas_path.is_file():
            raise FileNotFoundError("Atlas download failed.")

        # 6️⃣ Generate synthetic time‑series and compute connectivity
        subjects_data = _generate_synthetic_time_series(
            num_subjects=len(cleaned_df), n_timepoints=200, n_rois=400, seed=seed
        )
        matrices, _ = generate_group_connectivity_results(
            subjects_data=subjects_data,
            atlas_path=atlas_path,
            output_dir=Path(output_dir),
            chunk_size=50,
        )
        check_memory_limit()

        # 7️⃣ Write placeholder connectivity statistics CSV
        conn_stats_path = Path(output_dir) / "connectivity_results.csv"
        _write_placeholder_csv(
            conn_stats_path,
            [
                "connection_id",
                "t_stat",
                "p_value",
                "q_value",
                "effect_size",
                "ci_lower",
                "ci_upper",
            ],
        )
        check_memory_limit()

        # 8️⃣ NBS placeholder results
        nbs_results = run_nbs_analysis(str(cleaned_csv_path))
        nbs_path = Path(output_dir) / "nbs_results.csv"
        nbs_results.to_csv(nbs_path, index=False)
        check_memory_limit()

        # 9️⃣ Correlation & sensitivity placeholders
        corr_results = process_correlation_analysis(str(cleaned_csv_path))
        sens_results = process_sensitivity_analysis(corr_results)

        corr_out_path = Path(output_dir) / "correlation_results.csv"
        sens_out_path = Path(output_dir) / "sensitivity_analysis.csv"
        process_correlation_output(corr_results, sens_results,
                                   str(corr_out_path), str(sens_out_path))
        check_memory_limit()

        elapsed = time.time() - start_time
        logger.info(
            f"Verification Mode completed in {elapsed:.2f}s. Memory: {get_memory_usage_report()}"
        )
        return True
    except MemoryLimitExceeded as e:
        logger.error(f"Memory limit exceeded: {e}")
        return False
    except Exception as e:
        logger.error(f"Verification Mode failed: {e}")
        logger.error(traceback.format_exc())
        return False

def run_real_mode(data_path: str, output_dir: str) -> bool:
    """Stub for real‑data mode – reports unavailability and writes a status JSON."""
    logger.info("Starting REAL‑DATA MODE pipeline (stub).")
    # The real ingestion script handles messaging and status file creation.
    from data.real_ingest import main as real_ingest_main
    # The real_ingest script always exits with code 0 per the updated spec.
    exit_code = real_ingest_main()
    return exit_code == 0

def main():
    parser = argparse.ArgumentParser(description="Musical Training Connectivity Analysis")
    parser.add_argument("--mode", type=str, required=True, choices=["synthetic", "real"])
    parser.add_argument("--n-subjects", type=int, default=100)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-permutations", type=int, default=1000)
    parser.add_argument("--data-path", type=str, default="./data/raw")
    parser.add_argument("--output-dir", type=str, default="./data/processed")
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = parser.parse_args()

    # Initialise logging – configure_logger does not accept a ``log_level`` keyword,
    # so we call it without arguments and then set the logger level explicitly.
    configure_logger()
    logger.setLevel(args.log_level)

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    if args.mode == "synthetic":
        success = run_verification_mode(args.output_dir, args.n_subjects, args.seed)
    else:
        success = run_real_mode(args.data_path, args.output_dir)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
