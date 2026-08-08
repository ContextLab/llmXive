import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cap_probability(prob: float) -> float:
    """
    Caps the probability value to the range [0.01, 0.99] to prevent numerical instability.
    
    Args:
        prob: The probability value to cap.
        
    Returns:
        The capped probability value.
    """
    return max(0.01, min(0.99, prob))

def calculate_expected_probability(white_rating: float, black_rating: float) -> float:
    """
    Calculates the expected win probability for the white player using the standard Elo logistic formula.
    
    P = 1 / (1 + 10^((R2-R1)/400))
    
    Args:
        white_rating: The rating of the white player.
        black_rating: The rating of the black player.
        
    Returns:
        The expected win probability for the white player, capped to [0.01, 0.99].
    """
    rating_diff = black_rating - white_rating
    expected_prob = 1 / (1 + 10 ** (rating_diff / 400))
    return cap_probability(expected_prob)

def map_outcome_to_result(outcome: str) -> float:
    """
    Maps the game outcome string to a numerical result.
    
    1 = White wins (1.0)
    0 = Black wins (0.0)
    0.5 = Draw (0.5)
    
    Args:
        outcome: The game outcome string (e.g., '1-0', '0-1', '1/2-1/2', '*').
        
    Returns:
        The numerical result (1.0, 0.0, 0.5, or 0.0 for unknown).
    """
    if outcome == '1-0':
        return 1.0
    elif outcome == '0-1':
        return 0.0
    elif outcome == '1/2-1/2':
        return 0.5
    else:
        # Treat unknown/aborted games as 0.0 (or could return NaN, but Spec implies handling)
        logger.warning(f"Unknown outcome '{outcome}' mapped to 0.0")
        return 0.0

def calculate_outcome_deviation(actual_result: float, expected_prob: float) -> float:
    """
    Calculates the outcome deviation as (actual_result - expected_prob).
    
    Args:
        actual_result: The actual game result (1.0, 0.0, or 0.5).
        expected_prob: The expected win probability (already capped).
        
    Returns:
        The outcome deviation.
    """
    return actual_result - expected_prob

def process_game_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes a single game record to calculate derived features.
    
    Args:
        record: A dictionary containing raw game data.
        
    Returns:
        A dictionary containing the processed game record with derived features.
    """
    white_rating = record.get('white_rating', 0)
    black_rating = record.get('black_rating', 0)
    outcome = record.get('outcome', '*')
    
    expected_prob = calculate_expected_probability(white_rating, black_rating)
    actual_result = map_outcome_to_result(outcome)
    outcome_deviation = calculate_outcome_deviation(actual_result, expected_prob)
    
    processed_record = record.copy()
    processed_record['elo_expected_prob'] = expected_prob
    processed_record['outcome_deviation'] = outcome_deviation
    
    return processed_record

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes a DataFrame of game records to calculate derived features.
    
    Args:
        df: A DataFrame containing raw game data.
        
    Returns:
        A DataFrame containing the processed game records with derived features.
    """
    processed_records = []
    for _, row in df.iterrows():
        processed_record = process_game_record(row.to_dict())
        processed_records.append(processed_record)
    
    return pd.DataFrame(processed_records)

def calculate_and_save_inclusion_metrics(total_games: int, parsed_games: int, output_path: str) -> float:
    """
    Calculates the inclusion rate and unconditionally saves it to a JSON file.
    
    Args:
        total_games: The total number of games in the input stream.
        parsed_games: The number of successfully parsed games.
        output_path: The path where the inclusion metrics JSON file will be saved.
        
    Returns:
        The calculated inclusion rate.
        
    Raises:
        ValueError: If the inclusion rate is less than 0.95.
    """
    if total_games == 0:
        logger.warning("Total games is 0, setting inclusion rate to 0.0")
        inclusion_rate = 0.0
    else:
        inclusion_rate = parsed_games / total_games
    
    metrics = {
        "total_games": total_games,
        "parsed_games": parsed_games,
        "inclusion_rate": float(inclusion_rate)
    }
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path_obj, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved inclusion metrics to {output_path}")
    logger.info(f"Inclusion rate: {inclusion_rate:.4f} ({parsed_games}/{total_games})")
    
    return inclusion_rate

def validate_inclusion_rate(inclusion_rate: float, threshold: float = 0.95) -> None:
    """
    Validates the inclusion rate against a threshold.
    
    Args:
        inclusion_rate: The calculated inclusion rate.
        threshold: The minimum acceptable inclusion rate.
        
    Raises:
        RuntimeError: If the inclusion rate is below the threshold.
    """
    if inclusion_rate < threshold:
        error_msg = f"Inclusion rate {inclusion_rate:.4f} is below the threshold {threshold}. Pipeline halted."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def main():
    """
    Main entry point for the process module.
    
    This function is intended to be called by the main pipeline orchestrator.
    It does not perform any direct file I/O or data processing on its own.
    """
    logger.info("Process module loaded. Call process_dataframe or calculate_and_save_inclusion_metrics as needed.")

if __name__ == "__main__":
    main()