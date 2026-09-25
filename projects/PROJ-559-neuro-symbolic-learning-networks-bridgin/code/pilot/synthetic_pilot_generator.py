"""
Synthetic Pilot Data Generator for Calibration Logic Testing.

This module generates a deterministic synthetic pilot dataset (>= 50 records)
to satisfy the schema requirements of T031b and enable CI reproducibility.

It simulates realistic human-like distributions for problem solving:
- Correctness based on problem difficulty
- Response times with log-normal distribution (skewed right)
- Comprehension ratings correlated with correctness and difficulty

The output is saved to data/pilot/real_pilot_data.csv to match the 
expected artifact path for the calibration pipeline.

CRITICAL: This is ONLY for CI/testing. T030b/T030c must replace this
with actual human data for production validation.
"""
import os
import sys
import random
import math
import csv
import hashlib
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fixed seed for reproducibility
RANDOM_SEED = 42
MIN_RECORDS = 50
TARGET_RECORDS = 100  # Generate slightly more than minimum for robustness

# Problem difficulty levels (simulated from real distribution)
DIFFICULTY_LEVELS = ['easy', 'medium', 'hard']
DIFFICULTY_WEIGHTS = [0.4, 0.4, 0.2]  # 40% easy, 40% medium, 20% hard

# Condition types for the pilot study
CONDITIONS = ['neural', 'symbolic', 'neuro_symbolic']
CONDITION_WEIGHTS = [0.33, 0.33, 0.34]

def set_seed(seed: int) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)

def weighted_choice(choices: List[str], weights: List[float]) -> str:
    """Select an item from choices based on weights."""
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    for choice, weight in zip(choices, weights):
        cumulative += weight
        if r <= cumulative:
            return choice
    return choices[-1]

def simulate_correctness(difficulty: str, condition: str) -> int:
    """
    Simulate correctness probability based on difficulty and condition.
    
    This mimics realistic human performance:
    - Easy problems: high success rate (~85-95%)
    - Medium problems: moderate success rate (~60-75%)
    - Hard problems: lower success rate (~30-50%)
    - Neuro-symbolic condition tends to perform slightly better
    """
    base_prob = {
        'easy': 0.90,
        'medium': 0.70,
        'hard': 0.40
    }
    
    # Condition adjustments (neuro-symbolic gives slight boost)
    condition_boost = {
        'neural': 0.0,
        'symbolic': -0.05,  # Symbolic might struggle with ambiguity
        'neuro_symbolic': 0.05
    }
    
    prob = base_prob[difficulty] + condition_boost[condition]
    prob = max(0.1, min(0.99, prob))  # Clamp between 10% and 99%
    
    return 1 if random.random() < prob else 0

def simulate_response_time(difficulty: str, correct: int) -> float:
    """
    Simulate response time in seconds using log-normal distribution.
    
    Realistic human response times:
    - Easy: 2-8 seconds
    - Medium: 5-20 seconds
    - Hard: 10-60 seconds
    - Incorrect answers often take longer (hesitation) or very short (guess)
    """
    # Base parameters for log-normal distribution
    if difficulty == 'easy':
        mu, sigma = 1.0, 0.6  # Median ~2.7s
    elif difficulty == 'medium':
        mu, sigma = 2.0, 0.8  # Median ~7.4s
    else:  # hard
        mu, sigma = 2.8, 1.0  # Median ~16.4s
    
    # Adjust for correctness: incorrect often takes longer (struggle) or shorter (guess)
    if not correct:
        # 50% chance of long struggle, 50% chance of quick guess
        if random.random() < 0.5:
            mu += 0.5  # Longer
        else:
            mu -= 0.3  # Shorter (guess)
    
    rt = math.exp(random.gauss(mu, sigma))
    return round(max(0.5, min(120.0, rt)), 2)  # Clamp 0.5s to 2min

def simulate_comprehension_rating(correct: int, difficulty: str, rt: float) -> int:
    """
    Simulate self-reported comprehension rating (1-5 scale).
    
    Correlated with correctness but allows for "illusion of understanding".
    """
    base = 3  # Neutral
    
    if correct:
        base += 1
        if difficulty == 'easy':
            base += 0.5
        elif difficulty == 'hard':
            base += 0.2  # Proud of solving hard problem
    else:
        base -= 0.5
        if rt > 20:  # Struggled long
            base -= 0.5
    
    # Add noise
    rating = int(round(base + random.gauss(0, 0.5)))
    return max(1, min(5, rating))  # Clamp 1-5

def generate_pilot_record(record_id: int) -> Dict[str, Any]:
    """Generate a single synthetic pilot record."""
    difficulty = weighted_choice(DIFFICULTY_LEVELS, DIFFICULTY_WEIGHTS)
    condition = weighted_choice(CONDITIONS, CONDITION_WEIGHTS)
    
    correct = simulate_correctness(difficulty, condition)
    rt_seconds = simulate_response_time(difficulty, correct)
    comprehension = simulate_comprehension_rating(correct, difficulty, rt_seconds)
    
    return {
        'problem_id': f'PROB_{record_id:04d}',
        'condition': condition,
        'correct': correct,
        'rt_seconds': rt_seconds,
        'comprehension_rating': comprehension
    }

def generate_dataset(num_records: int) -> List[Dict[str, Any]]:
    """Generate the full pilot dataset."""
    logger.info(f"Generating {num_records} synthetic pilot records with seed {RANDOM_SEED}...")
    set_seed(RANDOM_SEED)
    
    records = []
    for i in range(num_records):
        record = generate_pilot_record(i)
        records.append(record)
    
    logger.info(f"Generated {len(records)} records.")
    return records

def calculate_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def save_dataset(records: List[Dict[str, Any]], output_path: str) -> None:
    """Save dataset to CSV and generate checksum."""
    if not records:
        raise ValueError("No records to save.")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write CSV
    fieldnames = ['problem_id', 'condition', 'correct', 'rt_seconds', 'comprehension_rating']
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Saved dataset to {output_path} ({len(records)} records).")
    
    # Generate checksum
    checksum_path = output_path + '.sha256'
    checksum = calculate_checksum(output_path)
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {os.path.basename(output_path)}\n")
    logger.info(f"Saved checksum to {checksum_path}")

def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic pilot dataset for calibration testing."
    )
    parser.add_argument(
        '--num-records',
        type=int,
        default=TARGET_RECORDS,
        help=f"Number of records to generate (default: {TARGET_RECORDS}, min: {MIN_RECORDS})"
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/pilot',
        help="Output directory for the dataset (default: data/pilot)"
    )
    
    args = parser.parse_args()
    
    num_records = max(args.num_records, MIN_RECORDS)
    output_path = os.path.join(args.output_dir, 'real_pilot_data.csv')
    
    logger.info(f"Starting synthetic pilot generation: {num_records} records -> {output_path}")
    
    try:
        records = generate_dataset(num_records)
        save_dataset(records, output_path)
        logger.info("Synthetic pilot generation completed successfully.")
    except Exception as e:
        logger.error(f"Failed to generate synthetic pilot data: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()