"""
Authentication Manager for LSMS-ISA and Copernicus Data Space Ecosystem.

This module handles the retrieval, validation, and token refresh logic
for external data providers required by the pipeline.

It strictly adheres to the "Fail Loudly" principle: if credentials are
missing or invalid, it raises a FatalError immediately rather than
attempting silent fallbacks.
"""
import os
import sys
import time
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import requests

# Import local project utilities
# Note: Using relative import structure based on project plan
try:
    from src.utils.io_helpers import FatalError
except ImportError:
    # Fallback for direct execution or different import context
    class FatalError(Exception):
        """Custom exception for fatal pipeline errors."""
        pass


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Constants for API endpoints
WB_LSMS_API_BASE = "https://microdata.worldbank.org/api/v1"
WB_TOKEN_VALIDATION_ENDPOINT = f"{WB_LSMS_API_BASE}/auth/me"

CDS_API_BASE = "https://cds-api.ecmwf.int/api"
CDS_TOKEN_ENDPOINT = f"{CDS_API_BASE}/authentication"
CDS_TOKEN_REFRESH_INTERVAL = 3600  # 1 hour in seconds


class AuthManager:
    """
    Manages authentication tokens for World Bank LSMS-ISA and Copernicus Data Space.
    
    Attributes:
        wb_token (str | None): Validated World Bank token.
        cds_token (str | None): Validated Copernicus token.
        cds_token_expires_at (float | None): Unix timestamp when CDS token expires.
    """

    def __init__(self):
        self.wb_token: Optional[str] = None
        self.cds_token: Optional[str] = None
        self.cds_token_expires_at: Optional[float] = None
        
        self._validate_environment()

    def _validate_environment(self) -> None:
        """
        Validates that required environment variables are present.
        Raises FatalError immediately if any are missing.
        """
        missing_vars = []

        if not os.getenv("WB_LSMS_TOKEN"):
            missing_vars.append("WB_LSMS_TOKEN")
        
        if not os.getenv("CDS_USERNAME"):
            missing_vars.append("CDS_USERNAME")
        
        if not os.getenv("CDS_PASSWORD"):
            missing_vars.append("CDS_PASSWORD")

        if missing_vars:
            raise FatalError(
                f"CRITICAL: Missing required environment variables: {', '.join(missing_vars)}. "
                "Please configure your credentials as per the quickstart guide."
            )

        logger.info("Environment variables found.")

    def get_wb_token(self, force_refresh: bool = False) -> str:
        """
        Retrieves and validates the World Bank LSMS-ISA token.
        
        Args:
            force_refresh: If True, re-validates the token against the API.
        
        Returns:
            str: The validated token string.
        
        Raises:
            FatalError: If the token is invalid or the API validation fails.
        """
        if self.wb_token and not force_refresh:
            return self.wb_token

        token = os.getenv("WB_LSMS_TOKEN")
        if not token:
            raise FatalError("WB_LSMS_TOKEN is missing from environment.")

        logger.info("Validating World Bank LSMS-ISA token...")
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(WB_TOKEN_VALIDATION_ENDPOINT, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self.wb_token = token
                logger.info("World Bank token validated successfully.")
                return token
            else:
                raise FatalError(
                    f"World Bank token validation failed with status {response.status_code}. "
                    f"Response: {response.text}. Please check your WB_LSMS_TOKEN."
                )
        except requests.exceptions.RequestException as e:
            raise FatalError(f"Failed to connect to World Bank API for token validation: {e}")

    def _get_cds_credentials(self) -> Tuple[str, str]:
        """
        Retrieves CDS username and password from environment.
        
        Returns:
            Tuple[str, str]: (username, password)
        """
        return os.getenv("CDS_USERNAME"), os.getenv("CDS_PASSWORD")

    def _fetch_cds_token(self) -> str:
        """
        Fetches a new access token from the Copernicus Data Space Ecosystem.
        
        Returns:
            str: The access token.
        
        Raises:
            FatalError: If authentication fails.
        """
        username, password = self._get_cds_credentials()
        
        logger.info("Fetching new Copernicus Data Space token...")
        
        payload = {
            "username": username,
            "password": password
        }
        
        try:
            response = requests.post(CDS_TOKEN_ENDPOINT, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                # The API typically returns {'access_token': '...'}
                token = data.get("access_token")
                if not token:
                    raise FatalError("Copernicus API returned 200 but no access_token in response.")
                
                # Assume standard JWT expiration logic or set a safe default if not provided
                # For now, we set a hardcoded expiration of 1 hour from now
                self.cds_token_expires_at = time.time() + CDS_TOKEN_REFRESH_INTERVAL
                logger.info("Copernicus token fetched successfully.")
                return token
            else:
                # Handle specific CDS error messages if available
                error_detail = response.text
                raise FatalError(
                    f"Copernicus authentication failed with status {response.status_code}. "
                    f"Details: {error_detail}. Check CDS_USERNAME and CDS_PASSWORD."
                )
        except requests.exceptions.RequestException as e:
            raise FatalError(f"Failed to connect to Copernicus API: {e}")

    def get_cds_token(self, force_refresh: bool = False) -> str:
        """
        Retrieves the Copernicus token, refreshing if necessary or expired.
        
        Args:
            force_refresh: If True, ignores cache and fetches a new token.
        
        Returns:
            str: The valid access token.
        
        Raises:
            FatalError: If token refresh fails.
        """
        # Check if we have a valid cached token
        if self.cds_token and self.cds_token_expires_at:
            if not force_refresh and time.time() < self.cds_token_expires_at:
                return self.cds_token
        
        # Token is missing or expired, fetch new one
        new_token = self._fetch_cds_token()
        self.cds_token = new_token
        return new_token

    def validate_all(self) -> Dict[str, bool]:
        """
        Validates all configured credentials.
        
        Returns:
            Dict[str, bool]: Status of each authentication source.
        
        Raises:
            FatalError: If any validation fails, halting the process immediately.
        """
        results = {}
        
        try:
            self.get_wb_token(force_refresh=True)
            results["world_bank"] = True
        except FatalError as e:
            logger.error(f"World Bank validation failed: {e}")
            raise # Re-raise to stop pipeline
        
        try:
            self.get_cds_token(force_refresh=True)
            results["copernicus"] = True
        except FatalError as e:
            logger.error(f"Copernicus validation failed: {e}")
            raise # Re-raise to stop pipeline
        
        return results


def main():
    """
    CLI entry point to validate authentication.
    Usage: python -m src.utils.auth_manager
    """
    print("Starting Authentication Validation...")
    manager = AuthManager()
    
    try:
        status = manager.validate_all()
        print("\n--- Authentication Status ---")
        for service, is_valid in status.items():
            status_str = "VALID" if is_valid else "INVALID"
            print(f"{service.capitalize()}: {status_str}")
        print("\nAll credentials validated successfully.")
        return 0
    except FatalError as e:
        print(f"\nFATAL ERROR: {e}")
        return 1
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
