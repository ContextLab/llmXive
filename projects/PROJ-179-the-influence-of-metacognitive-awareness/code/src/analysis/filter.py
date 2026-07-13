"""
Filter module for T026 (Modality-Specific Analysis).
Splits trial data by stimulus_modality.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DERIVED_DIR = DATA_DIR / "derived"

def setup_directories():
    """Ensure output directories exist."""
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

def load_trial_data():
    """Load the preprocessed trial data."""
    input_path = DERIVED_DIR / "trial_data.csv"
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run T012 first.")
    
    logging.info(f"Loading trial data from: {input_path}")
    return pd.read_csv(input_path)

def filter_by_modality(df: pd.DataFrame, modality: str) -> pd.DataFrame:
    """Filter dataframe by a specific stimulus_modality."""
    if 'stimulus_modality' not in df.columns:
        raise ValueError("Column 'stimulus_modality' not found in data.")
    
    filtered = df[df['stimulus_modality'] == modality].copy()
    logging.info(f"Filtered {len(filtered)} rows for modality: {modality}")
    return filtered

def write_output(df: pd.DataFrame, filename: str):
    """Write dataframe to CSV."""
    output_path = DERIVED_DIR / filename
    df.to_csv(output_path, index=False)
    logging.info(f"Wrote {len(df)} rows to {output_path}")

def run_filter_analysis():
    """Main logic for T026."""
    setup_directories()
    df = load_trial_data()
    
    # Define expected modalities
    modalities = ['visual', 'auditory']
    
    for mod in modalities:
        mod_df = filter_by_modality(df, mod)
        if len(mod_df) > 0:
            write_output(mod_df, f"{mod}_trials.csv")
        else:
            logging.warning(f"No data found for modality: {mod}")

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Starting filter analysis (T026)...")
    try:
        run_filter_analysis()
        logging.info("Filter analysis completed successfully.")
        return 0
    except Exception as e:
        logging.error(f"Filter analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())