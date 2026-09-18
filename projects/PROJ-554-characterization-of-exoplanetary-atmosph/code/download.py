import os
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

def fetch_raw_metadata(api_url: str) -> List[Dict[str, Any]]:
    """
    Placeholder for fetching raw metadata from the API.
    In a real implementation, this would make an API call.
    """
    # Replace with actual API call
    # This is just sample data for demonstration
    return [
        {"planet_name": "HD 209458 b", "temperature": 1200, "metallicity": 1.0, "snr": 20, "resolution": 50000, "instrument": "HST"},
        {"planet_name": "WASP-12 b", "temperature": 1600, "metallicity": 2.0, "snr": 15, "resolution": 40000, "instrument": "Spitzer"},
        {"planet_name": "GJ 1214 b", "temperature": 500, "metallicity": 0.5, "snr": 10, "resolution": 30000, "instrument": "HST"},
    ]

def classify_planet(temperature: float, radius: float) -> str:
    """
    Classifies a planet as "Hot Jupiter" or "Temperate Super-Earth".
    """
    if temperature > 1000 and radius > 1.0:
        return "Hot Jupiter"
    elif radius < 1.6 and temperature < 1000:
        return "Temperate Super-Earth"
    else:
        return "Unknown"

def process_metadata(raw_metadata: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Processes raw metadata and adds the planet_category.
    """
    processed_metadata = []
    for item in raw_metadata:
        planet_category = classify_planet(item["temperature"], item["metallicity"])
        item["planet_category"] = planet_category
        processed_metadata.append(item)
    return processed_metadata

def save_metadata_csv(metadata: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves the metadata to a CSV file.
    """
    df = pd.DataFrame(metadata)
    df.to_csv(output_path, index=False)

def count_unique_planets(metadata: List[Dict[str, Any]]) -> int:
    """
    Counts the number of unique planets in the metadata.
    """
    return len(set([item["planet_name"] for item in metadata]))

def report_sample_size(count: int, output_path: str) -> None:
    """
    Reports the sample size and logs a warning if it's outside the target range.
    """
    with open(output_path, "w") as f:
        if 30 <= count <= 45:
            f.write(json.dumps({"count": count, "note": "Sample size reported; pipeline proceeds regardless of count."}))
        else:
            f.write(json.dumps({"count": count, "note": "Sample size reported; pipeline proceeds regardless of count."}))
            logging.warning(f"Sample size {count} is outside target range [30-45].")

def download_all_spectra(api_url: str) -> List[Dict[str, Any]]:
    """
    Downloads all available spectra matching the criteria.
    """
    raw_metadata = fetch_raw_metadata(api_url)
    return raw_metadata

def main():
    """
    Main function to download spectra and save metadata.
    """
    api_url = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    output_path = "data/processed/metadata.csv"
    sample_size_report_path = "data/processed/sample_size_report.json"

    raw_metadata = download_all_spectra(api_url)
    processed_metadata = process_metadata(raw_metadata)
    save_metadata_csv(processed_metadata, output_path)
    count = count_unique_planets(processed_metadata)
    report_sample_size(count, sample_size_report_path)

    logging.info(f"Metadata saved to {output_path}")
    logging.info(f"Sample size report saved to {sample_size_report_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()