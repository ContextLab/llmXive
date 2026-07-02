"""
Open Access Checker Module.

Validates Open Access status of publication links using DOI content-type checks.
"""
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def is_open_access(url: str, timeout: int = 10) -> bool:
    """
    Check if a publication URL is Open Access.
    
    Uses the Crossref/DOI content negotiation or a direct HEAD/GET request
    to determine if the resource is freely accessible.
    
    Args:
        url: The publication URL (ideally containing a DOI).
        timeout: Request timeout in seconds.
        
    Returns:
        True if the resource appears to be Open Access, False otherwise.
    """
    if not url:
        logger.warning("Empty URL provided to OA checker.")
        return False

    # Strategy: Try to fetch the URL with a specific Accept header for HTML.
    # If we get a 200 OK and the content type is HTML (or text), it's likely OA.
    # If we get 403, 401, or a redirect to a login/paywall page, it's not.
    
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "User-Agent": "Mozilla/5.0 (compatible; llmXive-OA-Checker/1.0)"
    }

    try:
        # Use HEAD first if possible to save bandwidth, but some servers behave differently.
        # We'll use GET with stream=True to check the response quickly.
        logger.info(f"Checking OA status for: {url}")
        
        # Some publishers block non-browser user agents or require specific headers.
        # We rely on the fact that OA articles usually return 200 immediately.
        # Paywalled articles often return 200 but redirect to a login, or return 403.
        # A robust check often involves looking for "login" or "subscription" in the URL
        # or response, but the primary signal here is the HTTP status and content type.
        
        # Let's try a GET request with a short timeout.
        # If the URL is a DOI resolver (dx.doi.org), it redirects. We need to follow redirects.
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        # Check status code
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '').lower()
            # If it's HTML or text, it's likely the article page itself (OA)
            if 'text/html' in content_type or 'text/plain' in content_type:
                # Additional heuristic: check for common paywall indicators in the URL
                # or response text if we were to parse it, but for this task,
                # a successful 200 with HTML content is a strong signal of OA availability
                # compared to a 403 or a redirect to a login page (which usually ends in 200
                # on the login page, but the URL changes).
                
                # Check if the final URL still looks like a publisher page and not a login page
                final_url = response.url.lower()
                if 'login' in final_url or 'signin' in final_url or 'access' in final_url:
                    logger.info(f"URL redirected to a login/access page: {final_url}")
                    return False
                
                logger.info(f"URL is accessible (Status 200, Content-Type: {content_type})")
                return True
            else:
                # Might be a PDF or other file, which is also OA if accessible
                logger.info(f"URL is accessible (Status 200, Content-Type: {content_type})")
                return True
        else:
            # 403, 401, 404 usually mean not accessible
            logger.warning(f"OA check failed for {url}: Status {response.status_code}")
            return False

    except requests.exceptions.Timeout:
        logger.error(f"Request timed out for {url}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking OA status for {url}: {e}")
        return False

# For testing purposes, a simple mockable function could be wrapped, 
# but the implementation above is the real logic.