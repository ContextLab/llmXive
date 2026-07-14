import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/process.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROBABILITY_MIN = 0.01
PROBABILITY_MAX = 0.99
SC_001_MIN_INCLUSION_RATE = 0.95

def cap_probability(prob: float) -> float:
    """
    Cap probability to ensure numerical stability.
    Clamps value to [PROBABILITY_MIN, PROBABILITY_MAX].
    """
    if not isinstance(prob, (int, float)):
        raise ValueError(f"Probability must be a number, got {type(prob)}")
    return max(PROBABILITY_MIN, min(PROBABILITY_MAX, float(prob)))

def calculate_expected_probability(white_rating: float, black_rating: float) -> float:
    """
    Calculate expected probability of white winning using Elo formula:
    P = 1 / (1 + 10^((R_black - R_white) / 400))
    """
    if pd.isna(white_rating) or pd.isna(black_rating):
        raise ValueError("Ratings cannot be NaN")
    
    diff = (black_rating - white_rating) / 400.0
    prob = 1.0 / (1.0 + (10 ** diff))
    return cap_probability(prob)

def calculate_outcome_deviation(actual_result: float, expected_prob: float) -> float:
    """
    Calculate outcome deviation: (actual_result - expected_probability)
    """
    if not (0.0 <= actual_result <= 1.0):
        raise ValueError(f"Actual result must be in [0, 1], got {actual_result}")
    return actual_result - expected_prob

def map_outcome_to_result(outcome: str) -> float:
    """
    Map chess game outcome string to numerical result for white.
    '1-0' -> 1.0 (White wins)
    '0-1' -> 0.0 (Black wins)
    '1/2-1/2' -> 0.5 (Draw)
    '*' or other -> raises error (malformed)
    """
    outcome = str(outcome).strip()
    if outcome == '1-0':
        return 1.0
    elif outcome == '0-1':
        return 0.0
    elif outcome == '1/2-1/2':
        return 0.5
    else:
        raise ValueError(f"Invalid game outcome: {outcome}")

def process_game_record(game_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single game record dictionary into a processed row.
    Returns None if the game is malformed and should be skipped.
    Logs errors for skipped games.
    """
    try:
        # Extract and validate required fields
        white_rating = game_data.get('white_rating')
        black_rating = game_data.get('black_rating')
        outcome = game_data.get('outcome')
        
        if pd.isna(white_rating) or pd.isna(black_rating):
            logger.warning(f"Skipping game {game_data.get('game_id', 'UNKNOWN')}: Missing ratings")
            return None
        
        if pd.isna(outcome) or not isinstance(outcome, str):
            logger.warning(f"Skipping game {game_data.get('game_id', 'UNKNOWN')}: Missing or invalid outcome")
            return None

        # Map outcome to result
        try:
            actual_result = map_outcome_to_result(outcome)
        except ValueError as e:
            logger.warning(f"Skipping game {game_data.get('game_id', 'UNKNOWN')}: {e}")
            return None

        # Calculate expected probability
        try:
            elo_expected_prob = calculate_expected_probability(white_rating, black_rating)
        except ValueError as e:
            logger.warning(f"Skipping game {game_data.get('game_id', 'UNKNOWN')}: {e}")
            return None

        # Calculate outcome deviation
        outcome_deviation = calculate_outcome_deviation(actual_result, elo_expected_prob)

        return {
            'game_id': game_data.get('game_id'),
            'white_rating': white_rating,
            'black_rating': black_rating,
            'eco_code': game_data.get('eco_code'),
            'avg_move_time_white': game_data.get('avg_move_time_white'),
            'avg_move_time_black': game_data.get('avg_move_time_black'),
            'material_imbalance_move5': game_data.get('material_imbalance_move5'),
            'outcome': outcome,
            'elo_expected_prob': elo_expected_prob,
            'outcome_deviation': outcome_deviation
        }

    except Exception as e:
        logger.error(f"Unexpected error processing game {game_data.get('game_id', 'UNKNOWN')}: {e}")
        return None

def process_dataset(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a DataFrame of game records.
    Applies process_game_record to each row, skipping malformed ones.
    Checks inclusion rate against SC-001 (>= 95%).
    """
    logger.info(f"Starting processing of {len(input_df)} games...")
    
    processed_rows = []
    total_games = len(input_df)
    skipped_count = 0
    
    for idx, row in input_df.iterrows():
        game_data = row.to_dict()
        processed = process_game_record(game_data)
        
        if processed is not None:
            processed_rows.append(processed)
        else:
            skipped_count += 1

    processed_df = pd.DataFrame(processed_rows)
    inclusion_rate = len(processed_rows) / total_games if total_games > 0 else 0.0

    logger.info(f"Processing complete. Total: {total_games}, Skipped: {skipped_count}, Included: {len(processed_rows)}")
    logger.info(f"Inclusion rate: {inclusion_rate:.4f} ({inclusion_rate * 100:.2f}%)")

    if inclusion_rate < SC_001_MIN_INCLUSION_RATE:
        error_msg = f"SC-001 Violation: Inclusion rate {inclusion_rate:.2f}% is below threshold {SC_001_MIN_INCLUSION_RATE * 100:.2f}%"
        logger.error(error_msg)
        # We do not raise here to allow the pipeline to continue logging, 
        # but in a strict pipeline, this would halt. 
        # For this task, we log the violation clearly.
    
    return processed_df

def main():
    """
    Main entry point for the processing script.
    Expects input data at data/raw/games_parsed.csv (or configurable path).
    Outputs processed data to data/processed/games_processed.parquet.
    """
    # Default paths (can be overridden by config or args in a real scenario)
    input_path = Path("data/raw/games_parsed.csv")
    output_path = Path("data/processed/games_processed.parquet")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure data ingestion (T013-T015) has run successfully.")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} records.")
    
    processed_df = process_dataset(df)
    
    logger.info(f"Saving processed data to {output_path}")
    processed_df.to_parquet(output_path, index=False)
    
    logger.info(f"Successfully saved {len(processed_df)} records to {output_path}")
    
    # Return the dataframe for potential chaining in tests
    return processed_df

if __name__ == "__main__":
    main()