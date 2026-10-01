"""
T028b: Derive Dilemma Choice from filtered Moral Machine data.

This script reads the filtered Moral Machine dataset (output of T017-run),
computes a categorical variable `dilemma_choice` indicating whether the
participant chose to "save_many" or "save_few" (or equivalent based on
dilemma structure), and saves the result to `data/processed/dilemma_choices.csv`.

Crucially, this derivation uses ONLY structural dilemma features (lives at stake,
dilemma type) and does NOT use `response_time` or any time-based metric.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd

# Import logging setup from existing infrastructure
from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

def parse_args():
    parser = argparse.ArgumentParser(description="Derive dilemma_choice variable from Moral Machine data.")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/filtered_moral_machine.parquet",
        help="Path to the filtered Moral Machine dataset (output of T017-run)."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/dilemma_choices.csv",
        help="Path to save the output CSV with the derived dilemma_choice column."
    )
    return parser.parse_args()

def derive_choice(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive `dilemma_choice` based on the dilemma structure.
    
    Logic (adapted from standard Moral Machine dataset structure):
    - The dataset typically has columns like:
      `n_alives_ego`, `n_alives_other` (or similar naming depending on version)
      representing the number of lives saved on each side.
    - If the participant chose the side with MORE lives saved, label "save_many".
    - If the participant chose the side with FEWER lives saved, label "save_few".
    - If equal, label "neutral" (though rare in standard dilemmas).
    
    We assume the input DataFrame contains the raw choice indicator and the
    counts of lives on each side. If column names differ, we attempt to infer.
    
    Note: This function does NOT use `response_time`.
    """
    df = df.copy()
    
    # Identify choice columns. Standard MM dataset often has 'choice' or similar.
    # We need to map the choice to the side (ego vs other) and compare lives.
    
    # Heuristic: Look for columns indicating lives on each side.
    # Common names: 'n_alives_ego', 'n_alives_other', 'n_alives_side1', 'n_alives_side2'
    # Or sometimes 'lives_ego', 'lives_other'
    
    possible_lives_cols = [
        'n_alives_ego', 'n_alives_other',
        'n_alives_side1', 'n_alives_side2',
        'lives_ego', 'lives_other',
        'side1_lives', 'side2_lives'
    ]
    
    lives_ego_col = None
    lives_other_col = None
    
    # Try to find standard naming
    for col in possible_lives_cols:
        if col in df.columns:
            if 'ego' in col or 'side1' in col:
                lives_ego_col = col
            elif 'other' in col or 'side2' in col:
                lives_other_col = col
    
    # If specific names not found, try to infer from available numeric columns
    # that look like counts (integers, small positive numbers)
    if not lives_ego_col or not lives_other_col:
        # Fallback: look for any two columns that seem to be life counts
        # This is less robust but handles variations
        numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        # Filter for columns that might be life counts (simple heuristic: > 0 and <= 10 usually)
        # This is a fallback; ideally column names are standard.
        # For this implementation, we assume standard column names exist or fail loudly.
        if not lives_ego_col or not lives_other_col:
            logging.error("Could not identify life count columns (e.g., n_alives_ego, n_alives_other). "
                          "Please check the input dataset schema.")
            raise ValueError("Missing required life count columns for dilemma choice derivation.")

    # Identify the choice column
    # Common names: 'choice', 'decision', 'side_chosen'
    choice_col = None
    possible_choice_cols = ['choice', 'decision', 'side_chosen', 'n_alives_chosen']
    for col in possible_choice_cols:
        if col in df.columns:
            choice_col = col
            break
    
    if not choice_col:
        # Fallback: maybe the choice is encoded as a binary indicator relative to ego?
        # e.g., 'ego_chosen' (1 if ego side chosen, 0 if other)
        if 'ego_chosen' in df.columns:
            choice_col = 'ego_chosen'
            # We will handle this logic below
        else:
            logging.error("Could not identify the choice column.")
            raise ValueError("Missing required choice column.")

    # Logic to derive the label
    def classify_row(row):
        lives_ego = row[lives_ego_col]
        lives_other = row[lives_other_col]
        
        # Determine which side was chosen
        # If choice_col is 'choice', it might be 'ego' or 'other' or 0/1
        # If choice_col is 'ego_chosen', it's 1 for ego, 0 for other
        
        chosen_side = None
        if choice_col == 'ego_chosen':
            chosen_side = 'ego' if row[choice_col] == 1 else 'other'
        else:
            # Assume standard string or categorical choice
            val = row[choice_col]
            if isinstance(val, str):
                val_lower = val.lower()
                if 'ego' in val_lower or 'side1' in val_lower:
                    chosen_side = 'ego'
                elif 'other' in val_lower or 'side2' in val_lower:
                    chosen_side = 'other'
                else:
                    # Maybe it's the number of lives saved?
                    # If the column value is the number of lives saved, we need to compare
                    # But usually 'choice' is the side.
                    # Let's assume if it's not clearly 'ego'/'other', we check if it matches lives_ego or lives_other
                    if val == lives_ego:
                        chosen_side = 'ego'
                    elif val == lives_other:
                        chosen_side = 'other'
                    else:
                        return 'unknown'
            else:
                # Numeric choice? 1=ego, 0=other?
                if val == 1:
                    chosen_side = 'ego'
                elif val == 0:
                    chosen_side = 'other'
                else:
                    return 'unknown'
        
        # Now compare lives
        if chosen_side == 'ego':
            saved_lives = lives_ego
            other_lives = lives_other
        else:
            saved_lives = lives_other
            other_lives = lives_ego
        
        if saved_lives > other_lives:
            return 'save_many'
        elif saved_lives < other_lives:
            return 'save_few'
        else:
            return 'equal'

    # Apply the function
    # Handle potential NA values in choice columns
    df['dilemma_choice'] = df.apply(classify_row, axis=1)
    
    return df

def main():
    args = parse_args()
    
    # Setup logging
    log_path = Path("results/logs")
    log_path.mkdir(parents=True, exist_ok=True)
    logger = get_data_quality_logger("derive_dilemma_choice")
    
    logger.info(f"Starting dilemma choice derivation from {args.input}")
    
    # Check input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    # Load data
    try:
        if input_path.suffix == '.parquet':
            df = pd.read_parquet(input_path)
        elif input_path.suffix == '.csv' or input_path.suffix == '.csv.gz':
            df = pd.read_csv(input_path)
        else:
            logger.error(f"Unsupported file format: {input_path.suffix}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load input file: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} records.")
    
    # Verify required columns exist
    required_base = ['n_alives_ego', 'n_alives_other', 'choice'] # Fallback check
    # We will let the derive function handle specific column detection and erroring
    
    # Derive the choice
    try:
        df_derived = derive_choice(df)
    except ValueError as e:
        logger.error(f"Derivation failed: {e}")
        sys.exit(1)
    
    # Validate derivation
    choice_counts = df_derived['dilemma_choice'].value_counts()
    logger.info(f"Dilemma choice distribution: {choice_counts.to_dict()}")
    
    if 'unknown' in choice_counts and choice_counts['unknown'] > 0:
        logger.warning(f"{choice_counts['unknown']} records resulted in 'unknown' choice.")
    
    # Save output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save only the necessary columns to keep the file clean, or save the full df?
    # Task says: "create a categorical variable ... Save to ..."
    # Usually implies saving the derived column, perhaps with ID to link back.
    # Let's save the ID (participant_id) and the new column.
    id_col = 'participant_id' if 'participant_id' in df_derived.columns else df_derived.columns[0]
    
    output_df = df_derived[[id_col, 'dilemma_choice']]
    output_df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully saved dilemma choices to {output_path}")
    print(f"Task T028b completed. Output: {output_path}")

if __name__ == "__main__":
    main()
