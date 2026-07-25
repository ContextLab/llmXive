"""
Open Access checker for publication links and DOIs.
"""
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def is_open_access(url: str) -> bool:
    """
    Check if a URL points to an Open Access resource.
    
    Uses a HEAD request to check content-type and status.
    Falls back to a GET request if HEAD is not supported or fails.
    
    Args:
        url: The URL of the publication.
        
    Returns:
        True if the resource appears to be Open Access (200 OK and appropriate content type),
        False otherwise.
    """
    if not url:
        return False

    headers = {
        "User-Agent": "llmXive-Research-Agent/1.0",
        "Accept": "application/json, application/pdf, text/html, application/xml"
    }

    try:
        # Try HEAD first
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        
        # If HEAD fails or returns 405 (Method Not Allowed), try GET
        if response.status_code == 405:
            logger.warning(f"HEAD not allowed for {url}, trying GET")
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "").lower()
            # Check for common OA indicators
            if any(indicator in content_type for indicator in [
                "application/pdf", 
                "application/json", 
                "text/html", 
                "application/xml"
            ]):
                # Additional check: if it's HTML, look for OA indicators in headers or body?
                # For now, successful 200 with reasonable content type is a good heuristic
                # for a reachable resource. True OA often involves specific licenses,
                # but simple accessibility is the first filter.
                return True
            else:
                logger.debug(f"Content-Type {content_type} not recognized as OA for {url}")
                return False
        else:
            logger.debug(f"Non-200 status {response.status_code} for {url}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return False

def check_doi_oa_status(doi: str) -> Dict[str, Any]:
    """
    Check Open Access status for a DOI using the Unpaywall or similar API.
    Since we don't have an API key for Unpaywall in this simple setup,
    we will use the Crossref DOI resolution to check content type.
    
    Args:
        doi: The DOI string.
        
    Returns:
        A dictionary with 'status' (open_access, closed_access, unknown) and 'url'.
    """
    if not doi:
        return {"status": "unknown", "url": None}

    # Crossref DOI resolution
    # https://doi.org/10.1000/182
    url = f"https://doi.org/{doi}"
    headers = {
        "User-Agent": "llmXive-Research-Agent/1.0",
        "Accept": "application/json"
    }

    try:
        # Follow redirects to get the final URL
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        final_url = response.url
        
        if response.status_code == 200:
            # Check if the final URL is a known OA repository or if the content type suggests OA
            # A more robust check would use Unpaywall API, but for this implementation:
            # If it resolves to a PDF or a journal page that is accessible, we assume OA for the purpose of this pipeline's "fetchable" check.
            # However, strictly speaking, we should check the "license" in Crossref metadata.
            # Let's try to fetch Crossref metadata.
            
            # Alternative: Use Crossref API for metadata
            metadata_url = f"https://api.crossref.org/works/{doi}"
            meta_resp = requests.get(metadata_url, headers=headers, timeout=10)
            
            if meta_resp.status_code == 200:
                data = meta_resp.json()
                if "message" in data:
                    message = data["message"]
                    # Check for open-access field
                    if "is-oa" in message:
                        is_oa = message.get("is-oa", False)
                        status = "open_access" if is_oa else "closed_access"
                        return {
                            "status": status,
                            "url": final_url,
                            "source": "crossref"
                        }
            return {"status": "unknown", "url": final_url}
        else:
            return {"status": "unknown", "url": None}

    except requests.exceptions.RequestException as e:
        logger.error(f"DOI check failed for {doi}: {e}")
        return {"status": "unknown", "url": None}
