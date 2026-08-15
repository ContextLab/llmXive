import os
import sys
import json
import logging
import argparse
from pathlib import Path

# Import from ingestion module
from ingestion import validate_data_gap, ensure_output_dirs

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def create_small_sample_dataset():
    """
    Create a small sample dataset (N < 30) to test the data gap validation.
    This is used for testing T017b.
    """
    ensure_output_dirs()
    
    # Create a small CSV with 29 rows (as per T017c requirement)
    # This simulates the output of the ingestion pipeline when data is insufficient
    output_path = Path("data/processed/step_final_cleaned.csv")
    count_path = Path("data/processed/final_count.txt")
    
    # We assume the ingestion pipeline has already produced a CSV.
    # For this test, we just write the count.
    # In a real scenario, the ingestion pipeline would produce the CSV and the count.
    
    # Simulate N=29
    count = 29
    with open(count_path, 'w') as f:
        f.write(str(count))
    
    logger.info(f"Created test dataset with {count} entries in {count_path}")
    return count_path

def main():
    """Main entry point for the gap test script."""
    parser = argparse.ArgumentParser(description="Test Data Gap Validation")
    parser.add_argument("--create-test", action="store_true", help="Create a small test dataset")
    args = parser.parse_args()
    
    if args.create_test:
        create_small_sample_dataset()
    
    # Run the validation
    validate_data_gap()

if __name__ == "__main__":
    main()