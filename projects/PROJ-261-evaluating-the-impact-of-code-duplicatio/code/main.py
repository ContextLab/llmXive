"""
Main pipeline orchestration for code duplication impact analysis.

This module orchestrates the full pipeline:
1. Load raw data from data/raw/
2. Compute clone density metrics (from ast_cloner)
3. Compute perplexity scores (from model_metrics)
4. Join metrics and save to data/processed/

Per T021 requirements:
- Join clone-density and perplexity metrics
- Save to data/processed/clone_metrics.csv
- Save to data/processed/perplexity_scores.csv
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from config import (
    get_clone_thresholds,
    get_random_seed,
    get_memory_limit_mb,
    get_max_runtime_seconds,
    get_min_valid_segments,
    get_correlation_method,
    get_significance_threshold,
    get_dataset_name,
    get_model_name,
    get_quantization_bits,
    get_streaming_enabled,
    get_pii_scan_enabled,
)
from ast_cloner import (
    parse_python_file,
    extract_function_nodes,
    extract_class_nodes,
    compute_node_hash,
    compute_clone_density,
    compute_clone_density_batch,
    save_clone_metrics,
)
from model_metrics import (
    load_model_and_tokenizer,
    load_model_8bit,
    validate_perplexity,
    compute_perplexity,
    compute_perplexity_batch,
    save_perplexity_scores,
)
from memory_monitor import (
    get_total_memory_mb,
    check_memory_limit,
    validate_memory_within_limit,
    memory_monitor,
    setup_memory_monitoring,
)
from checksum_manifest import (
    setup_logging as checksum_setup_logging,
    compute_file_checksum,
    compute_all_artifact_checksums,
    load_manifest,
    save_manifest,
    record_artifact_checksums,
    verify_artifact_checksums,
    get_artifact_hashes,
)
from parse_failure_logger import (
    init_logger,
    get_parse_failures_path,
    log_parse_failure,
    clear_parse_failures,
    count_parse_failures,
    handle_parse_error,
)
from pii_scanner import (
    setup_logging as pii_setup_logging,
    should_scan_file,
    scan_file_for_pii,
    scan_directory,
    write_findings_to_csv,
    run_pii_scan,
)

# Configure module-level logger
logger = logging.getLogger(__name__)


def setup_logging(log_dir: Optional[Path] = None) -> logging.Logger:
    """
    Setup logging for the main pipeline.

    Args:
        log_dir: Directory for log files. Defaults to data/processed/.

    Returns:
        Configured logger instance.
    """
    if log_dir is None:
        log_dir = Path("data/processed")

    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"pipeline_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return logging.getLogger(__name__)


def load_raw_data(raw_data_path: Path) -> pd.DataFrame:
    """
    Load raw data from CSV file.

    Args:
        raw_data_path: Path to the raw data CSV file.

    Returns:
        DataFrame with raw code samples.
    """
    logger.info(f"Loading raw data from {raw_data_path}")

    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")

    df = pd.read_csv(raw_data_path)

    logger.info(f"Loaded {len(df)} records from {raw_data_path}")

    return df


def compute_clone_metrics_batch(
    data_df: pd.DataFrame,
    output_dir: Path,
    logger: logging.Logger
) -> pd.DataFrame:
    """
    Compute clone density for all Python files in the dataset.

    Args:
        data_df: DataFrame with code samples (must have 'code' or 'content' column).
        output_dir: Directory to save clone metrics.
        logger: Logger instance.

    Returns:
        DataFrame with clone density metrics.
    """
    logger.info("Computing clone density metrics...")

    output_dir.mkdir(parents=True, exist_ok=True)
    clone_metrics_path = output_dir / "clone_metrics.csv"

    clone_thresholds = get_clone_thresholds()
    results = []
    parse_failures = 0

    for idx, row in data_df.iterrows():
        try:
            code_content = row.get('code', row.get('content', ''))

            if not code_content or not isinstance(code_content, str):
                log_parse_failure(
                    file_path=f"row_{idx}",
                    error_type="invalid_content",
                    error_message="Content is not a valid string",
                    logger=logger
                )
                parse_failures += 1
                continue

            # Compute clone density for this code sample
            density = compute_clone_density(code_content)

            results.append({
                'file_id': idx,
                'clone_density': density,
                'clone_threshold': clone_thresholds[0],
                'timestamp': pd.Timestamp.now().isoformat()
            })

            if idx % 100 == 0:
                logger.info(f"Processed {idx} files...")

        except SyntaxError as e:
            log_parse_failure(
                file_path=f"row_{idx}",
                error_type="syntax_error",
                error_message=str(e),
                logger=logger
            )
            parse_failures += 1
        except Exception as e:
            handle_parse_error(
                file_path=f"row_{idx}",
                error=e,
                logger=logger
            )
            parse_failures += 1

    # Save clone metrics
    clone_df = pd.DataFrame(results)

    if len(clone_df) > 0:
        clone_df.to_csv(clone_metrics_path, index=False)
        logger.info(f"Saved {len(clone_df)} clone metrics to {clone_metrics_path}")
    else:
        logger.warning("No valid clone metrics computed")

    logger.info(f"Parse failures: {parse_failures}")

    return clone_df


def compute_perplexity_scores_batch(
    data_df: pd.DataFrame,
    output_dir: Path,
    logger: logging.Logger
) -> pd.DataFrame:
    """
    Compute perplexity scores for all code samples using the model.

    Args:
        data_df: DataFrame with code samples.
        output_dir: Directory to save perplexity scores.
        logger: Logger instance.

    Returns:
        DataFrame with perplexity scores.
    """
    logger.info("Computing perplexity scores...")

    output_dir.mkdir(parents=True, exist_ok=True)
    perplexity_path = output_dir / "perplexity_scores.csv"

    model_name = get_model_name()
    quantization_bits = get_quantization_bits()

    logger.info(f"Loading model: {model_name} (8-bit quantization)")

    try:
        # Load model in 8-bit quantization
        model, tokenizer = load_model_8bit(model_name)

        logger.info("Model loaded successfully")

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    results = []
    invalid_scores = 0

    for idx, row in data_df.iterrows():
        try:
            code_content = row.get('code', row.get('content', ''))

            if not code_content or not isinstance(code_content, str):
                log_parse_failure(
                    file_path=f"row_{idx}",
                    error_type="invalid_content",
                    error_message="Content is not a valid string",
                    logger=logger
                )
                invalid_scores += 1
                continue

            # Compute perplexity
            perplexity = compute_perplexity(model, tokenizer, code_content)

            # Validate perplexity value
            if not validate_perplexity(perplexity):
                logger.warning(f"Invalid perplexity at row {idx}: {perplexity}")
                invalid_scores += 1
                continue

            results.append({
                'file_id': idx,
                'perplexity': perplexity,
                'model': model_name,
                'timestamp': pd.Timestamp.now().isoformat()
            })

            if idx % 100 == 0:
                logger.info(f"Processed {idx} perplexity scores...")

        except Exception as e:
            handle_parse_error(
                file_path=f"row_{idx}",
                error=e,
                logger=logger
            )
            invalid_scores += 1

    # Save perplexity scores
    perplexity_df = pd.DataFrame(results)

    if len(perplexity_df) > 0:
        perplexity_df.to_csv(perplexity_path, index=False)
        logger.info(f"Saved {len(perplexity_df)} perplexity scores to {perplexity_path}")
    else:
        logger.warning("No valid perplexity scores computed")

    logger.info(f"Invalid scores: {invalid_scores}")

    return perplexity_df


def join_metrics(
    clone_df: pd.DataFrame,
    perplexity_df: pd.DataFrame,
    output_dir: Path,
    logger: logging.Logger
) -> pd.DataFrame:
    """
    Join clone density and perplexity metrics by file_id.

    Args:
        clone_df: DataFrame with clone density metrics.
        perplexity_df: DataFrame with perplexity scores.
        output_dir: Directory to save joined metrics.
        logger: Logger instance.

    Returns:
        DataFrame with joined metrics.
    """
    logger.info("Joining clone density and perplexity metrics...")

    # Merge on file_id
    joined_df = pd.merge(
        clone_df,
        perplexity_df,
        on='file_id',
        how='inner'
    )

    logger.info(f"Joined {len(joined_df)} records")

    # Save joined metrics
    joined_path = output_dir / "clone_metrics.csv"
    joined_df.to_csv(joined_path, index=False)

    logger.info(f"Saved joined metrics to {joined_path}")

    return joined_df


def run_pipeline(
    raw_data_path: Path,
    output_dir: Path,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Run the full pipeline: load data, compute metrics, join, and save.

    Args:
        raw_data_path: Path to raw data CSV.
        output_dir: Directory for output files.
        logger: Logger instance.

    Returns:
        Dictionary with pipeline results and statistics.
    """
    results = {
        'raw_data_path': str(raw_data_path),
        'output_dir': str(output_dir),
        'clone_metrics_path': None,
        'perplexity_scores_path': None,
        'joined_metrics_path': None,
        'total_records': 0,
        'valid_records': 0,
        'parse_failures': 0,
        'invalid_scores': 0,
    }

    # Setup memory monitoring (FIXED: only pass logger, not memory limit)
    setup_memory_monitoring(logger)

    # Stage 1: Load raw data
    logger.info("=" * 60)
    logger.info("Stage 1: Loading raw data")
    logger.info("=" * 60)

    data_df = load_raw_data(raw_data_path)
    results['total_records'] = len(data_df)

    # Stage 2: Compute clone density
    logger.info("=" * 60)
    logger.info("Stage 2: Computing clone density")
    logger.info("=" * 60)

    output_dir.mkdir(parents=True, exist_ok=True)
    clone_df = compute_clone_metrics_batch(data_df, output_dir, logger)
    results['clone_metrics_path'] = str(output_dir / "clone_metrics.csv")

    # Stage 3: Compute perplexity scores
    logger.info("=" * 60)
    logger.info("Stage 3: Computing perplexity scores")
    logger.info("=" * 60)

    perplexity_df = compute_perplexity_scores_batch(data_df, output_dir, logger)
    results['perplexity_scores_path'] = str(output_dir / "perplexity_scores.csv")

    # Stage 4: Join metrics
    logger.info("=" * 60)
    logger.info("Stage 4: Joining metrics")
    logger.info("=" * 60)

    joined_df = join_metrics(clone_df, perplexity_df, output_dir, logger)
    results['joined_metrics_path'] = str(output_dir / "clone_metrics.csv")
    results['valid_records'] = len(joined_df)

    # Stage 5: Record checksums
    logger.info("=" * 60)
    logger.info("Stage 5: Recording artifact checksums")
    logger.info("=" * 60)

    manifest_path = output_dir / "artifact_checksums.json"
    record_artifact_checksums(
        manifest_path=manifest_path,
        artifacts=[results['clone_metrics_path'], results['perplexity_scores_path']],
        logger=logger
    )

    logger.info("=" * 60)
    logger.info("Pipeline completed successfully")
    logger.info("=" * 60)

    return results


def save_results(
    results: Dict[str, Any],
    output_path: Path,
    logger: logging.Logger
) -> None:
    """
    Save pipeline results to a JSON file.

    Args:
        results: Dictionary with pipeline results.
        output_path: Path to save results.
        logger: Logger instance.
    """
    import json

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Saved results to {output_path}")


def main() -> int:
    """
    Main entry point for the pipeline.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    # Setup logging
    logger = setup_logging()

    logger.info("=" * 60)
    logger.info("Code Duplication Impact Analysis Pipeline")
    logger.info("=" * 60)

    try:
        # Get paths from config or use defaults
        raw_data_path = Path("data/raw/github-code-sample.csv")
        output_dir = Path("data/processed")

        # Verify raw data exists
        if not raw_data_path.exists():
            logger.error(f"Raw data not found: {raw_data_path}")
            logger.error("Please run data_loader.py first to download the dataset")
            return 1

        # Run the pipeline
        results = run_pipeline(raw_data_path, output_dir, logger)

        # Save results summary
        results_summary_path = output_dir / "pipeline_results.json"
        save_results(results, results_summary_path, logger)

        # Verify outputs
        clone_metrics_path = output_dir / "clone_metrics.csv"
        perplexity_scores_path = output_dir / "perplexity_scores.csv"

        if clone_metrics_path.exists():
            clone_df = pd.read_csv(clone_metrics_path)
            logger.info(f"clone_metrics.csv: {len(clone_df)} records")
        else:
            logger.error(f"Output file not created: {clone_metrics_path}")
            return 1

        if perplexity_scores_path.exists():
            perplexity_df = pd.read_csv(perplexity_scores_path)
            logger.info(f"perplexity_scores.csv: {len(perplexity_df)} records")
        else:
            logger.error(f"Output file not created: {perplexity_scores_path}")
            return 1

        logger.info("Pipeline completed successfully!")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())