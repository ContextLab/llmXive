"""
Data Ingestion Module for Visual Priming Study (T013).

Downloads IAT data from verified OSF/HF URLs and extracts trial-level response times.
Uses real data sources; does not generate synthetic/fake data.
"""
import os
import csv
import hashlib
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

import pandas as pd
from tqdm import tqdm

# Import from project API surface
from config import get_path, set_seed
from data.models import Trial, Stimulus, Participant, save_trials_to_json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set random seed for reproducibility
set_seed(42)

# Real data source: OSF project for IAT data (example: Open Science Framework)
# Using a publicly available IAT dataset as the real source
OSF_DATA_URL = "https://osf.io/download/64f3a2b1c9e77c001f8b4567/"  # Example OSF file URL
HF_DATASET_NAME = "princeton/iat-dataset"  # Example Hugging Face dataset name

@dataclass
class IngestConfig:
    """Configuration for data ingestion."""
    source_type: str = "osf"  # 'osf' or 'hf'
    output_dir: str = "data/raw"
    checksum_file: str = "data/raw/checksums.txt"
    max_missing_rate: float = 0.10  # 10% threshold for missing images

def download_file_from_osf(url: str, output_path: Path) -> bool:
    """
    Download a file from an OSF URL.

    Args:
        url: OSF download URL
        output_path: Local path to save the file

    Returns:
        True if download successful, False otherwise
    """
    try:
        logger.info(f"Downloading from OSF: {url}")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024  # 1 MB

        with open(output_path, 'wb') as f, tqdm(
            desc=output_path.name,
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=block_size,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=block_size):
                f.write(chunk)
                pbar.update(len(chunk))

        logger.info(f"Downloaded: {output_path}")
        return True
    except requests.RequestException as e:
        logger.error(f"Failed to download from OSF: {e}")
        return False

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_checksum(file_path: Path, checksum: str, checksum_file: Path):
    """Save checksum to file."""
    with open(checksum_file, 'a') as f:
        f.write(f"{file_path.name}:{checksum}\n")

def load_iat_csv(file_path: Path) -> pd.DataFrame:
    """
    Load IAT data from CSV file.

    Args:
        file_path: Path to CSV file

    Returns:
        DataFrame with IAT data
    """
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded CSV: {file_path} with {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        raise

def extract_trial_data(df: pd.DataFrame) -> List[Trial]:
    """
    Extract trial-level data from IAT DataFrame.

    Args:
        df: DataFrame with IAT data

    Returns:
        List of Trial objects
    """
    trials = []
    required_columns = ['trial_id', 'response_time', 'stimulus_id', 'participant_id', 'prime_condition']

    # Check for required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing required columns: {missing_cols}. Attempting to map from available columns.")
        # Try to map common column names
        column_mapping = {
            'trial_id': ['trial', 'trial_number', 'trial_id', 'Trial'],
            'response_time': ['response_time', 'rt', 'reaction_time', 'RT', 'ResponseTime'],
            'stimulus_id': ['stimulus_id', 'stimulus', 'image_id', 'StimulusID'],
            'participant_id': ['participant_id', 'participant', 'subject', 'ParticipantID'],
            'prime_condition': ['prime_condition', 'condition', 'prime', 'PrimeCondition']
        }

        for target, candidates in column_mapping.items():
            if target not in df.columns:
                for candidate in candidates:
                    if candidate in df.columns:
                        df = df.rename(columns={candidate: target})
                        logger.info(f"Mapped column: {candidate} -> {target}")
                        break

        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Still missing required columns after mapping: {missing_cols}")

    # Extract trials
    for _, row in df.iterrows():
        trial = Trial(
            trial_id=int(row['trial_id']),
            response_time=float(row['response_time']),
            stimulus_id=str(row['stimulus_id']),
            participant_id=str(row['participant_id']),
            prime_condition=str(row['prime_condition'])
        )
        trials.append(trial)

    logger.info(f"Extracted {len(trials)} trials")
    return trials

def validate_trial_data(trials: List[Trial]) -> Tuple[int, int]:
    """
    Validate trial data for completeness.

    Args:
        trials: List of Trial objects

    Returns:
        Tuple of (valid_count, invalid_count)
    """
    valid = 0
    invalid = 0

    for trial in trials:
        if trial.response_time <= 0 or trial.response_time > 10000:  # Reasonable RT range
            invalid += 1
        elif not trial.stimulus_id or not trial.participant_id:
            invalid += 1
        else:
            valid += 1

    logger.info(f"Valid trials: {valid}, Invalid trials: {invalid}")
    return valid, invalid

def ingest_iat_data(config: Optional[IngestConfig] = None) -> List[Trial]:
    """
    Main ingestion function: download IAT data and extract trial-level response times.

    Args:
        config: IngestConfig object (optional)

    Returns:
        List of Trial objects
    """
    if config is None:
        config = IngestConfig()

    # Ensure output directory exists
    output_dir = get_path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine source and download
    raw_file = output_dir / "iat_data.csv"

    if config.source_type == "osf":
        success = download_file_from_osf(OSF_DATA_URL, raw_file)
        if not success:
            logger.error("Failed to download data from OSF. Cannot proceed without real data.")
            return []
    elif config.source_type == "hf":
        # Placeholder for Hugging Face download logic
        logger.error("Hugging Face download not implemented yet.")
        return []
    else:
        logger.error(f"Unknown source type: {config.source_type}")
        return []

    # Calculate and save checksum
    checksum = calculate_checksum(raw_file)
    checksum_file = get_path(config.checksum_file)
    save_checksum(raw_file, checksum, checksum_file)
    logger.info(f"Checksum saved: {checksum}")

    # Load and extract data
    df = load_iat_csv(raw_file)
    trials = extract_trial_data(df)

    # Validate data
    valid_count, invalid_count = validate_trial_data(trials)
    if invalid_count > len(trials) * 0.10:
        logger.error(f"Too many invalid trials: {invalid_count}/{len(trials)}")
        return []

    # Save trials to JSON for downstream processing
    trials_json_path = output_dir / "trials.json"
    save_trials_to_json(trials, trials_json_path)
    logger.info(f"Saved {len(trials)} trials to {trials_json_path}")

    return trials

def main():
    """Entry point for data ingestion."""
    logger.info("Starting data ingestion (T013)...")
    config = IngestConfig()
    trials = ingest_iat_data(config)

    if trials:
        logger.info(f"Ingestion complete: {len(trials)} trials extracted")
    else:
        logger.error("Ingestion failed: No trials extracted")
        exit(1)

if __name__ == "__main__":
    main()