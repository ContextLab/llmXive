import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Generator
from pathlib import Path
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INCLUSION_COUNTS_PATH = Path("data/results/inclusion_counts.json")
INCLUSION_METRICS_PATH = Path("data/results/inclusion_metrics.json")
MIN_INCLUSION_RATE = 0.95


class OnlineAccumulator:
    """
    Accumulates statistics for game records in an online manner.
    Tracks total games seen, successfully parsed games, and aggregates metrics.
    """
    def __init__(self):
        self.total_games = 0
        self.parsed_games = 0
        self.outcome_deviation_sum = 0.0
        self.outcome_deviation_sq_sum = 0.0
        self.feature_sums: Dict[str, float] = {}
        self.feature_sq_sums: Dict[str, float] = {}
        
    def update(self, record: Dict[str, Any]) -> None:
        """
        Update accumulators with a single game record.
        
        Args:
            record: A dictionary containing game record data.
        """
        self.total_games += 1
        
        # Extract and accumulate outcome deviation
        if 'outcome_deviation' in record:
            val = float(record['outcome_deviation'])
            self.outcome_deviation_sum += val
            self.outcome_deviation_sq_sum += val * val
        
        # Accumulate feature statistics
        for key, value in record.items():
            if key not in ['game_id', 'outcome', 'eco_code', 'outcome_deviation', 'elo_expected_prob']:
                if isinstance(value, (int, float)):
                    if key not in self.feature_sums:
                        self.feature_sums[key] = 0.0
                        self.feature_sq_sums[key] = 0.0
                    self.feature_sums[key] += float(value)
                    self.feature_sq_sums[key] += float(value) ** 2
        
        self.parsed_games += 1
        
        # Early exit check for inclusion rate
        if self.total_games > 0:
            current_rate = self.parsed_games / self.total_games
            if current_rate < MIN_INCLUSION_RATE and self.total_games > 100:  # Only check after some data
                logger.warning(f"Inclusion rate dropped below threshold: {current_rate:.2f}")
                # Note: We don't halt here to allow full processing, but T017 will enforce the gate

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current accumulated statistics.
        
        Returns:
            Dictionary containing accumulated statistics.
        """
        stats = {
            'total_games': self.total_games,
            'parsed_games': self.parsed_games,
        }
        
        if self.parsed_games > 0:
            stats['mean_outcome_deviation'] = self.outcome_deviation_sum / self.parsed_games
            variance = (self.outcome_deviation_sq_sum / self.parsed_games) - (stats['mean_outcome_deviation'] ** 2)
            stats['variance_outcome_deviation'] = max(0.0, variance)  # Ensure non-negative
        
        return stats


def process_stream(
    generator: Generator[Dict[str, Any], None, None],
    output_path: Optional[Path] = None
) -> OnlineAccumulator:
    """
    Process a stream of game records, accumulating statistics online.
    
    Args:
        generator: A generator yielding game record dictionaries.
        output_path: Optional path to save the processed data as parquet.
        
    Returns:
        OnlineAccumulator instance with final statistics.
    """
    accumulator = OnlineAccumulator()
    records_batch = []
    batch_size = 1000
    
    for record in generator:
        accumulator.update(record)
        records_batch.append(record)
        
        # Write in chunks to avoid memory issues
        if len(records_batch) >= batch_size:
            if output_path:
                df_batch = pd.DataFrame(records_batch)
                if output_path.exists():
                    df_batch.to_parquet(output_path, mode='a', append=True, engine='pyarrow')
                else:
                    df_batch.to_parquet(output_path, engine='pyarrow')
            records_batch = []
    
    # Process remaining records
    if records_batch and output_path:
        df_batch = pd.DataFrame(records_batch)
        if output_path.exists():
            df_batch.to_parquet(output_path, mode='a', append=True, engine='pyarrow')
        else:
            df_batch.to_parquet(output_path, engine='pyarrow')
    
    return accumulator


def save_inclusion_metrics(
    total_games: int,
    parsed_games: int,
    output_path: Path = INCLUSION_METRICS_PATH
) -> None:
    """
    Calculate the inclusion rate and save it to a JSON file.
    Validates the inclusion rate against the minimum threshold.
    
    Args:
        total_games: Total number of games encountered.
        parsed_games: Number of games successfully parsed.
        output_path: Path to save the inclusion metrics JSON file.
        
    Raises:
        ValueError: If the inclusion rate is below the minimum threshold.
        RuntimeError: If file operations fail.
    """
    if total_games == 0:
        raise ValueError("Total games count cannot be zero.")
    
    inclusion_rate = parsed_games / total_games
    
    metrics = {
        'total_games': total_games,
        'parsed_games': parsed_games,
        'inclusion_rate': inclusion_rate
    }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save metrics to JSON
    try:
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Inclusion metrics saved to {output_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to save inclusion metrics: {e}")
    
    # Read back and validate
    try:
        with open(output_path, 'r') as f:
            saved_metrics = json.load(f)
        
        # Verify the saved rate matches calculation
        if abs(saved_metrics['inclusion_rate'] - inclusion_rate) > 1e-9:
            raise RuntimeError("Saved inclusion rate does not match calculated rate.")
        
        # Validate against threshold
        if saved_metrics['inclusion_rate'] < MIN_INCLUSION_RATE:
            error_msg = (
                f"Data quality gate failed: Inclusion rate {saved_metrics['inclusion_rate']:.4f} "
                f"is below the minimum threshold of {MIN_INCLUSION_RATE}. "
                f"Total games: {saved_metrics['total_games']}, Parsed games: {saved_metrics['parsed_games']}. "
                "Pipeline halted due to low data quality."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Inclusion rate validation passed: {inclusion_rate:.4f} >= {MIN_INCLUSION_RATE}")
        
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to read back saved metrics: Invalid JSON - {e}")
    except FileNotFoundError as e:
        raise RuntimeError(f"Failed to read back saved metrics: File not found - {e}")


def validate_inclusion_rate(
    inclusion_rate: float,
    threshold: float = MIN_INCLUSION_RATE
) -> bool:
    """
    Validate that the inclusion rate meets the minimum threshold.
    
    Args:
        inclusion_rate: The calculated inclusion rate.
        threshold: The minimum acceptable inclusion rate.
        
    Returns:
        True if the rate meets the threshold, False otherwise.
        
    Raises:
        ValueError: If the rate is below the threshold.
    """
    if inclusion_rate < threshold:
        raise ValueError(
            f"Inclusion rate {inclusion_rate:.4f} is below the required threshold of {threshold:.2f}."
        )
    return True


def main():
    """
    Main entry point for the inclusion metrics calculation and validation.
    This function reads the counts from inclusion_counts.json (produced by T015),
    calculates the inclusion rate, saves it to inclusion_metrics.json, and validates it.
    """
    if not INCLUSION_COUNTS_PATH.exists():
        raise FileNotFoundError(
            f"Required input file not found: {INCLUSION_COUNTS_PATH}. "
            "Ensure T015 has completed and generated the counts file."
        )
    
    # Read counts from T015 output
    try:
        with open(INCLUSION_COUNTS_PATH, 'r') as f:
            counts_data = json.load(f)
        
        total_games = counts_data.get('total_games')
        parsed_games = counts_data.get('parsed_games')
        
        if total_games is None or parsed_games is None:
            raise ValueError("Missing 'total_games' or 'parsed_games' in input file.")
        
        if not isinstance(total_games, int) or not isinstance(parsed_games, int):
            raise ValueError("Counts must be integers.")
            
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in input file: {e}")
    
    logger.info(f"Processing counts: total={total_games}, parsed={parsed_games}")
    
    # Calculate and save metrics
    save_inclusion_metrics(total_games, parsed_games, INCLUSION_METRICS_PATH)
    
    logger.info("Inclusion metrics task completed successfully.")


if __name__ == "__main__":
    main()