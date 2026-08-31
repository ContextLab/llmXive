"""
T017 Implementation: Generate standardized CSV output with checksums.

This script loads the preprocessed data (with Markov surprisal computed),
validates the schema, ensures the required columns are present, and writes
the standardized CSV to `data/processed/standardized.csv`. It also computes
and logs the SHA256 checksum.

Dependencies:
  - T016: Must have produced `data/processed/markov_state.json` and
          `data/processed/preprocessed_with_surprisal.csv` (or similar).
"""
import hashlib
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
STANDARDIZED_OUTPUT_PATH = PROCESSED_DIR / "standardized.csv"
MARKOV_STATE_PATH = PROCESSED_DIR / "markov_state.json"
PREPROCESSED_INPUT_PATH = PROCESSED_DIR / "preprocessed_with_surprisal.csv"

# Required columns for the standardized output
REQUIRED_COLUMNS = [
    'participant_id',
    'stimulus_sequence',
    'duration_estimate',
    'surprisal',
    'sequence_length'
]

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_schema(df: pd.DataFrame, required_cols: List[str]) -> bool:
    """Validate that the DataFrame contains all required columns."""
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Schema validation failed. Missing columns: {missing_cols}")
        return False
    return True

def verify_markov_derivation() -> bool:
    """
    Verify that the Markov model state file exists and is valid.
    This ensures T016 completed successfully before generating output.
    """
    if not MARKOV_STATE_PATH.exists():
        logger.error(f"Markov state file not found at {MARKOV_STATE_PATH}. "
                     "Ensure T016 (compute_markov_surprisal) has run.")
        return False

    try:
        with open(MARKOV_STATE_PATH, 'r') as f:
            markov_data = json.load(f)

        # Verify required keys as per T016/T017b requirements
        required_keys = ['transition_matrix', 'alphabet', 'order']
        for key in required_keys:
            if key not in markov_data:
                logger.error(f"Markov state missing required key: {key}")
                return False

        # Type checks
        if not isinstance(markov_data['transition_matrix'], dict):
            logger.error("transition_matrix must be a dict")
            return False
        if not isinstance(markov_data['alphabet'], list):
            logger.error("alphabet must be a list")
            return False
        if not isinstance(markov_data['order'], int):
            logger.error("order must be an int")
            return False

        logger.info(f"Markov state verified: order={markov_data['order']}, "
                    f"alphabet size={len(markov_data['alphabet'])}")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in markov_state.json: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading markov_state.json: {e}")
        return False

def load_intermediate_data() -> pd.DataFrame:
    """Load the preprocessed data with surprisal."""
    if not PREPROCESSED_INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Preprocessed data not found at {PREPROCESSED_INPUT_PATH}. "
            "Ensure T015/T016 (preprocess.py) has run successfully."
        )

    try:
        # Use chunked loading if file is large, though for standardized output
        # we assume it fits in memory or T015 already capped it.
        logger.info(f"Loading preprocessed data from {PREPROCESSED_INPUT_PATH}")
        df = pd.read_csv(PREPROCESSED_INPUT_PATH)
        logger.info(f"Loaded {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Failed to load preprocessed data: {e}")
        raise

def run_t017() -> Dict[str, Any]:
    """
    Main execution logic for T017.
    1. Verify Markov artifacts exist.
    2. Load preprocessed data.
    3. Validate schema.
    4. Ensure >= 100 rows.
    5. Write standardized CSV.
    6. Compute and log checksum.
    """
    results = {
        'status': 'failed',
        'message': '',
        'output_path': str(STANDARDIZED_OUTPUT_PATH),
        'checksum': None,
        'row_count': 0
    }

    # Step 1: Verify Markov derivation
    if not verify_markov_derivation():
        results['message'] = "Markov state verification failed."
        return results

    # Step 2: Load data
    try:
        df = load_intermediate_data()
    except FileNotFoundError as e:
        results['message'] = str(e)
        return results

    # Step 3: Validate schema
    if not validate_schema(df, REQUIRED_COLUMNS):
        results['message'] = "Schema validation failed."
        return results

    # Step 4: Check row count
    if len(df) < 100:
        msg = f"Insufficient data: {len(df)} rows found, need >= 100."
        logger.error(msg)
        results['message'] = msg
        return results

    # Step 5: Write standardized CSV
    try:
        # Ensure directory exists
        STANDARDIZED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Select only required columns to ensure standardization
        df_output = df[REQUIRED_COLUMNS].copy()

        # Write to CSV
        df_output.to_csv(STANDARDIZED_OUTPUT_PATH, index=False)
        logger.info(f"Standardized CSV written to {STANDARDIZED_OUTPUT_PATH}")

        # Step 6: Compute checksum
        checksum = compute_sha256(STANDARDIZED_OUTPUT_PATH)
        results['checksum'] = checksum
        results['row_count'] = len(df_output)
        results['status'] = 'success'
        results['message'] = f"Success: Generated {len(df_output)} rows. Checksum: {checksum}"

        logger.info(f"Task T017 completed successfully. Output: {STANDARDIZED_OUTPUT_PATH}")

    except Exception as e:
        logger.error(f"Failed to write standardized CSV: {e}")
        results['message'] = f"Write failed: {e}"

    return results

def main():
    """Entry point for the script."""
    logger.info("Starting T017: Generate Standardized CSV Output")

    # Change to project root to ensure relative paths work if run from anywhere
    os.chdir(PROJECT_ROOT)

    results = run_t017()

    if results['status'] == 'success':
        logger.info(f"Result: {results['message']}")
        sys.exit(0)
    else:
        logger.error(f"Result: {results['message']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
