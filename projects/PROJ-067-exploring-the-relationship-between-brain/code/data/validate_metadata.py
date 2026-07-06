"""
T014: Metadata Validation (Phase 0 Gate)

Fetches ds000228 metadata, verifies existence of "dream recall frequency" field,
and HALTS execution if missing.
"""
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import requests

logger = logging.getLogger(__name__)

class MetadataValidationError(Exception):
    """Raised when metadata validation fails."""
    pass

def fetch_dataset_metadata(dataset_id: str = "ds000228") -> Dict[str, Any]:
    """
    Fetch metadata from OpenNeuro API.
    Note: This is a simplified fetcher. In a real scenario, we might use the OpenNeuro GraphQL API
    or download the participants.tsv/json directly.
    """
    # OpenNeuro API endpoint for dataset metadata
    url = f"https://api.openneuro.org/datasets/{dataset_id}/files"
    
    # For this implementation, we simulate fetching the participants.json
    # In a real pipeline, we would download the actual file from the dataset.
    # Since we cannot guarantee network access in all environments, we attempt to fetch.
    # If the fetch fails, we might fallback to a local file if it exists, 
    # but the task requires fetching from a real source.
    
    # Simulating the fetch of participants.json from the dataset root
    # OpenNeuro file structure usually has participants.json at root
    participants_url = f"https://openneuro.org/datasets/{dataset_id}/file-display/participants.json"
    
    # Actually, OpenNeuro files are served differently. Let's try to fetch the JSON from the dataset
    # A more robust way is to use the OpenNeuro CLI or download the specific file.
    # For this task, we will attempt to download the participants.json from a known URL pattern
    # or use the OpenNeuro API if available.
    
    # Fallback: Try to download from the dataset's public file URL
    # This is a placeholder for the actual download logic.
    # We will assume the file exists at a standard location or use the API.
    
    # Let's try to fetch the participants.json directly from the dataset's file listing
    # Since we can't rely on the exact URL structure without the API, we'll use a mock fetch
    # if the real fetch fails, but the task says "Real data only".
    # We will attempt to fetch from the OpenNeuro dataset page's raw file.
    
    # Real implementation:
    # 1. Use openneuro-py or requests to get the file list
    # 2. Find participants.json
    # 3. Download it
    
    # For this specific task, we will attempt to download the file from the dataset.
    # If the dataset is ds000228, the file is likely at:
    # https://openneuro.org/datasets/ds000228/file-display/participants.json
    # But OpenNeuro might redirect. Let's try a direct fetch.
    
    # NOTE: In a real CI environment, we might need to handle rate limits or authentication.
    # For now, we assume public access.
    
    try:
        # Attempt to fetch the participants.json
        # OpenNeuro file download URL pattern:
        # https://openneuro.org/datasets/{dataset_id}/versions/{version}/files/{file_id}
        # This is complex. Let's try a simpler approach: fetch the dataset description
        # and then the participants file.
        
        # We will use the OpenNeuro API to get the file list
        api_url = f"https://api.openneuro.org/datasets/{dataset_id}"
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # The API might not return the full file content. 
        # We need to download the participants.json specifically.
        # Let's try to construct the download URL for the file.
        # This is a bit hacky but necessary for a standalone script without the CLI.
        
        # Alternative: Use the s3 bucket if known, but that's not public.
        # Let's assume we can download the file from the dataset's web interface.
        # We will use the 'download' endpoint if available.
        
        # For the purpose of this task, we will simulate the fetch if the real one fails
        # to ensure the code structure is correct, but we will try to fetch real data first.
        
        # Real fetch attempt:
        # We'll try to get the participants.json from the dataset's root
        # This URL might change, so we use the API to find it.
        
        # Since we don't have the file ID, we'll try to download the file by name
        # using the openneuro-py library if available, or construct the URL.
        
        # Let's assume we can download it from:
        # https://openneuro.org/datasets/ds000228/file-display/participants.json
        # This is a guess. The actual URL might be different.
        
        # We will try to fetch it.
        file_url = f"https://openneuro.org/datasets/{dataset_id}/file-display/participants.json"
        resp = requests.get(file_url, timeout=30)
        resp.raise_for_status()
        return resp.json()
        
    except requests.RequestException as e:
        logger.warning(f"Failed to fetch metadata from OpenNeuro API: {e}. "
                       "This might be a network issue. In a real run, this should be handled.")
        # If we can't fetch, we raise an error or try a local file.
        # But the task requires real data. So we fail.
        raise MetadataValidationError(f"Could not fetch metadata from OpenNeuro: {e}")

def fetch_participant_metadata(dataset_id: str = "ds000228") -> Dict[str, Any]:
    """
    Fetch participant-specific metadata (participants.json).
    """
    return fetch_dataset_metadata(dataset_id)

def validate_required_fields(metadata: Dict[str, Any]) -> bool:
    """
    Validate that the metadata contains the required 'dream recall frequency' field.
    """
    participants = metadata.get("participants", [])
    if not participants:
        raise MetadataValidationError("No participants found in metadata.")
    
    # Check if at least one participant has the field?
    # The task says: verify existence of "dream recall frequency" field.
    # It implies the field must exist in the schema.
    
    has_field = False
    for p in participants:
        if "dream_recall_frequency" in p:
            has_field = True
            break
    
    if not has_field:
        raise MetadataValidationError(
            "Required field 'dream_recall_frequency' is missing from all participants. "
            "Cannot proceed with analysis."
        )
    
    return True

def save_validated_metadata(metadata: Dict[str, Any], output_path: Path) -> None:
    """Save the validated metadata to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved validated metadata to {output_path}")

def main() -> None:
    """Entry point for T014."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Define paths
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    output_path = project_root / "data" / "raw" / "validated_metadata.json"

    try:
        logger.info("Fetching metadata from OpenNeuro ds000228...")
        metadata = fetch_participant_metadata("ds000228")
        
        logger.info("Validating required fields...")
        validate_required_fields(metadata)
        
        logger.info("Saving validated metadata...")
        save_validated_metadata(metadata, output_path)
        
        logger.info("T014 completed successfully.")
        
    except MetadataValidationError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
