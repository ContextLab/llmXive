"""
Main pipeline orchestration for US1: Compute Clone Density and Model Perplexity.

This script orchestrates the full pipeline:
1. Load raw data from data/raw/github-code-sample.csv
2. Compute clone density metrics using AST-based clone detection
3. Compute perplexity scores using quantized language model
4. Join metrics and save to data/processed/
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np

# Import from sibling modules (per API surface)
from config import (
    get_model_name,
    get_quantization_bits,
    get_random_seed,
    get_memory_limit_mb,
)
from ast_cloner import compute_clone_density_batch, save_clone_metrics
from model_metrics import compute_perplexity_batch, save_perplexity_scores
from checksum_manifest import record_artifact_checksums
from parse_failure_logger import handle_parse_error, count_parse_failures
from memory_monitor import check_memory_limit, setup_memory_monitoring

# Set random seed for reproducibility
np.random.seed(get_random_seed())

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """
    Setup logging configuration for the pipeline.

    Args:
        log_file: Optional path to log file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("main_pipeline")
    logger.setLevel(logging.INFO)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger

def save_results(
    clone_metrics: pd.DataFrame,
    perplexity_scores: pd.DataFrame,
    output_dir: Path,
    logger: logging.Logger,
) -> Dict[str, str]:
    """
    Save pipeline results to CSV files.

    Args:
        clone_metrics: DataFrame with clone density metrics
        perplexity_scores: DataFrame with perplexity scores
        output_dir: Directory to save output files
        logger: Logger instance

    Returns:
        Dictionary mapping metric type to output file path
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save clone metrics
    clone_metrics_path = output_dir / "clone_metrics.csv"
    clone_metrics.to_csv(clone_metrics_path, index=False)
    logger.info(f"Saved clone metrics to {clone_metrics_path}")

    # Save perplexity scores
    perplexity_path = output_dir / "perplexity_scores.csv"
    perplexity_scores.to_csv(perplexity_path, index=False)
    logger.info(f"Saved perplexity scores to {perplexity_path}")

    return {
        "clone_metrics": str(clone_metrics_path),
        "perplexity_scores": str(perplexity_path),
    }

def run_pipeline(
    raw_data_path: Path,
    output_dir: Path,
    logger: logging.Logger,
) -> Dict[str, Any]:
    """
    Run the full pipeline to compute clone density and perplexity metrics.

    Args:
        raw_data_path: Path to raw data CSV file
        output_dir: Directory to save processed outputs
        logger: Logger instance

    Returns:
        Dictionary with pipeline results and metadata
    """
    results = {
        "success": False,
        "clone_metrics_path": None,
        "perplexity_scores_path": None,
        "files_processed": 0,
        "parse_failures": 0,
        "memory_limit_mb": get_memory_limit_mb(),
    }

    # Setup memory monitoring
    setup_memory_monitoring(get_memory_limit_mb(), logger)

    # Step 1: Load raw data
    logger.info("Loading raw data from {raw_data_path}")
    if not raw_data_path.exists():
        logger.error(f"Raw data not found: {raw_data_path}")
        return results

    try:
        raw_data = pd.read_csv(raw_data_path)
        logger.info(f"Loaded {len(raw_data)} files from raw data")
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        return results

    # Step 2: Get list of file paths to process
    # The raw data CSV should have a 'file_path' or 'path' column
    if "file_path" in raw_data.columns:
        file_paths = raw_data["file_path"].tolist()
    elif "path" in raw_data.columns:
        file_paths = raw_data["path"].tolist()
    else:
        logger.error("Raw data CSV must have 'file_path' or 'path' column")
        return results

    sample_files = [Path(p) for p in file_paths if p]
    logger.info(f"Processing {len(sample_files)} files")

    if len(sample_files) == 0:
        logger.warning("No valid file paths found in raw data")
        # Create empty output files for validation
        output_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=["file_path", "clone_density", "parse_success"]).to_csv(
            output_dir / "clone_metrics.csv", index=False
        )
        pd.DataFrame(columns=["file_path", "perplexity", "valid"]).to_csv(
            output_dir / "perplexity_scores.csv", index=False
        )
        results["success"] = True
        results["clone_metrics_path"] = str(output_dir / "clone_metrics.csv")
        results["perplexity_scores_path"] = str(output_dir / "perplexity_scores.csv")
        return results

    # Step 3: Compute clone density metrics
    logger.info("Computing clone density metrics...")
    try:
        clone_metrics = compute_clone_density_batch(
            sample_files, output_dir, logger
        )
        logger.info(f"Computed clone density for {len(clone_metrics)} files")
        results["files_processed"] = len(clone_metrics)
    except Exception as e:
        logger.error(f"Clone density computation failed: {e}")
        # Handle parse failures
        results["parse_failures"] = count_parse_failures()
        handle_parse_error(e, logger)
        return results

    # Step 4: Compute perplexity scores
    logger.info("Computing perplexity scores...")
    try:
        perplexity_scores = compute_perplexity_batch(
            sample_files, output_dir, logger
        )
        logger.info(f"Computed perplexity for {len(perplexity_scores)} files")
    except Exception as e:
        logger.error(f"Perplexity computation failed: {e}")
        handle_parse_error(e, logger)
        return results

    # Step 5: Join metrics
    logger.info("Joining clone density and perplexity metrics...")
    try:
        # Ensure both DataFrames have a common key
        if "file_path" not in clone_metrics.columns:
            clone_metrics["file_path"] = [str(f) for f in sample_files[: len(clone_metrics)]]
        if "file_path" not in perplexity_scores.columns:
            perplexity_scores["file_path"] = [str(f) for f in sample_files[: len(perplexity_scores)]]

        # Merge on file_path
        merged_metrics = pd.merge(
            clone_metrics,
            perplexity_scores,
            on="file_path",
            how="outer",
            suffixes=("_clone", "_perp"),
        )
        logger.info(f"Merged metrics for {len(merged_metrics)} files")
    except Exception as e:
        logger.error(f"Failed to merge metrics: {e}")
        return results

    # Step 6: Save results
    logger.info("Saving pipeline results...")
    try:
        output_paths = save_results(
            clone_metrics, perplexity_scores, output_dir, logger
        )
        results["clone_metrics_path"] = output_paths["clone_metrics"]
        results["perplexity_scores_path"] = output_paths["perplexity_scores"]
        results["success"] = True
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        return results

    # Step 7: Record checksums for output artifacts
    try:
        if results["clone_metrics_path"]:
            record_artifact_checksums(
                [Path(results["clone_metrics_path"])],
                logger,
            )
        if results["perplexity_scores_path"]:
            record_artifact_checksums(
                [Path(results["perplexity_scores_path"])],
                logger,
            )
    except Exception as e:
        logger.warning(f"Failed to record checksums: {e}")

    return results

def main() -> int:
    """
    Main entry point for the pipeline.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup logging
    log_file = Path("data/pipeline.log")
    logger = setup_logging(log_file)

    logger.info("=" * 60)
    logger.info("Starting pipeline for US1: Clone Density and Perplexity")
    logger.info("=" * 60)

    # Define paths
    project_root = Path(__file__).parent.parent
    raw_data_path = project_root / "data" / "raw" / "github-code-sample.csv"
    output_dir = project_root / "data" / "processed"

    # Run pipeline
    results = run_pipeline(raw_data_path, output_dir, logger)

    # Report results
    logger.info("=" * 60)
    if results["success"]:
        logger.info("Pipeline completed successfully!")
        logger.info(f"  Files processed: {results['files_processed']}")
        logger.info(f"  Parse failures: {results['parse_failures']}")
        logger.info(f"  Clone metrics: {results['clone_metrics_path']}")
        logger.info(f"  Perplexity scores: {results['perplexity_scores_path']}")
        logger.info("=" * 60)
        return 0
    else:
        logger.error("Pipeline failed!")
        logger.error(f"  Clone metrics path: {results['clone_metrics_path']}")
        logger.error(f"  Perplexity scores path: {results['perplexity_scores_path']}")
        logger.info("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())