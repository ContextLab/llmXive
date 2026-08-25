"""
save_processed_data.py
Saves the final processed dataset to data/processed/cleaned_316L.csv
and updates state.yaml with the new file hash.
"""
import os
import sys
import logging
from pathlib import Path

from preprocess import preprocess_data
from utils import setup_logging, compute_file_hash, load_state, update_state

# Configure logging
logger = setup_logging("save_processed_data")

def save_dataset(df, output_path: Path):
    """Saves the dataframe to a CSV file."""
    df.to_csv(output_path, index=False)
    logger.info(f"Dataset saved to {output_path}")

def main():
    """
    Main entry point for saving processed data.
    1. Loads raw data and preprocesses it (calling existing preprocess_data).
    2. Saves the result to data/processed/cleaned_316L.csv.
    3. Computes the SHA-256 hash of the new file.
    4. Updates state.yaml with the new artifact hash.
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    raw_data_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    output_file = processed_dir / "cleaned_316L.csv"
    state_file = project_root / "state.yaml"

    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # 1. Preprocess data
    # Note: This relies on the logic implemented in T014/T016 which loads from data/raw/
    # and performs cleaning, normalization, and feature engineering.
    logger.info("Starting data preprocessing...")
    
    try:
        # We assume preprocess_data handles loading from the raw directory 
        # defined in the project structure or environment.
        # If preprocess_data expects specific arguments, they should be passed here.
        # Based on the API surface, it seems to operate on the project root context.
        df_clean = preprocess_data(project_root)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

    # 2. Save the dataset
    logger.info(f"Saving processed dataset to {output_file}...")
    save_dataset(df_clean, output_file)

    # 3. Compute file hash
    file_hash = compute_file_hash(output_file)
    logger.info(f"File hash computed: {file_hash}")

    # 4. Update state.yaml
    if state_file.exists():
        state = load_state(state_file)
        # Update the artifact entry for the cleaned dataset
        # Assuming the key in state.yaml is 'cleaned_dataset' or similar
        # If the key doesn't exist, we create it.
        artifact_key = "cleaned_316L"
        if "artifacts" not in state:
            state["artifacts"] = {}
        
        state["artifacts"][artifact_key] = {
            "path": str(output_file.relative_to(project_root)),
            "hash": file_hash,
            "version": state.get("artifacts", {}).get(artifact_key, {}).get("version", 1) + 1
        }
        
        update_state(state_file, state)
        logger.info(f"State updated for {artifact_key}")
    else:
        logger.warning(f"State file {state_file} not found. Skipping state update.")

    logger.info("Process completed successfully.")

if __name__ == "__main__":
    main()
