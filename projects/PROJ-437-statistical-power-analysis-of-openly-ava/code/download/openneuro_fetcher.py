import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datasets import load_dataset

def get_dataset_info(dataset_id: str) -> Dict[str, Any]:
    """
    Fetches information about a dataset from OpenNeuro.
    """
    try:
        dataset = load_dataset(dataset_id, streaming=True)
        dataset_info = dataset.info
        return {
            "dataset_id": dataset_id,
            "features": dataset_info.features,
            "splits": dataset_info.splits
        }
    except Exception as e:
        logging.error(f"Failed to fetch dataset info for {dataset_id}: {e}")
        raise ValueError(f"Failed to fetch dataset info for {dataset_id}") from e

def download_dataset_file(dataset_id: str, file_name: str, destination_path: str) -> None:
    """
    Downloads a specific file from an OpenNeuro dataset.
    """
    try:
        dataset = load_dataset(dataset_id, streaming=True)
        data_iter = dataset.iter()
        # Assuming files are accessible via iteration
        for data in data_iter:
            if file_name in data:
                # Write file to destination path
                with open(destination_path, 'wb') as f:
                    f.write(data[file_name])
                return
        logging.warning(f"File {file_name} not found in dataset {dataset_id}")
    except Exception as e:
        logging.error(f"Failed to download file {file_name} from {dataset_id}: {e}")
        raise ValueError(f"Failed to download file {file_name} from {dataset_id}") from e

def get_subjects_list(dataset_id: str) -> List[str]:
    """
    Retrieves the list of subjects from a BIDS dataset.
    """
    try:
        dataset = load_dataset(dataset_id, streaming=True)
        # Assuming subject IDs are in the file names or a specific field
        subjects = []
        data_iter = dataset.iter()
        for data in data_iter:
            for key in data.keys():
                if 'subject' in key.lower():
                    subjects.append(data[key])
                    break
        return subjects
    except Exception as e:
        logging.error(f"Failed to get subjects list for {dataset_id}: {e}")
        raise ValueError(f"Failed to get subjects list for {dataset_id}") from e

def download_subject_data(dataset_id: str, subject_id: str, destination_path: str) -> None:
    """
    Downloads data for a specific subject from an OpenNeuro dataset.
    """
    try:
        dataset = load_dataset(dataset_id, streaming=True)
        # Assuming subject data is accessible via filters
        data_iter = dataset.filter(lambda x: x['subject'] == subject_id).iter()
        for data in data_iter:
            # Write data to destination path
            with open(destination_path, 'wb') as f:
                f.write(data)
        return
    except Exception as e:
        logging.error(f"Failed to download data for subject {subject_id} from {dataset_id}: {e}")
        raise ValueError(f"Failed to download data for subject {subject_id} from {dataset_id}") from e

def fetch_paradigm_data(dataset_id: str) -> Dict[str, Any]:
    """
    Fetches paradigm-specific data from an OpenNeuro dataset.
    """
    try:
        dataset = load_dataset(dataset_id, streaming=True)
        # Assuming paradigm data is stored in a specific file or field
        paradigm_data = {}
        data_iter = dataset.iter()
        for data in data_iter:
            if 'paradigm' in data:
                paradigm_data = data['paradigm']
                break
        return paradigm_data
    except Exception as e:
        logging.error(f"Failed to fetch paradigm data for {dataset_id}: {e}")
        raise ValueError(f"Failed to fetch paradigm data for {dataset_id}") from e

def main():
    """
    Main function to download data from OpenNeuro.
    """
    dataset_id = "ds000030"  # Replace with actual dataset ID
    try:
        get_dataset_info(dataset_id)
        subjects = get_subjects_list(dataset_id)
        for subject in subjects:
            destination_path = f"data/raw/{dataset_id}/{subject}"
            os.makedirs(destination_path, exist_ok=True)
            download_subject_data(dataset_id, subject, f"{destination_path}/subject_data.nii.gz")
    except ValueError as e:
        logging.error(f"Error downloading data: {e}")
        raise
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        raise

if __name__ == "__main__":
    main()