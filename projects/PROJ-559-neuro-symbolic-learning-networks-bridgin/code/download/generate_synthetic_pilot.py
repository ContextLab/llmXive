"""
Generate a deterministic synthetic pilot dataset for calibration.

This script generates a synthetic dataset of student interactions to be used
for BKT calibration if human pilot data is missing (as flagged by T031b).

The dataset is deterministic based on a fixed seed to ensure reproducibility.
It mimics the structure of the ASSISTments dataset format.

Output:
    data/pilot/synthetic_pilot_data.csv with is_synthetic=true flag.
"""

import os
import sys
import json
import logging
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
SEED = 42
MIN_RECORDS = 50
OUTPUT_PATH = "data/pilot/synthetic_pilot_data.csv"
DATA_DIR = "data/pilot"

# Problem types and correct answers (simplified for pilot)
PROBLEMS = [
    {"id": "P001", "type": "algebra", "question": "2x + 3 = 7", "answer": 2},
    {"id": "P002", "type": "algebra", "question": "3x - 5 = 10", "answer": 5},
    {"id": "P003", "type": "geometry", "question": "Area of rectangle 4x5", "answer": 20},
    {"id": "P004", "type": "geometry", "question": "Perimeter of square side 3", "answer": 12},
    {"id": "P005", "type": "arithmetic", "question": "12 / 4 + 2", "answer": 5},
    {"id": "P006", "type": "arithmetic", "question": "15 - 3 * 2", "answer": 9},
    {"id": "P007", "type": "algebra", "question": "x^2 = 16 (x>0)", "answer": 4},
    {"id": "P008", "type": "algebra", "question": "5x = 25", "answer": 5},
]

def generate_synthetic_student_data(num_participants: int = 100) -> pd.DataFrame:
    """
    Generate deterministic synthetic student interaction data.

    Args:
        num_participants: Number of synthetic participants to generate.

    Returns:
        DataFrame with columns matching the expected pilot data schema.
    """
    np.random.seed(SEED)

    records = []
    start_time = datetime(2024, 1, 1, 8, 0, 0)

    for student_idx in range(num_participants):
        student_id = f"S{student_idx + 1:04d}"
        # Simulate a student attempting a subset of problems
        # Each student attempts between 5 and 10 problems
        num_attempts = np.random.randint(5, 11)
        selected_problems = np.random.choice(PROBLEMS, size=num_attempts, replace=False)

        for attempt_idx, problem in enumerate(selected_problems):
            # Simulate correctness based on a hidden "skill" level (0.0 to 1.0)
            # Add some noise to make it realistic
            skill_level = (student_idx % 10) / 10.0 + np.random.uniform(-0.1, 0.1)
            skill_level = max(0.0, min(1.0, skill_level))

            # Probability of correct answer
            prob_correct = skill_level + np.random.uniform(-0.1, 0.1)
            is_correct = 1 if np.random.random() < prob_correct else 0

            # Simulate response time (seconds) - faster if correct, slower if wrong
            base_time = 10.0 + (problem['id'][1:] * 0.5)
            if is_correct:
                rt = max(2.0, base_time * np.random.uniform(0.5, 1.5))
            else:
                rt = max(5.0, base_time * np.random.uniform(1.5, 3.0))

            # Comprehension rating (1-5)
            # Correlated with correctness but with noise
            base_rating = 3 if is_correct else 2
            rating = int(np.clip(base_rating + np.random.randint(-1, 2), 1, 5))

            # Timestamp
            timestamp = start_time + timedelta(seconds=student_idx * 3600 + attempt_idx * 60 + np.random.randint(0, 30))

            record = {
                "student_id": student_id,
                "problem_id": problem['id'],
                "problem_type": problem['type'],
                "question": problem['question'],
                "answer": problem['answer'],
                "student_answer": problem['answer'] if is_correct else np.random.randint(0, 20),
                "is_correct": is_correct,
                "rt_seconds": round(rt, 2),
                "comprehension_rating": rating,
                "timestamp": timestamp.isoformat(),
                "data_source": "synthetic",
                "is_synthetic": True
            }
            records.append(record)

    return pd.DataFrame(records)

def save_synthetic_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the synthetic dataframe to CSV with explicit header flag.

    Args:
        df: DataFrame to save.
        output_path: Path to save the CSV file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Synthetic pilot data saved to {output_path}")
    logger.info(f"Total records: {len(df)}")
    logger.info(f"Unique students: {df['student_id'].nunique()}")
    logger.info(f"Unique problems: {df['problem_id'].nunique()}")

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic pilot data for calibration.")
    parser.add_argument("--num-participants", type=int, default=100,
                        help="Number of synthetic participants to generate (default: 100)")
    parser.add_argument("--output", type=str, default=OUTPUT_PATH,
                        help="Output path for the CSV file (default: data/pilot/synthetic_pilot_data.csv)")
    args = parser.parse_args()

    logger.warning("--------------------------------------------------")
    logger.warning("WARNING: Synthetic data is being generated for calibration.")
    logger.warning("This is a fallback due to missing human pilot data.")
    logger.warning("Results should be treated as preliminary and validated")
    logger.warning("against real human data when available.")
    logger.warning("--------------------------------------------------")

    # Validate minimum records
    if args.num_participants < MIN_RECORDS:
        logger.error(f"Number of participants ({args.num_participants}) must be at least {MIN_RECORDS}.")
        sys.exit(1)

    # Generate data
    df = generate_synthetic_student_data(args.num_participants)

    # Save data
    save_synthetic_data(df, args.output)

    # Verify output
    if os.path.exists(args.output):
        logger.info("SUCCESS: Synthetic pilot data generated and saved.")
        sys.exit(0)
    else:
        logger.error("FAILED: Output file was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()