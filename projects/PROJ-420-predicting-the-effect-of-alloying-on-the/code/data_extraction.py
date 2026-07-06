"""
Data extraction module for fetching alloy data from public repositories.
Implements T009 (Materials Project) and T010 (NIST) extraction logic.
"""
import json
import os
import time
from typing import Any, Dict, List, Optional
from pathlib import Path
import requests

from schemas.alloy_record import AlloyRecord, MeasurementProvenance
from config import get_config
from logging_config import setup_logging, get_logger

# Initialize logger
logger = get_logger(__name__)

def save_records_to_json(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save a list of records to a JSON file.
    Ensures the directory exists before writing.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, default=str)
    logger.info(f"Saved {len(records)} records to {output_path}")

def extract_materials_project_data(output_path: Path) -> List[Dict[str, Any]]:
    """
    Fetch aluminum alloys from Materials Project API.
    Endpoint: GET https://next-gen.materialsproject.org/api/v2/materials/
    Query params: elements=Al, elastic_properties
    Validates against AlloyRecord schema ensuring measurement_method is present.
    """
    config = get_config()
    api_key = os.getenv("MP_API_KEY")
    
    if not api_key:
        # Fallback or error handling if key is missing in environment
        # In a real pipeline, this should halt or warn appropriately
        logger.warning("MP_API_KEY not found in environment. Extraction may fail or be rate-limited.")
    
    base_url = "https://next-gen.materialsproject.org/api/v2/materials"
    params = {
        "elements": "Al",
        "api_key": api_key,
        "fields": "material_id,elements,formula_pretty,nsites,structure,elasticity,properties"
    }
    
    valid_records = []
    total_fetched = 0
    page = 1
    limit = 100  # MP API typical limit per page

    logger.info(f"Starting extraction from Materials Project for Al alloys to {output_path}")

    while True:
        params["page"] = page
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            results = data.get("data", [])
            if not results:
                logger.info(f"No more results found on page {page}. Stopping pagination.")
                break

            logger.info(f"Fetched page {page} with {len(results)} materials.")
            
            for item in results:
                total_fetched += 1
                # Filter for entries with elastic properties
                if "elasticity" not in item or not item["elasticity"]:
                    continue
                
                elasticity = item["elasticity"]
                
                # Extract Poisson's ratio and Young's Modulus
                # MP usually provides voigt, reuss, vrh averages
                poisson = elasticity.get("poisson_ratio")
                youngs_modulus = elasticity.get("youngs_modulus")
                
                # We need to map MP data to our AlloyRecord schema
                # MP doesn't always have a direct "measurement_method" string in the API response for elasticity
                # We must infer or set a default based on the source (MP is DFT calculated)
                # However, T014/T014b logic handles the exclusion of 'calculated' later.
                # For T009, we must ensure the field is PRESENT in the record we save.
                
                # Determine measurement method
                # MP data is theoretically calculated (DFT). 
                # We set this explicitly so downstream T014 can filter it if needed, 
                # but T009 requirement is just to ensure the field exists.
                measurement_method = "calculated_dft" 
                
                # Extract composition
                composition_dict = {}
                if "elements" in item:
                    for elem_data in item["elements"]:
                        symbol = elem_data.get("symbol")
                        fraction = elem_data.get("fraction")
                        if symbol and fraction is not None:
                            composition_dict[symbol] = fraction

                # Construct the record dict matching AlloyRecord structure
                record_dict = {
                    "material_id": item.get("material_id"),
                    "formula": item.get("formula_pretty"),
                    "composition": composition_dict,
                    "poisson_ratio": poisson,
                    "youngs_modulus_gpa": youngs_modulus,
                    "bulk_modulus_gpa": elasticity.get("bulk_modulus_vrh"),
                    "shear_modulus_gpa": elasticity.get("shear_modulus_vrh"),
                    "measurement_method": measurement_method,
                    "measurement_source": "materials_project",
                    "provenance": {
                        "source_url": f"{base_url}/{item.get('material_id')}",
                        "extraction_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "api_version": "v2"
                    }
                }

                # Validate against AlloyRecord schema to ensure structure integrity
                # This raises ValidationError if fields are missing or types wrong
                try:
                    AlloyRecord(**record_dict)
                    valid_records.append(record_dict)
                except Exception as e:
                    logger.warning(f"Skipping invalid record {item.get('material_id')}: {e}")
                    continue

            page += 1
            # Small delay to be polite to the API
            time.sleep(0.1)

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            break
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            break

    logger.info(f"Extraction complete. Total processed: {total_fetched}, Valid records saved: {len(valid_records)}")
    return valid_records

def extract_nist_data(output_path: Path) -> List[Dict[str, Any]]:
    """
    Fetch aluminum alloys from NIST Materials Data Repository.
    Note: NIST does not have a single public API endpoint like MP.
    This function attempts to query a specific dataset if available,
    or returns an empty list if the specific endpoint is unreachable/undefined.
    Placeholder for T010 implementation.
    """
    logger.info("NIST extraction requested. No specific public API endpoint configured.")
    # Since T010 is marked as FAILED: unspecified in the prompt, and no URL is provided,
    # we return an empty list to indicate no data was fetched, avoiding fabrication.
    # In a real scenario, this would require a specific dataset URL or API key.
    return []

def run_extraction() -> None:
    """
    Main orchestration for data extraction.
    Fetches from Materials Project and NIST, validates, and saves to data/raw/.
    """
    config = get_config()
    raw_data_dir = config.data_dir / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    # T009: Materials Project
    mp_path = raw_data_dir / "mp_aluminum.json"
    mp_records = extract_materials_project_data(mp_path)
    
    # T010: NIST (currently returns empty list due to unspecified endpoint)
    nist_path = raw_data_dir / "nist_aluminum.json"
    nist_records = extract_nist_data(nist_path)
    save_records_to_json(nist_records, nist_path)

    logger.info("Data extraction pipeline finished.")

def main():
    setup_logging()
    run_extraction()

if __name__ == "__main__":
    main()
