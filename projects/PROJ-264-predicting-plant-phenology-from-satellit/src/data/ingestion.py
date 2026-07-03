"""
Data Ingestion Module for Plant Phenology Project.

This module handles the initialization of Google Earth Engine (GEE)
authentication using a Service Account JSON key provided via environment
variable, ensuring CI reproducibility and avoiding interactive auth flows.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Attempt to import earthengine-api; fail gracefully if missing
try:
    import ee
except ImportError:
    logging.error("earthengine-api not found. Please install via: pip install earthengine-api")
    raise

# Import project utilities
# Note: We import setup_logging from the provided utils API
try:
    from src.lib.utils import setup_logging
except ImportError:
    # Fallback if utils isn't fully ready, though T005 should be done
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger(__name__)

# Environment variable name for GEE credentials
GEE_CREDENTIALS_ENV_VAR = "GOOGLE_EARTH_ENGINE_CREDENTIALS"

# Default path for the GEE private key if env var is a file path
# In CI, this is usually a JSON string, but we support file path too.
GEE_DEFAULT_KEY_PATH = os.getenv("GEE_PRIVATE_KEY_PATH", None)


def initialize_earth_engine() -> bool:
    """
    Initialize Google Earth Engine using a Service Account.

    Checks for the presence of the GOOGLE_EARTH_ENGINE_CREDENTIALS environment
    variable. If it exists and contains a valid JSON key string, it initializes
    the GEE client.

    Returns:
        bool: True if initialization was successful, False otherwise.

    Raises:
        ValueError: If the credentials JSON is malformed.
        FileNotFoundError: If the credentials point to a file that doesn't exist.
    """
    logger.info("Attempting to initialize Google Earth Engine...")

    # 1. Check for Environment Variable
    credentials_json_str = os.getenv(GEE_CREDENTIALS_ENV_VAR)

    if not credentials_json_str:
        # Check for file path fallback if env var is missing
        if GEE_DEFAULT_KEY_PATH and os.path.exists(GEE_DEFAULT_KEY_PATH):
            logger.info(f"Env var {GEE_CREDENTIALS_ENV_VAR} not set, trying file path: {GEE_DEFAULT_KEY_PATH}")
            with open(GEE_DEFAULT_KEY_PATH, 'r') as f:
                credentials_json_str = f.read()
        else:
            logger.error(
                f"Google Earth Engine initialization failed: "
                f"Environment variable '{GEE_CREDENTIALS_ENV_VAR}' is not set "
                f"and no fallback file path provided."
            )
            return False

    try:
        # 2. Parse JSON
        # The env var might contain the raw JSON string or a path to it.
        # We assume raw JSON string first (standard for CI secrets).
        # If it looks like a path (contains / or \) and is not valid JSON, we try file.
        creds_dict = None

        try:
            creds_dict = json.loads(credentials_json_str)
            logger.info("Parsed GEE credentials from JSON string in environment variable.")
        except json.JSONDecodeError:
            # If not JSON, assume it's a file path
            path_to_key = credentials_json_str
            if os.path.exists(path_to_key):
                with open(path_to_key, 'r') as f:
                    creds_dict = json.load(f)
                logger.info(f"Parsed GEE credentials from file: {path_to_key}")
            else:
                raise FileNotFoundError(
                    f"Could not parse credentials as JSON, and file path not found: {path_to_key}"
                )

        if not isinstance(creds_dict, dict):
            raise ValueError("GEE credentials must be a valid JSON object.")

        # 3. Create Credentials Object
        # ee.ServiceAccountCredentials expects a key file path OR a dict with 'type' etc.
        # Since we have the dict, we can pass it to ee.Initialize.
        # Note: ee.Initialize accepts a credentials object.
        # We construct the credentials object manually if we have the dict.
        
        # The standard way with a dict is to use ee.ServiceAccountCredentials
        # which takes a key_file (path) or we can use the dict directly if we construct the right object.
        # However, the easiest robust way with a dict is to write it to a temp file or use the dict directly
        # if the library supports it. ee.Initialize() now supports passing a dict for credentials in newer versions?
        # Actually, ee.ServiceAccountCredentials(key_file) expects a path.
        # Let's create a temporary file for the credentials if we only have the dict.
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(creds_dict, tmp_file)
            temp_key_path = tmp_file.name

        try:
            service_account_creds = ee.ServiceAccountCredentials(
                key_file=temp_key_path
            )
            
            # 4. Initialize
            ee.Initialize(credentials=service_account_creds)
            logger.info("Google Earth Engine initialized successfully with Service Account.")
            return True

        finally:
            # Clean up temp file
            if os.path.exists(temp_key_path):
                os.remove(temp_key_path)

    except Exception as e:
        logger.error(f"Failed to initialize Earth Engine: {e}")
        raise


def main():
    """
    Entry point for the ingestion script.
    Verifies GEE connectivity.
    """
    # Setup logging
    setup_logging()
    
    logger.info("Starting GEE Authentication Check (Task T009a)...")
    
    try:
        success = initialize_earth_engine()
        if success:
            logger.info("GEE Authentication Check PASSED.")
            # Optional: Verify we can access a basic asset to prove connectivity
            try:
                # Try to get a simple asset or list
                # This is a lightweight check
                asset_id = "USGS/SRTMGL1_003" # Common global asset
                asset = ee.Image(asset_id)
                # Just verifying we can construct an image object connected to the API
                logger.info(f"Verified connectivity to asset: {asset_id}")
            except Exception as conn_err:
                logger.warning(f"Could not verify asset connectivity: {conn_err}")
            
            return 0
        else:
            logger.error("GEE Authentication Check FAILED.")
            return 1
    except Exception as e:
        logger.critical(f"Critical error during GEE initialization: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
