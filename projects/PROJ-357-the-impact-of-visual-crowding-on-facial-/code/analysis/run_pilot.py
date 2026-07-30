"""
Execution script for Task T027: Execute Synthetic Pilot.

This script orchestrates the synthetic pilot study by:
1. Loading the stimuli manifest (T014).
2. Invoking the synthetic data generator (T025) to create realistic human judgment data.
3. Orchestrating the pilot runner (T026) logic to save the raw output.

It acts as the entry point to generate the raw synthetic response data required for
downstream analysis (T030, T033).
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import set_all_seeds, ensure_directories
from analysis.pilot_runner import load_manifest, run_pilot
from analysis.synthetic_data_generator import generate_synthetic_responses

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Execute Synthetic Pilot Study (T027)")
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--participants",
        type=int,
        default=10,
        help="Number of simulated participants (default: 10, min: 5)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/interim",
        help="Directory to save raw synthetic data"
    )
    args = parser.parse_args()

    # 1. Setup Environment
    logger.info(f"Initializing pilot execution with seed={args.seed}")
    set_all_seeds(args.seed)
    output_path = Path(args.output_dir)
    ensure_directories([output_path])

    # 2. Load Stimuli Manifest (T014)
    manifest_path = output_path.parent / "interim" / "stimuli_manifest.json"
    # Fallback if running from a different context, though spec implies standard structure
    if not manifest_path.exists():
        manifest_path = Path("data/interim/stimuli_manifest.json")
    
    if not manifest_path.exists():
        logger.error(f"Stimuli manifest not found at {manifest_path}. "
                     "Please ensure T014 (Generate Manifest) is completed first.")
        sys.exit(1)

    logger.info(f"Loading stimuli manifest from {manifest_path}")
    stimuli_data = load_manifest(manifest_path)
    
    if not stimuli_data or len(stimuli_data) == 0:
        logger.error("Manifest is empty. Cannot run pilot.")
        sys.exit(1)

    logger.info(f"Loaded {len(stimuli_data)} stimuli for pilot generation.")

    # 3. Generate Synthetic Data (T025 logic)
    logger.info(f"Generating synthetic responses for {args.participants} participants...")
    
    # We call the generator directly to ensure we get the raw data structure
    # The pilot_runner logic is essentially orchestrating this, but T027 requires
    # the actual generation step to be executed and saved.
    raw_responses = generate_synthetic_responses(
        stimuli_list=stimuli_data,
        num_participants=args.participants,
        seed=args.seed
    )

    # 4. Save Raw Output (T026/T027 requirement)
    output_file = output_path / "synthetic_pilot_raw_responses.csv"
    
    try:
        import pandas as pd
        df = pd.DataFrame(raw_responses)
        df.to_csv(output_file, index=False)
        logger.info(f"Successfully wrote {len(df)} rows to {output_file}")
        
        # Verification log
        unique_participants = df['participant_id'].nunique()
        unique_stimuli = df['stimulus_id'].nunique()
        logger.info(f"Generated data for {unique_participants} participants and {unique_stimuli} stimuli.")
        
    except Exception as e:
        logger.error(f"Failed to save synthetic data: {e}")
        sys.exit(1)

    logger.info("T027 Synthetic Pilot Execution Complete.")

if __name__ == "__main__":
    main()