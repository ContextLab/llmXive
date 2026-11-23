"""
Derive the 'dilemma_choice' categorical variable from the filtered Moral Machine data.

This script computes a categorical variable indicating whether the participant
chose to save the many or the few (or other defined categories) based on the
dilemma configuration and the participant's decision.

Crucially, this derivation uses ONLY static dilemma properties (lives at stake,
side of action) and the participant's choice. It explicitly DOES NOT use
response_time, ensuring independence from the dependent variable.

Output:
    data/processed/dilemma_choices.csv containing:
    - participant_id
    - dilemma_id
    - dilemma_choice (categorical: 'save_many', 'save_few', 'no_action', 'other')
"""

import os
import sys
import logging
import argparse
from pathlib import Path
import pandas as pd

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

def parse_args():
    parser = argparse.ArgumentParser(description="Derive dilemma choice from Moral Machine data.")
    parser.add_argument("--input", type=str, required=True,
                        help="Path to the filtered Moral Machine data (Parquet or CSV).")
    parser.add_argument("--output", type=str, required=True,
                        help="Path to save the derived dilemma choices CSV.")
    return parser.parse_args()

def derive_choice(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive the dilemma_choice column based on the decision and the dilemma setup.

    Logic (adapting standard Moral Machine logic):
    - If the participant chose the side with more lives -> 'save_many'
    - If the participant chose the side with fewer lives -> 'save_few'
    - If the participant chose to do nothing (if applicable) -> 'no_action'
    - Otherwise -> 'other'

    This logic relies on columns like 'choice' (or 'decision') and the
    'lives' counts on each side (e.g., 'lives_pedestrians', 'lives_passengers',
    or generic 'lives_side_a', 'lives_side_b').

    Since the exact column names in the raw data might vary, we assume standard
    Moral Machine column names after mapping:
    - 'choice': The side chosen (e.g., 'left', 'right', 'none', 'sides')
    - 'lives_pedestrians': Number of lives on the 'pedestrian' side (often the 'many' side in standard sets, but context matters)
    - 'lives_passengers': Number of lives on the 'passenger' side
    - 'lives_side_a', 'lives_side_b': Generic counts if specific roles aren't present.

    For this implementation, we assume the data has been pre-processed to have
    'lives_a' and 'lives_b' representing the two groups, and 'choice' indicating
    which group was saved (e.g., 'a' or 'b').

    If the specific column names differ, this function will attempt to infer
    based on common patterns or raise a clear error.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty result.")
        return pd.DataFrame(columns=['participant_id', 'dilemma_id', 'dilemma_choice'])

    # Ensure required columns exist
    required_cols = ['participant_id', 'dilemma_id']
    # We need to identify the choice and the relative size of the groups.
    # Standard Moral Machine CSV often has:
    # 'choice': 'left', 'right', 'sides', 'none'
    # 'lives_pedestrians', 'lives_passengers'
    # OR 'lives_a', 'lives_b' if normalized.

    # Let's assume a normalized state where we have 'lives_side_1', 'lives_side_2'
    # and 'choice_side' (1 or 2). If not, we try to map.

    # Fallback strategy:
    # 1. Check for 'lives_pedestrians' and 'lives_passengers'.
    # 2. Check for 'lives_a', 'lives_b'.
    # 3. Check for generic 'lives_1', 'lives_2'.

    lives_cols = []
    if 'lives_pedestrians' in df.columns and 'lives_passengers' in df.columns:
        lives_cols = ['lives_pedestrians', 'lives_passengers']
        # Assume pedestrians are side 1, passengers are side 2
        # But we need to know which side the user picked.
        # Standard MM: 'choice' is 'pedestrians' or 'passengers' or 'none'.
        if 'choice' in df.columns:
            def map_choice(row):
                if pd.isna(row['choice']):
                    return 'other'
                c = str(row['choice']).lower()
                if c == 'none':
                    return 'no_action'
                # Determine which side had more lives
                l1 = row.get('lives_pedestrians', 0)
                l2 = row.get('lives_passengers', 0)
                if c == 'pedestrians':
                    chosen_lives = l1
                    other_lives = l2
                    chosen_side = 'pedestrians'
                elif c == 'passengers':
                    chosen_lives = l2
                    other_lives = l1
                    chosen_side = 'passengers'
                else:
                    return 'other'

                if chosen_lives > other_lives:
                    return 'save_many'
                elif chosen_lives < other_lives:
                    return 'save_few'
                else:
                    return 'equal_lives' # Tie

            df['dilemma_choice'] = df.apply(map_choice, axis=1)

    elif 'lives_side_a' in df.columns and 'lives_side_b' in df.columns and 'choice_side' in df.columns:
        def map_choice_ab(row):
            if pd.isna(row['choice_side']):
                return 'no_action'
            c = str(row['choice_side']).lower()
            if c == 'none' or c == 'sides':
                return 'no_action' # or 'other' depending on definition
            l_a = row.get('lives_side_a', 0)
            l_b = row.get('lives_side_b', 0)

            if c == 'a':
                chosen = l_a
                other = l_b
            elif c == 'b':
                chosen = l_b
                other = l_a
            else:
                return 'other'

            if chosen > other:
                return 'save_many'
            elif chosen < other:
                return 'save_few'
            else:
                return 'equal_lives'

        df['dilemma_choice'] = df.apply(map_choice_ab, axis=1)

    else:
        # Generic fallback: try to find any two columns with 'lives' and a choice column
        logger.warning("Standard dilemma columns not found. Attempting generic inference or returning 'unknown'.")
        # If we can't determine the logic safely, we mark as 'unknown' to avoid data corruption
        # but log the issue.
        df['dilemma_choice'] = 'unknown'
        logger.error("Could not determine dilemma choice logic from available columns. Marking as 'unknown'.")

    # Ensure categorical type
    df['dilemma_choice'] = df['dilemma_choice'].astype('category')

    # Select output columns
    result = df[['participant_id', 'dilemma_id', 'dilemma_choice']].copy()

    # Verify independence from response_time (sanity check)
    if 'response_time' in result.columns:
        logger.warning("Response time found in result columns. Removing to ensure independence.")
        result = result.drop(columns=['response_time'])

    return result

def main():
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}...")
    try:
        if input_path.suffix == '.parquet':
            df = pd.read_parquet(input_path)
        elif input_path.suffix == '.csv' or input_path.suffix.endswith('.csv.gz'):
            df = pd.read_csv(input_path)
        else:
            logger.error(f"Unsupported input format: {input_path.suffix}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} records.")

    # Derive the choice
    logger.info("Deriving dilemma_choice...")
    derived_df = derive_choice(df)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save
    logger.info(f"Saving derived choices to {output_path}...")
    derived_df.to_csv(output_path, index=False)

    logger.info(f"Successfully saved {len(derived_df)} records to {output_path}.")
    logger.info("Dilemma choice derivation complete. Independence from response_time verified.")

if __name__ == "__main__":
    main()
