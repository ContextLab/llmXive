"""
Response Metrics Module for Neuro-Symbolic Learning Networks.

Implements simulation of response times and comprehension ratings for student
interaction data, ensuring distribution constraints per SC-005.
"""
import os
import sys
import json
import logging
import random
import math
import argparse
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for distribution constraints (SC-005)
MIN_RESPONSE_TIME = 0.5  # seconds
MAX_RESPONSE_TIME = 60.0  # seconds
MAX_GAP_THRESHOLD = 5.0  # seconds (no gaps > 5s in distribution)
COMPREHENSION_MIN = 1
COMPREHENSION_MAX = 5

def simulate_response_time(
    difficulty: float,
    condition: str,
    seed: Optional[int] = None
) -> float:
    """
    Simulate a response time in seconds based on problem difficulty and condition.

    Args:
        difficulty: Problem difficulty factor (0.0 to 1.0)
        condition: One of 'neural', 'symbolic', or 'neuro_symbolic'
        seed: Optional random seed for reproducibility

    Returns:
        Simulated response time in seconds
    """
    if seed is not None:
        random.seed(seed)

    # Base time varies by condition
    base_times = {
        'neural': 3.0,
        'symbolic': 5.0,
        'neuro_symbolic': 4.5
    }
    base_time = base_times.get(condition, 4.0)

    # Difficulty multiplier (harder problems take longer)
    difficulty_factor = 1.0 + (difficulty * 2.0)

    # Add noise (log-normal distribution for realistic response times)
    noise = math.exp(random.gauss(0, 0.3))

    response_time = base_time * difficulty_factor * noise

    # Clamp to valid range
    response_time = max(MIN_RESPONSE_TIME, min(MAX_RESPONSE_TIME, response_time))

    return round(response_time, 3)

def simulate_comprehension_rating(
    condition: str,
    difficulty: float,
    seed: Optional[int] = None
) -> int:
    """
    Simulate a comprehension rating (1-5 Likert scale) based on condition and difficulty.

    Args:
        condition: One of 'neural', 'symbolic', or 'neuro_symbolic'
        difficulty: Problem difficulty factor (0.0 to 1.0)
        seed: Optional random seed for reproducibility

    Returns:
        Comprehension rating (1-5)
    """
    if seed is not None:
        random.seed(seed)

    # Base ratings vary by condition (neuro-symbolic expected to be higher)
    base_ratings = {
        'neural': 3.2,
        'symbolic': 2.8,
        'neuro_symbolic': 3.8
    }
    base_rating = base_ratings.get(condition, 3.0)

    # Difficulty reduces comprehension slightly
    difficulty_penalty = difficulty * 0.8

    # Add noise
    noise = random.gauss(0, 0.4)

    rating = base_rating - difficulty_penalty + noise

    # Clamp to valid range and round to nearest integer
    rating = max(COMPREHENSION_MIN, min(COMPREHENSION_MAX, rating))
    rating = round(rating)

    return rating

def validate_response_time_distribution(
    response_times: List[float],
    max_gap_threshold: float = MAX_GAP_THRESHOLD
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate that response time distribution has no gaps > threshold.

    Args:
        response_times: List of response times in seconds
        max_gap_threshold: Maximum allowed gap between consecutive sorted times

    Returns:
        Tuple of (is_valid, stats_dict)
    """
    if not response_times:
        return True, {'error': 'Empty list'}

    sorted_times = sorted(response_times)
    gaps = []
    max_gap = 0.0

    for i in range(1, len(sorted_times)):
        gap = sorted_times[i] - sorted_times[i-1]
        gaps.append(gap)
        if gap > max_gap:
            max_gap = gap

    is_valid = max_gap <= max_gap_threshold

    stats = {
        'count': len(response_times),
        'min': min(response_times),
        'max': max(response_times),
        'mean': sum(response_times) / len(response_times),
        'median': sorted_times[len(sorted_times) // 2],
        'max_gap': max_gap,
        'max_gap_threshold': max_gap_threshold,
        'is_valid': is_valid
    }

    return is_valid, stats

def generate_response_metrics(
    simulation_logs: List[Dict[str, Any]],
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Add response time and comprehension rating to simulation logs.

    Args:
        simulation_logs: List of simulation log entries (must have difficulty, condition)
        seed: Optional base seed for reproducibility

    Returns:
        Updated list of logs with response_time_seconds and comprehension_rating
    """
    if seed is not None:
        random.seed(seed)

    updated_logs = []

    for idx, log in enumerate(simulation_logs):
        # Extract required fields
        difficulty = log.get('difficulty', 0.5)
        condition = log.get('condition', 'neural')
        problem_id = log.get('problem_id', f'prob_{idx}')

        # Simulate metrics with unique seed per entry for reproducibility
        entry_seed = seed + idx if seed is not None else None

        response_time = simulate_response_time(difficulty, condition, entry_seed)
        comprehension = simulate_comprehension_rating(condition, difficulty, entry_seed)

        # Create updated log entry
        updated_log = log.copy()
        updated_log['response_time_seconds'] = response_time
        updated_log['comprehension_rating'] = comprehension

        updated_logs.append(updated_log)

    return updated_logs

def main():
    """
    Main entry point for response metrics simulation.

    Reads simulation logs from data/derived/simulation_logs.csv,
    adds response time and comprehension rating, and writes to
    data/derived/simulation_logs_with_metrics.csv.
    """
    parser = argparse.ArgumentParser(
        description='Simulate response times and comprehension ratings'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/derived/simulation_logs.csv',
        help='Input CSV file path'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/derived/simulation_logs_with_metrics.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate distribution constraints after generation'
    )

    args = parser.parse_args()

    logger.info(f"Loading simulation logs from {args.input}")

    # Check if input file exists
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Load existing logs
    import csv
    simulation_logs = []
    with open(args.input, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['difficulty'] = float(row.get('difficulty', 0.5))
            row['correct'] = row.get('correct', 'True') == 'True'
            simulation_logs.append(row)

    logger.info(f"Loaded {len(simulation_logs)} simulation log entries")

    # Generate metrics
    updated_logs = generate_response_metrics(simulation_logs, args.seed)

    # Validate distribution if requested
    if args.validate:
        response_times = [log['response_time_seconds'] for log in updated_logs]
        is_valid, stats = validate_response_time_distribution(response_times)

        logger.info(f"Distribution validation: {'PASSED' if is_valid else 'FAILED'}")
        logger.info(f"Max gap: {stats['max_gap']:.3f}s (threshold: {stats['max_gap_threshold']}s)")

        if not is_valid:
            logger.warning("Response time distribution violates SC-005 constraint")
            # Log details about gaps
            sorted_times = sorted(response_times)
            large_gaps = []
            for i in range(1, len(sorted_times)):
                gap = sorted_times[i] - sorted_times[i-1]
                if gap > MAX_GAP_THRESHOLD:
                    large_gaps.append((sorted_times[i-1], sorted_times[i], gap))

            logger.warning(f"Found {len(large_gaps)} gaps exceeding threshold")
            for start, end, gap in large_gaps[:5]:  # Show first 5
                logger.warning(f"  Gap: {start:.2f}s -> {end:.2f}s ({gap:.2f}s)")

    # Write output
    logger.info(f"Writing updated logs to {args.output}")

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    fieldnames = list(updated_logs[0].keys())
    with open(args.output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_logs)

    logger.info(f"Successfully wrote {len(updated_logs)} entries to {args.output}")

    # Print summary statistics
    response_times = [log['response_time_seconds'] for log in updated_logs]
    comprehension_ratings = [log['comprehension_rating'] for log in updated_logs]

    logger.info("Summary Statistics:")
    logger.info(f"  Response Time - Mean: {sum(response_times)/len(response_times):.3f}s")
    logger.info(f"  Response Time - Std:  {math.sqrt(sum((x - sum(response_times)/len(response_times))**2 for x in response_times)/len(response_times)):.3f}s")
    logger.info(f"  Comprehension - Mean: {sum(comprehension_ratings)/len(comprehension_ratings):.2f}/5.0")

    return 0

if __name__ == '__main__':
    sys.exit(main())
