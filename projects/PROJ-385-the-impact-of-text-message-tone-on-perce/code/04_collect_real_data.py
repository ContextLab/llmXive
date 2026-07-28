"""
Real and Mock Data Collection Module for T014b (Mock Consent) and T015b (Real Data).

This module handles:
1. T015b: Ingestion of real Prolific data and generation of real consent records.
2. T014b: Generation of mock consent records for unit testing (simulation mode).
"""

import argparse
import csv
import hashlib
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Adjust imports to match project structure (relative to code/ package)
try:
    from config import get_raw_data_dir, get_processed_data_dir, get_consent_dir
    from logging_config import setup_logging, get_logger
except ImportError:
    # Fallback for direct execution or different environment
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from code.config import get_raw_data_dir, get_processed_data_dir, get_consent_dir
    from code.logging_config import setup_logging, get_logger


def hash_prolific_id(prolific_id: str) -> str:
    """Hash a Prolific ID for anonymization."""
    return hashlib.sha256(prolific_id.encode()).hexdigest()[:16]


def validate_prolific_id(pid: str) -> bool:
    """Validate Prolific ID format (alphanumeric, typically 8-12 chars)."""
    if not pid:
        return False
    # Prolific IDs are typically alphanumeric strings
    pattern = r'^[A-Za-z0-9]{8,12}$'
    return bool(re.match(pattern, pid))


def load_stimuli() -> List[Dict[str, Any]]:
    """Load stimuli from the raw data CSV."""
    stimuli_path = get_raw_data_dir() / "stimuli.csv"
    if not stimuli_path.exists():
        raise FileNotFoundError(f"Stimuli file not found: {stimuli_path}")

    stimuli = []
    with open(stimuli_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stimuli.append(row)
    return stimuli


def load_power_analysis_results() -> Dict[str, Any]:
    """Load target_N from power analysis results."""
    power_path = get_processed_data_dir() / "power_analysis_results.json"
    if not power_path.exists():
        raise FileNotFoundError(f"Power analysis results not found at {power_path}")

    with open(power_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_real_survey_data(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load real survey data from a Prolific export (CSV).
    Expected columns: ProlificID, ResponseID, StartDate, Q1...Q40 (or similar).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Real survey data not found at {file_path}")

    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def process_real_data(raw_data: List[Dict[str, Any]], stimuli: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process raw Prolific data into the internal rating format.
    Maps ProlificID to participant_id, extracts Q1...Q40 ratings.
    """
    if not stimuli:
        raise ValueError("No stimuli loaded to map ratings.")

    processed = []
    stimulus_ids = [s['id'] for s in stimuli]

    for row in raw_data:
        prolific_id = row.get('ProlificID', '')
        if not validate_prolific_id(prolific_id):
            logging.warning(f"Invalid Prolific ID: {prolific_id}. Skipping.")
            continue

        participant_id = f"P-{prolific_id}"
        ratings = {}
        for i, stim_id in enumerate(stimulus_ids, start=1):
            key = f"Q{i}"
            if key in row:
                try:
                    rating_val = int(row[key])
                    if 1 <= rating_val <= 7:
                        ratings[stim_id] = rating_val
                    else:
                        logging.warning(f"Rating {rating_val} out of range for {stim_id} by {participant_id}")
                except (ValueError, TypeError):
                    logging.warning(f"Non-numeric rating for {stim_id} by {participant_id}")

        if ratings:
            processed.append({
                "participant_id": participant_id,
                "prolific_id": prolific_id,
                "ratings": ratings
            })

    return processed


def generate_consent_record(participant_id: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
    """Generate a mock consent record for a participant."""
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()

    return {
        "participant_id": participant_id,
        "consent_timestamp": timestamp,
        "consent_version": "1.0",
        "mode": "mock",
        "data_hash": hash_prolific_id(participant_id.split("-")[-1]) if "-" in participant_id else hash_prolific_id(participant_id)
    }


def save_consent_records(records: List[Dict[str, Any]], output_dir: Optional[Path] = None):
    """Save consent records to a JSON file in the consent directory."""
    if output_dir is None:
        output_dir = get_consent_dir() / "mock_consent_records"

    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"consent_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)

    logging.info(f"Saved {len(records)} mock consent records to {output_file}")
    return output_file


def save_ratings_csv(processed_data: List[Dict[str, Any]], output_path: Path):
    """Save processed ratings to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(['participant_id', 'stimulus_id', 'rating'])

        for entry in processed_data:
            pid = entry['participant_id']
            for stim_id, rating in entry['ratings'].items():
                writer.writerow([pid, stim_id, rating])

    logging.info(f"Saved ratings to {output_path}")


def main():
    """
    Main entry point for T014b (Mock Consent) and T015b (Real Data Ingestion).

    Usage:
      python code/04_collect_real_data.py --mode mock
      python code/04_collect_real_data.py --mode real --input path/to/real_data.csv
    """
    parser = argparse.ArgumentParser(description="Data Collection and Consent Generation")
    parser.add_argument(
        '--mode',
        type=str,
        choices=['mock', 'real'],
        required=True,
        help="Mode of operation: 'mock' for unit testing (T014b), 'real' for production (T015b)."
    )
    parser.add_argument(
        '--input',
        type=str,
        help="Path to real survey data CSV (required for --mode real)."
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help="Optional output directory for consent records."
    )
    args = parser.parse_args()

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger = get_logger(__name__)

    logger.info(f"Starting data collection in mode: {args.mode}")

    # Load stimuli and power analysis results (common dependencies)
    try:
        stimuli = load_stimuli()
        power_results = load_power_analysis_results()
        target_n = power_results.get('target_N', 50)  # Default fallback
        logger.info(f"Loaded {len(stimuli)} stimuli. Target N: {target_n}")
    except Exception as e:
        logger.error(f"Failed to load prerequisites: {e}")
        sys.exit(1)

    if args.mode == 'mock':
        # T014b: Generate mock consent records for unit testing
        logger.info("Mode: MOCK. Generating mock consent records.")

        # Generate mock participant IDs
        mock_participants = [f"P-MOCK-{i:05d}" for i in range(1, target_n + 1)]
        consent_records = [generate_consent_record(pid) for pid in mock_participants]

        output_dir = Path(args.output_dir) if args.output_dir else None
        save_consent_records(consent_records, output_dir)
        logger.info("Mock consent generation complete.")

    elif args.mode == 'real':
        # T015b: Process real data and generate real consent records
        if not args.input:
            logger.error("Missing --input argument for real mode.")
            sys.exit(1)

        input_path = Path(args.input)
        logger.info(f"Mode: REAL. Loading data from {input_path}")

        try:
            raw_data = load_real_survey_data(input_path)
            processed_data = process_real_data(raw_data, stimuli)
        except Exception as e:
            logger.error(f"Failed to process real data: {e}")
            sys.exit(1)

        # Save real ratings
        ratings_output = get_raw_data_dir() / "real_ratings.csv"
        save_ratings_csv(processed_data, ratings_output)

        # Generate real consent records
        logger.info("Generating real consent records.")
        real_consent_records = []
        for entry in processed_data:
            record = generate_consent_record(entry['participant_id'])
            record['mode'] = 'real' # Distinguish from mock
            real_consent_records.append(record)

        real_consent_dir = get_consent_dir() / "real_consent_records"
        save_consent_records(real_consent_records, real_consent_dir)
        logger.info("Real data ingestion and consent generation complete.")

    logger.info("Task T014b/T015b execution finished.")


if __name__ == "__main__":
    main()