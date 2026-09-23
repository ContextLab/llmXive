"""
API Fetcher for Solder Hardness Data Ingestion.

This module implements fetching logic for verified/provisional API sources:
1. Materials Project API
2. NIST/UCI repositories (via requests)
3. OpenAlloy

It reads configuration from `data/config/sources.yaml` and handles
authentication and rate limiting. It strictly fails on fetch errors
without falling back to synthetic data.
"""
import os
import sys
import logging
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
import pandas as pd

# Import project utilities
# Note: We assume the project root is in sys.path or we handle relative imports
try:
    from utils.error_handlers import ConfigurationError
    from utils.logging_config import get_logger
except ImportError:
    # Fallback for direct execution context if utils not in path yet
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.error_handlers import ConfigurationError
    from utils.logging_config import get_logger

# Constants
SOURCES_CONFIG_PATH = Path("data/config/sources.yaml")
RAW_DATA_DIR = Path("data/raw")
CHECKSUMS_FILE = Path("data/checksums.txt")

# Rate limiting configuration (requests per second)
RATE_LIMIT_DELAY = 1.0 

logger = get_logger(__name__)


class DataFetchError(Exception):
    """Raised when a real data fetch fails."""
    pass


class APIFetcher:
    """
    Handles fetching data from multiple API sources defined in sources.yaml.
    """

    def __init__(self, sources_path: Path = SOURCES_CONFIG_PATH):
        self.sources_path = sources_path
        self.sources_data = self._load_sources()
        self.fetched_records: List[Dict[str, Any]] = []
        self.fetch_errors: List[Dict[str, str]] = []

    def _load_sources(self) -> Dict[str, Any]:
        """Load and validate sources.yaml."""
        if not self.sources_path.exists():
            raise ConfigurationError(f"Sources configuration missing: {self.sources_path}")
        
        import yaml
        with open(self.sources_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not config:
            raise ConfigurationError("Sources configuration is empty.")
        
        return config

    def _ensure_raw_dir(self):
        """Ensure the raw data directory exists."""
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _fetch_materials_project(self) -> List[Dict[str, Any]]:
        """
        Fetch solder-related data from Materials Project.
        
        Note: The Materials Project API generally provides DFT data.
        We query for elements common in solders (Sn, Pb, Ag, Cu, Sb, Bi)
        and filter for binary/ternary alloys if possible, or specific
        hardness properties if exposed in the API (often 'band_gap', 'formation_energy').
        Since direct 'Vickers Hardness' is rare in MP standard endpoints,
        we attempt to fetch composition and formation energy as proxy data
        or specific properties if the endpoint supports it.
        
        For this implementation, we simulate the query structure required
        by the spec, but strictly adhere to the 'fail loud' policy.
        """
        records = []
        api_key = os.environ.get(self.sources_data['materials_project'].get('api_key_env', 'MP_API_KEY'))
        
        if not api_key:
            logger.warning("MP_API_KEY not found in environment. Skipping Materials Project fetch.")
            self.fetch_errors.append({
                "source": "Materials Project",
                "error": "Missing API Key (MP_API_KEY)"
            })
            return records

        base_url = self.sources_data['materials_project']['url']
        endpoint = self.sources_data['materials_project'].get('endpoint', '/materials')
        # Construct full URL
        # Note: MP API v1 structure is usually /materials/specific_id or /materials/search
        # We will attempt a search for solder-related elements.
        search_url = f"{base_url}/materials/search"
        
        params = {
            "api_key": api_key,
            "elements": "Sn,Pb,Ag,Cu", # Common solder elements
            "page_size": 50
        }

        try:
            logger.info(f"Fetching from Materials Project: {search_url}")
            time.sleep(RATE_LIMIT_DELAY) # Rate limiting
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse MP response structure (simplified for this task)
            # MP usually returns a 'data' list
            results = data.get('data', [])
            
            for item in results:
                # Extract composition and properties
                # MP data structure varies; we map to our expected schema
                composition = item.get('composition', {})
                # MP 'composition' is often { "Sn": 0.5, "Pb": 0.5 }
                # We need to format it for our pipeline
                
                # Note: MP does not typically have 'hardness_hv' directly in the search endpoint.
                # We will log this limitation. If the spec requires HV specifically from MP,
                # and MP doesn't provide it, we cannot fabricate it.
                # We will record the composition and mark hardness as missing or skip if strict.
                # However, the task asks to fetch data. We fetch what is available.
                
                if not composition:
                    continue

                # Try to find hardness if available in extended properties (often not in search)
                hardness = item.get('properties', {}).get('hardness_hv')
                if hardness is None:
                    # If the source is expected to provide hardness and it doesn't,
                    # we might skip or log. For now, we include the record but note missing HV.
                    # The cleaner will eventually filter or the validator will flag.
                    pass

                records.append({
                    "source": "Materials Project",
                    "composition": composition,
                    "hardness_hv": hardness,
                    "citation": "Materials Project",
                    "measurement_temp_c": 25.0 # Default assumption for DFT unless specified
                })

            logger.info(f"Materials Project fetched {len(results)} items.")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from Materials Project: {e}")
            self.fetch_errors.append({
                "source": "Materials Project",
                "error": str(e)
            })
            # Fail loud: Do not return empty list if we expected data and failed.
            # But if we just didn't find anything, that's okay.
            # If network error, we raise or log. The spec says "raise DataFetchError".
            # We will raise to trigger the pipeline halt if it's a network issue.
            raise DataFetchError(f"Materials Project fetch failed: {e}")

        return records

    def _fetch_nist_uci(self) -> List[Dict[str, Any]]:
        """
        Fetch data from NIST/UCI repository.
        
        The UCI repository typically hosts static CSV files.
        We attempt to download the specific dataset if the URL is known.
        """
        records = []
        nist_config = self.sources_data.get('nist_uci', {})
        url = nist_config.get('url')
        
        if not url:
            logger.warning("NIST/UCI URL not found in sources.yaml. Skipping.")
            self.fetch_errors.append({
                "source": "NIST/UCI",
                "error": "URL missing in config"
            })
            return records

        # Specific dataset URL pattern for solder alloys if available
        # Since the config just gives the base UCI URL, we assume a specific
        # file path or a known dataset ID.
        # We will attempt to fetch a known solder dataset if it exists.
        # Example: https://archive.ics.uci.edu/ml/machine-learning-databases/...
        # We will try a generic fetch and parse.
        
        # NOTE: The UCI repository does not have a single "solder_alloys" dataset
        # that is universally known by that ID. We must rely on the specific
        # URL provided in a real `sources.yaml` or a verified source.
        # Here we simulate the fetch attempt against the configured URL.
        
        # If the config has a specific dataset file URL, use it.
        # If only the base URL is there, we cannot guess the file.
        # We assume the 'sources.yaml' would have been populated with the exact CSV URL.
        
        # Let's check if there is a specific file URL in the config (simulated)
        # For this implementation, we try to fetch a known solder dataset URL
        # or fail if not configured correctly.
        
        # Attempting to fetch a specific known solder dataset from a public mirror
        # or the configured URL if it points to a file.
        try:
            # If the URL ends in .csv, fetch it.
            if url.endswith('.csv') or url.endswith('.data'):
                logger.info(f"Fetching NIST/UCI data from: {url}")
                time.sleep(RATE_LIMIT_DELAY)
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Parse CSV
                df = pd.read_csv(pd.io.common.StringIO(response.text))
                
                # Map columns to our schema
                # Expected columns: element, percentage, hardness_hv (or similar)
                # We assume a standard format or try to detect it.
                # For this task, we assume the CSV has 'composition' and 'hardness' columns.
                
                # If the CSV is in a specific format (e.g., wide or long), handle it.
                # Assuming a wide format: Sn, Pb, Cu, Ag, Hardness
                if 'Hardness' in df.columns:
                    for _, row in df.iterrows():
                        comp = {}
                        for col in df.columns:
                            if col.lower() in ['sn', 'pb', 'cu', 'ag', 'sb', 'bi', 'zn', 'ni']:
                                try:
                                    val = float(row[col])
                                    if val > 0:
                                        comp[col.upper()] = val
                                except (ValueError, TypeError):
                                    pass
                        
                        if comp:
                            records.append({
                                "source": "NIST/UCI",
                                "composition": comp,
                                "hardness_hv": row.get('Hardness', row.get('hardness_hv', None)),
                                "citation": "NIST/UCI Repository",
                                "measurement_temp_c": 25.0
                            })
                else:
                    logger.warning("NIST/UCI CSV does not contain expected 'Hardness' column.")
            
            else:
                # If it's a directory or search page, we cannot parse it directly.
                # This implies the config URL is incomplete.
                logger.error(f"NIST/UCI URL is not a direct file link: {url}")
                self.fetch_errors.append({
                    "source": "NIST/UCI",
                    "error": "URL does not point to a data file"
                })
                # Fail loud if we expected data
                raise DataFetchError(f"NIST/UCI URL is invalid for direct fetch: {url}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from NIST/UCI: {e}")
            self.fetch_errors.append({
                "source": "NIST/UCI",
                "error": str(e)
            })
            raise DataFetchError(f"NIST/UCI fetch failed: {e}")

        return records

    def _fetch_openalloy(self) -> List[Dict[str, Any]]:
        """
        Fetch data from OpenAlloy API.
        """
        records = []
        oa_config = self.sources_data.get('openalloy', {})
        url = oa_config.get('url')
        endpoint = oa_config.get('endpoint')
        
        if not url:
            logger.warning("OpenAlloy URL not found. Skipping.")
            self.fetch_errors.append({
                "source": "OpenAlloy",
                "error": "URL missing in config"
            })
            return records

        full_url = f"{url}{endpoint}"
        
        try:
            logger.info(f"Fetching from OpenAlloy: {full_url}")
            time.sleep(RATE_LIMIT_DELAY)
            response = requests.get(full_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse OpenAlloy response
            # Assuming a list of objects with 'composition' and 'properties'
            items = data.get('results', data.get('data', []))
            
            for item in items:
                comp = item.get('composition', {})
                props = item.get('properties', {})
                
                # Map to schema
                records.append({
                    "source": "OpenAlloy",
                    "composition": comp,
                    "hardness_hv": props.get('hardness_hv', props.get('vickers_hardness', None)),
                    "citation": "OpenAlloy Database",
                    "measurement_temp_c": props.get('temperature_c', 25.0)
                })
            
            logger.info(f"OpenAlloy fetched {len(items)} items.")

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from OpenAlloy: {e}")
            self.fetch_errors.append({
                "source": "OpenAlloy",
                "error": str(e)
            })
            raise DataFetchError(f"OpenAlloy fetch failed: {e}")

        return records

    def fetch_all(self) -> List[Dict[str, Any]]:
        """
        Execute fetch for all configured sources.
        Raises DataFetchError if any critical source fails.
        """
        self._ensure_raw_dir()
        
        all_records = []
        
        # 1. Materials Project
        try:
            mp_records = self._fetch_materials_project()
            all_records.extend(mp_records)
        except DataFetchError:
            # If MP fails, we continue if other sources exist, but log error.
            # The spec says "If *no* sources succeed... halt".
            pass

        # 2. NIST/UCI
        try:
            nist_records = self._fetch_nist_uci()
            all_records.extend(nist_records)
        except DataFetchError:
            pass

        # 3. OpenAlloy
        try:
            oa_records = self._fetch_openalloy()
            all_records.extend(oa_records)
        except DataFetchError:
            pass

        # Check if we got any data
        if not all_records:
            logger.error("No data fetched from any source.")
            raise DataFetchError("Total N = 0 after fetching from all sources.")

        # Save raw data
        self._save_raw_data(all_records)
        
        return all_records

    def _save_raw_data(self, records: List[Dict[str, Any]]):
        """Save fetched records to data/raw/ as JSON and generate checksum."""
        timestamp = int(time.time())
        filename = f"raw_api_fetch_{timestamp}.json"
        filepath = RAW_DATA_DIR / filename
        
        with open(filepath, 'w') as f:
            json.dump(records, f, indent=2)
        
        # Calculate checksum
        checksum = hashlib.sha256(open(filepath, 'rb').read()).hexdigest()
        
        # Append to checksums file
        with open(CHECKSUMS_FILE, 'a') as f:
            f.write(f"{filename}:{checksum}\n")
        
        logger.info(f"Saved raw data to {filepath} (Checksum: {checksum})")


def main():
    """Main entry point for the API Fetcher."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting API Fetcher...")
    
    try:
        fetcher = APIFetcher()
        records = fetcher.fetch_all()
        logger.info(f"Successfully fetched {len(records)} records.")
        
        if fetcher.fetch_errors:
            logger.warning(f"Encountered {len(fetcher.fetch_errors)} errors during fetch:")
            for err in fetcher.fetch_errors:
                logger.warning(f"  - {err['source']}: {err['error']}")
                
        return 0
        
    except ConfigurationError as e:
        logger.error(f"Configuration Error: {e}")
        return 1
    except DataFetchError as e:
        logger.error(f"Data Fetch Error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())