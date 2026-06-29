"""
Main pipeline orchestration for US1: Compute Clone Density and Model Perplexity.

This script orchestrates the full pipeline:
1. Load raw data from data_loader.py output
2. Compute clone density metrics using ast_cloner.py
3. Compute perplexity scores using model_metrics.py
4. Join metrics and save to processed output files
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

# Import from sibling modules - using names from API surface
from data_loader import load_raw_data
from ast_cloner import compute_clone_density_batch, save_clone_metrics
from model_metrics import compute_perplexity_batch, save_perplexity_scores
from checksum_manifest import record_artifact_checksums
from parse_failure_logger import log_parse_failure
from config import (
    get_random_seed,
    get_max_runtime_seconds,
    get_clone_thresholds,
    get_model_name,
    get_quantization_bits,
)

# Set random seed for reproducibility
np.random.seed(get_random_seed())

# Configure logging
def setup_logging(name: str) -> logging.Logger:
    """Setup logging configuration for pipeline components."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(Path("data/pipeline.log"))
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def load_raw_data_wrapper(logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Wrapper to load raw data from data_loader output.

    Args:
        logger: Logger instance

    Returns:
        DataFrame with raw code samples, or None if loading fails
    """
    raw_data_path = Path("data/raw/github-code-sample.csv")

    if not raw_data_path.exists():
        logger.error(f"Raw data not found: {raw_data_path}")
        logger.error("Please run: python code/data_loader.py")
        return None

    try:
        df = pd.read_csv(raw_data_path)
        logger.info(f"Loaded {len(df)} samples from {raw_data_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        return None

def compute_clone_metrics_batch(
    df: pd.DataFrame, logger: logging.Logger
) -> pd.DataFrame:
    """
    Compute clone density metrics for all code samples.

    Args:
        df: DataFrame with 'code' column containing Python code
        logger: Logger instance

    Returns:
        DataFrame with clone density metrics
    """
    results = []

    for idx, row in df.iterrows():
        code = row.get("code", "")
        file_id = row.get("file_id", idx)

        if not code or not isinstance(code, str):
            log_parse_failure(
                file_id=file_id,
                error_type="empty_code",
                error_message="Code field is empty or invalid",
                logger=logger,
            )
            results.append(
                {
                    "file_id": file_id,
                    "clone_density": None,
                    "parse_error": True,
                }
            )
            continue

        try:
            density = compute_clone_density_batch([code])
            results.append(
                {
                    "file_id": file_id,
                    "clone_density": density[0] if density else 0.0,
                    "parse_error": False,
                }
            )
        except SyntaxError as e:
            log_parse_failure(
                file_id=file_id,
                error_type="syntax_error",
                error_message=str(e),
                logger=logger,
            )
            results.append(
                {
                    "file_id": file_id,
                    "clone_density": None,
                    "parse_error": True,
                }
            )
        except Exception as e:
            log_parse_failure(
                file_id=file_id,
                error_type="parse_error",
                error_message=str(e),
                logger=logger,
            )
            results.append(
                {
                    "file_id": file_id,
                    "clone_density": None,
                    "parse_error": True,
                }
            )

    return pd.DataFrame(results)

def compute_perplexity_scores_batch(
    df: pd.DataFrame, logger: logging.Logger
) -> pd.DataFrame:
    """
    Compute perplexity scores for all code samples using quantized model.

    Args:
        df: DataFrame with 'code' column containing Python code
        logger: Logger instance

    Returns:
        DataFrame with perplexity scores
    """
    model_name = get_model_name()
    quantization_bits = get_quantization_bits()

    logger.info(f"Loading model: {model_name} (8-bit quantization)")

    try:
        perplexity_results = compute_perplexity_batch(
            codes=df["code"].tolist(),
            model_name=model_name,
            quantization_bits=quantization_bits,
            logger=logger,
        )

        results = []
        for idx, row in df.iterrows():
          file_id = row.get("file_id", idx)
          perplexity = perplexity_results[idx] if idx < len(perplexity_results) else None

          # Validate perplexity value
          if perplexity is None or np.isnan(perplexity) or np.isinf(perplexity):
              log_parse_failure(
                  file_id=file_id,
                  error_type="perplexity_error",
                  error_message=f"Invalid perplexity value: {perplexity}",
                  logger=logger,
              )
              results.append(
                  {
                      "file_id": file_id,
                      "perplexity": None,
                      "perplexity_error": True,
                  }
              )
          else:
              results.append(
                  {
                      "file_id": file_id,
                      "perplexity": perplexity,
                      "perplexity_error": False,
                  }
              )

        return pd.DataFrame(results)

    except Exception as e:
        logger.error(f"Failed to compute perplexity: {e}")
        # Return empty results with error flag
        return pd.DataFrame(
            [
                {
                    "file_id": row.get("file_id", idx),
                    "perplexity": None,
                    "perplexity_error": True,
                }
                for idx, row in df.iterrows()
            ]
        )

def join_metrics(
    clone_df: pd.DataFrame, perplexity_df: pd.DataFrame, logger: logging.Logger
) -> pd.DataFrame:
    """
    Join clone density and perplexity metrics on file_id.

    Args:
        clone_df: DataFrame with clone density metrics
        perplexity_df: DataFrame with perplexity scores
        logger: Logger instance

    Returns:
        Joined DataFrame with both metrics
    """
    if clone_df.empty:
        logger.warning("Clone metrics DataFrame is empty")
        return pd.DataFrame()

    if perplexity_df.empty:
        logger.warning("Perplexity scores DataFrame is empty")
        return pd.DataFrame()

    # Merge on file_id
    merged = pd.merge(
        clone_df, perplexity_df, on="file_id", how="outer"
    )

    logger.info(f"Merged metrics: {len(merged)} samples")

    # Count valid samples (both metrics present)
    valid_count = merged[
        (merged["clone_density"].notna()) & (merged["perplexity"].notna())
    ].shape[0]

    logger.info(f"Valid samples with both metrics: {valid_count}")

    return merged

def run_pipeline(logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Run the full pipeline: load data, compute metrics, join results.

    Args:
        logger: Logger instance

    Returns:
        Joined metrics DataFrame, or None if pipeline fails
    """
    logger.info("=" * 60)
    logger.info("Starting US1 Pipeline: Clone Density + Perplexity")
    logger.info("=" * 60)

    # Step 1: Load raw data
    logger.info("Step 1: Loading raw data...")
    raw_df = load_raw_data_wrapper(logger)
    if raw_df is None:
        logger.error("Pipeline failed: Could not load raw data")
        return None

    # Step 2: Compute clone density metrics
    logger.info("Step 2: Computing clone density metrics...")
    clone_df = compute_clone_metrics_batch(raw_df, logger)
    logger.info(f"Clone metrics computed for {len(clone_df)} samples")

    # Step 3: Compute perplexity scores
    logger.info("Step 3: Computing perplexity scores...")
    perplexity_df = compute_perplexity_scores_batch(raw_df, logger)
    logger.info(f"Perplexity scores computed for {len(perplexity_df)} samples")

    # Step 4: Join metrics
    logger.info("Step 4: Joining metrics...")
    joined_df = join_metrics(clone_df, perplexity_df, logger)

    logger.info("=" * 60)
    logger.info("Pipeline complete")
    logger.info("=" * 60)

    return joined_df

def save_results(
    joined_df: pd.DataFrame, logger: logging.Logger
) -> Dict[str, str]:
    """
    Save pipeline results to processed output files.

    Args:
        joined_df: Joined metrics DataFrame
        logger: Logger instance

    Returns:
        Dictionary mapping output type to file path
    """
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_files = {}

    # Save clone metrics
    clone_metrics_path = output_dir / "clone_metrics.csv"
    clone_df = joined_df[["file_id", "clone_density", "parse_error"]]
    clone_df.to_csv(clone_metrics_path, index=False)
    output_files["clone_metrics"] = str(clone_metrics_path)
    logger.info(f"Saved clone metrics to {clone_metrics_path}")

    # Save perplexity scores
    perplexity_path = output_dir / "perplexity_scores.csv"
    perplexity_df = joined_df[["file_id", "perplexity", "perplexity_error"]]
    perplexity_df.to_csv(perplexity_path, index=False)
    output_files["perplexity_scores"] = str(perplexity_path)
    logger.info(f"Saved perplexity scores to {perplexity_path}")

    # Save full joined metrics
    full_metrics_path = output_dir / "full_metrics.csv"
    joined_df.to_csv(full_metrics_path, index=False)
    output_files["full_metrics"] = str(full_metrics_path)
    logger.info(f"Saved full metrics to {full_metrics_path}")

    # Record checksums for all output files
    record_artifact_checksums(
        output_files,
        manifest_path=Path("data/checksum_manifest.json"),
        logger=logger,
    )

    return output_files

def main():
    """Main entry point for pipeline orchestration."""
    logger = setup_logging("main_pipeline")

    try:
        # Run pipeline
        joined_df = run_pipeline(logger)

        if joined_df is None or joined_df.empty:
            logger.error("Pipeline produced no results")
            sys.exit(1)

        # Save results
        output_files = save_results(joined_df, logger)

        logger.info(f"Pipeline completed successfully")
        logger.info(f"Output files: {output_files}")

        sys.exit(0)

    except Exception as e:
        logger.exception(f"Pipeline failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
