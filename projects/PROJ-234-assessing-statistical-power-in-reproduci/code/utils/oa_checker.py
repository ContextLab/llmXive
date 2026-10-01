"""
Open Access Checker utilities.

Refactored to extract OA-check logic into a shared helper.
"""
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def _check_url_content_type(url: str) -> Optional[str]:
    """
    Helper to fetch the content type of a URL without downloading the full body.
    
    Args:
        url: The URL to check.
        
    Returns:
        The Content-Type header value if successful, None otherwise.
    """
    try:
        # Use HEAD request to avoid downloading the full body
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.headers.get("Content-Type")
    except requests.RequestException as e:
        logger.warning(f"Failed to check content type for {url}: {e}")
        return None

def is_open_access(url: str) -> bool:
    """
    Determine if a publication URL is likely Open Access.
    
    This is a heuristic check based on content type. 
    PDFs and HTML from known OA domains are more likely to be OA.
    For strict DOI checks, use check_doi_oa_status.
    
    Args:
        url: The URL of the publication.
        
    Returns:
        True if likely Open Access, False otherwise.
    """
    if not url:
        return False
        
    content_type = _check_url_content_type(url)
    
    if content_type is None:
        logger.info(f"Could not determine content type for {url}, assuming paywalled.")
        return False
        
    # Heuristic: PDFs and HTML are often OA if accessible via HEAD
    # In a real scenario, we might check specific domains or patterns
    if "pdf" in content_type.lower() or "html" in content_type.lower():
        return True
        
    return False

def check_doi_oa_status(doi: str) -> Dict[str, Any]:
    """
    Check the Open Access status of a DOI using the Crossref/OA API.
    
    Args:
        doi: The DOI string (e.g., '10.1000/xyz').
        
    Returns:
        A dictionary with 'is_open' (bool) and 'license' (str or None).
    """
    if not doi:
        return {"is_open": False, "license": None}
        
    # Normalize DOI
    doi = doi.strip()
    if doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")
    elif doi.startswith("http://doi.org/"):
        doi = doi.replace("http://doi.org/", "")
        
    url = f"https://api.crossref.org/works/{doi}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        message = data.get("message", {})
        license_info = message.get("license", [])
        
        is_open = False
        license_url = None
        
        if license_info:
            # Check for license terms that indicate OA (e.g., CC-BY)
            for lic in license_info:
                if "content-version" in lic or "start" in lic:
                    is_open = True
                    license_url = lic.get("URL")
                    break
                    
        return {"is_open": is_open, "license": license_url}
        
    except requests.RequestException as e:
        logger.error(f"Failed to check OA status for DOI {doi}: {e}")
        return {"is_open": False, "license": None}
    except (ValueError, KeyError) as e:
        logger.error(f"Failed to parse OA response for DOI {doi}: {e}")
        return {"is_open": False, "license": None}
