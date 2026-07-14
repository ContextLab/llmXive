from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import yaml

# Import from project modules
from agency_scoring.ingest_transcripts import ingest_transcripts
from agency_scoring.detect_markers import detect_markers
from agency_scoring.compute_scores import compute_agency_scores
from adherence_extraction.extract_metrics import extract_metrics
from analysis.merge_datasets import merge_datasets
from analysis.run_regression import run_regression, MemoryProfiler
from utils.error_handler import PipelineError, log_and_exit
from logging.pipeline_logger import get_logger, log_dict
from utils.resource_monitor import enforce_limits

# Constants
BENCHMARK_DATA_PATH = Path("data/raw/benchmark")
BENCHMARK_OUTPUT_DIR = Path("data/processed/benchmark_results")
SUCCESS_CRITERIA_FILE = Path("data/processed/benchmark_results/success_criteria.json")
METRICS_ACCURACY_FILE = Path("data/processed/benchmark_results/metrics_accuracy.json")

logger = get_logger("benchmark")


def ensure_output_dir() -> Path:
    """Ensure the benchmark output directory exists."""
    BENCHMARK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return BENCHMARK_OUTPUT_DIR


def load_benchmark_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load benchmark datasets from data/raw/benchmark.
    Returns: (transcripts_df, adherence_df, ground_truth_df)
    """
    transcripts_path = BENCHMARK_DATA_PATH / "transcripts.csv"
    adherence_path = BENCHMARK_DATA_PATH / "adherence_metrics.csv"
    ground_truth_path = BENCHMARK_DATA_PATH / "ground_truth.csv"

    if not transcripts_path.exists():
        raise FileNotFoundError(f"Benchmark transcripts not found at {transcripts_path}")
    if not adherence_path.exists():
        raise FileNotFoundError(f"Benchmark adherence data not found at {adherence_path}")
    if not ground_truth_path.exists():
        raise FileNotFoundError(f"Ground truth data not found at {ground_truth_path}")

    transcripts_df = pd.read_csv(transcripts_path)
    adherence_df = pd.read_csv(adherence_path)
    ground_truth_df = pd.read_csv(ground_truth_path)

    logger.info("Loaded benchmark data", extra={
        "transcripts_rows": len(transcripts_df),
        "adherence_rows": len(adherence_df),
        "ground_truth_rows": len(ground_truth_df)
    })

    return transcripts_df, adherence_df, ground_truth_df


def run_agency_scoring_pipeline(transcripts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full agency scoring pipeline on benchmark transcripts.
    Returns: DataFrame with session_id and agency_score
    """
    # Step 1: Ingest transcripts
    logger.info("Starting agency scoring pipeline: ingestion")
    # Note: ingest_transcripts expects a file path, so we save to temp
    temp_path = BENCHMARK_OUTPUT_DIR / "temp_transcripts.csv"
    transcripts_df.to_csv(temp_path, index=False)
    ingest_result = ingest_transcripts(temp_path)

    # Step 2: Detect markers
    logger.info("Starting agency scoring pipeline: marker detection")
    markers_result = detect_markers(ingest_result)

    # Step 3: Compute scores
    logger.info("Starting agency scoring pipeline: score computation")
    scores_result = compute_agency_scores(markers_result)

    return scores_result


def run_adherence_pipeline(adherence_df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the adherence extraction pipeline on benchmark data.
    Returns: DataFrame with adherence metrics
    """
    logger.info("Starting adherence extraction pipeline")
    temp_path = BENCHMARK_OUTPUT_DIR / "temp_adherence.csv"
    adherence_df.to_csv(temp_path, index=False)
    result = extract_metrics(temp_path)
    return result


def compute_accuracy_metrics(
    agency_scores: pd.DataFrame,
    adherence_metrics: pd.DataFrame,
    ground_truth: pd.DataFrame
) -> Dict[str, Any]:
    """
    Compute accuracy metrics comparing pipeline outputs to ground truth.
    Returns: Dictionary with accuracy scores and error rates.
    """
    # Merge pipeline outputs with ground truth
    merged = agency_scores.merge(
        ground_truth,
        on="session_id",
        suffixes=("_pred", "_true")
    )

    # Calculate Mean Absolute Error for agency scores
    if "agency_score_true" in merged.columns:
        mae_agency = (merged["agency_score_pred"] - merged["agency_score_true"]).abs().mean()
    else:
        mae_agency = None

    # Calculate correlation
    if "agency_score_true" in merged.columns and not merged.empty:
        from scipy import stats
        corr, p_val = stats.pearsonr(
            merged["agency_score_pred"],
            merged["agency_score_true"]
        )
    else:
        corr, p_val = None, None

    # Check adherence metrics if available
    merged_adherence = adherence_metrics.merge(
        ground_truth,
        on="session_id",
        suffixes=("_pred", "_true")
    )

    return {
        "mae_agency_score": mae_agency,
        "pearson_correlation": corr,
        "p_value": p_val,
        "total_sessions": len(merged),
        "timestamp": datetime.now().isoformat()
    }


def verify_success_criteria(
    metrics: Dict[str, Any],
    ground_truth: pd.DataFrame
) -> Dict[str, Any]:
    """
    Verify success criteria:
    SC-001: >= 95% processing success rate
    SC-002: +/- 0.01 metric accuracy on ground-truth
    """
    total_sessions = len(ground_truth)
    processed_sessions = metrics.get("total_sessions", 0)

    success_rate = processed_sessions / total_sessions if total_sessions > 0 else 0.0
    mae = metrics.get("mae_agency_score", float("inf"))

    sc_001_pass = success_rate >= 0.95
    sc_002_pass = mae is not None and mae <= 0.01

    result = {
        "sc_001_success_rate": success_rate,
        "sc_001_passed": sc_001_pass,
        "sc_002_mae": mae,
        "sc_002_passed": sc_002_pass,
        "all_criteria_met": sc_001_pass and sc_002_pass,
        "timestamp": datetime.now().isoformat()
    }

    logger.info("Success criteria verification", extra=result)
    return result


def main() -> int:
    """
    Main entry point for the benchmark runner.
    Executes the full pipeline on benchmark data and verifies success criteria.
    """
    parser = argparse.ArgumentParser(description="Run benchmark on agency CBT pipeline")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(BENCHMARK_DATA_PATH),
        help="Directory containing benchmark data"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(BENCHMARK_OUTPUT_DIR),
        help="Directory for benchmark results"
    )
    parser.add_argument(
        "--memory-limit-gb",
        type=float,
        default=6.0,
        help="Memory limit in GB"
    )
    args = parser.parse_args()

    try:
        # Enforce resource limits
        enforce_limits(max_memory_gb=args.memory_limit_gb)

        # Ensure output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load benchmark data
        logger.info("Loading benchmark data")
        transcripts_df, adherence_df, ground_truth_df = load_benchmark_data()

        # Run Agency Scoring Pipeline
        logger.info("Running Agency Scoring Pipeline")
        start_time = time.time()
        agency_scores = run_agency_scoring_pipeline(transcripts_df)
        agency_time = time.time() - start_time

        # Run Adherence Pipeline
        logger.info("Running Adherence Extraction Pipeline")
        start_time = time.time()
        adherence_metrics = run_adherence_pipeline(adherence_df)
        adherence_time = time.time() - start_time

        # Compute Accuracy Metrics
        logger.info("Computing Accuracy Metrics")
        accuracy_metrics = compute_accuracy_metrics(
            agency_scores,
            adherence_metrics,
            ground_truth_df
        )
        accuracy_metrics["agency_pipeline_time_sec"] = agency_time
        accuracy_metrics["adherence_pipeline_time_sec"] = adherence_time

        # Verify Success Criteria
        logger.info("Verifying Success Criteria")
        success_criteria = verify_success_criteria(accuracy_metrics, ground_truth_df)

        # Write Results
        # Save full metrics
        metrics_path = output_dir / "benchmark_metrics.json"
        with open(metrics_path, "w") as f:
            json.dump(accuracy_metrics, f, indent=2)

        # Save success criteria
        success_path = output_dir / "success_criteria.json"
        with open(success_path, "w") as f:
            json.dump(success_criteria, f, indent=2)

        # Save processed outputs for inspection
        agency_scores.to_csv(output_dir / "agency_scores.csv", index=False)
        adherence_metrics.to_csv(output_dir / "adherence_metrics.csv", index=False)

        logger.info("Benchmark completed successfully", extra={
            "metrics_file": str(metrics_path),
            "success_file": str(success_path),
            "success_criteria_met": success_criteria["all_criteria_met"]
        })

        return 0 if success_criteria["all_criteria_met"] else 1

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except PipelineError as e:
        logger.error(f"Pipeline error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())