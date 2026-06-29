"""
Main pipeline orchestration for US1: Compute Clone Density and Model Perplexity.

This module orchestrates the end-to-end pipeline:
1. Load raw data from data/raw/
2. Compute clone density metrics using ast_cloner.py
3. Compute perplexity scores using model_metrics.py
4. Join metrics and save to data/processed/

Output files:
- data/processed/clone_metrics.csv
- data/processed/perplexity_scores.csv
"""
import logging
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from config import (
    get_clone_thresholds,
    get_random_seed,
    get_memory_limit_mb,
    get_max_runtime_seconds,
    get_min_valid_segments,
)
from ast_cloner import compute_clone_density_batch, save_clone_metrics
from model_metrics import compute_perplexity_batch, save_perplexity_scores
from memory_monitor import setup_memory_monitoring, validate_memory_within_limit
from parse_failure_logger import init_logger, log_parse_failure, count_parse_failures
from checksum_manifest import record_artifact_checksums, get_artifact_hashes
from pii_scanner import run_pii_scan

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = DATA_DIR / "logs"

# Output paths
CLONE_METRICS_PATH = PROCESSED_DIR / "clone_metrics.csv"
PERPLEXITY_SCORES_PATH = PROCESSED_DIR / "perplexity_scores.csv"
PARSE_FAILURES_PATH = DATA_DIR / "parse_failures.csv"

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Configure logging for the pipeline."""
    logger = logging.getLogger("main_pipeline")
    logger.setLevel(logging.INFO)

    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
    else:
        fh = logging.FileHandler(PROJECT_ROOT / "data" / "logs" / "pipeline.log")
        fh.setLevel(logging.INFO)

    # Format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

def load_raw_data_wrapper(logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Load raw data from the raw directory.
    This is a wrapper that calls data_loader.py if needed.
    """
    logger.info("Loading raw data from %s", RAW_DIR)

    # Check if data exists
    if not RAW_DIR.exists():
        logger.error("Raw data directory does not exist: %s", RAW_DIR)
        raise FileNotFoundError(f"Raw data directory not found: {RAW_DIR}")

    # Try to load from CSV
    csv_files = list(RAW_DIR.glob("*.csv"))
    if not csv_files:
        logger.error("No CSV files found in %s", RAW_DIR)
        raise FileNotFoundError(f"No CSV files in raw data directory: {RAW_DIR}")

    # Load first CSV file (should be github-code-sample.csv)
    data_file = csv_files[0]
    logger.info("Loading data from %s", data_file)

    try:
        df = pd.read_csv(data_file)
        logger.info("Loaded %d records from %s", len(df), data_file)
        return df.to_dict("records")
    except Exception as e:
        logger.error("Failed to load data: %s", str(e))
        raise

def compute_clone_metrics_batch(
    data: List[Dict[str, Any]], logger: logging.Logger
) -> pd.DataFrame:
    """
    Compute clone density metrics for all files in the dataset.
    """
    logger.info("Computing clone density metrics for %d files", len(data))

    clone_metrics = []
    parse_failures = 0

    for idx, record in enumerate(data):
        if (idx + 1) % 100 == 0:
            logger.info("Progress: %d/%d files processed", idx + 1, len(data))

        try:
            # Get file content or path
            file_content = record.get("content", "")
            file_path = record.get("path", f"file_{idx}.py")

            if not file_content:
                logger.warning("No content for file %s, skipping", file_path)
                parse_failures += 1
                log_parse_failure(
                    PARSE_FAILURES_PATH,
                    file_path,
                    "No content available",
                    logger,
                )
                continue

            # Compute clone density
            density_result = compute_clone_density_batch(
                [file_content], logger
            )

            if density_result and len(density_result) > 0:
                result = density_result[0]
                clone_metrics.append({
                    "file_path": file_path,
                    "clone_density": result.get("clone_density", 0.0),
                    "total_nodes": result.get("total_nodes", 0),
                    "clone_nodes": result.get("clone_nodes", 0),
                    "timestamp": result.get("timestamp", ""),
                })
            else:
                logger.warning("No clone density result for %s", file_path)
                parse_failures += 1
                log_parse_failure(
                    PARSE_FAILURES_PATH,
                    file_path,
                    "No clone density result",
                    logger,
                )

        except Exception as e:
            logger.error("Error processing file %s: %s", file_path, str(e))
            parse_failures += 1
            log_parse_failure(
                PARSE_FAILURES_PATH,
                file_path,
                str(e),
                logger,
            )

    logger.info("Clone metrics computation complete. Parse failures: %d", parse_failures)

    # Create DataFrame
    df = pd.DataFrame(clone_metrics)
    return df

def compute_perplexity_scores_batch(
    data: List[Dict[str, Any]], logger: logging.Logger
) -> pd.DataFrame:
    """
    Compute perplexity scores for all files in the dataset.
    """
    logger.info("Computing perplexity scores for %d files", len(data))

    perplexity_scores = []
    parse_failures = 0

    for idx, record in enumerate(data):
        if (idx + 1) % 100 == 0:
            logger.info("Progress: %d/%d files processed", idx + 1, len(data))

        try:
            # Get file content or path
            file_content = record.get("content", "")
            file_path = record.get("path", f"file_{idx}.py")

            if not file_content:
                logger.warning("No content for file %s, skipping", file_path)
                parse_failures += 1
                log_parse_failure(
                    PARSE_FAILURES_PATH,
                    file_path,
                    "No content available for perplexity",
                    logger,
                )
                continue

            # Compute perplexity
            perplexity_result = compute_perplexity_batch(
                [file_content], logger
            )

            if perplexity_result and len(perplexity_result) > 0:
                result = perplexity_result[0]
                perplexity_scores.append({
                    "file_path": file_path,
                    "perplexity": result.get("perplexity", float("nan")),
                    "token_count": result.get("token_count", 0),
                    "timestamp": result.get("timestamp", ""),
                })
            else:
                logger.warning("No perplexity result for %s", file_path)
                parse_failures += 1
                log_parse_failure(
                    PARSE_FAILURES_PATH,
                    file_path,
                    "No perplexity result",
                    logger,
                )

        except Exception as e:
            logger.error("Error computing perplexity for %s: %s", file_path, str(e))
            parse_failures += 1
            log_parse_failure(
                PARSE_FAILURES_PATH,
                file_path,
                str(e),
                logger,
            )

    logger.info("Perplexity computation complete. Parse failures: %d", parse_failures)

    # Create DataFrame
    df = pd.DataFrame(perplexity_scores)
    return df

def join_metrics(
    clone_df: pd.DataFrame, perplexity_df: pd.DataFrame, logger: logging.Logger
) -> pd.DataFrame:
    """
    Join clone density and perplexity metrics on file_path.
    """
    logger.info("Joining clone metrics (%d) with perplexity scores (%d)",
               len(clone_df), len(perplexity_df))

    # Merge on file_path
    merged = pd.merge(
        clone_df,
        perplexity_df,
        on="file_path",
        how="inner",
        suffixes=("_clone", "_perplexity")
    )

    logger.info("Joined metrics: %d records", len(merged))

    # Add computed fields
    merged["timestamp"] = pd.Timestamp.now().isoformat()

    return merged

def save_results(
    clone_df: pd.DataFrame,
    perplexity_df: pd.DataFrame,
    merged_df: pd.DataFrame,
    logger: logging.Logger,
) -> Dict[str, str]:
    """
    Save all metrics to CSV files and record checksums.
    """
    # Ensure output directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    output_files = {}

    # Save clone metrics
    clone_df.to_csv(CLONE_METRICS_PATH, index=False)
    output_files["clone_metrics"] = str(CLONE_METRICS_PATH)
    logger.info("Saved clone metrics to %s", CLONE_METRICS_PATH)

    # Save perplexity scores
    perplexity_df.to_csv(PERPLEXITY_SCORES_PATH, index=False)
    output_files["perplexity_scores"] = str(PERPLEXITY_SCORES_PATH)
    logger.info("Saved perplexity scores to %s", PERPLEXITY_SCORES_PATH)

    # Save merged metrics (for correlation analysis later)
    merged_path = PROCESSED_DIR / "merged_metrics.csv"
    merged_df.to_csv(merged_path, index=False)
    output_files["merged_metrics"] = str(merged_path)
    logger.info("Saved merged metrics to %s", merged_path)

    # Record checksums
    record_artifact_checksums(logger)

    return output_files

def run_pipeline(logger: logging.Logger) -> Dict[str, Any]:
    """
    Run the complete US1 pipeline.
    """
    logger.info("=" * 60)
    logger.info("Starting US1 Pipeline: Clone Density and Perplexity")
    logger.info("=" * 60)

    # Setup memory monitoring with CORRECTED parameter - pass Path, not logger
    log_dir = LOGS_DIR
    setup_memory_monitoring(log_dir)

    # Validate memory is within limit
    memory_limit_mb = get_memory_limit_mb()
    if not validate_memory_within_limit(memory_limit_mb):
        logger.error("Memory limit exceeded: limit=%dMB", memory_limit_mb)
        raise MemoryError(f"Memory limit {memory_limit_mb}MB exceeded")

    # Step 1: Load raw data
    logger.info("Step 1: Loading raw data")
    raw_data = load_raw_data_wrapper(logger)
    logger.info("Loaded %d records", len(raw_data))

    # Step 2: Compute clone density metrics
    logger.info("Step 2: Computing clone density metrics")
    clone_df = compute_clone_metrics_batch(raw_data, logger)
    logger.info("Computed clone density for %d files", len(clone_df))

    # Step 3: Compute perplexity scores
    logger.info("Step 3: Computing perplexity scores")
    perplexity_df = compute_perplexity_batch(raw_data, logger)
    logger.info("Computed perplexity for %d files", len(perplexity_df))

    # Step 4: Join metrics
    logger.info("Step 4: Joining metrics")
    merged_df = join_metrics(clone_df, perplexity_df, logger)

    # Step 5: Save results
    logger.info("Step 5: Saving results")
    output_files = save_results(clone_df, perplexity_df, merged_df, logger)

    # Final validation
    min_segments = get_min_valid_segments()
    if len(merged_df) < min_segments:
        logger.warning(
            "Segment count (%d) below minimum threshold (%d)",
            len(merged_df), min_segments
        )

    logger.info("=" * 60)
    logger.info("Pipeline complete!")
    logger.info("Output files: %s", output_files)
    logger.info("Total segments processed: %d", len(merged_df))
    logger.info("=" * 60)

    return {
        "output_files": output_files,
        "segment_count": len(merged_df),
        "clone_metrics_count": len(clone_df),
        "perplexity_metrics_count": len(perplexity_df),
    }

def main():
    """Main entry point for the pipeline."""
    logger = setup_logging()

    try:
        results = run_pipeline(logger)
        logger.info("Pipeline completed successfully")
        sys.exit(0)
    except Exception as e:
        logger.error("Pipeline failed: %s", str(e), exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
