from typing import Optional, List, Dict, Any, Tuple
from rdkit import Chem
from rdkit.Chem import AllChem
import logging
import requests
import time
import os
import json
from utils import get_logger, retry_with_backoff, load_config_env

logger = get_logger(__name__)

# NIST and Materials Project endpoints (placeholders for real API endpoints)
NIST_API_URL = "https://webbook.nist.gov/cgi/cbook.cgi"
MATERIALS_PROJECT_API_URL = "https://materialsproject.org/rest/v2/materials"

def is_valid_smiles(smiles: str) -> bool:
    """Check if a SMILES string is valid using RDKit."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False

def validate_smiles_and_convert(smiles: str) -> Optional[Chem.Mol]:
    """Validate SMILES and return RDKit Mol object if valid."""
    if not is_valid_smiles(smiles):
        logger.warning(f"Invalid SMILES string: {smiles}")
        return None
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.warning(f"RDKit failed to parse SMILES: {smiles}")
            return None
        return mol
    except Exception as e:
        logger.error(f"Error converting SMILES to Mol: {e}")
        return None

def validate_degradation_label(record: Dict[str, Any]) -> bool:
    """
    Validate presence of explicit 'degradation pathway' label.
    Returns True if the label exists and is non-empty, False otherwise.
    """
    # Check for degradation pathway label in various possible keys
    possible_keys = ['degradation_pathway', 'degradation_label', 'pathway', 'mechanism', 'degradation_mechanism']
    
    for key in possible_keys:
        if key in record:
            label = record[key]
            if label is not None and isinstance(label, str) and label.strip():
                return True
            else:
                logger.debug(f"Record has '{key}' but it is empty or invalid: {label}")
    
    logger.warning(f"Record missing explicit 'degradation pathway' label: {record.get('id', 'unknown')}")
    return False

@retry_with_backoff(max_retries=3)
def download_records_from_nist(query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Download polymer degradation records from NIST Chemistry WebBook.
    Implements rate-limit backoff as per FR-008.
    """
    # This is a placeholder implementation - real implementation would:
    # 1. Construct proper query URL with parameters
    # 2. Make HTTP request with proper headers
    # 3. Parse response (JSON/XML)
    # 4. Extract relevant fields including degradation pathway
    
    logger.info(f"Downloading records from NIST with params: {query_params}")
    
    # Simulate API call with rate limiting
    try:
        # In real implementation, this would be:
        # response = requests.get(NIST_API_URL, params=query_params, timeout=30)
        # response.raise_for_status()
        # data = response.json()
        
        # For now, return empty list as placeholder
        # Real implementation would parse actual NIST response
        return []
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download from NIST: {e}")
        raise

@retry_with_backoff(max_retries=3)
def download_records_from_materials_project(query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Download polymer degradation records from Materials Project API.
    Implements rate-limit backoff as per FR-008.
    """
    # This is a placeholder implementation - real implementation would:
    # 1. Construct proper API URL with authentication
    # 2. Make HTTP request with proper headers and API key
    # 3. Parse response (JSON)
    # 4. Extract relevant fields including degradation pathway
    
    logger.info(f"Downloading records from Materials Project with params: {query_params}")
    
    # Simulate API call with rate limiting
    try:
        # In real implementation, this would be:
        # api_key = load_config_env('MP_API_KEY')
        # headers = {'Authorization': f'Bearer {api_key}'}
        # response = requests.get(MATERIALS_PROJECT_API_URL, params=query_params, headers=headers, timeout=30)
        # response.raise_for_status()
        # data = response.json()
        
        # For now, return empty list as placeholder
        # Real implementation would parse actual Materials Project response
        return []
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download from Materials Project: {e}")
        raise

def filter_records_with_degradation_labels(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter records to keep only those with explicit 'degradation pathway' labels.
    Returns tuple of (valid_records, excluded_records).
    
    This implements the core requirement of T013: validate presence of explicit
    'degradation pathway' labels and EXCLUDE records if missing (FR-008).
    """
    valid_records = []
    excluded_records = []
    
    for record in records:
        if validate_degradation_label(record):
            valid_records.append(record)
        else:
            excluded_records.append(record)
    
    logger.info(f"Filtered records: {len(valid_records)} valid, {len(excluded_records)} excluded due to missing degradation pathway label")
    return valid_records, excluded_records

def main():
    """Main function to demonstrate degradation pathway label validation."""
    # Example records for testing
    test_records = [
        {
            "id": "polymer_001",
            "smiles": "CC(=O)O",
            "degradation_pathway": "hydrolysis",
            "temperature": 25.0,
            "ph": 7.0
        },
        {
            "id": "polymer_002",
            "smiles": "CCO",
            "degradation_label": "oxidation",
            "temperature": 30.0,
            "ph": 6.5
        },
        {
            "id": "polymer_003",
            "smiles": "CCC",
            # Missing degradation pathway label
            "temperature": 20.0,
            "ph": 7.5
        },
        {
            "id": "polymer_004",
            "smiles": "CCCC",
            "pathway": "",  # Empty degradation pathway
            "temperature": 35.0,
            "ph": 6.0
        }
    ]
    
    valid, excluded = filter_records_with_degradation_labels(test_records)
    
    print(f"Valid records: {len(valid)}")
    for record in valid:
        print(f"  - {record['id']}: {record.get('degradation_pathway') or record.get('degradation_label') or record.get('pathway')}")
    
    print(f"Excluded records: {len(excluded)}")
    for record in excluded:
        print(f"  - {record['id']}: Missing degradation pathway label")

if __name__ == "__main__":
    main()