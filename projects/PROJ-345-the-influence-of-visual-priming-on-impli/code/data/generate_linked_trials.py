"""
T017: Generate data/processed/linked_trials.csv
"""
import os
import csv
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_path
from data.ingest import load_iat_csv, extract_trial_data, validate_trial_data
from data.linkage import run_linkage_derivation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_linked_trials_csv():
    """
    Generates data/processed/linked_trials.csv with columns:
    trial_id, response_time, stimulus_id, prime_condition, participant_id
    
    This task depends on:
    1. Ingested data (T013) -> raw CSVs
    2. Linkage derivation (T016) -> stimulus_id mapping
    """
    logger.info("Starting T017: Generating linked_trials.csv")
    
    # Ensure output directory exists
    processed_dir = get_path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    output_path = processed_dir / "linked_trials.csv"
    
    # Load raw data (simulating T013 output)
    # In a real run, this would iterate over downloaded files in data/raw
    raw_dir = get_path("data/raw")
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    raw_files = list(raw_dir.glob("*.csv"))
    if not raw_files:
        logger.error("No CSV files found in data/raw. Run T013 first.")
        raise FileNotFoundError("No CSV files found in data/raw. Run T013 first.")
    
    logger.info(f"Found {len(raw_files)} raw CSV files.")
    
    all_trials = []
    
    for raw_file in raw_files:
        logger.info(f"Processing {raw_file.name}...")
        
        # Load and validate CSV (T013 logic)
        df = load_iat_csv(raw_file)
        trials = extract_trial_data(df)
        valid_trials = validate_trial_data(trials)
        
        # Run linkage derivation (T016 logic) to get stimulus_id
        # This returns a list of dicts with trial_id and derived stimulus_id
        linkage_map = run_linkage_derivation(valid_trials, raw_file.parent)
        
        # Merge trial data with linkage data
        for trial in valid_trials:
            trial_id = trial.get('trial_id')
            if not trial_id:
                continue
            
            # Find corresponding linkage info
            linked_info = None
            for link in linkage_map:
                if link['trial_id'] == trial_id:
                    linked_info = link
                    break
            
            if linked_info:
                stimulus_id = linked_info.get('stimulus_id')
                prime_condition = linked_info.get('prime_condition', 'unknown')
            else:
                # Fallback if linkage failed for this trial
                stimulus_id = None
                prime_condition = 'unknown'
            
            # Construct row
            row = {
                'trial_id': trial_id,
                'response_time': trial.get('response_time', trial.get('rt')),
                'stimulus_id': stimulus_id,
                'prime_condition': prime_condition,
                'participant_id': raw_file.stem  # Assuming filename is participant ID
            }
            all_trials.append(row)
    
    if not all_trials:
        logger.error("No valid trials found to write.")
        raise ValueError("No valid trials found.")
    
    # Write to CSV
    fieldnames = ['trial_id', 'response_time', 'stimulus_id', 'prime_condition', 'participant_id']
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_trials)
    
    logger.info(f"Successfully wrote {len(all_trials)} trials to {output_path}")
    
    # Log summary for SC-001 verification
    linked_count = sum(1 for t in all_trials if t['stimulus_id'] is not None)
    total_count = len(all_trials)
    linkage_rate = linked_count / total_count if total_count > 0 else 0
    logger.info(f"Linkage Rate: {linkage_rate:.2%} ({linked_count}/{total_count})")
    
    return output_path

def main():
    try:
        generate_linked_trials_csv()
        logger.info("T017 completed successfully.")
    except Exception as e:
        logger.error(f"T017 failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()