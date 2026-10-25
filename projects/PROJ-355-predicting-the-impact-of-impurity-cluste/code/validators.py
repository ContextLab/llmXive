"""
Basic validation utility for data source URLs.
"""
import logging
import requests
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Simplified whitelist for the purpose of the pipeline
VALIDATED_SOURCE_WHITELIST = [
    "https://materialsproject.org",
    "https://oqmd.org",
    "https://huggingface.co"
]

def validate_citations(url: str, metadata_path: str) -> Dict[str, Any]:
    """
    Validates a URL against a whitelist and performs a basic connectivity check.
    Returns a dict with 'success' and 'error_code'.
    """
    try:
        # Check whitelist
        if any(domain in url for domain in VALIDATED_SOURCE_WHITELIST):
            # Perform a quick HEAD request to verify the resource exists
            resp = requests.head(url, timeout=5)
            if resp.status_code < 400:
                return {"success": True, "error_code": None}
        
        return {"success": False, "error_code": "URL_INVALID", "message": "URL not in whitelist or unreachable"}
    except Exception as e:
        logger.warning(f"Validation check failed for {url}: {e}")
        return {"success": False, "error_code": "CONNECTION_ERROR", "message": str(e)}
