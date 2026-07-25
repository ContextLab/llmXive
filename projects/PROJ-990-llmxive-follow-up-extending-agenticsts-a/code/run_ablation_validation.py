"""
Task T008b: Execute ablation study on the Validation set.

Input: data/processed/validation_set.csv (from T014a)
Output: data/processed/ablation_labels_validation.json

This script loads the validation set trajectories and runs the ablation study
using the reusable engine function from code/ablation.py.
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ablation import run_ablation_study, generate_ablation_config, load_trajectories
from config import load_config_from_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('T008b_AblationValidation')

def main():
    """Execute ablation study on the validation set."""
    logger.info("Starting T008b: Ablation study on Validation set")
    
    # Load configuration
    config = load_config_from_file()
    processed_dir = Path(config['paths']['processed'])
    
    # Define input and output paths
    input_file = processed_dir / "validation_set.csv"
    output_file = processed_dir / "ablation_labels_validation.json"
    
    # Validate input exists
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("T014a (splitter) must be run first to generate validation_set.csv")
        sys.exit(1)
    
    logger.info(f"Loading validation set from: {input_file}")
    df = pd.read_csv(input_file)
    
    if df.empty:
        logger.error("Validation set is empty. Cannot run ablation study.")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} trajectories for ablation study")
    
    # Extract unique trajectory IDs
    trajectory_ids = df['trajectory_id'].unique().tolist()
    logger.info(f"Found {len(trajectory_ids)} unique trajectories")
    
    # Generate ablation configuration
    ablation_config = generate_ablation_config(
        dataset_name="validation",
          trajectory_ids=trajectory_ids,
          config=config
    )
    
    # Load trajectories (this reads from raw data based on IDs)
    # Note: load_trajectories expects to find raw data files
    logger.info("Loading trajectory data for ablation...")
    try:
        trajectories = load_trajectories(trajectory_ids, config)
        if not trajectories:
            logger.error("No trajectory data found for the specified IDs.")
            logger.error("Ensure data/raw/ contains valid trajectory files.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load trajectories: {e}")
        sys.exit(1)
    
    # Run the ablation study
    logger.info("Running ablation study (this may take a while)...")
    ablation_results = run_ablation_study(
        trajectories=trajectories,
        config=ablation_config
    )
    
    # Write output
    logger.info(f"Writing results to: {output_file}")
    with open(output_file, 'w') as f:
        json.dump(ablation_results, f, indent=2)
    
    logger.info(f"Ablation study complete. Generated {len(ablation_results)} labels.")
    logger.info("T008b completed successfully.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())