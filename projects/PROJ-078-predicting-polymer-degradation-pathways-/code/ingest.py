import os
import time
import logging
import json
import csv
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from data_models import PolymerRecord
from utils import get_logger, get_project_paths, retry_with_backoff

# Configuration constants
NIST_SEARCH_URL = "https://webbook.nist.gov/cgi/cbook.cgi"
MATERIALS_PROJECT_API = "https://api.materialsproject.org"
RATE_LIMIT_DELAY = 1.0  # seconds between requests
MAX_RETRIES = 5
DEGRADATION_LABELS = ["hydrolysis", "oxidation", "photolysis", "thermal", "biodegradation"]

logger = get_logger(__name__)
paths = get_project_paths()

def enforce_rate_limit(last_request_time: float) -> float:
    """Enforce rate limiting by waiting if necessary."""
    elapsed = time.time() - last_request_time
    if elapsed < RATE_LIMIT_DELAY:
        wait_time = RATE_LIMIT_DELAY - elapsed
        logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
        time.sleep(wait_time)
    return time.time()

def is_valid_smiles(smiles: str) -> bool:
    """Basic SMILES validation - checks for empty string and common invalid characters."""
    if not smiles or not isinstance(smiles, str):
        return False
    smiles = smiles.strip()
    if not smiles:
        return False
    # Basic sanity check: should contain valid SMILES characters
    valid_chars = set("CNOcnpSsFBclIcC1234567890=+#-[]()\\/@")
    return all(c in valid_chars or c in smiles for c in smiles)

def validate_smiles_and_convert(smiles: str, record_id: str) -> Optional[Dict[str, Any]]:
    """Validate SMILES and attempt to convert to molecular graph using RDKit."""
    try:
        from rdkit import Chem
        from rdkit.Chem import rdMolDescriptors

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"RDKit failed to parse SMILES for record {record_id}: {smiles}")
            return None

        # Basic molecular properties
        num_atoms = mol.GetNumAtoms()
        num_bonds = mol.GetNumBonds()
        molecular_weight = rdMolDescriptors.CalcExactMolWt(mol)

        return {
            "smiles": smiles,
            "num_atoms": num_atoms,
            "num_bonds": num_bonds,
            "molecular_weight": molecular_weight,
            "is_valid": True
        }
    except Exception as e:
        logger.error(f"Error converting SMILES for record {record_id}: {e}")
        return None

def validate_degradation_label(label: str) -> bool:
    """Check if degradation label is in our known set."""
    return label.lower() in [l.lower() for l in DEGRADATION_LABELS]

def fetch_nist_record(record_id: str, last_request_time: float) -> Optional[Dict[str, Any]]:
    """Fetch a specific record from NIST Chemistry WebBook."""
    # Note: NIST WebBook doesn't have a direct API for degradation data.
    # This is a placeholder for the actual implementation that would
    # scrape or use a specific NIST endpoint if available.
    # For now, we simulate the structure expected from NIST.
    
    # In a real implementation, this would:
    # 1. Construct the URL for the specific compound
    # 2. Make the request with rate limiting
    # 3. Parse the HTML/JSON response
    # 4. Extract SMILES, degradation pathway, and environmental parameters
    
    logger.info(f"Fetching NIST record {record_id}")
    
    # Simulated response structure (would be replaced with real parsing)
    # This is where we'd implement the actual NIST WebBook scraping logic
    return {
        "source": "nist",
        "record_id": record_id,
        "smiles": None,  # Would be extracted from NIST
        "degradation_pathway": None,  # Would be extracted from NIST
        "temperature": None,
        "ph": None,
        "uv_intensity": None,
        "raw_data": {}
    }

def fetch_materials_project_record(record_id: str, last_request_time: float) -> Optional[Dict[str, Any]]:
    """Fetch a specific record from Materials Project API."""
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        logger.warning("MP_API_KEY not set, skipping Materials Project fetch")
        return None

    url = f"{MATERIALS_PROJECT_API}/materials/{record_id}"
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    try:
        response = retry_with_backoff(
            requests.get,
            url,
            headers=headers,
            max_retries=MAX_RETRIES,
            backoff_factor=2.0
        )
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant fields - structure depends on MP API response
        # This is a placeholder for actual MP data extraction
        return {
            "source": "materials_project",
            "record_id": record_id,
            "smiles": data.get("materials", {}).get("smiles"),
            "degradation_pathway": data.get("degradation", {}).get("pathway"),
            "temperature": data.get("environmental", {}).get("temperature"),
            "ph": data.get("environmental", {}).get("ph"),
            "uv_intensity": data.get("environmental", {}).get("uv_intensity"),
            "raw_data": data
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch Materials Project record {record_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing Materials Project record {record_id}: {e}")
        return None

def download_records_from_nist(record_ids: List[str], output_dir: str) -> List[Dict[str, Any]]:
    """Download records from NIST with rate limiting and validation."""
    records = []
    flagged_missing_labels = []
    last_request_time = 0.0

    for record_id in record_ids:
        last_request_time = enforce_rate_limit(last_request_time)
        record_data = fetch_nist_record(record_id, last_request_time)
        
        if record_data is None:
            logger.warning(f"Skipping NIST record {record_id} - fetch failed")
            continue

        # Validate SMILES
        if record_data.get("smiles"):
            validation = validate_smiles_and_convert(record_data["smiles"], record_id)
            if not validation or not validation["is_valid"]:
                logger.warning(f"Skipping NIST record {record_id} - invalid SMILES")
                continue
            record_data.update(validation)

        # Validate degradation label
        if not record_data.get("degradation_pathway"):
            flagged_missing_labels.append(record_data)
            logger.info(f"Flagging NIST record {record_id} - missing degradation pathway label")
            continue
        
        if not validate_degradation_label(record_data["degradation_pathway"]):
            flagged_missing_labels.append(record_data)
            logger.info(f"Flagging NIST record {record_id} - unknown degradation pathway: {record_data['degradation_pathway']}")
            continue

        records.append(record_data)

    # Save flagged records for curation
    if flagged_missing_labels:
        flagged_path = os.path.join(output_dir, "flagged_for_curation.csv")
        save_flagged_records(flagged_missing_labels, flagged_path)
        logger.info(f"Saved {len(flagged_missing_labels)} flagged records to {flagged_path}")

    return records

def download_records_from_materials_project(record_ids: List[str], output_dir: str) -> List[Dict[str, Any]]:
    """Download records from Materials Project with rate limiting and validation."""
    records = []
    flagged_missing_labels = []
    last_request_time = 0.0

    for record_id in record_ids:
        last_request_time = enforce_rate_limit(last_request_time)
        record_data = fetch_materials_project_record(record_id, last_request_time)
        
        if record_data is None:
            logger.warning(f"Skipping Materials Project record {record_id} - fetch failed")
            continue

        # Validate SMILES
        if record_data.get("smiles"):
            validation = validate_smiles_and_convert(record_data["smiles"], record_id)
            if not validation or not validation["is_valid"]:
                logger.warning(f"Skipping Materials Project record {record_id} - invalid SMILES")
                continue
            record_data.update(validation)

        # Validate degradation label
        if not record_data.get("degradation_pathway"):
            flagged_missing_labels.append(record_data)
            logger.info(f"Flagging Materials Project record {record_id} - missing degradation pathway label")
            continue
        
        if not validate_degradation_label(record_data["degradation_pathway"]):
            flagged_missing_labels.append(record_data)
            logger.info(f"Flagging Materials Project record {record_id} - unknown degradation pathway: {record_data['degradation_pathway']}")
            continue

        records.append(record_data)

    # Save flagged records for curation
    if flagged_missing_labels:
        flagged_path = os.path.join(output_dir, "flagged_for_curation.csv")
        save_flagged_records(flagged_missing_labels, flagged_path)
        logger.info(f"Saved {len(flagged_missing_labels)} flagged records to {flagged_path}")

    return records

def save_flagged_records(records: List[Dict[str, Any]], output_path: str):
    """Save flagged records to CSV for manual curation."""
    if not records:
        return

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        if records:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)

def filter_records_with_degradation_labels(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter records to only include those with valid degradation pathway labels."""
    return [r for r in records if r.get("degradation_pathway") and validate_degradation_label(r["degradation_pathway"])]

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Main entry point for data ingestion."""
    logger.info("Starting polymer degradation data ingestion pipeline")
    
    # Get configuration
    config = load_config_env()
    nist_ids = config.get("nist_record_ids", [])
    mp_ids = config.get("materials_project_record_ids", [])
    
    raw_data_dir = paths["data_raw"]
    os.makedirs(raw_data_dir, exist_ok=True)

    all_records = []

    # Download from NIST
    if nist_ids:
        logger.info(f"Downloading {len(nist_ids)} records from NIST")
        nist_records = download_records_from_nist(nist_ids, raw_data_dir)
        all_records.extend(nist_records)
        logger.info(f"Successfully ingested {len(nist_records)} valid NIST records")

    # Download from Materials Project
    if mp_ids:
        logger.info(f"Downloading {len(mp_ids)} records from Materials Project")
        mp_records = download_records_from_materials_project(mp_ids, raw_data_dir)
        all_records.extend(mp_records)
        logger.info(f"Successfully ingested {len(mp_records)} valid Materials Project records")

    # Save raw dataset
    if all_records:
        raw_output_path = os.path.join(raw_data_dir, "raw_polymer_records.csv")
        with open(raw_output_path, 'w', newline='') as f:
            if all_records:
                writer = csv.DictWriter(f, fieldnames=all_records[0].keys())
                writer.writeheader()
                writer.writerows(all_records)
        
        checksum = compute_file_checksum(raw_output_path)
        logger.info(f"Saved {len(all_records)} records to {raw_output_path}")
        logger.info(f"File checksum: {checksum}")
    else:
        logger.warning("No valid records were ingested from any source")

    logger.info("Data ingestion pipeline completed")

if __name__ == "__main__":
    main()
