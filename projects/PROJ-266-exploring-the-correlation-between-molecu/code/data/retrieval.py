"""
Data Retrieval Module.

This module fetches Caco-2 permeability data from the ChEMBL REST API,
filters for valid records, and saves the raw data to a CSV file.
It implements exponential backoff for rate limit errors and invokes
the checksum utility after saving.
"""

import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

from utils.logging import get_logger
from utils.config import get_project_root

logger = get_logger(__name__)

CHEMBL_API_BASE = "https://www.ebi.ac.uk/chembl/ws"
MAX_RETRIES = 3
INITIAL_DELAY = 5  # seconds
MAX_DELAY = 30  # seconds

def fetch_assay_page(offset: int = 0, limit: int = 100) -> Optional[Dict[str, Any]]:
    """
    Fetch a single page of assays from ChEMBL API.

    Args:
        offset: Pagination offset.
        limit: Number of records per page.

    Returns:
        JSON response or None if failed after retries.
    """
    url = f"{CHEMBL_API_BASE}/assays"
    params = {
        'assay_type': 'Caco-2',
        'standard_type': 'MEASUREMENT',
        'format': 'json',
        'limit': limit,
        'offset': offset
    }

    attempt = 0
    delay = INITIAL_DELAY

    while attempt < MAX_RETRIES:
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:  # Too Many Requests
                attempt += 1
                if attempt < MAX_RETRIES:
                    logger.warning(f"Rate limited. Retrying in {delay} seconds... (Attempt {attempt}/{MAX_RETRIES})")
                    time.sleep(delay)
                    delay = min(delay * 2, MAX_DELAY)  # Exponential backoff
                else:
                    logger.error("Max retries exceeded due to rate limiting.")
                    return None
            else:
                logger.error(f"HTTP error: {e}")
                return None
        except requests.exceptions.RequestException as e:
            attempt += 1
            if attempt < MAX_RETRIES:
                logger.warning(f"Request failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay = min(delay * 2, MAX_DELAY)
            else:
                logger.error("Max retries exceeded due to network error.")
                return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None

    return None

def extract_records(page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract relevant records from a ChEMBL API page.

    Args:
        page_data: JSON response from API.

    Returns:
        List of extracted records.
    """
    records = []
    assays = page_data.get('assays', [])

    for assay in assays:
        # Extract basic assay info
        assay_id = assay.get('assay_id')
        assay_chembl_id = assay.get('chembl_id')
        organism = assay.get('organism', {})
        organism_name = organism.get('scientific_name') if organism else None

        # Extract target info if available
        targets = assay.get('targets', [])
        target_organism = None
        if targets:
            target = targets[0]
            target_organism = target.get('organism', {}).get('scientific_name')

        # Extract documents info if available
        documents = assay.get('documents', [])
        doc_id = None
        if documents:
            doc_id = documents[0].get('doc_id')

        # Extract standard values if available
        # Note: We need to get the actual measurements from the 'activities' endpoint
        # For now, we'll store the assay metadata and assume we'll fetch activities later
        # But the task asks for records with logPapp, so we need to fetch activities

        # Actually, let's fetch the activities for this assay
        activities_url = f"{CHEMBL_API_BASE}/activities"
        activity_params = {
            'assay_id': assay_id,
            'standard_type': 'MEASUREMENT',
            'standard_units': 'logM',
            'format': 'json',
            'limit': 1000  # Fetch all activities for this assay
        }

        try:
            activity_response = requests.get(activities_url, params=activity_params, timeout=30)
            activity_response.raise_for_status()
            activity_data = activity_response.json()
            activities = activity_data.get('activities', [])

            for activity in activities:
                # Extract the required fields
                smiles = activity.get('molecule_structures', {}).get('canonical_smiles')
                logpapp = activity.get('standard_value')
                standard_units = activity.get('standard_units')
                standard_type = activity.get('standard_type')
                relation = activity.get('relation')
                comment = activity.get('comment')

                # Only include if we have SMILES and logPapp
                if smiles and logpapp is not None:
                    # Create protocol_metadata object
                    protocol_metadata = {
                        'standard_type': standard_type,
                        'heterogeneity_score': 0.0,  # Placeholder, will be calculated later
                        'assay_id': assay_id,
                        'assay_chembl_id': assay_chembl_id,
                        'organism': organism_name,
                        'target_organism': target_organism,
                        'doc_id': doc_id,
                        'standard_units': standard_units,
                        'relation': relation,
                        'comment': comment
                    }

                    record = {
                        'smiles': smiles,
                        'logPapp': float(logpapp),
                        'assay_id': str(assay_id),
                        'protocol_metadata': json.dumps(protocol_metadata)  # Serialize as JSON string
                    }
                    records.append(record)

        except Exception as e:
            logger.warning(f"Failed to fetch activities for assay {assay_id}: {e}")
            continue

    return records

def fetch_all_caco2_data(min_records: int = 600) -> List[Dict[str, Any]]:
    """
    Fetch all Caco-2 data from ChEMBL API until we have at least min_records.

    Args:
        min_records: Minimum number of records to fetch.

    Returns:
        List of all fetched records.
    """
    all_records = []
    offset = 0
    limit = 100

    logger.info(f"Starting to fetch Caco-2 data. Target: {min_records} records.")

    while len(all_records) < min_records:
        logger.info(f"Fetching page at offset {offset}...")
        page_data = fetch_assay_page(offset=offset, limit=limit)

        if page_data is None:
            logger.error("Failed to fetch page. Stopping.")
            break

        records = extract_records(page_data)
        all_records.extend(records)

        logger.info(f"Fetched {len(records)} records. Total: {len(all_records)}")

        # Check if we've reached the end of the data
        if len(page_data.get('assays', [])) == 0:
            logger.info("No more assays found. Stopping.")
            break

        # Move to next page
        offset += limit

        # Safety break to avoid infinite loops
        if offset > 10000:  # Arbitrary large number
            logger.warning("Reached offset limit. Stopping.")
            break

    logger.info(f"Total records fetched: {len(all_records)}")
    return all_records

def write_raw_data(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write records to a CSV file.

    Args:
        records: List of records to write.
        output_path: Path to the output CSV file.
    """
    if not records:
        logger.warning("No records to write.")
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ['smiles', 'logPapp', 'assay_id', 'protocol_metadata']

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Wrote {len(records)} records to {output_path}")

def invoke_checksum_utility() -> None:
    """
    Invoke the checksum utility to generate checksums for the saved data.
    """
    logger.info("Invoking checksum utility...")
    try:
        from utils.checksum import scan_and_register_data_files
        scan_and_register_data_files()
        logger.info("Checksum utility completed successfully.")
    except Exception as e:
        logger.error(f"Failed to invoke checksum utility: {e}")

def main():
    """
    Main entry point for data retrieval.
    """
    logger.info("Starting data retrieval process.")

    project_root = get_project_root()
    output_path = project_root / 'data' / 'raw' / 'chembl_raw.csv'

    # Fetch data
    records = fetch_all_caco2_data(min_records=600)

    if not records:
        logger.error("No records fetched. Exiting.")
        sys.exit(1)

    # Write to CSV
    write_raw_data(records, output_path)

    # Invoke checksum utility
    invoke_checksum_utility()

    logger.info("Data retrieval process completed.")

if __name__ == '__main__':
    main()
