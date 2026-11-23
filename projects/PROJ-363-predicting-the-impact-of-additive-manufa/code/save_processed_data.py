import os
import sys
import logging
from pathlib import Path
from preprocess import preprocess_data
from utils import setup_logging, compute_file_hash, load_state, update_state

def save_dataset(input_file: str, output_file: str, state_path: str) -> None:
    """
    Loads raw data, preprocesses it, saves the final clean dataset,
    and updates the state.yaml with the new hash.
    
    Args:
        input_file: Path to the raw data file (e.g., data/raw/316L_LPBF_dataset.csv)
        output_file: Path to save the final cleaned dataset (e.g., data/processed/cleaned_316L.csv)
        state_path: Path to the state.yaml file
    """
    logger = logging.getLogger(__name__)
    
    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    logger.info(f"Loading raw data from {input_file}...")
    
    try:
        df = preprocess_data(input_file)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise
    
    # Check for degenerate dataset flag logic inside preprocess_data
    # If the dataset was degenerate, preprocess_data might have written the flag
    # and we should handle the flow appropriately.
    # However, for T018, we assume the pipeline flow (T015b) has already handled the halt
    # if the flag exists. If we are here, the data is valid.
    
    logger.info(f"Saving processed dataset to {output_file}...")
    df.to_csv(output_file, index=False)
    
    # Compute hash
    file_hash = compute_file_hash(output_file)
    logger.info(f"Computed hash for {output_file}: {file_hash}")
    
    # Update state
    state = load_state(state_path)
    state = update_state(state, "cleaned_316L.csv", file_hash)
    
    # Write updated state
    with open(state_path, 'w') as f:
        import yaml
        yaml.dump(state, f)
    
    logger.info(f"State updated successfully.")

def main():
    logger = setup_logging("save_processed_data")
    
    # Project root relative to this script
    base_dir = Path(__file__).parent.parent
    input_file = str(base_dir / "data" / "raw" / "316L_LPBF_dataset.csv")
    output_file = str(base_dir / "data" / "processed" / "cleaned_316L.csv")
    state_path = str(base_dir / "state" / "state.yaml")
    
    try:
        save_dataset(input_file, output_file, state_path)
        logger.info("Dataset saved and state updated.")
    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
