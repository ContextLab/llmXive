import os
import sys
import csv
import hashlib
import logging
import time

def is_valid_url(url):
    """Simple check for valid URL format."""
    from urllib.parse import urlparse
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def download_file(url, filepath):
    """Downloads a file from a URL."""
    import requests
    response = requests.get(url, stream=True)
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def compute_sha256(filepath):
    """Computes the SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()

def get_dataset_info_from_openml(dataset_id):
  """Fetches dataset metadata from OpenML."""
  import openml
  try:
      dataset = openml.datasets.get_dataset(dataset_id)
      return {
          "sample_size": dataset.nrows,
          "continuous_vars": sum(1 for feature in dataset.features if dataset.features[feature].type == "continuous"),
          "group_labels": 0  # Placeholder - requires data download
      }
  except Exception as e:
    logging.error(f"Error fetching OpenML dataset {dataset_id}: {e}")
    return None

def fetch_openml_datasets(dataset_ids):
  """Fetches multiple datasets from OpenML."""
  results = []
  for dataset_id in dataset_ids:
      info = get_dataset_info_from_openml(dataset_id)
      if info:
          results.append(info)
  return results

def initialize_metadata_files():
    """Initializes datasets.csv and checksums.csv if they don't exist."""
    datasets_file = "data/datasets.csv"
    checksums_file = "data/checksums.csv"

    if not os.path.exists(datasets_file):
        with open(datasets_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["dataset_id", "source_url", "sample_size", "continuous_vars", "group_labels", "excluded_reason"])

    if not os.path.exists(checksums_file):
        with open(checksums_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["dataset_id", "sha256_hash"])

def append_to_datasets_csv(data, datasets_file="data/datasets.csv"):
    """Appends dataset information to datasets.csv."""
    with open(datasets_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data)

def append_to_checksums_csv(dataset_id, sha256_hash, checksums_file="data/checksums.csv"):
    """Appends SHA256 hash to checksums.csv."""
    with open(checksums_file, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([dataset_id, sha256_hash])

def process_uci_dataset(url, dataset_id):
  """Placeholder for UCI processing."""
  print("Processing UCI Dataset (placeholder)")
  # Replace with actual download and metadata extraction logic
  return {"sample_size": 100, "continuous_vars": 5, "group_labels": 2}

def process_openml_dataset(dataset_id):
  """Processes dataset from OpenML."""
  info = get_dataset_info_from_openml(dataset_id)
  if info:
      return info
  else:
    return None

def main():
    initialize_metadata_files()
    # Example usage (replace with your actual data sources and logic):
    uci_url = "http://example.com/uci_dataset.csv"  # Replace with actual URL
    openml_ids = [1590, 428] #Replace with desired IDs

    dataset_id_uci = 'uci_1'
    download_file(uci_url, f"data/raw/{dataset_id_uci}.csv")
    sha256_hash_uci = compute_sha256(f"data/raw/{dataset_id_uci}.csv")

    metadata_uci = process_uci_dataset(uci_url, dataset_id_uci)
    append_to_datasets_csv([dataset_id_uci, uci_url, metadata_uci['sample_size'], metadata_uci['continuous_vars'], metadata_uci['group_labels'], ''])
    append_to_checksums_csv(dataset_id_uci, sha256_hash_uci)

    for dataset_id in openml_ids:
      metadata = process_openml_dataset(dataset_id)
      if metadata:
        # Placeholder for OpenML download. Actual downloads handled by get_dataset_info_from_openml() which is called in the function.
        sha256_hash = compute_sha256("data/raw/placeholder") # Replace with actual path
        append_to_datasets_csv([dataset_id, "OpenML", metadata['sample_size'], metadata['continuous_vars'], metadata['group_labels'], ''])
        append_to_checksums_csv(dataset_id, sha256_hash)
