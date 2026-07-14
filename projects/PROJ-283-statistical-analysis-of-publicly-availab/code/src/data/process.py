import numpy as np
import pandas as pd
from typing import Union, List, Optional
import logging
import sys
from pathlib import Path

# Configure logging to stderr to ensure visibility in pipeline logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

# Constants
MIN_PROB = 0.01
MAX_PROB = 0.99
SC001_THRESHOLD = 0.95  # Minimum inclusion rate (95%)

def calculate_expected_probability(white_rating: Union[int, float], black_rating: Union[int, float]) -> float:
    """
    Calculate the expected probability of White winning using the Elo formula.
    P = 1 / (1 + 10^((R2 - R1) / 400))
    
    Args:
        white_rating: White player's Elo rating
        black_rating: Black player's Elo rating
        
    Returns:
        Expected probability of White winning, clamped to [0.01, 0.99] for stability.
    """
    if pd.isna(white_rating) or pd.isna(black_rating):
        return np.nan
        
    diff = black_rating - white_rating
    exponent = diff / 400.0
    prob = 1.0 / (1.0 + np.power(10.0, exponent))
    
    # Clamp for numerical stability
    return float(np.clip(prob, MIN_PROB, MAX_PROB))

def calculate_outcome_deviation(actual_result: Union[int, float], expected_probability: float) -> float:
    """
    Calculate the outcome deviation: actual_result - expected_probability.
    
    Args:
        actual_result: 1.0 for White win, 0.0 for Black win, 0.5 for draw.
        expected_probability: Expected probability of White winning.
        
    Returns:
        The deviation between actual and expected outcome.
    """
    if pd.isna(actual_result) or pd.isna(expected_probability):
        return np.nan
    return float(actual_result) - float(expected_probability)

def process_game_records(df: pd.DataFrame, validate: bool = True) -> pd.DataFrame:
    """
    Process a DataFrame of game records to calculate derived metrics and handle malformed data.
    
    This function:
    1. Calculates `elo_expected_prob` for each game.
    2. Calculates `outcome_deviation` for each game.
    3. Identifies and logs malformed games (missing critical fields or invalid outcomes).
    4. Filters out malformed games to ensure data quality.
    5. Verifies that the final inclusion rate meets SC-001 (>= 95% of valid PGNs processed).
    
    Args:
        df: Input DataFrame containing game records. Expected columns include:
            - 'white_rating': Elo rating of White player
            - 'black_rating': Elo rating of Black player
            - 'outcome': Actual game outcome (1.0, 0.5, or 0.0)
            - Other columns from previous parsing steps.
        validate: If True, performs strict validation and raises errors if SC-001 is violated.
                
    Returns:
        A cleaned DataFrame with new columns 'elo_expected_prob' and 'outcome_deviation'.
        
    Raises:
        RuntimeError: If the inclusion rate falls below SC-001 threshold and validation is enabled.
    """
    logger.info(f"Starting processing of {len(df)} game records.")
    
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df

    # Identify rows with missing critical data
    critical_columns = ['white_rating', 'black_rating', 'outcome']
    missing_mask = df[critical_columns].isna().any(axis=1)
    
    # Identify rows with invalid outcomes (must be 1.0, 0.5, or 0.0)
    valid_outcomes = [1.0, 0.5, 0.0]
    invalid_outcome_mask = ~df['outcome'].isin(valid_outcomes)
    
    # Combine masks to find malformed games
    malformed_mask = missing_mask | invalid_outcome_mask
    malformed_count = malformed_mask.sum()
    valid_count = len(df) - malformed_count
    
    if malformed_count > 0:
        logger.warning(f"Detected {malformed_count} malformed games (missing critical data or invalid outcomes).")
        # Log details of the first few malformed rows for debugging
        sample_malformed = df[malformed_mask].head(3)
        logger.debug(f"Sample malformed records:\n{sample_malformed}")
    
    # Filter out malformed games
    clean_df = df[~malformed_mask].copy()
    
    if clean_df.empty:
        logger.error("All games were malformed. Cannot proceed.")
        raise ValueError("No valid game records found in the input DataFrame.")
    
    # Calculate derived columns
    clean_df['elo_expected_prob'] = clean_df.apply(
        lambda row: calculate_expected_probability(row['white_rating'], row['black_rating']), 
        axis=1
    )
    
    clean_df['outcome_deviation'] = clean_df.apply(
        lambda row: calculate_outcome_deviation(row['outcome'], row['elo_expected_prob']), 
        axis=1
    )
    
    # Verify SC-001 Inclusion Rate
    inclusion_rate = len(clean_df) / len(df)
    logger.info(f"Processed {len(df)} records. Kept {len(clean_df)} ({inclusion_rate:.2%}).")
    
    if validate and inclusion_rate < SC001_THRESHOLD:
        error_msg = f"SC-001 Violation: Inclusion rate {inclusion_rate:.2%} is below threshold {SC001_THRESHOLD:.0%}."
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("Processing complete. Dataset meets SC-001 inclusion criteria.")
    return clean_df
