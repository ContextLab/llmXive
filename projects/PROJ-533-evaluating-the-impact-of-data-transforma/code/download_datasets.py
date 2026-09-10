import os
import sys
import csv
import hashlib
import logging
import time
import yaml
from pathlib import Path

# Ensure logging is configured if not already
try:
    logger = logging.getLogger(__name__)
except Exception:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

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

def update_project_state_artifact_hashes(dataset_id, sha256_hash, project_id="PROJ-533-evaluating-the-impact-of-data-transforma"):
    """
    Updates the artifact_hashes map in the project state YAML file.
    Creates the directory structure if it doesn't exist.
    """
    state_dir = Path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = state_dir / f"{project_id}.yaml"
    
    # Load existing state or initialize
    if state_file.exists():
        with open(state_file, 'r') as f:
            try:
                state = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state = {}
    else:
        state = {
            "project_id": project_id,
            "artifact_hashes": {}
        }
    
    # Ensure artifact_hashes key exists
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    # Update with the new hash
    state["artifact_hashes"][dataset_id] = sha256_hash
    
    # Write back to file
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

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
    
    # Ensure raw data directory exists
    os.makedirs("data/raw", exist_ok=True)
    
    # Example usage (replace with your actual data sources and logic):
    # Using a real small UCI dataset URL for demonstration
    uci_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
    openml_ids = [1590, 428] 

    dataset_id_uci = 'uci_iris'
    
    # Download UCI dataset
    try:
        download_file(uci_url, f"data/raw/{dataset_id_uci}.csv")
        logger.info(f"Downloaded UCI dataset: {dataset_id_uci}")
        
        # Compute SHA256 checksum
        sha256_hash_uci = compute_sha256(f"data/raw/{dataset_id_uci}.csv")
        logger.info(f"Computed SHA256 for {dataset_id_uci}: {sha256_hash_uci}")
        
        # Get metadata
        metadata_uci = process_uci_dataset(uci_url, dataset_id_uci)
        if metadata_uci:
            # Append to datasets.csv
            append_to_datasets_csv([
                dataset_id_uci, 
                uci_url, 
                metadata_uci['sample_size'], 
                metadata_uci['continuous_vars'], 
                metadata_uci['group_labels'], 
                ''
            ])
            
            # Append to checksums.csv
            append_to_checksums_csv(dataset_id_uci, sha256_hash_uci)
            
            # Update project state artifact hashes
            update_project_state_artifact_hashes(dataset_id_uci, sha256_hash_uci)
            logger.info(f"Updated project state for {dataset_id_uci}")
        else:
            logger.error(f"Failed to get metadata for {dataset_id_uci}")
            
    except Exception as e:
        logger.error(f"Error processing UCI dataset {dataset_id_uci}: {e}")

    # Process OpenML datasets
    for dataset_id in openml_ids:
        try:
            # Download from OpenML
            import openml
            dataset = openml.datasets.get_dataset(dataset_id)
            dataset.download_data()
            
            # OpenML downloads to a cache directory, we need to find the file
            # For this example, we'll use the cached path
            # In a real scenario, you might want to copy to data/raw/
            cache_path = dataset.data_file
            
            if os.path.exists(cache_path):
                # Copy to our raw data directory
                local_path = f"data/raw/openml_{dataset_id}.csv"
                import shutil
                shutil.copy2(cache_path, local_path)
                
                # Compute checksum
                sha256_hash = compute_sha256(local_path)
                logger.info(f"Computed SHA256 for OpenML {dataset_id}: {sha256_hash}")
                
                # Get metadata
                metadata = process_openml_dataset(dataset_id)
                if metadata:
                    # Append to datasets.csv
                    append_to_datasets_csv([
                        f"openml_{dataset_id}", 
                        "OpenML", 
                        metadata['sample_size'], 
                        metadata['continuous_vars'], 
                        metadata['group_labels'], 
                        ''
                    ])
                    
                    # Append to checksums.csv
                    append_to_checksums_csv(f"openml_{dataset_id}", sha256_hash)
                    
                    # Update project state artifact hashes
                    update_project_state_artifact_hashes(f"openml_{dataset_id}", sha256_hash)
                    logger.info(f"Updated project state for OpenML {dataset_id}")
            else:
                logger.warning(f"Could not find downloaded file for OpenML {dataset_id}")
                
        except Exception as e:
            logger.error(f"Error processing OpenML dataset {dataset_id}: {e}")

    logger.info("Download and checksum process completed.")

if __name__ == "__main__":
    main()