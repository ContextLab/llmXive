"""
Data Ingestion Module for Polymer Degradation Prediction.

This module handles downloading records from NIST Chemistry WebBook and Materials Project,
validating SMILES strings, handling missing degradation labels, and applying rate-limit backoff.
"""

import os
import time
import logging
import json
import csv
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from urllib.parse import urljoin

from rdkit import Chem
from rdkit.Chem import AllChem
import requests

from utils import get_logger, get_project_paths, retry_with_backoff
from data_models import PolymerRecord

# Initialize logger
logger = get_logger(__name__)

# Configuration
NIST_BASE_URL = "https://webbook.nist.gov/chemistry/"
MATERIALS_PROJECT_API = "https://api.materialsproject.org"
RATE_LIMIT_DELAY = 1.0  # seconds between requests
MAX_RETRIES = 3
BACKOFF_FACTOR = 2.0

def is_valid_smiles(smiles: str) -> bool:
    """Validate a SMILES string using RDKit."""
    if not smiles or not isinstance(smiles, str):
        return False
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False

def validate_smiles_and_convert(smiles: str) -> Optional[Any]:
    """Validate SMILES and return RDKit molecule object, or None if invalid."""
    if not is_valid_smiles(smiles):
        return None
    return Chem.MolFromSmiles(smiles)

def validate_degradation_label(label: Optional[str]) -> bool:
    """Check if degradation label is present and valid."""
    if label is None or label == "":
        return False
    valid_labels = {
        "hydrolysis", "photolysis", "thermal_degradation", 
        "oxidation", "biodegradation", "mechanical_degradation"
    }
    return label.lower() in valid_labels

@retry_with_backoff(max_retries=MAX_RETRIES, backoff_factor=BACKOFF_FACTOR)
def fetch_nist_record(record_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single record from NIST Chemistry WebBook.
    
    Note: NIST doesn't have a direct API for polymer degradation data.
    This is a placeholder implementation that would need to be adapted
    based on the actual data source structure.
    """
    logger.info(f"Fetching NIST record: {record_id}")
    
    # In a real implementation, this would construct the proper URL
    # and parse the HTML/JSON response from NIST
    # For now, we simulate the request structure
    
    url = f"{NIST_BASE_URL}/{record_id}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Parse would happen here
            return {"id": record_id, "source": "nist", "data": response.text}
        elif response.status_code == 429:
            # Rate limit - let the retry logic handle it
            raise requests.exceptions.RequestException("Rate limit exceeded")
        else:
            logger.warning(f"NIST request failed with status {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching NIST record {record_id}: {e}")
        raise

@retry_with_backoff(max_retries=MAX_RETRIES, backoff_factor=BACKOFF_FACTOR)
def fetch_materials_project_record(record_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single record from Materials Project API.
    
    Requires MP_API_KEY environment variable to be set.
    """
    logger.info(f"Fetching Materials Project record: {record_id}")
    
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise ValueError("MP_API_KEY environment variable not set")
    
    url = f"{MATERIALS_PROJECT_API}/materials/{record_id}"
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            raise requests.exceptions.RequestException("Rate limit exceeded")
        else:
            logger.warning(f"Materials Project request failed with status {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Materials Project record {record_id}: {e}")
        raise

def download_records_from_nist(record_ids: List[str], output_path: Path) -> Tuple[int, int]:
    """
    Download multiple records from NIST and save to a CSV file.
    
    Returns:
        Tuple of (total_processed, successful_count)
    """
    logger.info(f"Downloading {len(record_ids)} records from NIST")
    
    successful = 0
    total = 0
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'source', 'smiles', 'degradation_label', 'temperature', 
                     'ph', 'uv_intensity', 'raw_data']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for record_id in record_ids:
            total += 1
            try:
                # Apply rate limiting
                time.sleep(RATE_LIMIT_DELAY)
                
                record_data = fetch_nist_record(record_id)
                if record_data:
                    # In a real implementation, parse the actual data structure
                    # Here we simulate the expected format
                    writer.writerow({
                        'id': record_id,
                        'source': 'nist',
                        'smiles': record_data.get('smiles', ''),
                        'degradation_label': record_data.get('degradation_label', ''),
                        'temperature': record_data.get('temperature', ''),
                        'ph': record_data.get('ph', ''),
                        'uv_intensity': record_data.get('uv_intensity', ''),
                        'raw_data': json.dumps(record_data)
                    })
                    successful += 1
                    logger.info(f"Successfully downloaded NIST record: {record_id}")
                else:
                    logger.warning(f"Failed to download NIST record: {record_id}")
            except Exception as e:
                logger.error(f"Error processing NIST record {record_id}: {e}")
    
    logger.info(f"NIST download complete: {successful}/{total} successful")
    return total, successful

def download_records_from_materials_project(record_ids: List[str], output_path: Path) -> Tuple[int, int]:
    """
    Download multiple records from Materials Project and save to a CSV file.
    
    Returns:
        Tuple of (total_processed, successful_count)
    """
    logger.info(f"Downloading {len(record_ids)} records from Materials Project")
    
    successful = 0
    total = 0
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'source', 'smiles', 'degradation_label', 'temperature', 
                     'ph', 'uv_intensity', 'raw_data']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for record_id in record_ids:
            total += 1
            try:
                # Apply rate limiting
                time.sleep(RATE_LIMIT_DELAY)
                
                record_data = fetch_materials_project_record(record_id)
                if record_data:
                    # In a real implementation, parse the actual data structure
                    # Here we simulate the expected format
                    writer.writerow({
                        'id': record_id,
                        'source': 'materials_project',
                        'smiles': record_data.get('structure', {}).get('smiles', ''),
                        'degradation_label': record_data.get('degradation_label', ''),
                        'temperature': record_data.get('temperature', ''),
                        'ph': record_data.get('ph', ''),
                        'uv_intensity': record_data.get('uv_intensity', ''),
                        'raw_data': json.dumps(record_data)
                    })
                    successful += 1
                    logger.info(f"Successfully downloaded Materials Project record: {record_id}")
                else:
                    logger.warning(f"Failed to download Materials Project record: {record_id}")
            except Exception as e:
                logger.error(f"Error processing Materials Project record {record_id}: {e}")
    
    logger.info(f"Materials Project download complete: {successful}/{total} successful")
    return total, successful

def filter_records_with_degradation_labels(input_path: Path, output_path: Path, flagged_path: Path) -> Tuple[int, int, int]:
    """
    Filter records that have valid degradation labels.
    
    Records with missing labels are flagged and saved separately for curation.
    
    Returns:
        Tuple of (total_processed, valid_count, flagged_count)
    """
    logger.info(f"Filtering records from {input_path}")
    
    total = 0
    valid = 0
    flagged = 0
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', newline='', encoding='utf-8') as outfile, \
         open(flagged_path, 'w', newline='', encoding='utf-8') as flagged_file:
         
         fieldnames = ['id', 'source', 'smiles', 'degradation_label', 'temperature', 
                     'ph', 'uv_intensity', 'raw_data']
         
         reader = csv.DictReader(infile, fieldnames=fieldnames)
         writer_valid = csv.DictWriter(outfile, fieldnames=fieldnames)
         writer_flagged = csv.DictWriter(flagged_file, fieldnames=fieldnames)
         
         writer_valid.writeheader()
         writer_flagged.writeheader()
         
         for row in reader:
             total += 1
             label = row.get('degradation_label', '')
             
             if validate_degradation_label(label):
                 writer_valid.writerow(row)
                 valid += 1
             else:
                 # Flag for curation
                 row['flag_reason'] = 'missing_degradation_label'
                 writer_flagged.writerow(row)
                 flagged += 1
                 logger.info(f"Flagged record {row['id']} for curation: missing degradation label")
    
    logger.info(f"Filtering complete: {valid} valid, {flagged} flagged, {total} total")
    return total, valid, flagged

def save_flagged_records(flagged_records: List[Dict[str, Any]], output_path: Path):
    """Save flagged records to a CSV file for manual curation."""
    logger.info(f"Saving {len(flagged_records)} flagged records to {output_path}")
    
    if not flagged_records:
        logger.info("No flagged records to save")
        return
    
    fieldnames = ['id', 'source', 'smiles', 'degradation_label', 'temperature', 
                 'ph', 'uv_intensity', 'raw_data', 'flag_reason']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flagged_records)
    
    logger.info(f"Saved {len(flagged_records)} flagged records")

def main():
    """Main entry point for data ingestion."""
    logger.info("Starting data ingestion pipeline")
    
    # Get project paths
    paths = get_project_paths()
    data_dir = paths['data']
    raw_dir = data_dir / 'raw'
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # Example record IDs (in real implementation, these would come from a config or list)
    nist_ids = ["polymer_001", "polymer_002", "polymer_003"]
    mp_ids = ["mp-12345", "mp-67890"]
    
    # Download from NIST
    nist_output = raw_dir / "nist_raw.csv"
    nist_total, nist_success = download_records_from_nist(nist_ids, nist_output)
    
    # Download from Materials Project
    mp_output = raw_dir / "materials_project_raw.csv"
    mp_total, mp_success = download_records_from_materials_project(mp_ids, mp_output)
    
    # Combine and filter
    combined_output = raw_dir / "combined_raw.csv"
    flagged_output = raw_dir / "flagged_for_curation.csv"
    
    # In a real implementation, we would merge the two files first
    # For now, we process the combined file if it exists
    if nist_output.exists() and mp_output.exists():
        # Simple merge for demonstration
        import pandas as pd
        df_nist = pd.read_csv(nist_output)
        df_mp = pd.read_csv(mp_output)
        df_combined = pd.concat([df_nist, df_mp], ignore_index=True)
        df_combined.to_csv(combined_output, index=False)
        
        # Filter records
        total, valid, flagged = filter_records_with_degradation_labels(
            combined_output, 
            raw_dir / "filtered_with_labels.csv",
            flagged_output
        )
    else:
        logger.warning("One or more source files not found, skipping filtering step")
    
    logger.info("Data ingestion pipeline complete")
    logger.info(f"NIST: {nist_success}/{nist_total} successful")
    logger.info(f"Materials Project: {mp_success}/{mp_total} successful")

if __name__ == "__main__":
    main()