"""
Main pipeline orchestration for computing clone density and perplexity metrics.

This script orchestrates the complete pipeline:
1. Load raw data from data/raw/github-code-sample.csv
2. Compute clone density metrics for each code sample
3. Compute perplexity scores for each code sample
4. Join metrics and save to processed CSV files
"""
import logging
import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import (
    get_dataset_name,
    get_model_name,
    get_quantization_bits,
    get_streaming_enabled,
    get_random_seed,
    get_memory_limit_mb,
    get_max_runtime_seconds,
    get_min_valid_segments,
)
from data_loader import load_raw_data
from ast_cloner import compute_clone_density_batch, save_clone_metrics
from model_metrics import compute_perplexity_batch, save_perplexity_scores
from parse_failure_logger import log_parse_failure, handle_parse_error
from checksum_manifest import record_artifact_checksums, setup_logging as setup_manifest_logging
from memory_monitor import setup_memory_monitoring, check_memory_limit


def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Setup logging configuration for the pipeline."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def load_raw_data_wrapper(
    data_dir: Path,
    max_samples: Optional[int] = None,
    logger: Optional[logging.Logger] = None
) -> pd.DataFrame:
    """
    Wrapper for loading raw data from CSV.
    
    Args:
        data_dir: Path to data directory
        max_samples: Maximum number of samples to load
        logger: Logger instance
        
    Returns:
        DataFrame with code samples
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    input_path = data_dir / "raw" / "github-code-sample.csv"
    
    if not input_path.exists():
        logger.error(f"Raw data file not found: {input_path}")
        raise FileNotFoundError(f"Raw data file not found: {input_path}")

    logger.info(f"Loading raw data from {input_path}")
    
    try:
        # Load the CSV file into a DataFrame
        df = pd.read_csv(input_path)
        
        if df.empty:
            logger.warning("Loaded data is empty")
            return pd.DataFrame(columns=["code", "repo", "path", "language"])
        
        # Ensure we have a DataFrame (not a list)
        if not isinstance(df, pd.DataFrame):
            logger.error(f"Expected DataFrame but got {type(df)}")
            raise TypeError(f"Expected DataFrame but got {type(df)}")

        logger.info(f"Loaded {len(df)} samples from {input_path}")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        raise


def compute_clone_metrics_batch(
    df: pd.DataFrame,
    data_dir: Path,
    logger: Optional[logging.Logger] = None
) -> pd.DataFrame:
    """
    Compute clone density metrics for all code samples in batch.
    
    Args:
        df: DataFrame with code samples
        data_dir: Path to data directory
        logger: Logger instance
        
    Returns:
        DataFrame with clone metrics
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    if df.empty:
        logger.warning("No data to process for clone metrics")
        return pd.DataFrame(columns=["index", "clone_density", "num_nodes", "num_functions", "num_classes"])

    logger.info("Computing clone density metrics...")

    # Ensure df is a DataFrame, not a list
    if not isinstance(df, pd.DataFrame):
        logger.error(f"Expected DataFrame but got {type(df)}")
        raise TypeError(f"compute_clone_metrics_batch expects DataFrame, got {type(df)}")

    results = []
    parse_failures = []

    for idx, row in df.iterrows():
        try:
            code = row.get("code", "")
            if not code or not isinstance(code, str):
                logger.warning(f"Invalid code at index {idx}, skipping")
                parse_failures.append({
                    "index": idx,
                    "error": "Invalid or empty code",
                    "repo": row.get("repo", ""),
                    "path": row.get("path", "")
                })
                continue

            # Compute clone density using batch function
            density_result = compute_clone_density_batch([code])
            
            if density_result and len(density_result) > 0:
                result = density_result[0]
                results.append({
                    "index": idx,
                    "clone_density": result.get("clone_density", 0.0),
                    "num_nodes": result.get("num_nodes", 0),
                    "num_functions": result.get("num_functions", 0),
                    "num_classes": result.get("num_classes", 0),
                    "repo": row.get("repo", ""),
                    "path": row.get("path", ""),
                    "language": row.get("language", "")
                })
            else:
                logger.warning(f"Empty density result at index {idx}")
                parse_failures.append({
                    "index": idx,
                    "error": "Empty density result",
                    "repo": row.get("repo", ""),
                    "path": row.get("path", "")
                })
                
        except Exception as e:
            error_msg = handle_parse_error(e)
            logger.warning(f"Parse failure at index {idx}: {error_msg}")
            parse_failures.append({
                "index": idx,
                "error": error_msg,
                "repo": row.get("repo", ""),
                "path": row.get("path", "")
            })
            # Log to parse failures file
            log_parse_failure(
                repo=row.get("repo", ""),
                path=row.get("path", ""),
                error=error_msg
            )

    # Save parse failures to CSV
    if parse_failures:
        failures_df = pd.DataFrame(parse_failures)
        failures_path = data_dir / "parse_failures.csv"
        failures_df.to_csv(failures_path, index=False)
        logger.info(f"Logged {len(parse_failures)} parse failures to {failures_path}")

    clone_metrics_df = pd.DataFrame(results)
    
    if not clone_metrics_df.empty:
        # Save clone metrics to CSV
        output_path = data_dir / "processed" / "clone_metrics.csv"
        clone_metrics_df.to_csv(output_path, index=False)
        logger.info(f"Saved clone metrics to {output_path}")

    return clone_metrics_df


def compute_perplexity_scores_batch(
    df: pd.DataFrame,
    data_dir: Path,
    logger: Optional[logging.Logger] = None
) -> pd.DataFrame:
    """
    Compute perplexity scores for all code samples in batch.
    
    Args:
        df: DataFrame with code samples
        data_dir: Path to data directory
        logger: Logger instance
        
    Returns:
        DataFrame with perplexity scores
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    if df.empty:
        logger.warning("No data to process for perplexity scores")
        return pd.DataFrame(columns=["index", "perplexity", "token_count"])

    logger.info("Computing perplexity scores...")

    # Ensure df is a DataFrame, not a list
    if not isinstance(df, pd.DataFrame):
        logger.error(f"Expected DataFrame but got {type(df)}")
        raise TypeError(f"compute_perplexity_scores_batch expects DataFrame, got {type(df)}")

    results = []

    for idx, row in df.iterrows():
        try:
            code = row.get("code", "")
            if not code or not isinstance(code, str):
                logger.warning(f"Invalid code at index {idx}, skipping")
                continue

            # Compute perplexity using batch function
            perplexity_result = compute_perplexity_batch([code])
            
            if perplexity_result and len(perplexity_result) > 0:
                result = perplexity_result[0]
                perplexity = result.get("perplexity", float('nan'))
                token_count = result.get("token_count", 0)
                
                # Validate perplexity value
                if perplexity is None or (isinstance(perplexity, float) and (perplexity != perplexity or perplexity == float('inf') or perplexity == float('-inf'))):
                    logger.warning(f"Invalid perplexity at index {idx}, setting to NaN")
                    perplexity = float('nan')

                results.append({
                    "index": idx,
                    "perplexity": perplexity,
                    "token_count": token_count,
                    "repo": row.get("repo", ""),
                    "path": row.get("path", ""),
                    "language": row.get("language", "")
                })
            else:
                logger.warning(f"Empty perplexity result at index {idx}")
                
        except Exception as e:
            logger.error(f"Perplexity computation failed at index {idx}: {e}")

    perplexity_df = pd.DataFrame(results)
    
    if not perplexity_df.empty:
        # Save perplexity scores to CSV
        output_path = data_dir / "processed" / "perplexity_scores.csv"
        perplexity_df.to_csv(output_path, index=False)
        logger.info(f"Saved perplexity scores to {output_path}")

    return perplexity_df


def join_metrics(
    clone_metrics: pd.DataFrame,
    perplexity_scores: pd.DataFrame,
    logger: Optional[logging.Logger] = None
) -> pd.DataFrame:
    """
    Join clone density and perplexity metrics on index.
    
    Args:
        clone_metrics: DataFrame with clone metrics
        perplexity_scores: DataFrame with perplexity scores
        logger: Logger instance
        
    Returns:
        Joined DataFrame with all metrics
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    if clone_metrics.empty:
        logger.warning("Clone metrics is empty")
        return pd.DataFrame()

    if perplexity_scores.empty:
        logger.warning("Perplexity scores is empty")
        return pd.DataFrame()

    logger.info("Joining metrics...")

    # Join on 'index' column
    joined_df = pd.merge(
        clone_metrics,
        perplexity_scores,
        on="index",
        how="inner",
        suffixes=("_clone", "_perplexity")
    )

    logger.info(f"Joined {len(joined_df)} records")

    return joined_df


def run_pipeline(
    data_dir: Path,
    logger: Optional[logging.Logger] = None
) -> Optional[pd.DataFrame]:
    """
    Run the complete pipeline.
    
    Args:
        data_dir: Path to data directory
        logger: Logger instance
        
    Returns:
        Joined DataFrame with all metrics, or None on failure
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    logger.info("Starting pipeline...")

    # Setup memory monitoring
    setup_memory_monitoring(logger)

    try:
        # Stage 1: Load raw data
        logger.info("Stage 1: Loading raw data")
        raw_df = load_raw_data_wrapper(data_dir, logger=logger)
        
        if raw_df.empty:
            logger.error("No data loaded from raw data file")
            return None

        # Stage 2: Compute clone metrics
        logger.info("Stage 2: Computing clone metrics")
        clone_metrics = compute_clone_metrics_batch(raw_df, data_dir, logger=logger)
        
        if clone_metrics.empty:
            logger.error("No clone metrics computed")
            return None

        # Stage 3: Compute perplexity scores
        logger.info("Stage 3: Computing perplexity scores")
        perplexity_scores = compute_perplexity_scores_batch(raw_df, data_dir, logger=logger)
        
        if perplexity_scores.empty:
            logger.error("No perplexity scores computed")
            return None

        # Stage 4: Join metrics
        logger.info("Stage 4: Joining metrics")
        joined_df = join_metrics(clone_metrics, perplexity_scores, logger=logger)
        
        if joined_df.empty:
            logger.error("No joined metrics")
            return None

        # Save joined results
        output_path = data_dir / "processed" / "clone_metrics.csv"
        joined_df.to_csv(output_path, index=False)
        logger.info(f"Saved joined metrics to {output_path}")

        logger.info("Pipeline completed successfully!")
        return joined_df

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


def save_results(
    joined_df: pd.DataFrame,
    data_dir: Path,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Save final results and compute checksums.
    
    Args:
        joined_df: Joined DataFrame with all metrics
        data_dir: Path to data directory
        logger: Logger instance
    """
    if logger is None:
        logger = logging.getLogger(__name__)

    # Ensure processed directory exists
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Save joined metrics
    output_path = processed_dir / "clone_metrics.csv"
    joined_df.to_csv(output_path, index=False)
    logger.info(f"Saved joined metrics to {output_path}")

    # Record checksums for output files
    record_artifact_checksums(
        artifact_path=output_path,
        checksum_algorithm="sha256",
        logger=logger
    )


def main() -> int:
    """
    Main entry point for the pipeline.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Setup logging
    log_file = Path(__file__).parent.parent / "data" / "pipeline.log"
    logger = setup_logging(log_file)

    logger.info("Starting main pipeline orchestration...")

    # Get data directory
    data_dir = Path(__file__).parent.parent / "data"

    try:
        # Run the pipeline
        joined_df = run_pipeline(data_dir, logger=logger)

        if joined_df is not None:
            # Save final results
            save_results(joined_df, data_dir, logger=logger)
            logger.info("Pipeline completed successfully!")
            return 0
        else:
            logger.error("Pipeline returned no results")
            return 1

    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
