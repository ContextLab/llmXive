import os
import sys
import logging
from pathlib import Path
import pandas as pd
import hashlib

from config import get_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_and_verify(url, filepath, expected_sha256):
    """Downloads a file from a URL and verifies its SHA256 checksum."""
    try:
        logging.info(f"Downloading {url} to {filepath}")
        import requests  # Import here to avoid dependency issues if not used
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logging.info(f"Verifying checksum of {filepath}")
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(4096)
                if not chunk:
                    break
                sha256_hash.update(chunk)
        actual_sha256 = sha256_hash.hexdigest()

        if actual_sha256 != expected_sha256:
            raise ValueError(f"Checksum mismatch! Expected {expected_sha256}, got {actual_sha256}")

        logging.info(f"Successfully downloaded and verified {filepath}")
        return True

    except requests.exceptions.RequestException as e:
        logging.error(f"Download failed: {e}")
        return False
    except ValueError as e:
        logging.error(f"Checksum verification failed: {e}")
        return False
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")  # Catch-all for other errors
        return False

def load_and_convert_to_parquet(filepath, output_path):
  """Loads the downloaded data and converts it to Parquet format."""
  try:
      logging.info(f"Loading data from {filepath}")
      df = pd.read_csv(filepath)  # Assuming CSV format

      logging.info(f"Converting to Parquet and saving to {output_path}")
      df.to_parquet(output_path, index=False)
      return True
  except FileNotFoundError:
      logging.error(f"File not found: {filepath}")
      return False
  except Exception as e:
      logging.exception(f"Error loading and converting data: {e}")
      return False

def main():
    """Main function to download, verify, and convert the dataset."""
    dataset_url = "https://osf.io/download/xxxx-xxxx/"  # Replace with actual OSF DOI link
    expected_sha256 = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" #Replace with real SHA

    raw_data_path = get_path("data/raw/bronze.csv")  # Assuming CSV format
    parquet_path = get_path("data/raw/bronze.parquet")

    if download_and_verify(dataset_url, raw_data_path, expected_sha256):
        if load_and_convert_to_parquet(raw_data_path, parquet_path):
            logging.info("Data ingestion completed successfully.")
        else:
            logging.error("Failed to load and convert data to Parquet.")
            sys.exit(1) # Exit with non-zero code on failure
    else:
        logging.error("Failed to download or verify the dataset.")
        sys.exit(1)  # Exit with non-zero code on failure

if __name__ == "__main__":
    main()