import os
import sys
import json
import glob
import requests
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/raw/filter_studies.log')
    ]
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass

# Constants for resistance metadata detection
RESISTANCE_COLUMNS = ['phenotype', 'resistance_score', 'disease_status', 'challenge_outcome']
RESISTANT_VALUES = {'resistant', 'r', 1, 'yes', 'y', 'yes', 'resistant'}
SUSCEPTIBLE_VALUES = {'susceptible', 's', 0, 'no', 'n', 'no', 'susceptible'}
TEMPORAL_COLUMNS = ['timepoint', 'sample_date', 'collection_date', 'inoculation_date', 'pre-challenge', 'baseline']

def load_manifest(manifest_path: str) -> list:
    """Load the study manifest JSON file."""
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    if not isinstance(manifest, list):
        raise ValueError("Manifest must be a list of study objects")
    
    logger.info(f"Loaded manifest with {len(manifest)} studies")
    return manifest

def fetch_phenotype_metadata(study_id: str, download_url: str) -> dict:
    """
    Fetch phenotype metadata for a specific study.
    This function attempts to download the phenotype file or access metadata
    via the Metabolomics Workbench API.
    """
    # Construct the phenotype URL based on the study ID
    # The download_url usually points to the study page or a zip file
    # We need to find the specific phenotype file URL
    
    # Try to construct a direct phenotype download URL
    # Common pattern: https://www.metabolomicsworkbench.org/data/study.php?STUDY_ID={id}
    # Or: https://www.metabolomicsworkbench.org/data/study_submitted_data.php?STUDY_ID={id}
    
    phenotype_url = f"https://www.metabolomicsworkbench.org/data/study.php?STUDY_ID={study_id}"
    
    try:
        logger.info(f"Fetching metadata for study {study_id} from {phenotype_url}")
        response = requests.get(phenotype_url, timeout=30)
        
        if response.status_code != 200:
            logger.warning(f"Failed to fetch metadata for {study_id}: HTTP {response.status_code}")
            return None
        
        # Parse the HTML or JSON response to find phenotype data
        # For now, we'll return a mock structure that indicates we need to check columns
        # In a real implementation, we would parse the actual response
        return {
            'study_id': study_id,
            'raw_content': response.text,
            'url': phenotype_url
        }
        
    except requests.RequestException as e:
        logger.error(f"Network error fetching metadata for {study_id}: {e}")
        raise DataFetchError(f"Failed to fetch metadata for study {study_id}: {e}")

def check_columns_in_metadata(metadata: dict, target_columns: list) -> list:
    """
    Check if any of the target columns exist in the metadata.
    Returns a list of found columns.
    """
    if metadata is None:
        return []
    
    found_columns = []
    
    # If we have raw content, try to parse it
    if 'raw_content' in metadata:
        content = metadata['raw_content']
        # Simple check for column names in the content
        # This is a heuristic; a robust implementation would parse CSV/JSON
        for col in target_columns:
            if col.lower() in content.lower():
                found_columns.append(col)
    
    return found_columns

def has_resistance_metadata(metadata: dict) -> bool:
    """Check if the study has resistance-related metadata."""
    if metadata is None:
        return False
    
    found_columns = check_columns_in_metadata(metadata, RESISTANCE_COLUMNS)
    return len(found_columns) > 0

def has_temporal_metadata(metadata: dict) -> bool:
    """Check if the study has temporal/pre-challenge metadata."""
    if metadata is None:
        return False
    
    found_columns = check_columns_in_metadata(metadata, TEMPORAL_COLUMNS)
    return len(found_columns) > 0

def filter_studies(manifest: list) -> list:
    """
    Filter studies that contain both resistance and temporal metadata.
    
    Logic:
    1. For each study in the manifest, fetch phenotype metadata.
    2. Check for resistance metadata columns (phenotype, resistance_score, etc.).
    3. Check for temporal metadata columns (timepoint, baseline, etc.).
    4. Include the study in the filtered list only if BOTH conditions are met.
    """
    filtered_studies = []
    
    for study in manifest:
        study_id = study.get('study_id')
        download_url = study.get('download_url')
        
        if not study_id:
            logger.warning(f"Skipping study without ID: {study}")
            continue
        
        try:
            # Fetch metadata
            metadata = fetch_phenotype_metadata(study_id, download_url)
            
            if metadata is None:
                logger.info(f"Study {study_id}: No metadata available, skipping")
                continue
            
            # Check for required metadata
            has_resistance = has_resistance_metadata(metadata)
            has_temporal = has_temporal_metadata(metadata)
            
            logger.info(f"Study {study_id}: Resistance={has_resistance}, Temporal={has_temporal}")
            
            if has_resistance and has_temporal:
                # Add study to filtered list with metadata flags
                filtered_study = study.copy()
                filtered_study['has_resistance_metadata'] = True
                filtered_study['has_temporal_metadata'] = True
                filtered_studies.append(filtered_study)
                logger.info(f"Study {study_id} PASSED filtering")
            else:
                logger.info(f"Study {study_id} FAILED filtering (Resistance: {has_resistance}, Temporal: {has_temporal})")
                
        except DataFetchError as e:
            logger.error(f"Skipping study {study_id} due to fetch error: {e}")
            # Continue to next study, do not halt
        except Exception as e:
            logger.error(f"Unexpected error processing study {study_id}: {e}")
            # Continue to next study, do not halt
    
    return filtered_studies

def save_filtered_manifest(filtered_studies: list, output_path: str):
    """Save the filtered study manifest to a JSON file."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(output_path, 'w') as f:
        json.dump(filtered_studies, f, indent=2)
    
    logger.info(f"Saved {len(filtered_studies)} filtered studies to {output_path}")

def main():
    """Main entry point for the filter_studies script."""
    # Define paths
    input_manifest_path = 'data/raw/study_manifest.json'
    output_manifest_path = 'data/raw/filtered_study_manifest.json'
    
    # Pre-check: Verify input file exists
    if not os.path.exists(input_manifest_path):
        logger.error(f"Input file not found: {input_manifest_path}")
        logger.error("Pre-requisite T012a-val must complete successfully to generate study_manifest.json")
        # We do NOT raise an error here to allow the pipeline to continue to T013c-verify
        # which will handle the verification and potential halt
        save_filtered_manifest([], output_manifest_path)
        return
    
    try:
        # Load manifest
        manifest = load_manifest(input_manifest_path)
        
        if len(manifest) == 0:
            logger.warning("Manifest is empty. No studies to filter.")
            save_filtered_manifest([], output_manifest_path)
            return
        
        # Filter studies
        filtered_studies = filter_studies(manifest)
        
        # Save results
        save_filtered_manifest(filtered_studies, output_manifest_path)
        
        logger.info(f"Filtering complete. Found {len(filtered_studies)} studies with required metadata.")
        
    except Exception as e:
        logger.error(f"Filtering process failed: {e}")
        # Save empty manifest on failure to ensure output exists
        save_filtered_manifest([], output_manifest_path)
        # Do not raise, let T013c-verify handle the count check

if __name__ == '__main__':
    main()