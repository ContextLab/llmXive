import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.config import get_paths
from utils.logging_config import get_logger
from data.synthetic_generator import generate_synthetic_bmg_data

logger = get_logger(__name__)

def fetch_materials_project_data(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch BMG data from Materials Project API.
    NOTE: This is a placeholder for the actual API implementation.
    In a real scenario, this would make HTTP requests to the Materials Project API.
    """
    # For now, we raise an error to indicate that the API is not implemented
    # or not available, forcing the fallback to synthetic data.
    raise ConnectionError("Materials Project API is not available or not configured.")

def process_mp_materials(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process raw Materials Project data into a standardized format.
    
    Args:
        raw_data: List of raw data dictionaries from the API.
        
    Returns:
        List of processed data dictionaries.
    """
    processed = []
    for item in raw_data:
        # Placeholder for actual processing logic
        processed_item = {
            "composition": item.get("composition", ""),
            "shear_modulus_GPa": item.get("shear_modulus", None),
            "source": "materials_project"
        }
        processed.append(processed_item)
    return processed

def fallback_to_synthetic(output_path: Path, count: int = 100) -> List[Dict[str, Any]]:
    """
    Generate synthetic BMG data as a fallback when the API is unavailable.
    
    Args:
        output_path: Path to save the synthetic data CSV.
        count: Number of synthetic samples to generate.
        
    Returns:
        List of synthetic data dictionaries.
    """
    logger.info(f"Materials Project API unavailable. Generating {count} synthetic samples.")
    data = generate_synthetic_bmg_data(count)
    
    # Save to CSV
    save_to_csv(data, str(output_path))
    logger.info(f"Synthetic data saved to {output_path}")
    
    return data

def save_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """
    Save a list of dictionaries to a CSV file.
    
    Args:
        data: List of dictionaries to save.
        filepath: Path to the output CSV file.
    """
    if not data:
        logger.warning("No data to save.")
        return
        
    fieldnames = list(data[0].keys())
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    """
    Main function to run the data ingestion pipeline.
    Tries to fetch from Materials Project API, falls back to synthetic data.
    """
    paths = get_paths()
    output_file = paths["data_raw"] / "bmg_raw.csv"
    
    logger.info("Starting data ingestion pipeline.")
    
    try:
        # Attempt to fetch from Materials Project API
        raw_data = fetch_materials_project_data()
        processed_data = process_mp_materials(raw_data)
        save_to_csv(processed_data, str(output_file))
        logger.info(f"Successfully fetched and processed {len(processed_data)} samples from Materials Project.")
    except Exception as e:
        logger.warning(f"Failed to fetch from Materials Project API: {e}")
        logger.info("Falling back to synthetic data generation.")
        
        # Fallback to synthetic data
        synthetic_data = fallback_to_synthetic(output_file, count=100)
        logger.info(f"Generated {len(synthetic_data)} synthetic samples.")
        
    logger.info("Data ingestion pipeline completed.")

if __name__ == "__main__":
    main()
