"""
Caco-2 Permeability Data Retrieval from ChEMBL.

Fetches raw Caco-2 assay data from the ChEMBL REST API.
Filters for: assay_type = 'Caco-2', standard_type = 'MEASUREMENT'.
Implements exponential backoff for rate limiting.
Outputs raw data to data/raw/chembl_caco2_raw.csv.
"""
import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

# Project imports
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

# Constants
CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data/assay.json"
MAX_RETRIES = 5
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 30.0  # seconds
BATCH_SIZE = 500  # Assays per page
TARGET_RECORDS = 600
OUTPUT_DIR = "data/raw"
OUTPUT_FILENAME = "chembl_caco2_raw.csv"

logger = get_logger(__name__)

def fetch_assay_page(offset: int = 0, limit: int = BATCH_SIZE) -> Optional[Dict[str, Any]]:
    """
    Fetch a single page of assays from ChEMBL.
    Returns None if the request fails permanently or returns no data.
    """
    params = {
        "assay_type": "Caco-2",
        "format": "json",
        "limit": limit,
        "offset": offset
    }

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            logger.debug(f"Fetching ChEMBL page (offset={offset}, limit={limit})...")
            response = requests.get(CHEMBL_API_BASE, params=params, timeout=60)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limited
                wait_time = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
                logger.warning(f"Rate limited (429). Waiting {wait_time:.1f}s before retry {attempt + 1}/{MAX_RETRIES}...")
                time.sleep(wait_time)
                attempt += 1
            else:
                logger.error(f"ChEMBL API returned status {response.status_code}: {response.text[:200]}")
                return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error fetching page: {e}. Retry {attempt + 1}/{MAX_RETRIES}...")
            time.sleep(BASE_DELAY * (2 ** attempt))
            attempt += 1

    logger.error("Max retries exceeded for ChEMBL API.")
    return None

def extract_records(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract relevant fields from ChEMBL assay JSON.
    We need: SMILES (from target_dictionary), logPapp (from documents/standard_value).
    Note: ChEMBL assay API returns assay metadata. We often need to link to documents or targets.
    However, for Caco-2, the standard_value is often directly on the assay if it's a direct measurement,
    or we need to fetch the related documents.
    
    The ChEMBL assay endpoint structure:
    - results: list of assays
    - Each assay has:
      - assay_chembl_id
      - assay_type
      - target_dictionary (if available) -> target_chembl_id
      - documents (list) -> each doc has standard_value, standard_units, standard_type, molecule_chembl_id
      
    We will iterate through the 'documents' associated with the assay to find MEASUREMENTs.
    """
    records = []
    results = data.get("results", [])
    
    for assay in results:
        # Basic filters
        if assay.get("assay_type") != "Caco-2":
            continue
        
        assay_id = assay.get("assay_chembl_id")
        target_dict = assay.get("target_dictionary", {})
        target_id = target_dict.get("target_chembl_id", "N/A")
        
        # Fetch documents for this assay if available in the main response, 
        # otherwise we might need a secondary call. 
        # The standard API response for /assay.json often includes a 'documents' key if requested or nested.
        # Let's check if documents are present. If not, we might need to fetch /assay/{id}/documents.
        
        docs = assay.get("documents", [])
        
        # If documents are not inline, we must fetch them. 
        # To keep it efficient, we try to fetch documents for this specific assay if the list is empty.
        if not docs and assay_id:
            doc_url = f"https://www.ebi.ac.uk/chembl/api/data/assay/{assay_id}/documents.json"
            try:
                doc_resp = requests.get(doc_url, timeout=30)
                if doc_resp.status_code == 200:
                    doc_data = doc_resp.json()
                    docs = doc_data.get("results", [])
                else:
                    logger.debug(f"Could not fetch documents for {assay_id}: {doc_resp.status_code}")
            except Exception as e:
                logger.debug(f"Error fetching docs for {assay_id}: {e}")

        for doc in docs:
            # Filter for MEASUREMENT
            if doc.get("standard_type") == "MEASUREMENT":
                standard_value = doc.get("standard_value")
                standard_units = doc.get("standard_units", "")
                molecule_id = doc.get("molecule_chembl_id")
                
                # We need SMILES. We can fetch it from molecule endpoint.
                # Optimization: Batch fetch SMILES? For now, fetch individually if needed.
                smiles = None
                if molecule_id:
                    mol_url = f"https://www.ebi.ac.uk/chembl/api/data/molecule/{molecule_id}.json"
                    try:
                        mol_resp = requests.get(mol_url, timeout=30)
                        if mol_resp.status_code == 200:
                            mol_data = mol_resp.json()
                            smiles = mol_data.get("molecule_structures", [{}])[0].get("canonical_smiles")
                    except Exception:
                        pass
                
                if standard_value is not None:
                    record = {
                        "assay_chembl_id": assay_id,
                        "target_chembl_id": target_id,
                        "molecule_chembl_id": molecule_id,
                        "smiles": smiles,
                        "logPapp": float(standard_value),
                        "units": standard_units,
                        "document_chembl_id": doc.get("document_chembl_id")
                    }
                    records.append(record)
    
    return records

def fetch_all_caco2_data(target_count: int = TARGET_RECORDS) -> List[Dict[str, Any]]:
    """
    Fetches Caco-2 data until target_count records are reached or API exhausted.
    """
    all_records = []
    offset = 0
    logger.info(f"Starting Caco-2 data retrieval. Target: {target_count} records.")
    
    while len(all_records) < target_count:
        page_data = fetch_assay_page(offset=offset, limit=BATCH_SIZE)
        if page_data is None:
            logger.warning("Failed to fetch page. Stopping retrieval.")
            break
        
        page_records = extract_records(page_data)
        if not page_records:
            logger.info("No more records found in this page or subsequent pages.")
            break
        
        all_records.extend(page_records)
        logger.info(f"Fetched {len(page_records)} records. Total: {len(all_records)}. Offset: {offset}")
        
        # Check if we have more pages
        if len(page_records) < BATCH_SIZE:
            # It's possible we got fewer records because we hit the end, 
            # or because many assays didn't have valid docs.
            # We should continue to the next page to see if there are more assays.
            pass 
        
        # Move to next page
        # Note: The API pagination is based on assays, not records. 
        # If we got 0 records from an assay page, we still need to fetch the next assay page.
        # But if we got records, we might still need more assays.
        # We increment offset by the number of assays fetched (which is BATCH_SIZE usually).
        # The 'results' key in page_data contains the assays.
        assays_fetched = len(page_data.get("results", []))
        if assays_fetched == 0:
            break
        
        offset += assays_fetched
        
        # Safety break if we loop too long without progress
        if offset > 10000: # Arbitrary large number to prevent infinite loops if API behaves weirdly
            logger.warning("Offset limit reached. Stopping.")
            break

    return all_records

def write_raw_data(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Writes the raw records to a CSV file.
    """
    if not records:
        logger.warning("No records to write.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["assay_chembl_id", "target_chembl_id", "molecule_chembl_id", "smiles", "logPapp", "units", "document_chembl_id"]
    
    with open(output_path, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    logger.info(f"Wrote {len(records)} records to {output_path}")

def main():
    configure_root_logger()
    project_root = get_project_root()
    output_file = project_root / OUTPUT_DIR / OUTPUT_FILENAME
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Output file: {output_file}")
    
    try:
        records = fetch_all_caco2_data(target_count=TARGET_RECORDS)
        
        if not records:
            logger.error("Retrieved 0 records. Cannot proceed.")
            sys.exit(1)
        
        write_raw_data(records, output_file)
        
        logger.info(f"Retrieval complete. Total records: {len(records)}")
        
        if len(records) < TARGET_RECORDS:
            logger.warning(f"Retrieved {len(records)} records, which is less than the target of {TARGET_RECORDS}.")
        
    except Exception as e:
        logger.error(f"Fatal error during retrieval: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
