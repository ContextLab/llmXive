"""
Data processing module with online accumulation.
Implements T015, T016a, T016b, T017: Process stream and accumulate metrics.
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Generator
from pathlib import Path
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OnlineAccumulator:
    """
    Online accumulator for streaming statistics.
    Implements T015.
    """
    def __init__(self):
        self.total_games = 0
        self.parsed_games = 0
        self.outcome_deviation_sum = 0.0
        self.feature_sums = {}
        self.feature_counts = {}
    
    def add_record(self, record: Dict[str, Any]) -> None:
        """Add a record to the accumulator."""
        self.total_games += 1
        
        if record:
            self.parsed_games += 1
            
            # Accumulate outcome deviation
            if 'outcome_deviation' in record:
                self.outcome_deviation_sum += record['outcome_deviation']
            
            # Accumulate features
            for key, value in record.items():
                if key not in ['game_id', 'outcome_deviation']:
                    if key not in self.feature_sums:
                        self.feature_sums[key] = 0.0
                        self.feature_counts[key] = 0
                    if isinstance(value, (int, float)):
                        self.feature_sums[key] += value
                        self.feature_counts[key] += 1
    
    def get_inclusion_rate(self) -> float:
        """Get current inclusion rate."""
        return self.parsed_games / max(self.total_games, 1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get accumulated statistics."""
        return {
            'total_games': self.total_games,
            'parsed_games': self.parsed_games,
            'inclusion_rate': self.get_inclusion_rate(),
            'mean_outcome_deviation': self.outcome_deviation_sum / max(self.parsed_games, 1)
        }

def calculate_expected_probability(white_rating: float, black_rating: float) -> float:
    """
    Calculate expected win probability using Elo formula.
    Implements T016a.
    """
    diff = black_rating - white_rating
    prob = 1.0 / (1.0 + 10 ** (diff / 400.0))
    # Cap to [0.01, 0.99]
    return max(0.01, min(0.99, prob))

def calculate_outcome_deviation(actual_result: float, expected_prob: float) -> float:
    """
    Calculate outcome deviation.
    Implements T016b.
    """
    return actual_result - expected_prob

def process_stream(iterator: Generator[Dict[str, Any], None, None], 
                  accumulator: OnlineAccumulator) -> pd.DataFrame:
    """
    Process stream of records and accumulate statistics.
    Implements T015.
    """
    records = []
    
    for record in iterator:
        if record:
            # Calculate expected probability
            expected_prob = calculate_expected_probability(
                record['white_rating'], 
                record['black_rating']
            )
            
            # Calculate outcome deviation
            outcome_deviation = calculate_outcome_deviation(
                record['outcome'],
                expected_prob
            )
            
            record['elo_expected_prob'] = expected_prob
            record['outcome_deviation'] = outcome_deviation
            
            records.append(record)
            accumulator.add_record(record)
            
            # Early exit check
            if accumulator.get_inclusion_rate() < 0.95:
                raise ValueError(f"Inclusion rate dropped below 0.95: {accumulator.get_inclusion_rate():.2%}")
    
    return pd.DataFrame(records)

def save_inclusion_metrics(accumulator: OnlineAccumulator) -> None:
    """
    Save inclusion metrics to file.
    Implements T017.
    """
    output_path = Path("code/data/results/inclusion_counts.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    metrics = {
        'total_games': accumulator.total_games,
        'parsed_games': accumulator.parsed_games
    }
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Saved inclusion counts to {output_path}")

def validate_inclusion_rate(accumulator: OnlineAccumulator, threshold: float = 0.95) -> None:
    """
    Validate inclusion rate and save metrics.
    Implements T017.
    """
    rate = accumulator.get_inclusion_rate()
    
    # Save metrics file
    metrics_path = Path("code/data/results/inclusion_metrics.json")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    
    metrics = {
        'total_games': accumulator.total_games,
        'parsed_games': accumulator.parsed_games,
        'inclusion_rate': rate
    }
    
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Validate threshold
    if rate < threshold:
        raise ValueError(f"Inclusion rate {rate:.2%} below threshold {threshold:.2%}")
    
    logger.info(f"Validation passed: inclusion rate = {rate:.2%}")

def main():
    """Main entry point for testing."""
    pass
