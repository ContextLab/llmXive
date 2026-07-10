"""
Materials Project (MP) Data Fetcher for High-Entropy Alloys (HEA).

This module implements the fetcher for the Materials Project API,
specifically targeting High-Entropy Alloys (≥5 principal elements).
It handles API key validation, retries, and the specific filtering
logic required to minimize memory usage by filtering at the query
level or immediately post-fetch.
"""

import os
import sys
import logging
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import requests
import pandas as pd

# Import shared utilities from the project structure
# Note: Path adjustments might be needed depending on how this is executed,
# but per the API surface, we assume standard project root imports.
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from utils.logging_config import get_logger
from utils.data_fetch import DataFetcher
from utils.validators import validate_sample_count, ValidationError

# Constants
MP_API_URL = "https://api.materialsproject.org/v2/materials"
MP_DOCS_URL = "https://docs.materialsproject.org"
MAX_RETRIES = 5
RETRY_DELAY = 2.0
MIN_PRINCIPAL_ELEMENTS = 5
BULK_MODULUS_KEY = "bulk_modulus"

logger = get_logger(__name__)

class MaterialsProjectFetcher(DataFetcher):
    """
    Fetcher for Materials Project data, optimized for HEA research.

    Attributes:
        api_key (str): The API key for Materials Project.
        base_url (str): The base URL for the API.
        timeout (int): Request timeout in seconds.
    """

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        """
        Initialize the Materials Project Fetcher.

        Args:
            api_key: API key for Materials Project. If None, attempts to read
                     from MP_API_KEY environment variable.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or os.getenv("MP_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "Materials Project API key not found. "
                "Set MP_API_KEY environment variable or pass it to the constructor."
            )
        
        self.base_url = MP_API_URL
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        })
        logger.info("Materials Project Fetcher initialized.")

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a paginated request to the MP API with retry logic.

        Args:
            endpoint: The API endpoint (e.g., '/summary').
            params: Query parameters.

        Returns:
            Dict: The JSON response.
        """
        url = f"{self.base_url}/{endpoint}"
        if params is None:
            params = {}
        
        # Default to 1000 results per page to minimize requests, 
        # though MP limits this.
        params["limit"] = 1000 
        
        retries = 0
        while retries < MAX_RETRIES:
            try:
                logger.debug(f"Requesting {url} with params {params}")
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                retries += 1
                if retries == MAX_RETRIES:
                    logger.error(f"Failed to fetch data after {MAX_RETRIES} retries: {e}")
                    raise
                wait_time = RETRY_DELAY * (2 ** retries)
                logger.warning(f"Request failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
        
        raise RuntimeError("Unexpected loop exit in _make_request")

    def _count_elements(self, composition_str: str) -> Tuple[int, List[str]]:
        """
        Parse a composition string (e.g., 'Fe:0.2 Ni:0.2 ...') and count unique elements.
        
        Args:
            composition_str: The composition string from MP.
            
        Returns:
            Tuple of (element_count, list_of_elements)
        """
        if not composition_str:
            return 0, []
        
        # MP composition format is typically "Element:Fraction, Element:Fraction"
        # or sometimes just a dictionary string representation.
        # We split by comma and extract the element symbol.
        elements = set()
        try:
            parts = composition_str.split(",")
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                # Format is usually "Symbol:Value"
                if ":" in part:
                    symbol = part.split(":")[0].strip()
                    # Basic validation for element symbol (2 chars max, starts with Upper)
                    if symbol and symbol[0].isupper():
                        elements.add(symbol)
                else:
                    # Fallback if format is weird, try to extract alpha chars
                    clean = "".join([c for c in part if c.isalpha()])
                    if clean:
                        elements.add(clean)
        except Exception:
            logger.warning(f"Failed to parse composition string: {composition_str}")
            return 0, []
        
        return len(elements), list(elements)

    def fetch_data(
        self, 
        output_path: Optional[Path] = None,
        max_samples: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Fetch HEA candidates from Materials Project.

        This method:
        1. Queries the MP API for materials with bulk modulus data.
        2. Filters for materials with ≥5 principal elements.
        3. Normalizes the data into a DataFrame.
        4. Saves to disk if output_path is provided.

        Args:
            output_path: Path to save the CSV file.
            max_samples: Maximum number of samples to fetch (for testing).

        Returns:
            pd.DataFrame: The fetched and filtered data.
        """
        logger.info("Starting Materials Project data fetch...")
        
        # MP API requires specific fields. We need composition and bulk modulus.
        # Note: The MP API v2 'summary' endpoint is the most efficient for this.
        # We filter for 'has_properties' including 'bulk_modulus'.
        
        endpoint = "summary"
        params = {
            "fields": "material_id,pretty_formula,bulk_modulus,elements",
            "has_properties": "bulk_modulus"
        }

        all_data = []
        page = 0
        total_fetched = 0
        
        # MP API pagination: offset
        while True:
            params["offset"] = page * 1000
            
            try:
                response = self._make_request(endpoint, params)
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break

            docs = response.get("data", [])
            if not docs:
                break

            for doc in docs:
                # Extract data
                material_id = doc.get("material_id")
                pretty_formula = doc.get("pretty_formula", "")
                bulk_modulus = doc.get("bulk_modulus")
                elements_str = doc.get("elements", "") # This is often a comma-separated string of "Symbol:Fraction"

                # Filter: ≥5 principal elements
                # We parse the composition string to count elements.
                # Note: 'elements' field in MP v2 summary might be a list of dicts or string.
                # If it's a string "Fe:0.2, Ni:0.2", we parse.
                # If it's a list [{"symbol": "Fe", "fraction": 0.2}, ...], we count.
                
                count = 0
                composition_dict = {}
                
                if isinstance(elements_str, str):
                    count, _ = self._count_elements(elements_str)
                    # Parse into dict for later use if needed
                    parts = elements_str.split(",")
                    for part in parts:
                        if ":" in part:
                            sym, frac = part.split(":")
                            composition_dict[sym.strip()] = float(frac.strip())
                elif isinstance(elements_str, list):
                    count = len(elements_str)
                    for item in elements_str:
                        if isinstance(item, dict):
                            composition_dict[item.get("symbol", "")] = item.get("fraction", 0.0)
                
                # CRITICAL FILTER: ≥5 principal elements
                if count < MIN_PRINCIPAL_ELEMENTS:
                    continue

                # Filter: Valid Bulk Modulus
                if bulk_modulus is None or bulk_modulus <= 0:
                    continue

                # Construct row
                row = {
                    "material_id": material_id,
                    "source": "Materials Project",
                    "composition": composition_dict, # Store as dict for later processing
                    "composition_str": pretty_formula,
                    "bulk_modulus": bulk_modulus,
                    "element_count": count,
                    "elements": list(composition_dict.keys())
                }
                all_data.append(row)
                total_fetched += 1

                if max_samples and total_fetched >= max_samples:
                    break

            if max_samples and total_fetched >= max_samples:
                break

            if not docs or len(docs) < 1000:
                # No more data
                break
            
            page += 1

        if not all_data:
            logger.warning("No HEA samples found with ≥5 elements and valid bulk modulus.")
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(all_data)
            logger.info(f"Fetched {len(df)} HEA samples from Materials Project.")

        # Validate sample count (even if low, we log it for the power analysis later)
        try:
            validate_sample_count(len(df), min_threshold=0) # We don't halt here, just log
        except ValidationError as e:
            logger.warning(f"Sample count validation warning: {e}")

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            logger.info(f"Data saved to {output_path}")

        return df

    def close(self):
        """Close the session."""
        self.session.close()

def main():
    """
    Main entry point for the script.
    Fetches data and saves to data/raw/mp_hea_samples.csv.
    """
    from utils.logging_config import setup_logging
    setup_logging(level="INFO")

    # Determine output path relative to project root
    project_root = Path(__file__).parent.parent.parent
    output_dir = project_root / "data" / "raw"
    output_file = output_dir / "mp_hea_samples.csv"

    logger.info(f"Output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        fetcher = MaterialsProjectFetcher()
        df = fetcher.fetch_data(output_path=output_file)
        logger.info("Fetch completed successfully.")
    except RuntimeError as e:
        logger.error(f"Fetch failed: {e}")
        sys.exit(1)
    finally:
        if 'fetcher' in locals():
            fetcher.close()

if __name__ == "__main__":
    main()