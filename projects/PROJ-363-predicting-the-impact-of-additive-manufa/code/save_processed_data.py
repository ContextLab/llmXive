import os
import sys
import logging
from pathlib import Path
from preprocess import preprocess_data
from utils import setup_logging, compute_file_hash, load_state, update_state

def save_dataset(df, output_path):
    """
    Saves the processed DataFrame to a CSV file at the specified output path.
    
    Args:
        df (pd.DataFrame): The processed dataset to save.
        output_path (Path): The destination path for the CSV file.
    
    Raises:
        FileNotFoundError: If the directory for output_path does not exist.
        IOError: If the file cannot be written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Dataset saved to {output_path}")

def main():
    """
    Main entry point for the save processed data script.
    1. Loads raw data.
    2. Preprocesses data (normalization, cleaning, feature engineering).
    3. Saves the result to data/processed/cleaned_316L.csv.
    4. Computes the SHA-256 hash of the new file.
    5. Updates state.yaml with the new artifact hash.
    """
    logger = setup_logging()
    
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    raw_data_path = project_root / "data" / "raw" / "316L_LPBF_dataset.csv"
    output_path = project_root / "data" / "processed" / "cleaned_316L.csv"
    state_path = project_root / "state.yaml"

    if not raw_data_path.exists():
        logger.error(f"Raw data file not found at {raw_data_path}. Run download_data.py first.")
        sys.exit(1)

    try:
        # Preprocess the data
        # Note: preprocess_data handles loading, cleaning, normalization, and EV calculation
        df_processed = preprocess_data(raw_data_path)
        
        if df_processed is None or df_processed.empty:
            logger.error("Preprocessing resulted in an empty dataset. Aborting save.")
            sys.exit(1)

        # Save to CSV
        save_dataset(df_processed, output_path)

        # Compute hash of the saved file
        file_hash = compute_file_hash(output_path)
        logger.info(f"Computed SHA-256 hash for {output_path}: {file_hash}")

        # Update state.yaml
        if state_path.exists():
            state = load_state(state_path)
            state = update_state(state, "cleaned_316L.csv", str(output_path), file_hash)
            # Re-save state
            import yaml
            with open(state_path, 'w') as f:
                yaml.dump(state, f, default_flow_style=False, sort_keys=False)
            logger.info(f"Updated state.yaml with new hash for cleaned_316L.csv")
        else:
            logger.warning(f"state.yaml not found at {state_path}. Skipping state update.")

        logger.info("Task T018 completed successfully.")

    except Exception as e:
        logger.error(f"Error during T018 execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
