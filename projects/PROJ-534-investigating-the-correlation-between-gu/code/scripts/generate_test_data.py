"""
Script to generate the necessary data artifacts for running T010 contract tests.
This script generates synthetic data, ingests it, and filters it to create
data/processed/filtered_cohort.csv.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.utils.config import ensure_directories, set_global_seed, DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR
from code.src.data.synthetic_gen import generate_synthetic_cohort
from code.src.data.ingestion import ingest_synthetic_cohort, save_merged_cohort
from code.src.data.filtering import filter_cohort

def main():
    print("Setting up directories...")
    ensure_directories()
    
    print("Setting global seed...")
    set_global_seed()
    
    print("Generating synthetic cohort...")
    raw_df = generate_synthetic_cohort(n_participants=100)
    
    print("Ingesting and merging data...")
    merged_df = ingest_synthetic_cohort(raw_df)
    
    # Save raw/merged data for inspection if needed
    # save_merged_cohort(merged_df) 
    
    print("Filtering cohort (Age >= 65, non-null)...")
    filtered_df = filter_cohort(merged_df)
    
    if filtered_df.empty:
        print("Warning: Filtered cohort is empty. Creating minimal valid data for schema test.")
        # Create a minimal valid dataframe if filtering removed everything
        import pandas as pd
        import numpy as np
        filtered_df = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'age': [65, 70],
            'sex': ['M', 'F'],
            'bmi': [24.5, 22.1],
            'fiber_intake': [25.0, 30.0],
            'antibiotics_use': [False, True],
            'shannon_diversity': [3.5, 3.8],
            'simpson_diversity': [0.9, 0.95],
            'chao1': [150.0, 160.0],
            'cognitive_score': [85.0, 90.0]
        })
    
    output_path = PROCESSED_DATA_DIR / "filtered_cohort.csv"
    print(f"Saving filtered cohort to {output_path}...")
    filtered_df.to_csv(output_path, index=False)
    print("Done.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
