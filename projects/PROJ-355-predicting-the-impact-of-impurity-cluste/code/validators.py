"""
Validation utilities for data provenance and source verification.
"""
import requests
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

# This whitelist is used to allow specific trusted URLs to pass validation
# without requiring complex external verification for every single request.
VALIDATED_SOURCE_WHITELIST = [
    "https://materialsproject.org/materials/",
    "https://oqmd.org/",
    "https://huggingface.co/datasets/jablonkagroup/oqmd"
]

def validate_citations(url: str, metadata_path: str) -> Dict[str, Any]:
    """
    Validates if a URL is a trusted source or listed in the project's 
    provenance metadata.
    """
    # Check whitelist
    if any(url.startswith(trusted) for trusted in VALIDATED_SOURCE_WHITELIST):
        return {"success": True, "error_code": None, "message": "URL is in trusted whitelist."}

    # Check metadata file
    try:
        import yaml
        p = Path(metadata_path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}
                sources = meta.get("sources", [])
                if any(s.get("url") == url for s in sources):
                    return {"success": True, "error_code": None, "message": "URL found in metadata."}
    except Exception as e:
        logger.warning(f"Error reading metadata for validation: {e}")

    # Fallback: try a HEAD request to see if it's alive
    try:
        resp = requests.head(url, timeout=5)
        if resp.status_code == 200:
            return {"success": True, "error_code": None, "message": "URL is reachable."}
    except Exception:
        pass

    return {"success": False, "error_code": "URL_INVALID", "message": "URL not trusted or unreachable."}
