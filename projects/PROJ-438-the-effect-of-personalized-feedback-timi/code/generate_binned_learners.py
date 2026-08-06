import os
import sys
from pathlib import Path
from bin_feedback_groups import load_learner_intervals, assign_feedback_group, bin_feedback_groups, save_binned_data
from logging_config import get_logger, info, error, warning
from config import load_config

def main():
    """
    T026: Generate data/processed/learners_binned.csv with interval and group columns.
    
    This script orchestrates the binning process for User Story 2:
    1. Loads learner intervals from the previous stage (US2 compute_intervals/medians).
    2. Assigns feedback groups based on median intervals.
    3. Saves the final binned dataset to data/processed/learners_binned.csv.
    """
    logger = get_logger(__name__)
    info("Starting T026: Generate binned learners dataset")
    
    # Load configuration to get paths
    config = load_config()
    base_path = Path(config.get('base_path', '.'))
    input_path = base_path / Path(config.get('paths', {}).get('learners_medians', 'data/processed/learners_medians.csv'))
    output_path = base_path / Path(config.get('paths', {}).get('learners_binned', 'data/processed/learners_binned.csv'))
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        error(f"Input file not found: {input_path}")
        error("Prerequisite: Ensure T024 (compute_learner_medians) has been run successfully.")
        sys.exit(1)
    
    try:
        # Load intervals
        logger.info(f"Loading learner intervals from {input_path}")
        df_intervals = load_learner_intervals(input_path)
        
        if df_intervals is None or df_intervals.empty:
            error("No data loaded. Input file may be empty or malformed.")
            sys.exit(1)
        
        # Assign groups
        logger.info("Assigning feedback groups based on median intervals")
        df_binned = assign_feedback_group(df_intervals)
        
        # Bin groups (ensure categorical consistency)
        df_binned = bin_feedback_groups(df_binned)
        
        # Save output
        logger.info(f"Saving binned learners to {output_path}")
        save_binned_data(df_binned, output_path)
        
        logger.info(f"T026 Complete. Output written to {output_path}")
        logger.info(f"Total records binned: {len(df_binned)}")
        
        # Log distribution
        if 'feedback_group' in df_binned.columns:
            dist = df_binned['feedback_group'].value_counts()
            info("Group distribution:")
            for group, count in dist.items():
                logger.info(f"  {group}: {count}")
                
    except Exception as e:
        error(f"Error during T026 execution: {e}")
        raise

if __name__ == "__main__":
    main()
