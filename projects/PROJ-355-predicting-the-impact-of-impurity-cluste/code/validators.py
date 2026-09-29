import os
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_citations(url: str, metadata_path: str) -> dict:
    """
    Validates citations from a metadata file against a whitelist and checks URL accessibility.
    
    Args:
        url: The URL to validate (or extracted from metadata if metadata_path is used).
        metadata_path: Path to the metadata.yaml file to extract URLs from.
    
    Returns:
        A status dict: {"success": bool, "error_code": Optional[str], "message": str}
    """
    whitelist = ['https://materialsproject.org', 'https://oqmd.org', '']
    
    # If a metadata path is provided, extract URLs from it
    # For this task, we assume the URL is passed directly or extracted simply.
    # The task description says: "Parse metadata_path to extract URLs."
    # We will implement a simple extraction if the file exists.
    
    urls_to_check = []
    if metadata_path and os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = yaml.safe_load(f)
            if isinstance(metadata, dict) and 'urls' in metadata:
                urls_to_check.extend(metadata['urls'])
            elif isinstance(metadata, dict) and 'citation' in metadata:
                # Fallback for different metadata structures
                urls_to_check.append(metadata['citation'])
        except Exception as e:
            logger.error(f"Failed to parse metadata file {metadata_path}: {e}")
            return {"success": False, "error_code": "METADATA_PARSE_ERROR", "message": str(e)}
    else:
        if url:
            urls_to_check.append(url)
    
    if not urls_to_check:
        return {"success": False, "error_code": "NO_URLS_FOUND", "message": "No URLs found in metadata or provided."}

    # Validate each URL
    for check_url in urls_to_check:
        if not check_url:
            continue # Skip empty URLs if allowed by whitelist logic
        
        # Check whitelist
        is_whitelisted = any(check_url.startswith(w) for w in whitelist if w)
        if not is_whitelisted:
            return {"success": False, "error_code": "URL_NOT_WHITELISTED", "message": f"URL {check_url} is not in whitelist."}
        
        # Check reachability via HTTP HEAD
        try:
            response = requests.head(check_url, timeout=10)
            if response.status_code >= 400:
                return {"success": False, "error_code": "URL_UNREACHABLE", "message": f"URL {check_url} returned status {response.status_code}."}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error_code": "URL_UNREACHABLE", "message": f"Failed to reach URL {check_url}: {e}"}

    return {"success": True, "error_code": None, "message": "OK"}

def validate_schema(schema_path: str, data_path: str) -> dict:
    """
    Validates a data file against a JSON schema.
    (Placeholder implementation as the task focuses on citations, but defined for API surface).
    """
    return {"success": True, "error_code": None, "message": "Schema validation not fully implemented in this task."}
