"""
Process game data to compute derived metrics.

This module implements the calculation of outcome deviation,
which is defined as (actual_result - expected_probability).

It also provides utilities for capping probabilities and
calculating expected probabilities from Elo ratings.
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cap_probability(p: float, min_val: float = 0.01, max_val: float = 0.99) -> float:
    """
    Cap a probability value to a safe range to avoid numerical instability.
    
    Args:
        p: The probability value to cap.
        min_val: Minimum allowed value (default 0.01).
        max_val: Maximum allowed value (default 0.99).
        
    Returns:
        The capped probability value.
    """
    return max(min_val, min(max_val, p))

def calculate_expected_probability(white_rating: float, black_rating: float) -> float:
    """
    Calculate the expected probability of White winning based on Elo ratings.
    
    Formula: P = 1 / (1 + 10^((R_black - R_white) / 400))
    
    Args:
        white_rating: White player's Elo rating.
        black_rating: Black player's Elo rating.
        
    Returns:
        The expected probability of White winning, capped to [0.01, 0.99].
    """
    if pd.isna(white_rating) or pd.isna(black_rating):
        return np.nan
        
    diff = black_rating - white_rating
    exponent = diff / 400.0
    prob = 1.0 / (1.0 + (10.0 ** exponent))
    
    return cap_probability(prob)

def calculate_outcome_deviation(actual_result: float, expected_probability: float) -> float:
    """
    Calculate the outcome deviation for a game.
    
    Outcome deviation is defined as (actual_result - expected_probability).
    
    Args:
        actual_result: The actual game result (1.0 for White win, 0.5 for draw, 0.0 for Black win).
        expected_probability: The expected probability of White winning.
        
    Returns:
        The outcome deviation value.
    """
    if pd.isna(actual_result) or pd.isna(expected_probability):
        return np.nan
        
    return actual_result - expected_probability

def map_outcome_to_result(outcome: str) -> float:
    """
    Map a string outcome to a numeric result value.
    
    Args:
        outcome: The game outcome string (e.g., '1-0', '0-1', '1/2-1/2', '*').
        
    Returns:
        Numeric result (1.0, 0.5, 0.0) or np.nan if outcome is invalid/unknown.
    """
    outcome_map = {
        '1-0': 1.0,
        '0-1': 0.0,
        '1/2-1/2': 0.5,
        '*': np.nan,  # Unknown outcome
    }
    return outcome_map.get(str(outcome).strip(), np.nan)

def process_game_record(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process a DataFrame of game records to add derived metrics.
    
    This function:
    1. Calculates expected probability from ratings.
    2. Maps outcome strings to numeric results.
    3. Calculates outcome deviation.
    
    Args:
        df: DataFrame with columns including 'white_rating', 'black_rating', and 'outcome'.
        
    Returns:
        DataFrame with new columns: 'elo_expected_prob', 'outcome_result', 'outcome_deviation'.
    """
    logger.info(f"Processing {len(df)} game records...")
    
    # Create a copy to avoid modifying the original
    result_df = df.copy()
    
    # Calculate expected probability
    logger.info("Calculating expected probabilities...")
    result_df['elo_expected_prob'] = result_df.apply(
        lambda row: calculate_expected_probability(row['white_rating'], row['black_rating']),
        axis=1
    )
    
    # Map outcome to numeric result
    logger.info("Mapping outcomes to numeric results...")
    result_df['outcome_result'] = result_df['outcome'].apply(map_outcome_to_result)
    
    # Calculate outcome deviation
    logger.info("Calculating outcome deviations...")
    result_df['outcome_deviation'] = result_df.apply(
        lambda row: calculate_outcome_deviation(row['outcome_result'], row['elo_expected_prob']),
        axis=1
    )
    
    # Log statistics
    valid_deviation_count = result_df['outcome_deviation'].notna().sum()
    logger.info(f"Successfully calculated outcome deviation for {valid_deviation_count} records.")
    
    return result_df

def main():
    """
    Main entry point for processing game data.
    
    This function:
    1. Loads the processed game data from data/processed/games.parquet.
    2. Processes the data to add outcome deviation metrics.
    3. Saves the result to data/results/games_with_deviation.parquet.
    """
    # Define paths
    input_path = Path("data/processed/games.parquet")
    output_path = Path("data/results/games_with_deviation.parquet")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.info("Please run the ingestion pipeline first to generate games.parquet")
        return
    
    logger.info(f"Loading data from {input_path}...")
    df = pd.read_parquet(input_path)
    
    logger.info(f"Loaded {len(df)} records with columns: {list(df.columns)}")
    
    # Process the data
    processed_df = process_game_record(df)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the result
    logger.info(f"Saving processed data to {output_path}...")
    processed_df.to_parquet(output_path, index=False)
    
    logger.info("Processing complete!")
    logger.info(f"Output saved to: {output_path}")
    logger.info(f"Columns in output: {list(processed_df.columns)}")
    
    # Print sample of outcome deviation
    if 'outcome_deviation' in processed_df.columns:
        sample = processed_df[['outcome', 'white_rating', 'black_rating', 'elo_expected_prob', 'outcome_result', 'outcome_deviation']].head(5)
        logger.info("Sample of processed data:")
        print(sample.to_string())

if __name__ == "__main__":
    main()