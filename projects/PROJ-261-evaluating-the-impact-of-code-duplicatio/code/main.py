import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
import argparse
import csv

# Import from sibling modules using the API surface
from config import (
    get_random_seed,
    get_dataset_name,
    get_model_name,
    get_quantization_bits,
    get_clone_thresholds,
    get_all_config
)
from data_loader import load_raw_data, download_and_save_sample
from ast_cloner import compute_clone_density_batch, save_clone_metrics
from model_metrics import compute_perplexity_batch, save_perplexity_scores
from checksum_manifest import record_artifact_checksums, save_manifest
from parse_failure_logger import log_parse_failure, count_parse_failures

def setup_logging():
    """Setup logging configuration for main pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/pipeline.log')
        ]
    )
    return logging.getLogger(__name__)

def load_raw_data_wrapper(data_path: Path) -> List[Dict[str, Any]]:
    """Wrapper to load raw data with error handling."""
    logger = logging.getLogger(__name__)
    if not data_path.exists():
        logger.error(f"Raw data file not found: {data_path}")
        logger.error("Please run: python code/data_loader.py")
        raise FileNotFoundError(f"Raw data not found: {data_path}")

    try:
        data = load_raw_data(data_path)
        logger.info(f"Loaded {len(data)} samples from {data_path}")
        return data
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        raise

def compute_clone_metrics_batch(data: List[Dict[str, Any]],
                                output_path: Path) -> pd.DataFrame:
    """Compute clone density metrics for batch of code samples."""
    logger = logging.getLogger(__name__)
    logger.info(f"Computing clone density for {len(data)} samples")

    clone_metrics = []
    for i, sample in enumerate(data):
        try:
            code = sample.get('code', '')
            path = sample.get('path', f'sample_{i}.py')

            if not code or not isinstance(code, str):
                log_parse_failure(path, "Empty or invalid code", "main_pipeline")
                continue

            # Compute clone density using ast_cloner
            density = compute_clone_density_batch([code], [path])
            if density and len(density) > 0:
                clone_metrics.append({
                    'path': path,
                    'clone_density': float(density[0]),
                    'sample_id': i
                })
        except Exception as e:
            log_parse_failure(sample.get('path', f'sample_{i}.py'),
                             str(e), 'main_pipeline')
            continue

    # Save clone metrics
    clone_df = pd.DataFrame(clone_metrics)
    if len(clone_df) > 0:
        save_clone_metrics(clone_df, output_path)
        logger.info(f"Saved clone metrics to {output_path}")
    else:
        logger.warning("No valid clone metrics computed")
        clone_df.to_csv(output_path, index=False)

    return clone_df

def compute_perplexity_scores_batch(data: List[Dict[str, Any]],
                                    output_path: Path) -> pd.DataFrame:
    """Compute perplexity scores for batch of code samples."""
    logger = logging.getLogger(__name__)
    logger.info(f"Computing perplexity for {len(data)} samples")

    perplexity_scores = []
    for i, sample in enumerate(data):
        try:
            code = sample.get('code', '')
            path = sample.get('path', f'sample_{i}.py')

            if not code or not isinstance(code, str):
                log_parse_failure(path, "Empty or invalid code", "main_pipeline")
                continue

            # Compute perplexity using model_metrics
            perplexity = compute_perplexity_batch([code], [path])
            if perplexity and len(perplexity) > 0:
                perplexity_scores.append({
                    'path': path,
                    'perplexity': float(perplexity[0]),
                    'sample_id': i
                })
        except Exception as e:
            log_parse_failure(sample.get('path', f'sample_{i}.py'),
                             str(e), 'main_pipeline')
            continue

    # Save perplexity scores
    perplexity_df = pd.DataFrame(perplexity_scores)
    if len(perplexity_df) > 0:
        save_perplexity_scores(perplexity_df, output_path)
        logger.info(f"Saved perplexity scores to {output_path}")
    else:
        logger.warning("No valid perplexity scores computed")
        perplexity_df.to_csv(output_path, index=False)

    return perplexity_df

def join_metrics(clone_df: pd.DataFrame, perplexity_df: pd.DataFrame) -> pd.DataFrame:
    """Join clone density and perplexity metrics on sample_id."""
    logger = logging.getLogger(__name__)
    logger.info(f"Joining metrics: {len(clone_df)} clone, {len(perplexity_df)} perplexity")

    # Merge on sample_id
    merged = pd.merge(
        clone_df,
        perplexity_df,
        on='sample_id',
        how='inner'
    )

    logger.info(f"Merged metrics: {len(merged)} samples")
    return merged

def run_pipeline(raw_data_path: Path,
                clone_output_path: Path,
                perplexity_output_path: Path,
                merged_output_path: Path) -> pd.DataFrame:
    """Run the full pipeline: load data, compute metrics, join results."""
    logger = logging.getLogger(__name__)
    logger.info("Starting pipeline execution")

    # Step 1: Load raw data
    data = load_raw_data_wrapper(raw_data_path)

    # Step 2: Compute clone density
    clone_df = compute_clone_metrics_batch(data, clone_output_path)

    # Step 3: Compute perplexity
    perplexity_df = compute_perplexity_scores_batch(data, perplexity_output_path)

    # Step 4: Join metrics
    merged_df = join_metrics(clone_df, perplexity_df)

    logger.info(f"Pipeline complete. Final merged dataset: {len(merged_df)} samples")
    return merged_df

def save_results(merged_df: pd.DataFrame, output_path: Path) -> str:
    """Save merged results to CSV and record checksum."""
    logger = logging.getLogger(__name__)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved merged results to {output_path}")

    # Record checksum in manifest
    record_artifact_checksums([str(output_path)])

    return output_path

def main():
    """Main entry point for pipeline orchestration."""
    parser = argparse.ArgumentParser(description='Run code duplication analysis pipeline')
    parser.add_argument('--raw-data', type=str, default='data/raw/github-code-sample.csv',
                      help='Path to raw data CSV')
    parser.add_argument('--clone-output', type=str, default='data/processed/clone_metrics.csv',
                      help='Output path for clone metrics')
    parser.add_argument('--perplexity-output', type=str, default='data/processed/perplexity_scores.csv',
                      help='Output path for perplexity scores')
    parser.add_argument('--merged-output', type=str, default='data/processed/merged_metrics.csv',
                      help='Output path for merged metrics')

    args = parser.parse_args()
    logger = setup_logging()

    raw_data_path = Path(args.raw_data)
    clone_output_path = Path(args.clone_output)
    perplexity_output_path = Path(args.perplexity_output)
    merged_output_path = Path(args.merged_output)

    try:
        # Run pipeline
        merged_df = run_pipeline(
            raw_data_path=raw_data_path,
            clone_output_path=clone_output_path,
            perplexity_output_path=perplexity_output_path,
            merged_output_path=merged_output_path
        )

        # Save final results
        save_results(merged_df, merged_output_path)

        # Save individual outputs as well (for backward compatibility)
        if not clone_output_path.exists():
            save_results(merged_df[['path', 'clone_density', 'sample_id']].rename(
                columns={'clone_density': 'clone_density'}
            ), clone_output_path)

        if not perplexity_output_path.exists():
            save_results(merged_df[['path', 'perplexity', 'sample_id']].rename(
                columns={'perplexity': 'perplexity'}
            ), perplexity_output_path)

        logger.info("Pipeline completed successfully")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Pipeline failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
