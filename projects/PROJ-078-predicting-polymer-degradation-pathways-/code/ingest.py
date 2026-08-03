"""
Ingestion module for Polymer Degradation Pathways project.
Downloads records from NIST and Materials Project with rate-limit backoff.
"""
import os
import time
import logging
import json
import csv
import hashlib
import requests
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from utils import get_logger, get_project_paths, retry_with_backoff
from data_models import PolymerRecord

# Constants
NIST_BASE_URL = "https://webbook.nist.gov/cgi/cbook.cgi"
# Note: Materials Project requires an API key. We expect it in MP_API_KEY env var.
MP_API_KEY = os.getenv("MP_API_KEY")
MP_BASE_URL = "https://materialsproject.org/rest/v2/materials"

# Rate limiting parameters (seconds)
RATE_LIMIT_DELAY = 1.0  # Base delay between requests
MAX_RETRIES = 5
BACKOFF_FACTOR = 2.0

logger = get_logger(__name__)

def enforce_rate_limit(last_request_time: float) -> float:
    """
    Enforce rate limiting by sleeping if necessary.
    Returns the new timestamp after waiting.
    """
    current_time = time.time()
    elapsed = current_time - last_request_time
    if elapsed < RATE_LIMIT_DELAY:
        sleep_time = RATE_LIMIT_DELAY - elapsed
        logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
        time.sleep(sleep_time)
        return time.time()
    return current_time

def is_valid_smiles(smiles: str) -> bool:
    """
    Basic validation of SMILES string.
    Checks for non-empty and basic character set.
    """
    if not smiles or not isinstance(smiles, str):
        return False
    # Basic character set for SMILES
    valid_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-[]()@#%$")
    return all(c in valid_chars for c in smiles)

def validate_smiles_and_convert(smiles: str) -> Optional[str]:
    """
    Validate SMILES and attempt conversion via RDKit.
    Returns canonical SMILES if valid, None otherwise.
    """
    if not is_valid_smiles(smiles):
        return None
    
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        return Chem.MolToSmiles(mol)
    except Exception as e:
        logger.warning(f"RDKit conversion failed for {smiles}: {e}")
        return None

def validate_degradation_label(label: Optional[str]) -> bool:
    """
    Validate degradation pathway label.
    Returns True if label is present and non-empty.
    """
    return label is not None and isinstance(label, str) and len(label.strip()) > 0

def fetch_nist_record(smiles_or_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a record from NIST Chemistry WebBook.
    Note: NIST webbook is primarily for small molecules.
    For polymers, we might need to search by component or use specific endpoints.
    This implementation attempts to fetch by ID/SMILES if available.
    
    Returns a dict with structure:
    {
        'smiles': str,
        'temperature': float | None,
        'ph': float | None,
        'uv': float | None,
        'degradation_pathway': str | None,
        'source_id': str
    }
    """
    # NIST WebBook doesn't have a direct polymer degradation API.
    # We'll simulate fetching by using a generic search or returning None
    # if the specific data isn't available via public API.
    # In a real scenario, we'd parse HTML or use a specific chemical database.
    
    logger.warning(f"NIST fetch attempted for {smiles_or_id} - limited API support for polymers")
    
    # Placeholder: In a real implementation, we would:
    # 1. Construct the URL with the ID
    # 2. Fetch and parse the response
    # 3. Extract relevant fields
    
    # For now, return None to indicate data not available via this endpoint
    return None

def fetch_materials_project_record(material_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a record from Materials Project.
    Requires MP_API_KEY environment variable.
    
    Returns a dict with structure:
    {
        'smiles': str,
        'temperature': float | None,
        'ph': float | None,
        'uv': float | None,
        'degradation_pathway': str | None,
        'source_id': str
    }
    """
    if not MP_API_KEY:
        logger.warning("Materials Project API key not set. Skipping fetch.")
        return None

    url = f"{MP_BASE_URL}/{material_id}"
    params = {"_format": "json"}
    headers = {"X-API-Key": MP_API_KEY}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Extract relevant fields based on MP schema
        # Note: MP data structure may vary; this is a simplified extraction
        record = {
            'smiles': data.get('structure', {}).get('smiles', None),
            'temperature': None,  # MP doesn't typically store degradation temp
            'ph': None,           # MP doesn't typically store pH
            'uv': None,           # MP doesn't typically store UV exposure
            'degradation_pathway': None,  # MP doesn't store degradation pathways
            'source_id': material_id
        }
        
        return record
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch from Materials Project: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching MP record: {e}")
        return None

@retry_with_backoff(max_retries=MAX_RETRIES, backoff_factor=BACKOFF_FACTOR)
def download_records_from_nist(ids: List[str]) -> List[Dict[str, Any]]:
    """
    Download multiple records from NIST with rate limiting.
    """
    records = []
    last_request_time = 0.0
    
    for idx, rec_id in enumerate(ids):
        last_request_time = enforce_rate_limit(last_request_time)
        logger.info(f"Fetching NIST record {idx+1}/{len(ids)}: {rec_id}")
        
        record = fetch_nist_record(rec_id)
        if record:
            records.append(record)
        
        # Small delay to be polite
        time.sleep(0.5)
    
    return records

@retry_with_backoff(max_retries=MAX_RETRIES, backoff_factor=BACKOFF_FACTOR)
def download_records_from_materials_project(ids: List[str]) -> List[Dict[str, Any]]:
    """
    Download multiple records from Materials Project with rate limiting.
    """
    if not MP_API_KEY:
        logger.warning("Materials Project API key missing. Returning empty list.")
        return []
        
    records = []
    last_request_time = 0.0
    
    for idx, mat_id in enumerate(ids):
        last_request_time = enforce_rate_limit(last_request_time)
        logger.info(f"Fetching MP record {idx+1}/{len(ids)}: {mat_id}")
        
        record = fetch_materials_project_record(mat_id)
        if record:
            records.append(record)
        
        time.sleep(0.5)
    
    return records

def save_flagged_records(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save flagged records (e.g., missing labels) to a CSV file.
    """
    if not records:
        logger.info("No flagged records to save.")
        return
        
    fieldnames = ['smiles', 'temperature', 'ph', 'uv', 'degradation_pathway', 'source_id', 'flag_reason']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(record)
    
    logger.info(f"Saved {len(records)} flagged records to {output_path}")

def filter_records_with_degradation_labels(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter records into those with valid degradation labels and those without.
    Returns (valid_records, flagged_records).
    """
    valid = []
    flagged = []
    
    for record in records:
        if validate_degradation_label(record.get('degradation_pathway')):
            valid.append(record)
        else:
            record_copy = record.copy()
            record_copy['flag_reason'] = 'missing_degradation_label'
            flagged.append(record_copy)
    
    return valid, flagged

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """
    Main entry point for data ingestion.
    Downloads records from NIST and Materials Project, filters, and saves.
    """
    logger.info("Starting data ingestion pipeline.")
    
    paths = get_project_paths()
    raw_output_path = paths["data_raw"] / "raw_nist_mp_records.csv"
    flagged_output_path = paths["data_raw"] / "flagged_for_curation.csv"
    
    # Define sample IDs for demonstration
    # In a real scenario, these would come from a configuration or query
    nist_ids = []  # NIST doesn't have a public polymer degradation API
    mp_ids = ["mp-12345", "mp-67890"]  # Placeholder IDs
    
    all_records = []
    
    # Download from NIST (will likely return empty due to API limitations)
    if nist_ids:
        nist_records = download_records_from_nist(nist_ids)
        all_records.extend(nist_records)
    else:
        logger.info("No NIST IDs provided, skipping NIST fetch.")
    
    # Download from Materials Project
    if mp_ids:
        mp_records = download_records_from_materials_project(mp_ids)
        all_records.extend(mp_records)
    else:
        logger.info("No MP IDs provided, skipping MP fetch.")
    
    if not all_records:
        logger.warning("No records downloaded. Creating empty output files.")
        # Create empty CSV with headers
        with open(raw_output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['smiles', 'temperature', 'ph', 'uv', 'degradation_pathway', 'source_id'])
            writer.writeheader()
        return
    
    # Filter records
    valid_records, flagged_records = filter_records_with_degradation_labels(all_records)
    
    # Save flagged records
    save_flagged_records(flagged_records, flagged_output_path)
    
    # Save all records (including those with missing labels, as per T013 spec)
    # Note: T014 will handle the exclusion logic for training
    fieldnames = ['smiles', 'temperature', 'ph', 'uv', 'degradation_pathway', 'source_id']
    
    with open(raw_output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in all_records:
            writer.writerow(record)
    
    checksum = compute_file_checksum(raw_output_path)
    logger.info(f"Ingestion complete. Saved {len(all_records)} records to {raw_output_path}")
    logger.info(f"File checksum: {checksum}")
    logger.info(f"Flagged {len(flagged_records)} records for curation.")
    
    # Save checksum to a separate file
    checksum_path = paths["data_raw"] / "raw_nist_mp_records.csv.sha256"
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  raw_nist_mp_records.csv\n")

if __name__ == "__main__":
    main()
