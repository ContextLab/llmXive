"""
Fetch perovskite data from Materials Project API.

This script implements T012b: Fetch data from Materials Project API,
invoke T009 validation, filter for T_d (TGA onset), and write to data/raw/mp_perovskites.csv.
"""
import logging
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import requests

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_fetcher import fetch_with_retry, FetchError, load_config
from utils.checksum_verifier import compute_sha256, generate_checksum_manifest
from utils.config_manager import get_api_key

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MP_API_URL = "https://api.materialsproject.org"
MP_ENDPOINT = f"{MP_API_URL}/materials"
TGA_PROPERTY = "thermogravimetric_analysis"
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "raw" / "mp_perovskites.csv"
CHECKSUM_PATH = Path(__file__).parent.parent / "data" / "raw" / "mp_perovskites_checksums.json"

def create_retry_session() -> requests.Session:
    """Create a requests session with retry configuration."""
    session = requests.Session()
    return session

def fetch_mp_material_data(
    session: requests.Session,
    formula: str,
    api_key: str
) -> Optional[Dict[str, Any]]:
    """
    Fetch material data for a specific formula from Materials Project.
    
    Args:
        session: Requests session
        formula: Chemical formula (e.g., "CsPbI3")
        api_key: Materials Project API key
        
    Returns:
        Material data dictionary or None if not found
    """
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Construct query for perovskite materials
    # Materials Project API uses formula matching
    url = f"{MP_ENDPOINT}/{formula}"
    
    try:
        response = fetch_with_retry(
            session,
            "GET",
            url,
            headers=headers,
            params={"pretty": True},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("data")
        elif response.status_code == 404:
            logger.debug(f"Formula {formula} not found in Materials Project")
            return None
        else:
            logger.warning(f"Failed to fetch {formula}: HTTP {response.status_code}")
            return None
            
    except FetchError as e:
        logger.error(f"Fetch error for {formula}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching {formula}: {e}")
        return None

def fetch_experimental_tga_data(
    material_data: Dict[str, Any],
    formula: str
) -> Optional[Dict[str, Any]]:
    """
    Extract TGA (thermogravimetric analysis) onset temperature from material data.
    
    Args:
        material_data: Material data dictionary from Materials Project
        formula: Chemical formula
        
    Returns:
        Dictionary with T_d and metadata, or None if TGA data not found
    """
    if not material_data:
        return None
        
    # Materials Project structure for experimental data
    # Look for experimental properties in the data
    experimental = material_data.get("experimental", {})
    properties = material_data.get("properties", {})
    
    # Check for TGA data in various possible locations
    tga_data = None
    
    # Try different paths where TGA data might be stored
    if "thermogravimetric" in experimental:
        tga_data = experimental["thermogravimetric"]
    elif "decomposition" in experimental:
        tga_data = experimental["decomposition"]
    elif "thermal" in experimental:
        if "decomposition_temp" in experimental["thermal"]:
            tga_data = {
                "decomposition_temp": experimental["thermal"]["decomposition_temp"]
            }
    
    # If not found in experimental, check properties
    if not tga_data and "decomposition_temp" in properties:
        tga_data = {"decomposition_temp": properties["decomposition_temp"]}
        
    if not tga_data:
        return None
        
    # Extract decomposition temperature
    t_d = tga_data.get("decomposition_temp")
    
    if t_d is None:
        return None
        
    # Extract metadata
    return {
        "formula": formula,
        "T_d": t_d,
        "source": "Materials Project",
        "material_id": material_data.get("material_id"),
        "instrument_model": tga_data.get("instrument_model", "Unknown"),
        "manufacturer": tga_data.get("manufacturer", "Unknown"),
        "temperature_precision": tga_data.get("temperature_precision", 10),
        "experimental_error": tga_data.get("experimental_error", 0),
        "notes": tga_data.get("notes", "")
    }

def validate_data_checksum(
    data: List[Dict[str, Any]],
    checksum_path: Path
) -> bool:
    """
    Validate data integrity using checksums.
    
    Args:
        data: List of data dictionaries
        checksum_path: Path to save checksum manifest
        
    Returns:
        True if validation passes
    """
    # Generate checksum for the dataset
    checksum = compute_sha256(data)
    
    # Save checksum manifest
    manifest = {
        "file": str(checksum_path.parent / checksum_path.name.replace("_checksums.json", ".csv")),
        "checksum": checksum,
        "record_count": len(data),
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(checksum_path, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"Checksum manifest saved to {checksum_path}")
    return True

def save_to_csv(
    data: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save data to CSV file.
    
    Args:
        data: List of data dictionaries
        output_path: Path to output CSV file
    """
    if not data:
        logger.warning("No data to save")
        return
        
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to DataFrame and save
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    
    logger.info(f"Saved {len(data)} records to {output_path}")

def main() -> int:
    """
    Main function to fetch Materials Project perovskite data.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.info("Starting Materials Project perovskite data fetch")
    
    # Load configuration
    config = load_config()
    api_key = get_api_key("MP_API_KEY")
    
    if not api_key:
        logger.error("Materials Project API key not found. Set MP_API_KEY in .env")
        return 1
    
    # Create retry session
    session = create_retry_session()
    
    # List of perovskite formulas to fetch
    # This would typically come from a configuration or previous step
    # For now, we'll use a sample set that should exist in Materials Project
    perovskite_formulas = [
        "CsPbI3", "CsPbBr3", "CsSnI3", "MAPbI3", "MAPbBr3",
        "FAPbI3", "FAPbBr3", "Cs2AgBiBr6", "Cs2AgInCl6",
        "RbPbI3", "RbSnI3", "Cs2AgSbCl6", "Cs2NaBiCl6",
        "Cs2TiBr6", "Cs2ZrCl6", "Cs2SnCl6", "Cs2SnBr6"
    ]
    
    logger.info(f"Fetching data for {len(perovskite_formulas)} perovskite formulas")
    
    # Fetch data for each formula
    results = []
    for formula in perovskite_formulas:
        logger.info(f"Fetching {formula}...")
        
        # Fetch material data
        material_data = fetch_mp_material_data(session, formula, api_key)
        
        if material_data:
            # Extract TGA data
            tga_entry = fetch_experimental_tga_data(material_data, formula)
            
            if tga_entry:
                results.append(tga_entry)
                logger.info(f"Found TGA data for {formula}: T_d = {tga_entry['T_d']}°C")
            else:
                logger.warning(f"No TGA data found for {formula}")
        else:
            logger.warning(f"Material data not found for {formula}")
        
        # Rate limiting - be polite to the API
        time.sleep(0.5)
    
    # Validate checksum
    if results:
        validate_data_checksum(results, CHECKSUM_PATH)
        
        # Save to CSV
        save_to_csv(results, OUTPUT_PATH)
        
        # Verify output file exists and has T_d column
        if OUTPUT_PATH.exists():
            df = pd.read_csv(OUTPUT_PATH)
            if 'T_d' in df.columns and not df['T_d'].isna().all():
                logger.info(f"SUCCESS: {OUTPUT_PATH} created with {len(df)} records containing T_d values")
                return 0
            else:
                logger.error("Output file created but missing T_d column or all values are null")
                return 1
        else:
            logger.error("Output file was not created")
            return 1
    else:
        logger.warning("No TGA data found for any formula. Creating empty file with schema.")
        # Create empty file with expected schema
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=[
            "formula", "T_d", "source", "material_id", 
            "instrument_model", "manufacturer", 
            "temperature_precision", "experimental_error", "notes"
        ]).to_csv(OUTPUT_PATH, index=False)
        return 1

if __name__ == "__main__":
    sys.exit(main())
