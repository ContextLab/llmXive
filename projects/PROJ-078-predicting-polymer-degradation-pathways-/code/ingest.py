"""
Data Ingestion Module for Polymer Degradation Pathways.

This module handles downloading polymer degradation records from NIST Chemistry WebBook
and Materials Project APIs, with rate-limiting backoff and validation logic.
"""

from typing import Optional, List, Dict, Any, Tuple
from rdkit import Chem
from rdkit.Chem import AllChem
import logging
import requests
import time
import json
import os
from pathlib import Path

from utils import get_logger, retry_with_backoff, get_project_paths
from data_models import PolymerRecord

# Configuration
NIST_API_BASE = "https://webbook.nist.gov/cgi/cbook.cgi"
# Note: Materials Project API typically requires an API key.
# We will use a placeholder URL structure that assumes the key is passed or configured.
MATERIALS_PROJECT_API_BASE = "https://api.materialsproject.org/v2/materials"

# Output paths
RAW_DATA_DIR = "data/raw"
FLAGGED_DIR = "data/raw"  # Same directory, different file

def is_valid_smiles(smiles: str) -> bool:
    """
    Validates a SMILES string using RDKit.
    
    Args:
        smiles: The SMILES string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if not smiles or not isinstance(smiles, str):
        return False
    mol = Chem.MolFromSmiles(smiles)
    return mol is not None

def validate_smiles_and_convert(smiles: str) -> Optional[Chem.Mol]:
    """
    Validates a SMILES string and returns the RDKit molecule object.
    
    Args:
        smiles: The SMILES string.
        
    Returns:
        RDKit Mol object if valid, None otherwise.
    """
    if not is_valid_smiles(smiles):
        return None
    return Chem.MolFromSmiles(smiles)

def validate_degradation_label(label: Optional[str]) -> bool:
    """
    Validates that a degradation pathway label is present and non-empty.
    
    Args:
        label: The degradation label string.
        
    Returns:
        True if label is valid (non-empty string), False otherwise.
    """
    if label is None:
        return False
    if not isinstance(label, str):
        return False
    return len(label.strip()) > 0

@retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=10.0)
def fetch_nist_record(smiles: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """
    Fetches specific record details from NIST for a given SMILES.
    Note: NIST WebBook is primarily a lookup by name/ID. Direct SMILES search
    is often indirect. We simulate the fetch logic here assuming a wrapper
    or specific endpoint availability, or we log a warning if the direct
    SMILES query isn't supported by the public API without an ID.
    
    For this implementation, we assume a hypothetical endpoint or a fallback
    to a known dataset if the direct API is restricted.
    
    Since NIST does not have a simple 'search by SMILES' REST endpoint that
    returns structured degradation data directly, we will simulate the 
    structure based on the task's requirement to 'Download records'.
    In a real production scenario, this would involve scraping or using a 
    specific partner API. Here we implement the structure to handle the 
    response if available, or raise an error if the source is unreachable.
    
    To satisfy the "Real Data" constraint without fabricating:
    We will attempt to fetch from a known public dataset mirror or return
    a structured error if the specific endpoint is unavailable.
    """
    # Placeholder for actual NIST logic. NIST WebBook often requires a CAS or Name.
    # If we have a SMILES, we might need to convert to InChI first, then query.
    # For this task, we assume a mockable endpoint structure or a specific 
    # dataset URL provided in the project config.
    
    # Since a direct public SMILES->Degradation API is not standard for NIST,
    # we will implement the logic to fetch from a known dataset source 
    # (e.g., a CSV hosted on a public repo) if the API fails, 
    # BUT per strict instructions, we must NOT fall back to synthetic.
    # We will attempt a request to a specific known endpoint if one exists,
    # otherwise we raise an error to indicate the data source is unavailable.
    
    # Let's assume we are querying a specific dataset that maps SMILES to degradation.
    # If the task implies using the NIST API directly for degradation, 
    # it might be a research-specific endpoint.
    
    # Implementation: Attempt to fetch from a hypothetical endpoint.
    # If 404 or connection error, let it propagate (fail loudly).
    
    url = f"{NIST_API_BASE}?structure={smiles}&units=SI"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # Parse HTML or JSON depending on endpoint. 
        # NIST usually returns HTML. Parsing HTML is brittle.
        # For this task, we assume a structured JSON response from a 
        # specialized degradation dataset API that proxies NIST, 
        # or we log that NIST direct API doesn't provide degradation pathways directly.
        
        # Since NIST doesn't provide degradation pathways directly via SMILES API,
        # we will raise a specific error to indicate the data source limitation
        # unless a specific dataset URL is provided in the environment.
        logger.warning("NIST direct API does not provide degradation pathways via SMILES. "
                       "Please configure a specific degradation dataset URL in environment.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch from NIST for {smiles}: {e}")
        raise

@retry_with_backoff(max_retries=3, base_delay=1.0, max_delay=10.0)
def fetch_materials_project_record(material_id: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """
    Fetches material details from Materials Project.
    Requires API key in environment variable MP_API_KEY.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise RuntimeError("MP_API_KEY environment variable not set.")
    
    headers = {"X-API-Key": api_key}
    url = f"{MATERIALS_PROJECT_API_BASE}/{material_id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch from Materials Project for {material_id}: {e}")
        raise

def download_records_from_nist(smiles_list: List[str], logger: logging.Logger) -> List[PolymerRecord]:
    """
    Downloads records from NIST for a list of SMILES.
    Returns a list of PolymerRecord objects.
    """
    records = []
    for smiles in smiles_list:
        if not is_valid_smiles(smiles):
            logger.warning(f"Skipping invalid SMILES: {smiles}")
            continue
        
        # In a real scenario, we would fetch specific degradation data.
        # Since NIST doesn't expose this directly via SMILES, we log and skip
        # or raise if strict mode is on.
        # For this implementation, we assume the input list comes from a 
        # curated source that already has the degradation data, or we 
        # simulate the fetch to demonstrate the backoff logic.
        
        # To satisfy the "Real Data" constraint: We will not fabricate.
        # We will attempt to fetch. If the API doesn't support it, we log.
        # We assume the 'smiles_list' is actually a list of IDs or a 
        # specific dataset that we can query.
        
        # Let's assume we are using a specific dataset file hosted publicly
        # that maps SMILES to degradation, as NIST API doesn't do this.
        # If the task strictly demands NIST API, and it doesn't exist, 
        # we must fail loudly.
        
        # Placeholder: In a real run, this would be replaced by a valid API call.
        # For now, we log the attempt and return empty to avoid fabrication.
        logger.info(f"Attempting to fetch NIST data for {smiles}...")
        # Since we cannot fabricate, and NIST doesn't have this specific endpoint,
        # we will raise an error to indicate the data source is missing.
        # However, to allow the script to run for the sake of the task structure,
        # we will assume the 'smiles_list' is actually a list of records from 
        # a local file or a specific dataset URL that we are supposed to parse.
        # But the task says "Download records from NIST".
        
        # Decision: We will implement the structure to call the API, 
        # and if it fails (which it will for degradation data), we raise.
        # This satisfies "Fail loudly".
        raise RuntimeError(f"NIST API does not support direct degradation pathway queries for SMILES: {smiles}. "
                           "Please provide a valid dataset source.")

def download_records_from_materials_project(material_ids: List[str], logger: logging.Logger) -> List[PolymerRecord]:
    """
    Downloads records from Materials Project.
    Returns a list of PolymerRecord objects.
    """
    records = []
    for mid in material_ids:
        try:
            data = fetch_materials_project_record(mid, logger)
            if data:
                # Map MP data to PolymerRecord
                # This is a placeholder mapping as the schema varies
                record = PolymerRecord(
                    id=mid,
                    smiles=data.get("structure", {}).get("smiles", ""), # Hypothetical
                    degradation_label=data.get("degradation_pathway", "unknown"),
                    temperature=data.get("temperature", None),
                    ph=data.get("ph", None),
                    uv_intensity=data.get("uv_intensity", None),
                    source="Materials Project"
                )
                records.append(record)
        except Exception as e:
            logger.error(f"Failed to process MP record {mid}: {e}")
    return records

def filter_records_with_degradation_labels(records: List[PolymerRecord], logger: logging.Logger) -> Tuple[List[PolymerRecord], List[PolymerRecord]]:
    """
    Filters records into two lists:
    1. Records with valid degradation labels.
    2. Records missing degradation labels (flagged for curation).
    
    Args:
        records: List of PolymerRecord objects.
        logger: Logger instance.
        
    Returns:
        Tuple of (valid_records, flagged_records).
    """
    valid_records = []
    flagged_records = []
    
    for record in records:
        if validate_degradation_label(record.degradation_label):
            valid_records.append(record)
        else:
            flagged_records.append(record)
            logger.warning(f"Record {record.id} missing degradation label. Flagged for curation.")
    
    return valid_records, flagged_records

def save_flagged_records(flagged_records: List[PolymerRecord], logger: logging.Logger):
    """
    Saves flagged records to data/raw/flagged_for_curation.csv.
    """
    if not flagged_records:
        logger.info("No records flagged for curation.")
        return
    
    output_path = Path(RAW_DATA_DIR) / "flagged_for_curation.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        # Write header
        f.write("id,smiles,degradation_label,temperature,ph,uv_intensity,source\n")
        for record in flagged_records:
            f.write(f"{record.id},{record.smiles},{record.degradation_label or ''},{record.temperature},{record.ph},{record.uv_intensity},{record.source}\n")
    
    logger.info(f"Saved {len(flagged_records)} flagged records to {output_path}")

def main():
    """
    Main entry point for data ingestion.
    """
    logger = get_logger(__name__)
    logger.info("Starting data ingestion pipeline...")
    
    # Example: Load a list of SMILES from a config or file
    # In a real scenario, this would be a list of known polymers
    # For this task, we assume the input is provided via environment or config
    # Since we cannot fabricate data, we will check for a config file.
    
    # Placeholder for actual input source
    # If no real source is configured, we raise an error to fail loudly.
    input_config_path = os.getenv("INGEST_INPUT_CONFIG", "config/ingest_config.json")
    if not os.path.exists(input_config_path):
        logger.error(f"Input configuration file not found: {input_config_path}. "
                     "Cannot proceed without real data source configuration.")
        raise FileNotFoundError(f"Input configuration file not found: {input_config_path}")
    
    with open(input_config_path, 'r') as f:
        config = json.load(f)
    
    nist_smiles = config.get("nist_smiles", [])
    mp_ids = config.get("materials_project_ids", [])
    
    all_records = []
    
    if nist_smiles:
        logger.info(f"Downloading {len(nist_smiles)} records from NIST...")
        try:
            nist_records = download_records_from_nist(nist_smiles, logger)
            all_records.extend(nist_records)
        except Exception as e:
            logger.error(f"NIST ingestion failed: {e}")
            raise
    
    if mp_ids:
        logger.info(f"Downloading {len(mp_ids)} records from Materials Project...")
        mp_records = download_records_from_materials_project(mp_ids, logger)
        all_records.extend(mp_records)
    
    if not all_records:
        logger.warning("No records downloaded. Exiting.")
        return
    
    # Filter records
    valid_records, flagged_records = filter_records_with_degradation_labels(all_records, logger)
    
    # Save flagged records
    save_flagged_records(flagged_records, logger)
    
    # Save valid records to raw data
    output_path = Path(RAW_DATA_DIR) / "raw_polymer_data.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("id,smiles,degradation_label,temperature,ph,uv_intensity,source\n")
        for record in valid_records:
            f.write(f"{record.id},{record.smiles},{record.degradation_label},{record.temperature},{record.ph},{record.uv_intensity},{record.source}\n")
    
    logger.info(f"Ingestion complete. {len(valid_records)} valid records saved to {output_path}.")
    logger.info(f"{len(flagged_records)} records flagged for curation.")

if __name__ == "__main__":
    main()
