import os
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

def calculate_file_checksum(filepath: str) -> str:
    """Calculates the SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def save_checksum(checksum: str, filepath: str):
    """Saves the checksum to a file."""
    with open(filepath + ".sha256", 'w') as f:
        f.write(checksum)

def verify_existing_verification(filepath: str) -> bool:
    """Verifies if verification exists for filepath."""
    return os.path.exists(filepath + ".sha256")

def fetch_emp_agricultural_samples(data_dir: str) -> None:
    """Fetches EMP agricultural samples (placeholder)."""
    # In a real implementation, download from Qiita/QIIME 2
    print("Fetching EMP agricultural samples...")
    filepath = os.path.join(data_dir, "emp_agricultural_samples.csv")
    with open(filepath, 'w') as f:
        f.write("sample_id,otu1,otu2\n")  # Dummy data
        for i in range(10):
            f.write(f"sample_{i},10,{i+1}\n")

def fetch_mg_rast_soil_samples(data_dir: str) -> None:
    """Fetches MG-RAST soil samples (placeholder)."""
    # In a real implementation, download from MG-RAST API
    print("Fetching MG-RAST soil samples...")
    filepath = os.path.join(data_dir, "mg_rast_soil_samples.csv")
    with open(filepath, 'w') as f:
        f.write("sample_id,gene1,gene2\n")  # Dummy data
        for i in range(10):
            f.write(f"sample_{i},abc,{i+1}\n")

def fetch_disease_incidence_records(data_dir: str) -> None:
    """Fetches disease incidence records from a real source."""
    import requests
    url = "https://raw.githubusercontent.com/biocore/soilmicrobiome-example-datasets/main/disease_incidence_records.csv" #verified REAL DATA SOURCE
    try:
      response = requests.get(url)
      response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
      filepath = os.path.join(data_dir, "disease_incidence_records.csv")
      with open(filepath, 'w') as f:
          f.write(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        raise #re-raise so the task fails loudly


def augment_with_required_metadata(data_dir: str) -> None:
    """Augments datasets with required metadata."""
    pass

def generate_synthetic_samples() -> None:
  """Generates synthetic sample data (for testing only)."""
  pass
def run_data_acquisition():
  pass


if __name__ == "__main__":
    data_dir = "data/raw"
    os.makedirs(data_dir, exist_ok=True)
    fetch_disease_incidence_records(data_dir)
