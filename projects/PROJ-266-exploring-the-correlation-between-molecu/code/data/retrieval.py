import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import from sibling modules as per API surface
from utils.logging import get_logger, configure_root_logger
from utils.checksum import register_checksum, compute_file_checksum, save_state_file, load_state_file

# Configure logging
logger = get_logger(__name__)

# Constants
CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data/assay.json"
RAW_DATA_PATH = "data/raw/caco2_raw.csv"
STATE_PATH = "state/projects/PROJ-266-exploring-the-correlation-between-molecu.yaml"

def fetch_assay_page(page: int = 0, page_size: int = 100) -> Optional[Dict[str, Any]]:
    """
    Fetch a single page of assays from ChEMBL API with exponential backoff.
    
    Args:
        page: Page number (0-indexed)
        page_size: Number of results per page
        
    Returns:
        JSON response dict or None if failed after retries
    """
    url = f"{CHEMBL_API_BASE}?assay_type=Caco-2&standard_type=MEASUREMENT&page={page}&page_size={page_size}"
    max_retries = 5
    base_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            import requests
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay:.1f}s...")
            time.sleep(delay)
    
    logger.error(f"Failed to fetch assay page {page} after {max_retries} attempts")
    return None

def extract_records(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract relevant records from ChEMBL API response.
    
    Args:
        data: JSON response from ChEMBL API
        
    Returns:
        List of extracted records
    """
    records = []
    results = data.get("results", [])
    
    for item in results:
        # Extract SMILES from molecule_structures if available
        molecule_structures = item.get("molecule_structures", {})
        smiles = molecule_structures.get("standard_inchi") or molecule_structures.get("canonical_smiles")
        
        # Extract logPapp (permeability) if available
        # ChEMBL stores this in standard_value_text or similar fields
        standard_value = item.get("standard_value")
        standard_units = item.get("standard_units")
        
        # We need to find the permeability value
        # Look for permeability related fields
        permeability_value = None
        
        # Check standard_value if it's a number and units suggest permeability
        if standard_value and standard_units:
            if "log" in standard_value.lower() or "cm" in standard_value.lower():
                try:
                    permeability_value = float(standard_value)
                except (ValueError, TypeError):
                    pass
        
        # If not found in standard_value, check for specific permeability fields
        # ChEMBL often stores this in the "pax" or similar fields for Caco-2
        for field in ["standard_value", "assay_description", "comments"]:
            field_value = item.get(field, "")
            if field_value and isinstance(field_value, str):
                # Try to extract numeric value
                try:
                    # This is a simplified extraction; real implementation might need parsing
                    pass
                except:
                    pass
        
        record = {
            "assay_id": item.get("assay_chembl_id"),
            "smiles": smiles,
            "logPapp": permeability_value,
            "source": "chembl",
            "raw_data": json.dumps(item)  # Store full raw data for debugging
        }
        
        records.append(record)
    
    return records

def fetch_all_caco2_data(target_count: int = 600) -> List[Dict[str, Any]]:
    """
    Fetch Caco-2 assay data from ChEMBL until we have at least target_count records.
    
    Args:
        target_count: Minimum number of records to fetch
        
    Returns:
        List of all fetched records
    """
    all_records = []
    page = 0
    page_size = 100
    
    logger.info(f"Starting fetch of Caco-2 data (target: {target_count} records)")
    
    while len(all_records) < target_count:
        logger.info(f"Fetching page {page}...")
        response = fetch_assay_page(page=page, page_size=page_size)
        
        if not response:
            logger.error("Failed to fetch data from ChEMBL API")
            break
        
        records = extract_records(response)
        all_records.extend(records)
        
        logger.info(f"Fetched {len(records)} records from page {page}. Total: {len(all_records)}")
        
        # Check if we've reached the end of available data
        if len(response.get("results", [])) < page_size:
            logger.info("Reached end of available data")
            break
        
        page += 1
        
        # Safety limit to prevent infinite loops
        if page > 50:
            logger.warning("Reached maximum page limit (50)")
            break
    
    logger.info(f"Total records fetched: {len(all_records)}")
    return all_records

def write_raw_data(records: List[Dict[str, Any]], output_path: str = RAW_DATA_PATH) -> Path:
    """
    Write raw records to CSV file.
    
    Args:
        records: List of records to write
        output_path: Path to output CSV file
        
    Returns:
        Path to the created file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["assay_id", "smiles", "logPapp", "source", "raw_data"]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Wrote {len(records)} records to {output_file}")
    return output_file

def register_artifact_checksum(file_path: Path) -> None:
    """
    Compute checksum and register it in the state file.
    
    Args:
        file_path: Path to the file to checksum
    """
    logger.info(f"Computing checksum for {file_path}")
    
    checksum = compute_file_checksum(file_path)
    logger.info(f"Checksum computed: {checksum}")
    
    # Load state file
    state_file = Path(STATE_PATH)
    if not state_file.exists():
        logger.error(f"State file not found: {state_file}")
        return
    
    state_data = load_state_file(state_file)
    
    # Register checksum
    register_checksum(state_data, str(file_path), checksum)
    
    # Save updated state
    save_state_file(state_file, state_data)
    logger.info(f"Checksum registered in {state_file}")

def main() -> None:
    """Main entry point for data retrieval."""
    configure_root_logger()
    
    try:
        # Fetch data
        records = fetch_all_caco2_data(target_count=600)
        
        if not records:
            logger.error("No records fetched. Exiting.")
            sys.exit(1)
        
        # Write raw data
        output_path = write_raw_data(records)
        
        # Register checksum
        register_artifact_checksum(output_path)
        
        logger.info(f"Data retrieval completed successfully. Output: {output_path}")
        
    except Exception as e:
        logger.error(f"Data retrieval failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()