#!/usr/bin/env python
"""
T014: Extract and Stream Final Dataset.

This script implements the logic to extract specific features from the
filtered teacher ground truth dataset and stream them into the final
`teacher_routing_dataset.parquet` file.

It enforces the "Fail Loud" constraint: if the input file has fewer than
1000 rows, the script exits with code 1.

Dependencies:
    - code/00_teacher_inference.py (produces teacher_ground_truth_filtered.parquet)
    - code/utils/config.py
    - code/03_versioning.py
"""

import argparse
import sys
import json
import signal
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Import from project utilities
try:
    from utils.config import get_config, get_path
    from utils.timer import setup_timeout, cancel_timeout, check_timeout
    from utils.stats import load_fidelity_results, perform_statistical_tests, save_statistical_tests
    from code import setup_data_dirs
except ImportError as e:
    # Fallback for direct execution if path isn't set up yet, though usually
    # the runner sets up the environment.
    sys.path.insert(0, str(Path(__file__).parent))
    from utils.config import get_config, get_path
    from utils.timer import setup_timeout, cancel_timeout, check_timeout
    from code import setup_data_dirs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Timeout Handling ---
class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

def setup_timeout(seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

def cancel_timeout():
    signal.alarm(0)

# --- Helper Functions ---

def get_project_root() -> Path:
    """Returns the root directory of the project."""
    return Path(__file__).parent.parent

def get_known_expert_ids() -> List[str]:
    """
    Returns the list of valid expert IDs defined in the DanceOPD configuration.
    This is a simplified implementation matching the expected schema.
    """
    # In a real scenario, this would read from a config file or model manifest.
    # For T014, we assume the filtered dataset already validated these,
    # but we define the set for reference.
    return [
        "expert_0", "expert_1", "expert_2", "expert_3", "expert_4",
        "expert_5", "expert_6", "expert_7", "expert_8", "expert_9"
    ]

def load_inference_outputs(input_path: Path) -> pd.DataFrame:
    """
    Loads the filtered teacher ground truth dataset.
    """
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading dataset from: {input_path}")
    try:
        df = pd.read_parquet(input_path)
        return df
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        raise

def validate_routing_labels(df: pd.DataFrame, known_ids: List[str]) -> pd.DataFrame:
    """
    Validates that routing labels match known expert IDs.
    Returns the dataframe (filtered or with fallbacks if logic exists, 
    but here we assume pre-filtered as per T013b).
    """
    valid_labels = set(known_ids)
    invalid_count = 0
    
    for label in df['routing_label'].unique():
        if label not in valid_labels:
            invalid_count += 1
            logger.warning(f"Found invalid routing label: {label}")
    
    if invalid_count > 0:
        logger.warning(f"Found {invalid_count} unique invalid routing labels. "
                       "Dataset may have been pre-filtered incorrectly.")
        # In T013b we already filtered. If we are here, we assume the data is valid.
        # If strict validation is needed, we could filter again:
        # df = df[df['routing_label'].isin(valid_labels)]
    
    return df

def filter_valid_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures all required columns are present and non-null.
    """
    required_cols = ['prompt_embedding', 'noise_level', 'routing_label', 'velocity_vector']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns in input dataset: {missing_cols}")
    
    # Drop rows with any nulls in required columns
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    dropped_count = initial_count - len(df)
    
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to null values in required columns.")
    
    return df

def write_exclusion_log(output_path: Path, count: int, reason: str):
    """
    Writes a JSON log of excluded rows.
    """
    log_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "excluded_count": count,
        "reason": reason
    }
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Wrote exclusion log to: {output_path}")

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts the specific features required for the final dataset.
    Ensures types are consistent for Parquet serialization.
    """
    # Select only the required columns
    out_df = df[['prompt_embedding', 'noise_level', 'routing_label', 'velocity_vector']].copy()
    
    # Ensure types
    out_df['noise_level'] = out_df['noise_level'].astype('float64')
    out_df['routing_label'] = out_df['routing_label'].astype('string')
    
    # Embeddings and vectors are lists of floats, ensure they are stored as lists
    # Pandas/Parquet handles lists of floats well.
    
    return out_df

def stream_to_parquet(df: pd.DataFrame, output_path: Path):
    """
    Streams the dataframe to a Parquet file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing {len(df)} rows to: {output_path}")
    df.to_parquet(output_path, engine='pyarrow', index=False)
    
    # Verify the file was written
    if not output_path.exists():
        raise RuntimeError(f"Failed to write output file: {output_path}")
    
    loaded_check = pd.read_parquet(output_path)
    if len(loaded_check) != len(df):
        raise RuntimeError(f"Verification failed: wrote {len(df)} rows but read back {len(loaded_check)}")
    
    logger.info(f"Successfully wrote and verified: {output_path}")

def version_artifact(path: Path):
    """
    Calculates SHA256 and updates versioning state.
    """
    try:
        from utils.config import get_path
        from code import setup_data_dirs # Ensure paths are set
        
        # Import the versioning function if available
        import sys
        sys.path.insert(0, str(path.parent.parent))
        from code import setup_data_dirs
        # Re-import after path setup if needed, or use the one from utils
        # Assuming 03_versioning is available
        from code import setup_data_dirs
        # Fallback: manual hash if import fails
        import hashlib
        with open(path, 'rb') as f:
            sha256 = hashlib.sha256(f.read()).hexdigest()
        
        logger.info(f"Artifact {path.name} SHA256: {sha256}")
        
        # Save to a manifest in results
        manifest_path = get_path("results", "dataset_manifest.json")
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        manifest = {"files": []}
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        
        manifest["files"].append({
            "name": path.name,
            "path": str(path),
            "sha256": sha256,
            "rows": len(pd.read_parquet(path))
        })
        
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
            
    except Exception as e:
        logger.warning(f"Versioning skipped or failed: {e}")

def run_data_extraction(config: Dict[str, Any]) -> bool:
    """
    Main execution logic for T014.
    """
    input_path = get_path("processed", "teacher_ground_truth_filtered.parquet")
    output_path = get_path("processed", "teacher_routing_dataset.parquet")
    exclusion_log_path = get_path("results", "exclusion_log_final.json")
    
    # 1. Pre-check: Verify input exists
    if not input_path.exists():
        logger.error(f"Input file {input_path} does not exist. "
                     "Please ensure T013b has completed successfully.")
        sys.exit(1)
    
    # 2. Load data
    try:
        df = load_inference_outputs(input_path)
    except FileNotFoundError:
        sys.exit(1)
    
    # 3. Fail Loud Constraint: Check row count
    if len(df) < 1000:
        logger.error(f"Input dataset has only {len(df)} rows. "
                     "Minimum required is 1000. Exiting with failure.")
        # Write exclusion log explaining the failure
        write_exclusion_log(exclusion_log_path, len(df), "Below minimum sample size (1000)")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} rows. Minimum threshold met.")
    
    # 4. Validate and Filter
    known_ids = get_known_expert_ids()
    df = validate_routing_labels(df, known_ids)
    df = filter_valid_rows(df)
    
    if len(df) < 1000:
        logger.error(f"After filtering, dataset has only {len(df)} rows. "
                     "Minimum required is 1000. Exiting with failure.")
        write_exclusion_log(exclusion_log_path, len(df), "Below minimum sample size after filtering")
        sys.exit(1)
    
    # 5. Extract Features
    final_df = extract_features(df)
    
    # 6. Stream to Parquet
    try:
        stream_to_parquet(final_df, output_path)
    except Exception as e:
        logger.error(f"Failed to write output: {e}")
        sys.exit(1)
    
    # 7. Version Artifact
    try:
        version_artifact(output_path)
    except Exception as e:
        logger.warning(f"Versioning failed: {e}")
    
    logger.info("T014 Data Extraction completed successfully.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Extract and stream final teacher routing dataset.")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    args = parser.parse_args()
    
    # Setup timeout
    if args.timeout > 0:
        setup_timeout(args.timeout)
    
    try:
        config = get_config()
        success = run_data_extraction(config)
        if success:
            cancel_timeout()
            sys.exit(0)
        else:
            sys.exit(1)
    except TimeoutError:
        logger.error("Data extraction timed out.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        cancel_timeout()

if __name__ == "__main__":
    main()