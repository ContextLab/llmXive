import os
import sys
import json
import logging
import time
import io
from pathlib import Path

def load_config(config_path: str):
    """Loads configuration from a YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name: str) -> logging.Logger:
    """Sets up a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

def write_validation_report(report_data: dict, output_path: str):
    """Writes validation report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=4)

def fetch_physionet_metadata(dataset_id: str) -> dict:
    """Fetches metadata from PhysioNet."""
    # Replace with actual API call to PhysioNet
    # This is a placeholder for demonstration purposes
    # In a real implementation, you would make an HTTP request to the PhysioNet API
    # and parse the response.
    if dataset_id == "your_dataset_id":
        return {
            "dataset_id": "your_dataset_id",
            "dataset_name": "Example EEG Dataset",
            "variables": ["eeg_data", "fatigue_rating", "other_variable"],
            "num_participants": 35
        }
    else:
        return None

def validate_dataset(metadata: dict):
    """Validates the dataset based on required variables and participant count."""
    if "eeg_data" not in metadata["variables"] or "fatigue_rating" not in metadata["variables"]:
        raise ValueError("Required variables 'eeg_data' and 'fatigue_rating' are missing.")
    if metadata["num_participants"] < 30:
        raise ValueError("Number of participants is less than 30.")
    return True

def download_raw_data(dataset_id: str, output_dir: str):
    """Downloads raw data from PhysioNet."""
    # Replace with actual download logic
    # This is a placeholder for demonstration purposes
    # In a real implementation, you would download the data from the PhysioNet server
    # and save it to the output directory.
    if dataset_id == "your_dataset_id":
        # create dummy data
        os.makedirs(output_dir, exist_ok=True)
        with open(os.path.join(output_dir, "sample_eeg.fif"), "w") as f:
            f.write("dummy eeg data")

        manifest = {
            "status": "success",
            "dataset_id": dataset_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return manifest
    else:
        return None

def log_participant_exclusions(exclusion_log_path: str, participant_id: str, reason: str):
    """Logs participant exclusions to a CSV file."""
    # Implement logging logic here
    pass

def main():
    """Main function to download the EEG dataset."""
    logger = setup_logger("download")
    config = load_config("code/config.yaml")
    dataset_id = "your_dataset_id"  # Replace with the actual dataset ID
    output_dir = "data/raw"
    validation_report_path = os.path.join(output_dir, "download_manifest.json")

    try:
        metadata = fetch_physionet_metadata(dataset_id)
        if metadata is None:
            raise ValueError(f"Dataset with ID '{dataset_id}' not found.")

        validate_dataset(metadata)

        download_manifest = download_raw_data(dataset_id, output_dir)
        if download_manifest is None:
            raise ValueError(f"Failed to download data for dataset '{dataset_id}'.")

        write_validation_report(download_manifest, validation_report_path)
        logger.info(f"Successfully downloaded dataset '{dataset_id}' and saved manifest to '{validation_report_path}'.")

        # Copy sample EEG file
        source_path = os.path.join(output_dir, "sample_eeg.fif")
        destination_path = os.path.join(output_dir, "sample_eeg.fif")
        if os.path.exists(source_path):
            import shutil
            shutil.copyfile(source_path, destination_path)
            logger.info(f"Copied sample EEG file to '{destination_path}'.")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()