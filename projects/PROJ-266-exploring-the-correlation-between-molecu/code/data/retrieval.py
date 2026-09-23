"""
Data Retrieval Module for Caco-2 Permeability Dataset.

This module fetches raw Caco-2 assay data from the ChEMBL REST API,
applies exponential backoff for rate limiting, and saves the results
to a CSV file. It also invokes the checksum utility to ensure data integrity.
"""

import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

# Import local utilities
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

# Import checksum utility functions
from utils.checksum import scan_and_register_data_files

logger = get_logger(__name__)

# ChEMBL API Configuration
CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/api/data/assay.json"
MAX_RETRIES = 3
INITIAL_DELAY = 5  # seconds
MAX_DELAY = 30     # seconds

def fetch_assay_page(offset: int = 0, limit: int = 100) -> Optional[Dict[str, Any]]:
    """
    Fetch a single page of assay data from ChEMBL with exponential backoff.

    Args:
        offset: Pagination offset.
        limit: Number of records per page.

    Returns:
        JSON response dict or None if failed after retries.
    """
    params = {
        'format': 'json',
        'offset': offset,
        'limit': limit,
        'assay_type': 'Caco-2',
        'standard_type': 'MEASUREMENT'
    }

    delay = INITIAL_DELAY
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Fetching assay page (offset={offset}, attempt={attempt + 1})")
            response = requests.get(CHEMBL_API_BASE, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limited
                logger.warning(f"Rate limited (429). Waiting {delay}s before retry...")
                time.sleep(delay)
                delay = min(delay * 2, MAX_DELAY)
            else:
                logger.error(f"API returned status {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error on attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(delay)
                delay = min(delay * 2, MAX_DELAY)
            else:
                return None

    logger.error(f"Failed to fetch page after {MAX_RETRIES} attempts.")
    return None

def extract_records(api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract relevant records from the ChEMBL API response.

    Args:
        api_response: JSON response from ChEMBL API.

    Returns:
        List of processed record dictionaries.
    """
    records = []
    assays = api_response.get('assays', [])

    for assay in assays:
        # Extract basic assay info
        assay_id = assay.get('assay_id')
        mol_synonyms = assay.get('mol_synonyms', [])
        target_pref_name = assay.get('target_pref_name', '')
        
        # Extract measurements
        measurements = assay.get('measurements', [])
        
        for measurement in measurements:
            # We need the standard_value and standard_units for logPapp
            standard_value = measurement.get('standard_value')
            standard_units = measurement.get('standard_units')
            standard_relation = measurement.get('standard_relation', '=')
            molecule_chembl_id = measurement.get('molecule_chembl_id')
            document_chembl_id = measurement.get('document_chembl_id')
            
            # Extract SMILES from molecule if available
            # Note: The measurement endpoint might not have SMILES directly.
            # We often need to fetch the molecule separately or rely on the assay's molecule_synonyms.
            # For this task, we will attempt to fetch the molecule details if the SMILES is missing
            # or construct a record that flags it. However, the task requires SMILES.
            # Strategy: Fetch molecule details via the molecule_chembl_id if SMILES is not in the assay context.
            # To keep it efficient, we'll fetch the molecule record once per unique molecule_chembl_id.
            # But for simplicity in this single-file script, we will do a lazy fetch or rely on the API
            # returning the molecule data if we request it. The ChEMBL API for measurements usually links to the molecule.
            # Let's try to fetch the molecule details for the specific measurement.
            
            smiles = None
            if molecule_chembl_id:
                # Fetch molecule details to get SMILES
                mol_url = f"https://www.ebi.ac.uk/chembl/api/data/molecule/{molecule_chembl_id}.json"
                try:
                    mol_resp = requests.get(mol_url, timeout=10)
                    if mol_resp.status_code == 200:
                        mol_data = mol_resp.json()
                        smiles = mol_data.get('molecule_structures', [{}])[0].get('canonical_smiles')
                except Exception as e:
                    logger.warning(f"Failed to fetch molecule {molecule_chembl_id}: {e}")

            # Protocol Metadata: Construct from assay and measurement details
            # The schema requires: lab_id, temperature, passage
            protocol_metadata = {
                'lab_id': assay.get('src_id') or 'unknown',
                'temperature': measurement.get('standard_value_units') if measurement.get('standard_value_units') else (assay.get('assay_description', '').split('Temp: ')[1].split()[0] if 'Temp:' in assay.get('assay_description', '') else None),
                'passage': None, # Often not explicitly in standard API, set to null or parse from description
                'assay_type': assay.get('assay_type'),
                'assay_organism': assay.get('assay_organism'),
                'assay_cell_type': assay.get('assay_cell_type')
            }
            
            # Attempt to parse temperature from description if not explicit
            desc = assay.get('assay_description', '')
            if 'Temperature' in desc or 'Temp' in desc:
                # Simple heuristic parsing
                parts = desc.split()
                for i, part in enumerate(parts):
                    if 'Temp' in part or 'Temperature' in part:
                        # Look for number nearby
                        for p in parts[i:i+3]:
                            if any(c.isdigit() for c in p):
                                try:
                                    val = float(p.replace('°', '').replace('C', ''))
                                    protocol_metadata['temperature'] = val
                                except ValueError:
                                    pass
                                break

            record = {
                'smiles': smiles,
                'logPapp': float(standard_value) if standard_value and standard_units in ['cm/s', 'log cm/s'] else None,
                'mw': None, # Will be computed later or fetched if needed, but schema says number. 
                            # We can compute MW from SMILES if we have RDKit, but for raw retrieval we might leave null or fetch.
                            # For now, we leave as None or compute if we have the SMILES.
                'psa': None,
                'assay_id': f"{assay_id}_{measurement.get('measurement_id', '')}",
                'protocol_metadata': json.dumps(protocol_metadata) # Serialize as JSON string
            }

            # Compute MW if SMILES is available (using RDKit if available, else None)
            if smiles:
                try:
                    from rdkit import Chem
                    mol = Chem.MolFromSmiles(smiles)
                    if mol:
                        record['mw'] = sum(Chem.GetFormalCharge(mol.GetAtomWithIdx(i).GetMass() if hasattr(Chem.GetAtomWithIdx(i), 'GetMass') else 0) for i in range(mol.GetNumAtoms())) # Fallback to simple mass if available
                        # RDKit does not have a direct 'mass' property on atoms in standard installation without explicit calculation
                        # Let's use a simpler approach: use the molecular weight function if available
                        from rdkit.Chem import Descriptors
                        record['mw'] = Descriptors.MolWt(mol)
                        
                        # Compute PSA if available
                        record['psa'] = Descriptors.TPSA(mol)
                except Exception as e:
                    logger.debug(f"Could not compute MW/PSA for {smiles}: {e}")

            records.append(record)

    return records

def fetch_all_caco2_data(target_count: int = 600) -> List[Dict[str, Any]]:
    """
    Fetch all Caco-2 data until target count is reached or API exhausted.

    Args:
        target_count: Minimum number of records to fetch.

    Returns:
        List of all collected records.
    """
    all_records = []
    offset = 0
    limit = 100
    batch_count = 0

    while len(all_records) < target_count:
        response = fetch_assay_page(offset=offset, limit=limit)
        if not response:
            logger.warning("API returned no data or failed. Stopping fetch.")
            break

        records = extract_records(response)
        if not records:
            logger.info("No more records found in response.")
            break

        all_records.extend(records)
        batch_count += 1
        logger.info(f"Fetched batch {batch_count}: {len(records)} records. Total: {len(all_records)}")

        # Check if we have more pages
        if 'assays' not in response or len(response['assays']) < limit:
            logger.info("Reached end of API results.")
            break

        offset += limit

    logger.info(f"Total records fetched: {len(all_records)}")
    return all_records

def write_raw_data(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write records to a CSV file.

    Args:
        records: List of record dictionaries.
        output_path: Path to the output CSV file.
    """
    if not records:
        logger.warning("No records to write.")
        return

    fieldnames = ['smiles', 'logPapp', 'mw', 'psa', 'assay_id', 'protocol_metadata']
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Wrote {len(records)} records to {output_path}")

def invoke_checksum_utility() -> None:
    """
    Invoke the checksum utility to generate checksums for data files.
    """
    logger.info("Invoking checksum utility...")
    try:
        scan_and_register_data_files()
        logger.info("Checksum utility completed successfully.")
    except Exception as e:
        logger.error(f"Failed to run checksum utility: {e}")
        raise

def main():
    """
    Main entry point for data retrieval.
    """
    configure_root_logger()
    project_root = get_project_root()
    output_path = project_root / 'data' / 'raw' / 'chembl_raw.csv'

    logger.info("Starting Caco-2 data retrieval from ChEMBL.")
    
    try:
        records = fetch_all_caco2_data(target_count=600)
        
        if len(records) < 600:
            logger.warning(f"Only fetched {len(records)} records, which is less than the target of 600.")
        else:
            logger.info(f"Successfully fetched {len(records)} records (>= 600).")

        write_raw_data(records, output_path)
        
        if output_path.exists():
            invoke_checksum_utility()
        else:
            logger.error("Output file was not created.")
            
    except Exception as e:
        logger.critical(f"Retrieval process failed: {e}")
        sys.exit(1)

    logger.info("Data retrieval and checksum generation completed.")

if __name__ == '__main__':
    main()
