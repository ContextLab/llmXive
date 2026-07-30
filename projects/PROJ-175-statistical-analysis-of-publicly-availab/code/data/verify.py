"""
Task T038 & T042: Data Verification with Robust Error Handling
Implements specific HTTP error handling and schema validation for Recipe1M Ratings.
"""
import os
import sys
import json
import requests
import pandas as pd
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"

class DataUnavailableError(Exception):
    """Custom exception for data availability issues."""
    pass

def fetch_schema_sample(url, timeout=10):
    """
    Fetch a sample of the schema from a URL to verify accessibility.
    """
    try:
        response = requests.head(url, timeout=timeout)
        if response.status_code == 200:
            return {"status": "accessible", "url": url, "headers": dict(response.headers)}
        else:
            raise DataUnavailableError(f"URL returned status code {response.status_code}: {url}")
    except requests.RequestException as e:
        raise DataUnavailableError(f"Failed to fetch URL {url}: {str(e)}")

def verify_schema(df, expected_columns, file_path=None):
    """
    Verify that a DataFrame has the expected columns.
    """
    missing = set(expected_columns) - set(df.columns)
    if missing:
        error_msg = f"Missing columns in {file_path}: {missing}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    return True

def verify_data_sources(urls, log_file=None):
    """
    Verify a list of data source URLs.
    Logs errors to a specific file without synthetic fallback.
    """
    results = []
    errors = []
    
    if log_file is None:
        log_file = DATA_DIR / "download_errors.log"
    
    for url in urls:
        try:
            result = fetch_schema_sample(url)
            results.append(result)
        except DataUnavailableError as e:
            errors.append({"url": url, "error": str(e)})
            logger.error(f"Data source unavailable: {url} - {e}")
    
    # Write errors to log file
    with open(log_file, 'w') as f:
        json.dump(errors, f, indent=2)
    
    if errors:
        raise DataUnavailableError(f"Failed to verify {len(errors)} data sources. Check {log_file}")
    
    return results

def verify_counterfactual_label_schema(df):
    """
    Verify schema for counterfactual labels (if applicable).
    Note: Per Plan's Critical Reframe, this is largely superseded by Ratings verification.
    """
    required_cols = ["recipe_id", "ingredient_id", "label"]
    return verify_schema(df, required_cols)

def verify_data_sources_with_label_check(urls, sample_size=1000):
    """
    Verify data sources and perform basic schema checks on a sample.
    """
    # First verify URLs are accessible
    verify_data_sources(urls)
    
    # Note: Actual loading and schema check would happen in download/preprocess steps
    # This function is primarily for pre-flight URL verification
    return {"status": "verified", "urls_checked": len(urls)}

def main():
    """
    Main entry point for verification tasks.
    """
    # Example usage (to be replaced by actual URLs from T012)
    urls = [
        "https://huggingface.co/datasets/recipe1m/resolve/main/recipe1m.parquet",
        "https://huggingface.co/datasets/recipe1m/resolve/main/ratings.parquet"
    ]
    
    try:
        results = verify_data_sources(urls)
        print("All data sources verified successfully.")
        return 0
    except DataUnavailableError as e:
        print(f"Verification failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
