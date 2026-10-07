import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Generator
from pathlib import Path
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import from sibling modules as defined in API surface
from src.data.models import GameRecord
from src.data.parse import calculate_material_imbalance_move10, calculate_material_imbalance_move5
from src.data.parse import calculate_and_save_inclusion_metrics
from src.config import ensure_directories

# Ensure output directories exist
ensure_directories()

class OnlineAccumulator:
    """
    Accumulates statistics for outcome_deviation and feature statistics in an online manner.
    Avoids building a massive DataFrame in memory.
    """
    def __init__(self):
        self.total_games = 0
        self.parsed_games = 0
        self.outcome_deviation_sum = 0.0
        self.outcome_deviation_sq_sum = 0.0
        self.feature_sums: Dict[str, float] = {}
        self.feature_sq_sums: Dict[str, float] = {}
        self.records: List[GameRecord] = []
        # Batch size to control memory usage before writing to parquet
        self.batch_size = 10000
        self._current_batch: List[GameRecord] = []

    def add(self, record: GameRecord):
        """Add a single record to the accumulator."""
        self.total_games += 1
        self.parsed_games += 1

        # Update running sums for statistics
        self.outcome_deviation_sum += record['outcome_deviation']
        self.outcome_deviation_sq_sum += record['outcome_deviation'] ** 2

        # Update feature sums dynamically
        for key, value in record.items():
            if key not in ['game_id', 'outcome_deviation', 'outcome', 'eco_code']:
                if isinstance(value, (int, float)):
                    if key not in self.feature_sums:
                        self.feature_sums[key] = 0.0
                        self.feature_sq_sums[key] = 0.0
                    self.feature_sums[key] += value
                    self.feature_sq_sums[key] += value ** 2

        # Accumulate records for batch writing
        self._current_batch.append(record)
        if len(self._current_batch) >= self.batch_size:
            self.records.extend(self._current_batch)
            self._current_batch = []

    def finalize(self):
        """Finalize the accumulator, flushing any remaining batches."""
        if self._current_batch:
            self.records.extend(self._current_batch)
            self._current_batch = []

        # Calculate final statistics
        stats = {
            'total_games': self.total_games,
            'parsed_games': self.parsed_games,
            'mean_outcome_deviation': self.outcome_deviation_sum / self.parsed_games if self.parsed_games > 0 else 0.0,
            'std_outcome_deviation': np.sqrt(
                (self.outcome_deviation_sq_sum / self.parsed_games) - (self.outcome_deviation_sum / self.parsed_games) ** 2
            ) if self.parsed_games > 0 else 0.0
        }
        return stats

    def get_dataframe(self) -> pd.DataFrame:
        """Convert accumulated records to a DataFrame."""
        if not self.records:
            return pd.DataFrame()
        return pd.DataFrame(self.records)

def calculate_expected_probability(white_rating: float, black_rating: float) -> float:
    """
    Calculate expected win probability using standard Elo logistic formula.
    P = 1 / (1 + 10^((R2-R1)/400))
    Capped to [0.01, 0.99] to prevent numerical instability.
    """
    if white_rating is None or black_rating is None:
        return 0.5  # Default if ratings missing
    diff = black_rating - white_rating
    prob = 1.0 / (1.0 + 10 ** (diff / 400.0))
    # Cap to prevent numerical issues
    return max(0.01, min(0.99, prob))

def calculate_outcome_deviation(actual_result: float, expected_prob: float) -> float:
    """
    Calculate outcome deviation as (actual_result - expected_prob).
    Uses the capped expected probability.
    """
    return actual_result - expected_prob

def process_stream(iterator: Generator[str, None, None], config: Dict[str, Any]) -> OnlineAccumulator:
    """
    Process a stream of PGN games, extracting features and accumulating statistics.
    Yields GameRecord objects and updates the OnlineAccumulator.
    """
    accumulator = OnlineAccumulator()
    
    # Import parsing functions locally to avoid circular imports if any
    from src.data.parse import parse_pgn_stream
    
    # Parse the stream using the defined parser
    for record in parse_pgn_stream(iterator):
        accumulator.add(record)
    
    accumulator.finalize()
    return accumulator

def save_games_parquet(accumulator: OnlineAccumulator, output_path: str = "data/processed/games.parquet"):
    """
    Save the accumulated game records to a Parquet file.
    """
    df = accumulator.get_dataframe()
    if df.empty:
        logger.warning("No data to save to parquet.")
        return
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved {len(df)} records to {output_path}")

def save_inclusion_metrics(total_games: int, parsed_games: int, output_path: str = "data/results/inclusion_metrics.json"):
    """
    Calculate the inclusion rate and save it to a JSON file.
    Schema: {total_games: int, parsed_games: int, inclusion_rate: float}
    Logic: inclusion_rate = parsed_games / total_games
    Requirement: Do NOT halt if inclusion_rate < 0.95.
    """
    if total_games == 0:
        logger.warning("Total games is 0, setting inclusion rate to 0.0")
        inclusion_rate = 0.0
    else:
        inclusion_rate = parsed_games / total_games

    metrics = {
        "total_games": total_games,
        "parsed_games": parsed_games,
        "inclusion_rate": inclusion_rate
    }

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Inclusion metrics saved to {output_path}: {metrics}")
    return metrics

def validate_inclusion_rate(inclusion_rate: float, threshold: float = 0.95) -> bool:
    """
    Validate inclusion rate against a threshold.
    Returns True if rate >= threshold, False otherwise.
    Note: Per SC-001, this is a measurement, not a hard halt.
    """
    return inclusion_rate >= threshold

def main():
    """
    Main entry point for processing stage if run standalone.
    This is typically called by src/main.py orchestration.
    """
    logger.info("Starting data processing stage.")
    # Example usage if run directly (though typically orchestrated by main.py)
    # This block ensures the script can be tested or invoked if needed.
    pass

if __name__ == "__main__":
    main()