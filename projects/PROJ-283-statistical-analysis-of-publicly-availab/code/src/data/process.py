"""
Data processing module for Chess Elo Analysis.

Calculates:
- Expected probability of outcome based on Elo difference
- Outcome deviation (actual - expected)
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cap_probability(p: float) -> float:
    """Cap probability between 0.01 and 0.99 to avoid log(0) or division by zero."""
    return max(0.01, min(0.99, p))

def calculate_expected_probability(white_rating: float, black_rating: float) -> float:
    """
    Calculate expected probability of White winning using Elo formula.
    E_A = 1 / (1 + 10^((R_B - R_A) / 400))
    """
    if pd.isna(white_rating) or pd.isna(black_rating):
        return np.nan
    
    diff = black_rating - white_rating
    expected = 1.0 / (1.0 + 10 ** (diff / 400.0))
    return cap_probability(expected)

def calculate_outcome_deviation(actual: float, expected: float) -> float:
    """
    Calculate outcome deviation: actual_result - expected_probability.
    """
    if pd.isna(actual) or pd.isna(expected):
        return np.nan
    return actual - expected

def map_outcome_to_result(result_str: str) -> float:
    """Map PGN result string to numeric outcome."""
    mapping = {
        '1-0': 1.0,
        '1/2-1/2': 0.5,
        '0-1': 0.0,
        '*': np.nan
    }
    return mapping.get(result_str, np.nan)

def process_game_record(row: pd.Series) -> Dict[str, Any]:
    """Process a single game record row."""
    white_rating = row.get('white_rating')
    black_rating = row.get('black_rating')
    outcome = row.get('outcome')
    
    expected_prob = calculate_expected_probability(white_rating, black_rating)
    deviation = calculate_outcome_deviation(outcome, expected_prob)
    
    return {
        'game_id': row.get('game_id'),
        'white_rating': white_rating,
        'black_rating': black_rating,
        'eco_code': row.get('eco_code'),
        'outcome': outcome,
        'material_imbalance_move10': row.get('material_imbalance_move10'),
        'elo_expected_prob': expected_prob,
        'outcome_deviation': deviation
    }

def main():
    """
    Main entry point for processing.
    Reads from data/processed/games.parquet (intermediate) and updates with calculated fields.
    Actually, parse.py writes the initial record. This script adds the calculated fields.
    """
    input_path = Path("data/processed/games.parquet")
    output_path = Path("data/processed/games.parquet") # Overwrite or save to new? Task says save to games.parquet.
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return

    logger.info(f"Loading data from {input_path}...")
    df = pd.read_parquet(input_path)
    
    logger.info("Calculating expected probabilities and deviations...")
    processed_records = []
    for _, row in df.iterrows():
        processed_records.append(process_game_record(row))
    
    out_df = pd.DataFrame(processed_records)
    
    # Save to parquet
    out_df.to_parquet(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")

if __name__ == "__main__":
    main()
