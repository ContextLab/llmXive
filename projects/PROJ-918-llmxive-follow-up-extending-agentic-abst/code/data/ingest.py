"""
Data Ingestion Pipeline for 'Agentic Abstention' Benchmark.

Primary Source: Fetches the real 'Agentic Abstention' dataset from Hugging Face.
Fallback: If the real dataset is unavailable or fails verification, falls back
          to the Synthetic Agent Simulator (code/data/simulator.py).

Sequence:
1. Fetch/Verify Benchmark (Hugging Face: 'llmXive/agentic-abstention-benchmark')
2. If fail, fallback to Simulator.
"""
import os
import sys
import logging
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd

# Local imports matching API surface
from data.simulator import run_synthetic_simulator
from config import get_seed, get_path, load_config

# Ensure logging is configured
from logging_config import setup_logging

logger = setup_logging(__name__)

# Configuration constants
HF_DATASET_NAME = "llmXive/agentic-abstention-benchmark"
HF_FILE_NAME = "benchmark_data.csv"
EXPECTED_CHECKSUM_FILE = "expected_checksums.json"
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"

def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_expected_checksums() -> Dict[str, str]:
    """Load expected checksums from the project config or default location."""
    config = load_config()
    checksum_path = Path(config.get("paths", {}).get("checksums", "data/checksums.json"))
    
    if checksum_path.exists():
        with open(checksum_path, "r") as f:
            return json.load(f)
    
    # Fallback if no checksum file exists yet (first run)
    logger.warning("No expected checksums file found. Verification will be skipped for integrity, but file existence will be checked.")
    return {}

def verify_data_integrity(file_path: Path, expected_checksums: Dict[str, str]) -> bool:
    """Verify the downloaded file against expected checksums."""
    if not file_path.exists():
        return False
    
    filename = file_path.name
    if filename not in expected_checksums:
        logger.warning(f"No expected checksum for {filename}. Skipping integrity check.")
        return True
    
    actual_hash = calculate_file_hash(file_path)
    expected_hash = expected_checksums[filename]
    
    if actual_hash == expected_hash:
        logger.info(f"Integrity verified for {filename}: {actual_hash[:16]}...")
        return True
    else:
        logger.error(f"Integrity check FAILED for {filename}.")
        logger.error(f"Expected: {expected_hash}")
        logger.error(f"Actual:   {actual_hash}")
        return False

def fetch_benchmark_data(
    output_dir: Path,
    output_filename: str,
    seed: int,
    logger: logging.Logger
) -> Optional[Path]:
    """
    Attempts to fetch the REAL 'Agentic Abstention' benchmark from Hugging Face.
    
    Returns:
        Path to the downloaded CSV if successful, None if fetch fails.
    """
    try:
        # Dynamically import datasets to avoid hard dependency if not installed
        try:
            from datasets import load_dataset
        except ImportError:
            logger.error("The 'datasets' library is required to fetch the benchmark. Install with: pip install datasets")
            return None

        logger.info(f"Attempting to fetch dataset: {HF_DATASET_NAME}")
        
        # Load dataset
        dataset = load_dataset(HF_DATASET_NAME, split="train")
        
        # Convert to pandas
        df = dataset.to_pandas()
        
        # Validate basic schema (must have required columns)
        required_cols = ['task_id', 'search_count', 'error_freq', 'tokens', 'turns', 'abstention_label']
        if not all(col in df.columns for col in required_cols):
            missing = set(required_cols) - set(df.columns)
            logger.error(f"Dataset missing required columns: {missing}")
            return None
        
        # Save to CSV
        output_path = output_dir / output_filename
        df.to_csv(output_path, index=False)
        
        logger.info(f"Successfully fetched and saved benchmark data to {output_path}")
        logger.info(f"Dataset shape: {df.shape}")
        
        return output_path

    except Exception as e:
        logger.error(f"Failed to fetch benchmark data: {str(e)}")
        return None

def run_ingestion_pipeline(
    output_dir: Optional[Path] = None,
    output_filename: str = "abstention_benchmark.csv"
) -> Path:
    """
    Orchestrates the ingestion pipeline:
    1. Try to fetch real benchmark.
    2. If fail, run synthetic simulator.
    3. Returns path to the final data file.
    """
    if output_dir is None:
        output_dir = Path(get_path("raw_data"))
    
    output_dir.mkdir(parents=True, exist_ok=True)
    seed = get_seed()
    
    logger.info("Starting Ingestion Pipeline (T011)")
    logger.info(f"Target Output: {output_dir / output_filename}")

    # Step 1: Fetch Real Benchmark
    real_data_path = fetch_benchmark_data(
        output_dir=output_dir,
        output_filename=output_filename,
        seed=seed,
        logger=logger
    )

    if real_data_path and real_data_path.exists():
        # Verify integrity if checksums exist
        expected_checksums = load_expected_checksums()
        if verify_data_integrity(real_data_path, expected_checksums):
            logger.info("Ingestion Pipeline Complete: Real benchmark verified.")
            return real_data_path
        else:
            logger.warning("Real benchmark failed integrity check. Falling back to simulator.")
    else:
        logger.warning("Real benchmark fetch failed or file missing. Falling back to simulator.")

    # Step 2: Fallback to Simulator
    logger.info("Running Synthetic Agent Simulator as fallback.")
    sim_filename = "synthetic_abstention_fallback.csv"
    sim_path = run_synthetic_simulator(
        output_dir=output_dir,
        output_filename=sim_filename,
        seed=seed,
        logger=logger
    )
    
    if sim_path and sim_path.exists():
        logger.info("Ingestion Pipeline Complete: Synthetic fallback generated.")
        return sim_path
    
    # Step 3: Ultimate Failure
    logger.error("Ingestion Pipeline FAILED: Both real benchmark and simulator failed.")
    raise RuntimeError("Failed to ingest any data source.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run the data ingestion pipeline.")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    parser.add_argument("--output-filename", type=str, default="abstention_benchmark.csv", help="Override output filename")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None
    
    result_path = run_ingestion_pipeline(
        output_dir=output_dir,
        output_filename=args.output_filename
    )
    
    print(f"Pipeline completed successfully. Output written to: {result_path}")
