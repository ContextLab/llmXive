import os
import sys
import json
import logging
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.env_config import load_config, setup_logging

CONFIG = load_config()
BASE_DIR = Path(CONFIG.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
DATA_DIR = BASE_DIR / "data"
DERIVED_DIR = DATA_DIR / "derived"

INPUT_FILE = DERIVED_DIR / "trial_data.csv"
VISUAL_OUTPUT = DERIVED_DIR / "visual_trials.csv"
AUDITORY_OUTPUT = DERIVED_DIR / "auditory_trials.csv"

def setup_directories():
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)

def load_trial_data():
    if not INPUT_FILE.exists():
        logging.error(f"Trial data not found: {INPUT_FILE}")
        sys.exit(1)
    return pd.read_csv(INPUT_FILE)

def filter_by_modality(df, modality):
    return df[df['stimulus_modality'] == modality]

def write_output(df, path):
    df.to_csv(path, index=False)
    logging.info(f"Wrote {len(df)} rows to {path}")

def run_filter_analysis():
    logging.info("Starting filter analysis (T026)...")
    df = load_trial_data()
    
    visual_df = filter_by_modality(df, 'visual')
    auditory_df = filter_by_modality(df, 'auditory')
    
    write_output(visual_df, VISUAL_OUTPUT)
    write_output(auditory_df, AUDITORY_OUTPUT)
    
    logging.info("Filter analysis (T026) completed.")

def main():
    setup_directories()
    run_filter_analysis()

if __name__ == "__main__":
    logger = setup_logging("info")
    main()
