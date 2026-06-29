"""
Main pipeline orchestration for code duplication impact analysis.

This module orchestrates the end-to-end pipeline:
1. Load raw data from HuggingFace datasets
2. Compute clone density metrics
3. Compute perplexity scores
4. Join metrics and save results

Output files:
- data/processed/clone_metrics.csv
- data/processed/perplexity_scores.csv
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    get_clone_thresholds,
    get_random_seed,
    get_memory_limit_mb,
    get_max_runtime_seconds,
    get_min_valid_segments,
    get_streaming_enabled,
    get_dataset_name,
    get_model_name,
    get_quantization_bits,
    get_pii_scan_enabled
)
from data_loader import stream_dataset, save_raw_data_to_csv, download_and_save_sample
from ast_cloner import compute_clone_density_batch, save_clone_metrics
from model_metrics import load_model_8bit, compute_perplexity_batch, save_perplexity_scores
from pii_scanner import run_pii_scan
from parse_failure_logger import log_parse_failure, init_logger
from checksum_manifest import record_artifact_checksums
from memory_monitor import setup_memory_monitoring, check_memory_limit

# Setup logging
logger = logging.getLogger(__name__)


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure logging for the pipeline."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/pipeline.log')
        ]
    )
    return logger


def save_results(clone_metrics: pd.DataFrame, perplexity_scores: pd.DataFrame, output_dir: Path):
    """Save computed metrics to CSV files."""
    clone_metrics_path = output_dir / 'clone_metrics.csv'
    perplexity_path = output_dir / 'perplexity_scores.csv'

    clone_metrics.to_csv(clone_metrics_path, index=False)
    perplexity_scores.to_csv(perplexity_path, index=False)

    logger.info(f"Saved clone metrics to: {clone_metrics_path}")
    logger.info(f"Saved perplexity scores to: {perplexity_path}")

    return clone_metrics_path, perplexity_path


def run_pipeline(
    raw_data_path: Path,
    output_dir: Path,
    sample_size: int = 1000
) -> Dict[str, Any]:
    """
    Run the complete analysis pipeline.

    Args:
        raw_data_path: Path to raw data CSV file
        output_dir: Directory for output files
        sample_size: Number of files to process

    Returns:
        Dictionary with pipeline results and metadata
    """
    results = {
        'clone_metrics_path': None,
        'perplexity_path': None,
        'files_processed': 0,
        'parse_failures': 0,
        'memory_peak_mb': 0
    }

    # Setup memory monitoring
    setup_memory_monitoring(limit_mb=get_memory_limit_mb())

    # Initialize parse failure logger
    init_logger()

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load sample files from raw data
    logger.info(f"Loading {sample_size} files from: {raw_data_path}")

    # Read raw data CSV
    if not raw_data_path.exists():
        logger.error(f"Raw data not found: {raw_data_path}")
        # Sample files will be None, handled below
        sample_files = []
    else:
        raw_df = pd.read_csv(raw_data_path)
        # Sample files from the CSV - ensure this variable is always defined
        sample_files = raw_df['code'].head(sample_size).tolist()
        logger.info(f"Loaded {len(sample_files)} files from raw data")

    # Handle case where sample_files is empty
    if not sample_files:
        logger.warning("No sample files found, using empty list for processing")
        sample_files = []

    results['files_processed'] = len(sample_files)

    # Run PII scan on data directory
    if get_pii_scan_enabled():
        logger.info("Running PII scan on data directory...")
        run_pii_scan()

    # Compute clone density metrics
    logger.info("Computing clone density metrics...")
    try:
        clone_metrics = compute_clone_density_batch(
            sample_files,
            thresholds=get_clone_thresholds()
        )
        clone_metrics_path = save_clone_metrics(clone_metrics, output_dir / 'clone_metrics.csv')
        results['clone_metrics_path'] = clone_metrics_path
        logger.info(f"Computed clone density for {len(clone_metrics)} files")
    except Exception as e:
        logger.error(f"Clone density computation failed: {e}")
        clone_metrics = pd.DataFrame()
        results['parse_failures'] = len(sample_files)

    # Load model for perplexity computation
    logger.info("Loading model for perplexity computation...")
    try:
        model, tokenizer = load_model_8bit(
            model_name=get_model_name(),
            quantization_bits=get_quantization_bits()
        )
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Model loading failed: {e}")
        perplexity_scores = pd.DataFrame()
        results['perplexity_path'] = None
        # Continue without perplexity scores
        model = None
        tokenizer = None

    # Compute perplexity scores
    logger.info("Computing perplexity scores...")
    perplexity_scores = pd.DataFrame()
    if model is not None and tokenizer is not None and len(sample_files) > 0:
        try:
            # Check memory before computation
            if not check_memory_limit():
                logger.warning("Memory limit may be exceeded during perplexity computation")

            perplexity_scores = compute_perplexity_batch(
                sample_files,
                model,
                tokenizer
            )
            perplexity_path = save_perplexity_scores(perplexity_scores, output_dir / 'perplexity_scores.csv')
            results['perplexity_path'] = perplexity_path
            logger.info(f"Computed perplexity for {len(perplexity_scores)} files")
        except Exception as e:
            logger.error(f"Perplexity computation failed: {e}")
            results['perplexity_path'] = None

    # Save results
    if len(clone_metrics) > 0 or len(perplexity_scores) > 0:
        save_results(clone_metrics, perplexity_scores, output_dir)

    # Record checksums
    try:
        record_artifact_checksums(output_dir)
    except Exception as e:
        logger.warning(f"Checksum recording failed: {e}")

    return results


def main():
    """Main entry point for the pipeline."""
    setup_logging()

    logger.info("=" * 60)
    logger.info("Starting code duplication impact analysis pipeline")
    logger.info("=" * 60)

    # Configuration
    raw_data_path = Path('data/raw/github-code-sample.csv')
    output_dir = Path('data/processed')
    sample_size = get_min_valid_segments()

    # Run pipeline
    try:
        results = run_pipeline(raw_data_path, output_dir, sample_size)

        logger.info("=" * 60)
        logger.info("Pipeline execution completed")
        logger.info(f"Files processed: {results['files_processed']}")
        logger.info(f"Parse failures: {results['parse_failures']}")
        logger.info(f"Clone metrics saved: {results['clone_metrics_path']}")
        logger.info(f"Perplexity scores saved: {results['perplexity_path']}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == '__main__':
    sys.exit(main())
