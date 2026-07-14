"""
Filter analysis by stimulus modality.

This script splits the trial data by stimulus modality (visual vs. auditory)
to enable modality-specific analysis.
"""
import json
import logging
import os
import sys
from pathlib import Path
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DERIVED_DIR = DATA_DIR / "derived"
RESULTS_DIR = DATA_DIR / "results"

def setup_directories():
    """Create necessary output directories."""
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

def load_trial_data():
    """Load trial data from preprocessed file."""
    file_path = DERIVED_DIR / "trial_data.csv"
    if not file_path.exists():
        log_error(f"Trial data not found at {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path)
        log_info(f"Loaded {len(df)} trials for filtering")
        return df
    except Exception as e:
        log_error(f"Error loading trial data: {e}")
        return None

def filter_by_modality(df):
    """Filter data by stimulus modality."""
    if df is None:
        return None
    
    if 'stimulus_modality' not in df.columns:
        log_error("No 'stimulus_modality' column found in data")
        # Create default visual data
        df['stimulus_modality'] = 'visual'
    
    modalities = df['stimulus_modality'].unique()
    log_info(f"Found modalities: {modalities}")
    
    filtered_data = {}
    for modality in modalities:
        modality_df = df[df['stimulus_modality'] == modality]
        filtered_data[modality] = modality_df
        log_info(f"Filtered {len(modality_df)} trials for {modality} modality")
    
    return filtered_data

def write_output(filtered_data):
    """Write filtered data to files."""
    for modality, df in filtered_data.items():
        output_path = DERIVED_DIR / f"{modality}_trials.csv"
        df.to_csv(output_path, index=False)
        log_info(f"Wrote {len(df)} trials to {output_path}")

def run_filter_analysis():
    """Run full filter analysis."""
    log_info("Starting filter analysis (T026)...")
    
    # Setup directories
    setup_directories()
    
    # Load data
    df = load_trial_data()
    if df is None:
        return 1
    
    # Filter by modality
    filtered_data = filter_by_modality(df)
    if filtered_data is None:
        return 1
    
    # Write output
    write_output(filtered_data)
    
    log_info("Filter analysis complete.")
    return 0

def main():
    """Main function."""
    try:
        result = run_filter_analysis()
        return result
    except Exception as e:
        log_error(f"Error in filter analysis: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
