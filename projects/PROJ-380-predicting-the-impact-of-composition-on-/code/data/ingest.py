import os
import sys
import json
import logging
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
import yaml

from utils.config import get_paths
from utils.logging_config import get_logger
from utils.provenance import record_artifact
from data.synthetic_generator import generate_synthetic_bmg_data

logger = get_logger(__name__)

# Constants for schema validation
REQUIRED_FIELDS = ["composition", "shear_modulus_GPa", "source"]

def validate_schema(data: List[Dict[str, Any]], schema_path: Path) -> bool:
    """
    Validate data against the BMGEntry schema.
    
    Args:
        data: List of data dictionaries to validate.
        schema_path: Path to the schema YAML file.
        
    Returns:
        True if validation passes, False otherwise.
    """
    if not schema_path.exists():
        logger.warning(f"Schema file not found: {schema_path}. Skipping validation.")
        return True
        
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    required = schema.get("required", REQUIRED_FIELDS)
    
    for i, item in enumerate(data):
        for field in required:
            if field not in item:
                logger.error(f"Validation failed at index {i}: missing required field '{field}'")
                return False
            if item[field] is None:
                logger.error(f"Validation failed at index {i}: field '{field}' is null")
                return False
    
    logger.info(f"Schema validation passed for {len(data)} records.")
    return True

def fetch_materials_project_data(api_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch BMG data from Materials Project API.
    
    Args:
        api_key: Optional API key. If None, uses environment variable MP_API_KEY.
        
    Returns:
        List of raw material dictionaries from the API.
        
    Raises:
        ConnectionError: If API is unavailable or returns no BMG data.
        ValueError: If API key is missing.
    """
    api_key = api_key or os.getenv("MP_API_KEY")
    if not api_key:
        raise ValueError("Materials Project API key not found. Set MP_API_KEY environment variable.")
    
    base_url = "https://api.materialsproject.org/v2/materials"
    # Query for materials with elastic data (shear modulus)
    # Note: This is a simplified query; real implementation would filter for glassy phases
    params = {
        "api_key": api_key,
        "fields": "formula_pretty,elasticity.g_voigt_reuss_hill,structure"
    }
    
    try:
        # Attempt to fetch a sample of materials (limit to avoid rate limits)
        url = f"{base_url}/all"
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        materials = data.get("results", [])
        if not materials:
            raise ConnectionError("Materials Project API returned no results.")
        
        # Filter for potential BMG candidates (simplified logic)
        # Real implementation would use phase stability or glass-forming ability criteria
        bmg_candidates = []
        for mat in materials:
            if mat.get("elasticity") and mat["elasticity"].get("g_voigt_reuss_hill") is not None:
                bmg_candidates.append(mat)
        
        if not bmg_candidates:
            raise ConnectionError("No BMG candidates found in Materials Project response.")
        
        logger.info(f"Fetched {len(bmg_candidates)} potential BMG candidates from Materials Project.")
        return bmg_candidates
        
    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Failed to connect to Materials Project API: {e}")

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
        composition = item.get("formula_pretty", "")
        shear_modulus = item.get("elasticity", {}).get("g_voigt_reuss_hill")
        
        if shear_modulus is not None:
            processed_item = {
                "composition": composition,
                "shear_modulus_GPa": float(shear_modulus),
                "source": "materials_project"
            }
            processed.append(processed_item)
    
    logger.info(f"Processed {len(processed)} materials into standardized format.")
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
    Validates schema and records provenance.
    """
    paths = get_paths()
    output_file = paths["data_raw"] / "bmg_raw.csv"
    schema_path = paths["contracts"] / "bmg_entry.schema.yaml"
    
    logger.info("Starting data ingestion pipeline.")
    
    data = None
    
    try:
        # Attempt to fetch from Materials Project API
        logger.info("Attempting to fetch data from Materials Project API...")
        raw_data = fetch_materials_project_data()
        processed_data = process_mp_materials(raw_data)
        
        if not validate_schema(processed_data, schema_path):
            raise ValueError("Schema validation failed for Materials Project data.")
        
        save_to_csv(processed_data, str(output_file))
        logger.info(f"Successfully fetched and processed {len(processed_data)} samples from Materials Project.")
        data = processed_data
        
    except Exception as e:
        logger.warning(f"Failed to fetch from Materials Project API: {e}")
        logger.info("Falling back to synthetic data generation.")
        
        # Fallback to synthetic data
        # Note: generate_synthetic_bmg_data already saves to data/raw/synthetic_bmg_seed.csv
        # We read it here and save to the expected output location
        synthetic_source = paths["data_raw"] / "synthetic_bmg_seed.csv"
        
        if synthetic_source.exists():
            # Read existing synthetic data
            with open(synthetic_source, 'r') as f:
                reader = csv.DictReader(f)
                synthetic_data = list(reader)
            
            # Convert shear_modulus to float
            for item in synthetic_data:
                if item.get("shear_modulus_GPa"):
                    item["shear_modulus_GPa"] = float(item["shear_modulus_GPa"])
            
            if not validate_schema(synthetic_data, schema_path):
                raise ValueError("Schema validation failed for synthetic data.")
            
            save_to_csv(synthetic_data, str(output_file))
            data = synthetic_data
            logger.info(f"Loaded {len(synthetic_data)} synthetic samples from {synthetic_source}.")
        else:
            # Generate new synthetic data if file doesn't exist
            synthetic_data = fallback_to_synthetic(output_file, count=100)
            data = synthetic_data
            logger.info(f"Generated {len(synthetic_data)} synthetic samples.")
    
    # Record provenance
    if data and output_file.exists():
        try:
            record_artifact(output_file)
            logger.info(f"Provenance recorded for {output_file}")
        except Exception as e:
            logger.error(f"Failed to record provenance: {e}")
    
    logger.info("Data ingestion pipeline completed.")

if __name__ == "__main__":
    main()
