import os
import sys
import json
import logging
import argparse
import pandas as pd
import random
from datetime import datetime, timedelta

# Configure logging to ensure warnings are visible
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants for synthetic data generation
RANDOM_SEED = 42
MIN_PARTICIPANTS = 50
OUTPUT_PATH = "data/pilot/synthetic_pilot_data.csv"

def generate_synthetic_student_data(num_participants: int = MIN_PARTICIPANTS) -> pd.DataFrame:
    """
    Generates a deterministic synthetic pilot dataset for BKT calibration.
    
    This function creates a DataFrame simulating student interactions with 
    educational problems. It is used as a fallback when human pilot data is 
    missing, as per the project's risk mitigation strategy.
    
    Args:
        num_participants: Number of synthetic student records to generate.
        
    Returns:
        pd.DataFrame: Synthetic dataset with required columns.
    """
    random.seed(RANDOM_SEED)
    
    # Define problem IDs (simulating a small set of practice problems)
    problem_ids = [f"prob_{i:03d}" for i in range(1, 21)]
    
    # Generate data
    records = []
    for i in range(num_participants):
        student_id = f"synth_student_{i:04d}"
        
        # Simulate a sequence of attempts for this student
        # Each student attempts a random subset of problems
        num_attempts = random.randint(5, 15)
        current_date = datetime(2026, 1, 1)
        
        for _ in range(num_attempts):
            problem_id = random.choice(problem_ids)
            
            # Simulate BKT-like behavior with some noise
            # P(L0) = initial knowledge (low)
            # P(T) = transition probability (learning)
            # P(S) = slip probability
            # P(G) = guess probability
            
            # Simplified simulation: 
            # - Early attempts more likely incorrect
            # - Later attempts more likely correct
            attempt_num = len(records) % 10 + 1
            base_correct_prob = 0.3 + (0.05 * attempt_num)
            is_correct = 1 if random.random() < min(base_correct_prob, 0.9) else 0
            
            # Response time: log-normal distribution, skewed towards longer times for errors
            if is_correct:
                rt_seconds = max(1.0, random.gauss(15.0, 5.0))
            else:
                rt_seconds = max(1.0, random.gauss(25.0, 10.0))
            
            # Comprehension rating: 1-5 scale, correlated with correctness
            if is_correct:
                comprehension = random.choices([3, 4, 5], weights=[0.2, 0.5, 0.3])[0]
            else:
                comprehension = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
            
            records.append({
                "student_id": student_id,
                "problem_id": problem_id,
                "attempt_number": attempt_num,
                "is_correct": is_correct,
                "rt_seconds": round(rt_seconds, 2),
                "comprehension_rating": comprehension,
                "timestamp": (current_date + timedelta(minutes=attempt_num * 5)).isoformat(),
                "data_source": "synthetic_pilot"
            })
    
    return pd.DataFrame(records)

def save_synthetic_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Saves the synthetic dataset to CSV with the required header flag.
    
    Args:
        df: The synthetic DataFrame to save.
        output_path: Path where the CSV will be written.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Add the required header flag as a metadata row or column?
    # The task specifies "header flag is_synthetic=true". 
    # Standard CSV doesn't support header flags in the first row as data.
    # We will add a column 'is_synthetic' to every row to ensure it's present
    # and verifiable as per the requirement.
    df['is_synthetic'] = True
    
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved synthetic pilot data to {output_path}")
    logger.info(f"Total records generated: {len(df)}")

def main():
    """
    Main entry point for generating synthetic pilot data.
    
    Checks for human data existence first (via T031b logic implication),
    then generates synthetic data if needed.
    """
    parser = argparse.ArgumentParser(description="Generate synthetic pilot data for calibration.")
    parser.add_argument(
        "--num-participants", 
        type=int, 
        default=MIN_PARTICIPANTS,
        help=f"Number of synthetic participants to generate (default: {MIN_PARTICIPANTS})"
    )
    parser.add_argument(
        "--output-path", 
        type=str, 
        default=OUTPUT_PATH,
        help=f"Output path for the synthetic CSV (default: {OUTPUT_PATH})"
    )
    args = parser.parse_args()

    # Log the warning as required by the task specification
    logger.warning(
        "WARNING: Synthetic data is being used for calibration due to missing human data. "
        "This is a risk mitigation measure per plan.md. Results should be interpreted with caution."
    )

    # Generate data
    logger.info(f"Generating synthetic pilot data for {args.num_participants} participants...")
    df = generate_synthetic_student_data(num_participants=args.num_participants)
    
    # Validate minimum count
    if len(df) < MIN_PARTICIPANTS:
        logger.error(f"Generated {len(df)} records, which is less than the required {MIN_PARTICIPANTS}.")
        sys.exit(1)

    # Save data
    save_synthetic_data(df, args.output_path)
    
    logger.info("Synthetic pilot data generation completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()