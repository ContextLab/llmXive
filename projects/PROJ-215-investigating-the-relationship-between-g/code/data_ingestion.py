import os
import time
import json
import logging
import requests
import pandas as pd

from pathlib import Path

from config import get_output_path, calculate_median_depth, estimate_rarefaction_loss
from utils.logging import get_logger

class IngestionResult:
    def __init__(self, valid_samples, excluded_samples):
        self.valid_samples = valid_samples
        self.excluded_samples = excluded_samples

def exponential_backoff_retry(func, max_retries=5, base_delay=2):
    def wrapper(*args, **kwargs):
        for i in range(max_retries):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                logging.warning(f"Attempt {i + 1} failed with error: {e}")
                if i < max_retries - 1:
                    time.sleep(base_delay * (2**i))  # Exponential backoff
                else:
                    raise  # Re-raise after last attempt
    return wrapper

@exponential_backoff_retry()
def fetch_study_metadata(api_url):
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()

@exponential_backoff_retry()
def fetch_otu_table(api_url):
    response = requests.get(api_url)
    response.raise_for_status()
    return pd.read_csv(response.text) # Assuming CSV format


def load_agp_data_from_mirror(metadata_url, otu_table_url):
    try:
        metadata = fetch_study_metadata(metadata_url)
        otu_table = fetch_otu_table(otu_table_url)

        # Assuming 'sample_id' is present in both metadata and OTU table.
        merged_data = pd.merge(otu_table, metadata, on='sample_id', how='inner')
        return merged_data
    except Exception as e:
        logging.error(f"Error loading data from mirror: {e}")
        return None

def check_feasibility(df):
    # Check if both S rRNA and PHQ-9/GAD-7 metadata are present for overlapping samples
    if df[['S rRNA', 'PHQ-9', 'GAD-7']].isnull().values.any():
        logging.warning("Data gap found: Missing S rRNA or mental health data.")
        return False
    return True

def merge_data(otu_table, metadata):
  merged_data = pd.merge(otu_table, metadata, on='sample_id', how='inner')
  return merged_data

def run_ingestion():
    logger = get_logger(__name__)
    output_path = get_output_path("cleaned_dataset.csv")
    metadata_url = "https://qiita.ucsd.edu/api/v1/study/10317/samples"  # Replace with your actual URL
    otu_table_url = "https://qiita.ucsd.edu/api/v1/study/10317/otu-table" # Replace with your actual URL

    logger.info("Starting data ingestion...")
    data = load_agp_data_from_mirror(metadata_url, otu_table_url)

    if data is None:
        logger.error("Data ingestion failed. Halting analysis.")
        return

    if not check_feasibility(data):
      logger.error("Feasibility check failed. Halting Analysis")
      return

    # Save the merged data to a CSV file
    data.to_csv(output_path, index=False)
    logger.info(f"Data saved to {output_path}")
    return output_path

if __name__ == "__main__":
  run_ingestion()