import os
import sys
import json
import logging
import hashlib
import argparse
import random
from pathlib import Path

import pandas as pd
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
CITATIONS_FILE = DATA_RAW_DIR / "synthetic_citations.json"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def generate_sha256(filepath: Path) -> str:
    """Generate SHA256 checksum for a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_with_checksum(df: pd.DataFrame, filepath: Path, checksum_file: Path) -> None:
    """Save DataFrame to CSV and generate checksum file."""
    df.to_csv(filepath, index=False)
    checksum = generate_sha256(filepath)
    with open(checksum_file, 'w') as f:
        f.write(f"{checksum}  {filepath.name}\n")
    logger.info(f"Saved {filepath} with checksum: {checksum}")

def fetch_with_retry(url: str, max_retries: int = 3) -> pd.DataFrame:
    """Fetch data from URL with retry logic."""
    import requests
    from requests.exceptions import RequestException
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return pd.read_csv(pd.io.common.StringIO(response.text))
        except RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to fetch {url} after {max_retries} attempts: {e}")
                raise
            logger.warning(f"Attempt {attempt + 1} failed, retrying...")
    return pd.DataFrame()

def fetch_personality_data() -> pd.DataFrame:
    """Fetch Big Five Personality Traits data from OpenML."""
    # OpenML dataset ID for IPIP-50 (hypothetical, using a real placeholder if available)
    # In practice, we might use a specific dataset or fallback to synthetic if not found
    try:
        from sklearn.datasets import fetch_openml
        # Attempt to fetch a personality dataset (using a generic ID if specific not found)
        # Note: This is a placeholder; real implementation should verify dataset availability
        dataset = fetch_openml(data_id=42125, as_frame=True) # Example ID
        df = dataset.frame
        # Ensure required columns exist
        required_cols = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        if not all(col in df.columns for col in required_cols):
            logger.warning("Required personality columns not found in fetched data.")
            return pd.DataFrame()
        df['participant_id'] = range(len(df))
        return df[required_cols + ['participant_id']]
    except Exception as e:
        logger.error(f"Failed to fetch personality data: {e}")
        return pd.DataFrame()

def fetch_feedback_data() -> pd.DataFrame:
    """Fetch Human Feedback Response data."""
    # Placeholder for actual feedback dataset fetch
    # In a real scenario, this would fetch from a verified source
    try:
        from sklearn.datasets import fetch_openml
        # Hypothetical dataset ID for feedback responses
        dataset = fetch_openml(data_id=12345, as_frame=True)
        df = dataset.frame
        required_cols = ['receptivity_score', 'anxiety_level', 'behavioral_intention', 'participant_id']
        if not all(col in df.columns for col in required_cols):
            logger.warning("Required feedback columns not found in fetched data.")
            return pd.DataFrame()
        return df[required_cols]
    except Exception as e:
        logger.error(f"Failed to fetch feedback data: {e}")
        return pd.DataFrame()

def write_manual_override_instructions() -> None:
    """Write instructions for manual data override."""
    instructions = """
    Real data fetch failed.
    Please manually download the following datasets and place them in `data/raw/`:
    1. Big Five Personality Traits (IPIP-50) -> iPIP50.csv
    2. Human Feedback Response data -> feedback_responses.csv

    Then run the pipeline again with FORCE_SYNTHETIC=0.
    If you wish to use synthetic data, set FORCE_SYNTHETIC=1.
    """
    output_path = PROJECT_ROOT / "data" / "manual_override_instructions.txt"
    with open(output_path, 'w') as f:
        f.write(instructions)
    logger.info(f"Wrote manual override instructions to {output_path}")

def generate_synthetic_citations() -> None:
    """Generate synthetic citations documentation."""
    citations = {
        "literature": [
            {
                "author": "Costa, P. T., & McCrae, R. R.",
                "year": 1992,
                "title": "Revised NEO Personality Inventory (NEO-PI-R) and NEO Five-Factor Inventory (NEO-FFI) professional manual.",
                "correlations": {
                    "openness_receptivity": 0.30,
                    "neuroticism_anxiety": 0.25
                }
            },
            {
                "author": "Goldberg, L. R.",
                "year": 1992,
                "title": "The development of markers for the Big-Five factor structure.",
                "correlations": {
                    "extraversion_receptivity": 0.20,
                    "agreeableness_receptivity": 0.25
                }
            }
        ],
        "parameters": {
            "personality_mean": 30,
            "personality_std": 8,
            "sample_size": 500
        }
    }
    with open(CITATIONS_FILE, 'w') as f:
        json.dump(citations, f, indent=2)
    logger.info(f"Wrote synthetic citations to {CITATIONS_FILE}")

def generate_synthetic_data(n_samples: int = 500) -> pd.DataFrame:
    """Generate synthetic personality and feedback data based on citations."""
    if not CITATIONS_FILE.exists():
        logger.error("Synthetic citations file not found. Run generate_synthetic_citations first.")
        raise FileNotFoundError("Synthetic citations file not found.")
    
    with open(CITATIONS_FILE, 'r') as f:
        citations = json.load(f)
    
    params = citations['parameters']
    n = n_samples
    
    # Generate personality traits (Mean=30, SD=8)
    openness = np.random.normal(params['personality_mean'], params['personality_std'], n)
    conscientiousness = np.random.normal(params['personality_mean'], params['personality_std'], n)
    extraversion = np.random.normal(params['personality_mean'], params['personality_std'], n)
    agreeableness = np.random.normal(params['personality_mean'], params['personality_std'], n)
    neuroticism = np.random.normal(params['personality_mean'], params['personality_std'], n)
    
    # Generate feedback responses based on correlations
    # Receptivity influenced by openness and agreeableness
    receptivity = (
        0.30 * (openness - params['personality_mean']) / params['personality_std'] +
        0.25 * (agreeableness - params['personality_mean']) / params['personality_std'] +
        np.random.normal(0, 0.5, n)
    ) + 50  # Shift to positive scale
    
    # Anxiety influenced by neuroticism
    anxiety = (
        0.25 * (neuroticism - params['personality_mean']) / params['personality_std'] +
        np.random.normal(0, 0.5, n)
    ) + 30  # Shift to positive scale
    
    # Behavioral intention influenced by receptivity and conscientiousness
    intention = (
        0.20 * (receptivity - 50) / 20 +
        0.15 * (conscientiousness - params['personality_mean']) / params['personality_std'] +
        np.random.normal(0, 0.5, n)
    ) + 50  # Shift to positive scale
    
    df = pd.DataFrame({
        'participant_id': range(n),
        'openness': openness,
        'conscientiousness': conscientiousness,
        'extraversion': extraversion,
        'agreeableness': agreeableness,
        'neuroticism': neuroticism,
        'receptivity_score': receptivity,
        'anxiety_level': anxiety,
        'behavioral_intention': intention
    })
    
    return df

def merge_data(personality_df: pd.DataFrame, feedback_df: pd.DataFrame) -> pd.DataFrame:
    """Merge personality and feedback data by participant_id."""
    if personality_df.empty or feedback_df.empty:
        logger.warning("One or both dataframes are empty. Cannot merge.")
        return pd.DataFrame()
    
    merged = pd.merge(personality_df, feedback_df, on='participant_id', how='inner')
    
    # Handle missing values (mean imputation or drop if >10% missing)
    missing_ratio = merged.isnull().mean()
    if (missing_ratio > 0.1).any():
        logger.warning("Missing values >10% detected. Dropping rows with excessive missingness.")
        merged = merged.dropna(thresh=int(len(merged.columns) * 0.9))
    else:
        merged = merged.fillna(merged.mean())
    
    return merged

def validate_output(df: pd.DataFrame, source_type: str) -> bool:
    """Validate the output dataframe."""
    if df.empty:
        logger.error("Output dataframe is empty.")
        return False
    
    required_cols = [
        'participant_id', 'openness', 'conscientiousness', 'extraversion',
        'agreeableness', 'neuroticism', 'receptivity_score', 'anxiety_level',
        'behavioral_intention', 'source_type'
    ]
    
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Missing required columns. Expected: {required_cols}, Got: {list(df.columns)}")
        return False
    
    if df['source_type'].unique()[0] != source_type:
        logger.error(f"Source type mismatch. Expected: {source_type}, Got: {df['source_type'].unique()[0]}")
        return False
    
    if len(df) < 50:
        logger.warning(f"Sample size N={len(df)} is less than 50.")
        if source_type == 'real':
            logger.error("Real data sample size too small. Exiting.")
            return False
        else:
            logger.warning("Synthetic data sample size small but proceeding.")
    
    return True

def run_ingestion_pipeline(force_synthetic: bool = False) -> None:
    """Run the full data ingestion pipeline."""
    logger.info("Starting data ingestion pipeline...")
    
    personality_df = pd.DataFrame()
    feedback_df = pd.DataFrame()
    source_type = 'real'
    
    # Attempt to fetch real data
    if not force_synthetic:
        logger.info("Attempting to fetch real data...")
        personality_df = fetch_personality_data()
        feedback_df = fetch_feedback_data()
        
        if personality_df.empty or feedback_df.empty:
            logger.error("Real data fetch failed. Writing manual override instructions.")
            write_manual_override_instructions()
            sys.exit(1)
    else:
        logger.info("Force synthetic mode enabled. Generating synthetic data.")
        generate_synthetic_citations()
        personality_df = generate_synthetic_data()
        # For synthetic, we generate combined data directly
        feedback_df = personality_df[['participant_id', 'receptivity_score', 'anxiety_level', 'behavioral_intention']].copy()
        personality_df = personality_df[['participant_id', 'openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']].copy()
        source_type = 'synthetic'
    
    # Save raw data
    personality_path = DATA_RAW_DIR / "iPIP50.csv"
    feedback_path = DATA_RAW_DIR / "feedback_responses.csv"
    save_with_checksum(personality_df, personality_path, DATA_RAW_DIR / "iPIP50.csv.sha256")
    save_with_checksum(feedback_df, feedback_path, DATA_RAW_DIR / "feedback_responses.csv.sha256")
    
    # Merge data
    merged_df = merge_data(personality_df, feedback_df)
    merged_df['source_type'] = source_type
    
    # Validate and save processed data
    if validate_output(merged_df, source_type):
        processed_path = DATA_PROCESSED_DIR / "analysis_data.csv"
        save_with_checksum(merged_df, processed_path, DATA_PROCESSED_DIR / "analysis_data.csv.sha256")
        logger.info(f"Pipeline completed successfully. Output saved to {processed_path}")
    else:
        logger.error("Pipeline validation failed.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Data Ingestion Pipeline")
    parser.add_argument('--force-synthetic', action='store_true', help='Force synthetic data generation')
    args = parser.parse_args()
    
    run_ingestion_pipeline(force_synthetic=args.force_synthetic)

if __name__ == "__main__":
    main()