import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime

# Local imports based on API surface
from config import load_simulation_params, get_random_seed
from utils import set_seed, ensure_directory
from logger import get_logger

logger = get_logger(__name__)

def fetch_real_data():
    """
    Fetches real data for meta-analysis.
    Since no specific real dataset ID was provided in the prompt's 'VERIFIED REAL DATA SOURCE' block,
    and we cannot fabricate data, this function attempts to load a placeholder or raises an error.
    
    In a real implementation, this would call datasets.load_dataset('<valid-id>') or fetch from a URL.
    For the purpose of T012e implementation, we implement the structure and the validation logic,
    but the data source must be real.
    
    NOTE: This function is a stub for the loader logic. It will FAIL LOUDLY if no real source is configured.
    """
    logger.warning("Attempting to fetch real meta-analysis data...")
    
    # Placeholder for real data loading logic
    # Example: dataset = load_dataset("some_real_dataset_id", split="train")
    # df = dataset.to_pandas()
    
    # Since we cannot fabricate real data, we raise an error if no source is found.
    # This satisfies the "FAIL LOUDLY" constraint.
    raise FileNotFoundError(
        "No real data source configured for meta-analysis. "
        "Please set the 'DATA_SOURCE_URL' or 'DATASET_ID' in config/simulation_parameters.json "
        "to a valid, programmatically accessible source."
    )

def validate_design_adherence(df: pd.DataFrame, expected_design: str) -> bool:
    """
    Validates that the loaded dataset strictly adheres to the chosen design.
    
    For between-subjects: Each participant_id must appear exactly once.
    For within-subjects: Each participant_id must appear exactly 4 times.
    
    Raises ValueError if validation fails.
    """
    logger.info(f"Validating design adherence for {expected_design} design (Meta-Analysis Data)...")
    
    unique_participants = df['participant_id'].nunique()
    total_rows = len(df)
    
    if expected_design == "between":
        counts = df['participant_id'].value_counts()
        if not (counts == 1).all():
            raise ValueError(
                f"Design Violation: Between-subjects design expected. "
                f"Found {unique_participants} unique participants but {total_rows} rows. "
                f"Some participants appear multiple times."
            )
        logger.info(f"Validation passed: Between-subjects design confirmed ({unique_participants} participants, 1 row each).")
        
    elif expected_design == "within":
        counts = df['participant_id'].value_counts()
        expected_combinations = 4
        
        if not (counts == expected_combinations).all():
            raise ValueError(
                f"Design Violation: Within-subjects design expected. "
                f"Found {unique_participants} unique participants but {total_rows} rows. "
                f"Expected {expected_combinations} rows per participant."
            )
        
        # Verify condition combinations
        unique_combos = df.groupby('participant_id')[['status_level', 'observed_behavior']].apply(
            lambda x: set(zip(x['status_level'], x['observed_behavior']))
        )
        
        required_set = {
            ("High", "Risky"), ("High", "Conservative"),
            ("Low", "Risky"), ("Low", "Conservative")
        }
        
        for pid, combos in unique_combos.items():
            if combos != required_set:
                missing = required_set - combos
                raise ValueError(
                    f"Design Violation: Participant {pid} missing conditions: {missing}. "
                    f"Within-subjects design requires all 4 condition combinations per participant."
                )
        
        logger.info(f"Validation passed: Within-subjects design confirmed ({unique_participants} participants, {expected_combinations} rows each).")
    else:
        raise ValueError(f"Unknown design type for validation: {expected_design}")

    return True

def main():
    parser = argparse.ArgumentParser(description="Load and validate meta-analysis data.")
    parser.add_argument("--design", type=str, default="between", choices=["between", "within"],
                        help="Expected design type")
    parser.add_argument("--output", type=str, default="data/raw/meta_data.csv",
                        help="Output file path")
    
    args = parser.parse_args()
    
    try:
        df = fetch_real_data()
        df.to_csv(args.output, index=False)
        logger.info(f"Data saved to {args.output}")
        
        validate_design_adherence(df, args.design)
        logger.info("Design validation successful.")
        
    except FileNotFoundError as e:
        logger.error(f"Data fetch failed (as expected if no source configured): {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Meta-analysis processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
