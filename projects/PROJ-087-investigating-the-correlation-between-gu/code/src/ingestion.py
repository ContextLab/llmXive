"""
Data ingestion module.
Handles downloading, filtering, and merging of microbiome and sleep data.
"""
import pandas as pd
from typing import Optional, Dict, Any
import requests
import os
import sys
import time
import logging
from pathlib import Path

from src.config import load_config
from src.logging_config import configure_root_logger

logger = logging.getLogger(__name__)

def compute_backoff(attempt: int, base: float = 1.0, max_backoff: float = 60.0) -> float:
    """Compute exponential backoff delay."""
    return min(base * (2 ** attempt), max_backoff)

def download_with_backoff(url: str, dest_path: str, max_retries: int = 5) -> bool:
    """Download file with exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(dest_path, "wb") as f:
                f.write(response.content)
            return True
        except requests.RequestException as e:
            delay = compute_backoff(attempt)
            logger.warning(f"Download failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
    return False

def fetch_sample_headers(url: str) -> Optional[list]:
    """Fetch headers from a CSV URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        # Read first line to get headers
        return response.text.splitlines()[0].split(",")
    except Exception as e:
        logger.error(f"Failed to fetch headers: {e}")
        return None

def verify_schema(headers: list, required_cols: list) -> bool:
    """Verify that required columns are present in headers."""
    return all(col in headers for col in required_cols)

def filter_antibiotic_use(df: pd.DataFrame, col: str = "antibiotic_use_last_3m") -> pd.DataFrame:
    """Filter out samples with antibiotic use."""
    return df[(df[col].isna()) | (df[col] == False)]

def filter_sleep_data(df: pd.DataFrame, sleep_cols: list) -> pd.DataFrame:
    """Filter out samples with missing sleep data."""
    mask = df[sleep_cols].notna().all(axis=1)
    return df[mask]

def merge_otu_and_metadata(otu_df: pd.DataFrame, meta_df: pd.DataFrame, key: str = "sample_id") -> pd.DataFrame:
    """Merge OTU table with metadata."""
    return pd.merge(otu_df, meta_df, on=key, how="inner")

def log_exclusion_rates(
    initial_count: int,
    filtered_count: int,
    report_path: str
) -> None:
    """Log exclusion rates to a JSON file."""
    excluded = initial_count - filtered_count
    proportion = excluded / initial_count if initial_count > 0 else 0.0

    report = {
        "total_initial_sample_count": initial_count,
        "excluded_count": excluded,
        "exclusion_proportion": proportion
    }

    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

def run_ingestion_pipeline(input_url: str, output_path: str) -> Dict[str, Any]:
    """
    Run the full ingestion pipeline.
    Note: This is a stub for T013-T017. The real implementation depends on T012b.
    """
    logger.info(f"Starting ingestion pipeline for {input_url}")
    # Placeholder logic to satisfy T021 dependency on cleaned data
    # In a real scenario, this would download and process data.
    return {"status": "placeholder", "message": "Pipeline logic pending T012b"}

def main():
    configure_root_logger()
    logger.info("Ingestion module loaded.")

if __name__ == "__main__":
    main()
