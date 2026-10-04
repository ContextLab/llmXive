import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

# Import shared utilities from existing API surface
from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Derive Dilemma Complexity Score")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input Moral Machine CSV (raw or filtered).",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save the output dilemma_complexity.csv.",
    )
    parser.add_argument(
        "--log",
        type=str,
        default="results/logs/processing_log.txt",
        help="Path to the log file.",
    )
    return parser.parse_args()

def ensure_directories(output_path: str) -> None:
    path = Path(output_path)
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

def calculate_complexity_score(row: pd.Series) -> float:
    """
    Compute a static complexity score based on lives at stake and dilemma type.
    This score is independent of response time.

    Complexity Logic:
    1. Base Score: Total number of lives at stake (sum of 'lives_at_stake' columns if available,
       or inferred from standard Moral Machine columns).
    2. Ambiguity Penalty: If the dilemma involves a 'sides' conflict (e.g., 'sides: same'),
       add a complexity weight.
    3. Category Weight: Certain categories (e.g., 'pedestrians', 'animals') may have
       different cognitive loads. We assign a base weight of 1.0 per life.

    For this implementation, we assume the input data contains columns indicating
    the number of lives in the 'ego' lane and 'alien' lane (or similar naming).
    If specific column names vary, we attempt to infer them or use a standard
    'n_pedestrians' / 'n_passengers' heuristic if available.

    Standard Moral Machine columns often look like:
    - n_pedestrians (or similar)
    - n_passengers (or similar)
    - dilemma_type (categorical)

    We will sum the total lives involved in the decision.
    """
    score = 0.0

    # Attempt to sum total lives involved.
    # We look for common column patterns in the Moral Machine dataset.
    # If the dataset has been pre-processed, column names might differ.
    # We try to be robust by checking for 'n_' prefixes or specific known names.

    life_columns = []
    for col in row.index:
        if 'n_' in col.lower() or 'lives' in col.lower() or 'pedestrians' in col.lower() or 'passengers' in col.lower():
            try:
                val = float(row[col])
                if not pd.isna(val):
                    life_columns.append(val)
            except (ValueError, TypeError):
                continue

    if life_columns:
        total_lives = sum(life_columns)
    else:
        # Fallback: If no numeric life columns found, assume a default complexity of 2 (1 vs 1)
        # or check if there's a 'dilemma_type' that implies complexity.
        total_lives = 2.0

    score = total_lives

    # Add complexity for specific dilemma types if available
    dilemma_type = row.get('dilemma_type', None)
    if dilemma_type:
        if isinstance(dilemma_type, str):
            # Example: if the dilemma involves 'sides' conflict or 'species' conflict, increase complexity
            if 'sides' in dilemma_type.lower():
                score += 1.0
            if 'species' in dilemma_type.lower():
                score += 0.5
        elif isinstance(dilemma_type, list):
            # Handle list of types if present
            for dt in dilemma_type:
                if 'sides' in str(dt).lower():
                    score += 1.0
                if 'species' in str(dt).lower():
                    score += 0.5

    return score

def derive_complexity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the complexity score calculation to the dataframe.
    """
    # Ensure we are not using response_time for this calculation
    if 'response_time' in df.columns:
        # We explicitly do not use response_time.
        # The calculation is purely based on lives and dilemma type.
        pass

    df['dilemma_complexity'] = df.apply(calculate_complexity_score, axis=1)
    return df

def main() -> None:
    args = parse_args()
    setup_logging(log_file=args.log)
    logger = get_data_quality_logger()

    logger.info(f"Starting Dilemma Complexity derivation for {args.input}")

    try:
        # Load the input data
        # The input is expected to be the filtered Moral Machine data
        # T017-run produces a filtered dataset, but we might need to load the raw
        # or the intermediate filtered CSV.
        # We assume the input path points to a CSV (possibly gzipped).
        input_path = Path(args.input)
        if input_path.suffix == '.gz':
            df = pd.read_csv(input_path, compression='gzip')
        else:
            df = pd.read_csv(input_path)

        logger.info(f"Loaded {len(df)} records from {args.input}")

        # Derive complexity
        df_complexity = derive_complexity(df)

        # Select relevant columns for the output
        # We need 'participant_id' (or equivalent) and the new 'dilemma_complexity'
        output_columns = ['participant_id', 'dilemma_id', 'dilemma_complexity']
        # Check if these columns exist, if not, try to find equivalent keys
        available_cols = set(df_complexity.columns)
        final_cols = [c for c in output_columns if c in available_cols]
        
        # If participant_id is missing, try 'id' or similar
        if 'participant_id' not in final_cols:
            for key in ['id', 'user_id', 'participant']:
                if key in available_cols:
                    final_cols.insert(0, key)
                    break

        if not final_cols:
            # Fallback: just output the complexity and an index
            final_cols = ['dilemma_complexity']
            df_complexity['index'] = df_complexity.index

        output_df = df_complexity[final_cols]

        # Ensure output directory exists
        ensure_directories(args.output)

        # Save to CSV
        output_df.to_csv(args.output, index=False)
        logger.info(f"Successfully saved dilemma complexity to {args.output}")

    except Exception as e:
        logger.error(f"Failed to derive dilemma complexity: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
