"""
Authentication Manager for LSMS-ISA and related data sources.

This module handles authentication logic for the World Bank LSMS-ISA API,
including token validation and error handling.
"""

import os
import logging
import requests
from typing import Optional

from src.utils.io_helpers import FatalError

logger = logging.getLogger(__name__)

# World Bank API base URL for LSMS-ISA
# The World Bank Open Data API is generally used for metadata and survey info.
# Authentication is typically required for restricted microdata or specific endpoints.
# We validate the token by attempting a simple metadata fetch that requires auth
# or by checking the token format against known patterns if the endpoint is public but token-restricted.
# For this implementation, we assume the token is required for the specific microdata endpoint.
# A common validation endpoint is the user info or a specific survey list that requires auth.
# Since LSMS-ISA microdata often requires a specific token for download, we validate against
# a known public endpoint that accepts the token or a metadata endpoint.
# If the token is invalid, the API returns 401 or 403.

# Using a generic World Bank API endpoint that might require auth or validates the token context.
# Alternatively, we can check if the token is non-empty and format-compliant, then attempt a 
# specific LSMS-ISA metadata request if available.
# For robustness, we will attempt to fetch a specific survey list or metadata that requires the token.
# If the token is invalid, we raise FatalError.

# Note: The exact endpoint for token validation might vary. 
# Using a standard World Bank API endpoint for demonstration of auth check.
# In a real scenario, this would be the specific LSMS-ISA microdata access endpoint.
# We will use a metadata endpoint that lists surveys, which typically requires auth for specific regions.
LSMS_API_BASE = "https://microdata.worldbank.org/index.php/api"
# Endpoint to list surveys (might require auth token in header for restricted access)
LSMS_SURVEY_LIST_ENDPOINT = f"{LSMS_API_BASE}/v1/surveys"

def validate_lsms_token(token: str) -> bool:
    """
    Validates the provided LSMS-ISA token against the World Bank API.
    
    Args:
        token: The API token string.
        
    Returns:
        True if the token is valid.
        
    Raises:
        FatalError: If the token is missing, invalid, or the API request fails.
    """
    if not token:
        raise FatalError("LSMS-ISA token is missing. Please set the WB_LSMS_TOKEN environment variable.")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        # Attempt to fetch a small piece of metadata to validate the token.
        # If the token is invalid, the API should return 401/403.
        # We use a timeout to avoid hanging.
        response = requests.get(LSMS_SURVEY_LIST_ENDPOINT, headers=headers, timeout=10)
        
        if response.status_code == 200:
            logger.info("LSMS-ISA token validation successful.")
            return True
        elif response.status_code in (401, 403):
            logger.error(f"LSMS-ISA token validation failed: {response.status_code} {response.text}")
            raise FatalError(f"Invalid LSMS-ISA token. API returned {response.status_code}. Please check WB_LSMS_TOKEN.")
        else:
            # Other errors might be network issues or API unavailability
            logger.warning(f"LSMS-ISA API returned unexpected status {response.status_code}: {response.text}")
            # We might want to be strict here and fail, or warn and proceed if the token format is valid.
            # Given the task requirement to "raise a FatalError if invalid", we assume non-200 means invalid in this context
            # if the endpoint is expected to work.
            raise FatalError(f"LSMS-ISA token validation failed with status {response.status_code}.")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during LSMS-ISA token validation: {e}")
        # If we can't reach the API, we can't validate. 
        # Depending on policy, we might fail or warn. 
        # Given "raise FatalError if invalid", and we can't verify validity, 
        # we should probably fail to be safe, or at least log strongly.
        # However, if the API is down, the token might still be valid.
        # But the task says "validate token against World Bank API". If API is unreachable, validation fails.
        raise FatalError(f"Could not connect to World Bank API to validate token: {e}")

def get_lsms_token() -> str:
    """
    Retrieves the LSMS-ISA token from the environment variable.
    
    Returns:
        The token string.
        
    Raises:
        FatalError: If the token is not set.
    """
    token = os.getenv("WB_LSMS_TOKEN")
    if not token:
        raise FatalError("WB_LSMS_TOKEN environment variable is not set.")
    return token

def validate_lsms_credentials() -> None:
    """
    Main entry point to validate LSMS-ISA credentials.
    
    Reads the token from the environment, validates it against the API,
    and raises FatalError if validation fails.
    """
    token = get_lsms_token()
    if not validate_lsms_token(token):
        # This path should theoretically be unreachable if validate_lsms_token raises on failure,
        # but kept for safety if logic changes.
        raise FatalError("LSMS-ISA credentials validation failed.")

def main() -> None:
    """
    CLI entry point for testing token validation.
    """
    try:
        validate_lsms_credentials()
        print("LSMS-ISA authentication validated successfully.")
    except FatalError as e:
        print(f"Fatal Error: {e}")
        raise

if __name__ == "__main__":
    main()
