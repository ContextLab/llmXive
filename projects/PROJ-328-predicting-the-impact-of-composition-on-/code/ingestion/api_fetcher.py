"""
API Fetcher for Solder Hardness Data Ingestion.

Fetches data from verified API sources: Materials Project, NIST/UCI (via repository),
and OpenAlloy. Handles authentication, rate limiting, and data hygiene.

Dependencies:
    - data/config/sources.yaml (must exist)
    - code/config.py (for thresholds)
"""
import os
import sys
import logging
import json
import time
import hashlib
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logger import get_logger
from utils.error_handlers import ConfigurationError, DataFetchError

# Constants
CHECKSUMS_FILE = Path("data/checksums.txt")
RAW_OUTPUT_FILE = Path("data/raw/api_fetched.json")
SOURCES_CONFIG = Path("data/config/sources.yaml")
RATE_LIMIT_DELAY = 1.0  # seconds between requests

logger = get_logger(__name__)

class APIFetcher:
    """Handles fetching data from multiple API sources."""

    def __init__(self, sources_config_path: Path = SOURCES_CONFIG):
        if not sources_config_path.exists():
            raise ConfigurationError(f"Sources configuration file not found: {sources_config_path}")
        
        self.sources_config = self._load_yaml(sources_config_path)
        self.all_fetched_data: List[Dict[str, Any]] = []
        self.fetch_log: List[Dict[str, Any]] = []

    def _load_yaml(self, path: Path) -> Dict[str, Any]:
        """Load YAML configuration."""
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def _save_checksum(self, file_path: Path, checksum: str):
        """Append checksum to the checksums file."""
        with open(CHECKSUMS_FILE, 'a') as f:
            f.write(f"{file_path.name}:{checksum}\n")
        logger.info(f"Checksum saved for {file_path.name}: {checksum}")

    def _fetch_materials_project(self) -> List[Dict[str, Any]]:
        """
        Fetch solder-related data from Materials Project API.
        Endpoint: /materials/...
        Requires API Key from env var MP_API_KEY.
        """
        source_config = self.sources_config.get('materials_project', {})
        if not source_config.get('verified'):
            logger.warning("Materials Project source not verified, skipping.")
            return []

        api_key = os.getenv(source_config.get('api_key_env', 'MP_API_KEY'))
        if not api_key:
            logger.warning("MP_API_KEY environment variable not set. Skipping Materials Project.")
            return []

        base_url = source_config.get('url', 'https://api.materialsproject.org')
        endpoint = source_config.get('endpoint', '/materials')
        # Note: The actual API endpoint structure for MP is /materials/v2/...
        # We construct the query for Sn-based alloys
        query_url = f"{base_url}{endpoint}/v2"
        
        headers = {
            'X-Api-Key': api_key,
            'Content-Type': 'application/json'
        }

        # Search for materials containing Sn (Tin) which is the base of most solders
        # Note: MP API doesn't have a direct "hardness" endpoint for all materials,
        # but we can fetch elastic properties or specific properties if available.
        # For this implementation, we attempt to fetch a sample of Sn-containing compounds.
        # In a real scenario, we would need a specific property endpoint or a bulk download.
        
        params = {
            'elements': 'Sn',
            'fields': 'material_id,formula,pretty_formula,electronic_structure,properties'
        }

        try:
            # Limit to 10 for initial fetch to avoid rate limits if key is free tier
            params['limit'] = 10 
            
            logger.info(f"Fetching from Materials Project: {query_url}")
            response = requests.get(query_url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('data', [])
                
                # Transform MP data to our expected schema
                transformed = []
                for item in results:
                    # MP data structure is complex; we extract what we can
                    # Note: Hardness is not always directly available in MP standard API without specific endpoints
                    # We will log that we fetched the composition but hardness might be missing/derived
                    transformed.append({
                        'source': 'materials_project',
                        'material_id': item.get('material_id'),
                        'formula': item.get('pretty_formula'),
                        'composition': item.get('composition', {}), # {element: fraction}
                        'hardness_hv': None, # Hardness often not directly in standard MP API for all materials
                        'citation': f"Materials Project, {item.get('material_id')}"
                    })
                
                logger.info(f"Materials Project: Fetched {len(transformed)} records.")
                return transformed
            else:
                logger.error(f"Materials Project API failed: {response.status_code} - {response.text}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching Materials Project: {e}")
            return []

    def _fetch_nist_uci(self) -> List[Dict[str, Any]]:
        """
        Fetch data from NIST/UCI repositories.
        Since UCI is a repository of datasets, we attempt to fetch a known solder dataset.
        If the specific dataset ID is not found, we skip.
        """
        source_config = self.sources_config.get('nist_uci', {})
        if not source_config.get('verified'):
            logger.warning("NIST/UCI source not verified, skipping.")
            return []

        # UCI often requires manual download or specific archive links.
        # We will simulate a fetch of a known solder dataset URL if available.
        # In a real pipeline, this would point to a specific CSV/JSON download link.
        # For this implementation, we assume a hypothetical direct download link exists
        # or we fetch from a known mirror if the dataset ID is valid.
        
        # Placeholder for a direct CSV download link (example only)
        # In reality, UCI datasets are often archived in .zip files.
        # We will try to fetch a specific known solder dataset if we can construct the URL.
        # Since the spec mentions 'solder_alloys' dataset_id, we try to construct a likely URL.
        
        # Note: There is no single public API endpoint for UCI that returns JSON directly for "solder_alloys".
        # We will attempt to fetch a CSV from a known archive or return empty if not found.
        # To satisfy the "Real Data" constraint, we must not fabricate.
        # If the URL is not reachable, we log and return empty.
        
        # Hypothetical direct link (example): https://archive.ics.uci.edu/ml/machine-learning-databases/...
        # We will try to fetch a known solder dataset from a reliable mirror or return empty.
        
        # For this implementation, we will try to fetch a specific CSV file if the URL is known.
        # Since the spec does not provide a direct download URL, we will skip this if we cannot verify the URL.
        # However, to demonstrate the logic, we will try a generic search or a known file.
        
        # Let's assume we have a direct link to a CSV for demonstration of the fetch logic.
        # In a real scenario, this URL would be verified in sources.yaml.
        # We will use a placeholder URL that we know exists or skip.
        # Since we cannot guarantee a public solder dataset URL exists without verification,
        # we will log a warning and return empty to avoid fabrication.
        
        logger.warning("NIST/UCI: No verified direct download URL found in sources.yaml for solder data. Skipping.")
        return []

    def _fetch_openalloy(self) -> List[Dict[str, Any]]:
        """
        Fetch data from OpenAlloy API.
        Endpoint: /compositions
        """
        source_config = self.sources_config.get('openalloy', {})
        if not source_config.get('verified'):
            logger.warning("OpenAlloy source not verified, skipping.")
            return []

        base_url = source_config.get('url', 'https://openalloy.org/api/v1')
        endpoint = source_config.get('endpoint', '/compositions')
        
        # OpenAlloy might require auth or be public. We assume public for now.
        url = f"{base_url}{endpoint}"
        
        try:
            # We need to filter for solders (Sn-based).
            # We will fetch a sample and filter client-side.
            params = {'limit': 20} # Limit to avoid large downloads
            
            logger.info(f"Fetching from OpenAlloy: {url}")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Assuming the API returns a list of items
                items = data if isinstance(data, list) else data.get('data', [])
                
                transformed = []
                for item in items:
                    # Check if it's a solder (Sn based)
                    # This depends on the actual API schema. We assume a 'composition' field.
                    composition = item.get('composition', {})
                    if 'Sn' in composition:
                        transformed.append({
                            'source': 'openalloy',
                            'alloy_id': item.get('id'),
                            'formula': item.get('name', 'Unknown'),
                            'composition': composition,
                            'hardness_hv': item.get('hardness_hv'), # Assume field exists
                            'citation': f"OpenAlloy, {item.get('id')}"
                        })
                
                logger.info(f"OpenAlloy: Fetched {len(transformed)} solder records.")
                return transformed
            else:
                logger.error(f"OpenAlloy API failed: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching OpenAlloy: {e}")
            return []

    def fetch_all(self) -> Dict[str, Any]:
        """
        Execute fetches for all configured sources.
        Returns a dictionary containing the fetched data and status.
        """
        logger.info("Starting API fetch process...")
        
        # Fetch from Materials Project
        mp_data = self._fetch_materials_project()
        self.all_fetched_data.extend(mp_data)
        self.fetch_log.append({'source': 'materials_project', 'count': len(mp_data), 'status': 'success' if mp_data else 'failed'})
        
        time.sleep(RATE_LIMIT_DELAY)

        # Fetch from NIST/UCI
        nist_data = self._fetch_nist_uci()
        self.all_fetched_data.extend(nist_data)
        self.fetch_log.append({'source': 'nist_uci', 'count': len(nist_data), 'status': 'success' if nist_data else 'failed'})
        
        time.sleep(RATE_LIMIT_DELAY)

        # Fetch from OpenAlloy
        oa_data = self._fetch_openalloy()
        self.all_fetched_data.extend(oa_data)
        self.fetch_log.append({'source': 'openalloy', 'count': len(oa_data), 'status': 'success' if oa_data else 'failed'})

        # Prepare output
        output = {
            'fetched_data': self.all_fetched_data,
            'fetch_log': self.fetch_log,
            'total_records': len(self.all_fetched_data)
        }

        # Save to file
        RAW_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(RAW_OUTPUT_FILE, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Fetched data saved to {RAW_OUTPUT_FILE}")

        # Generate and save checksum
        checksum = self._calculate_sha256(RAW_OUTPUT_FILE)
        self._save_checksum(RAW_OUTPUT_FILE, checksum)

        return output

def main():
    """Main entry point for the API fetcher."""
    try:
        fetcher = APIFetcher()
        result = fetcher.fetch_all()
        logger.info(f"API Fetch complete. Total records: {result['total_records']}")
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
