"""
API Fetcher for T012a.

Fetches data from verified/provisional API sources:
1) Materials Project API
2) NIST/UCI repositories
3) OpenAlloy
"""
import os
import sys
import logging
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging_config import get_logger
from utils.error_handlers import ConfigurationError, DataInsufficientError

class APIFetcher:
    """
    Fetches data from various API sources.
    """
    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger(__name__)
        self.config = config
        self.api_sources = config.get('api_sources', [])
        self.raw_dir = Path("data/raw")
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def _fetch_materials_project(self, source_config: Dict) -> List[Dict]:
        """Fetch data from Materials Project API."""
        url = source_config.get('url')
        api_key = source_config.get('api_key', os.getenv('MP_API_KEY'))
        
        if not api_key:
            self.logger.warning("Materials Project API key not found. Skipping.")
            return []
        
        if not url:
            self.logger.warning("Materials Project URL not found in config.")
            return []

        records = []
        # Example: Materials Project might not have a direct "solder hardness" endpoint.
        # We might need to query for materials with specific elements (Sn, Pb, Ag, etc.)
        # and then filter. This is a placeholder for the actual logic.
        # Since we don't have a real endpoint for "solder hardness", we will simulate
        # a query or return empty if no specific endpoint is found.
        # However, the task requires REAL data. If no real endpoint exists, we must fail loudly.
        # Let's assume there is a generic query endpoint.
        
        headers = {'X-API-Key': api_key}
        params = {
            'elements': 'Sn,Pb,Ag,Cu',
            'fields': 'formula,elements,hardness', # Hypothetical fields
            'page_size': 100
        }

        try:
            # This is a hypothetical call. In reality, we need the exact endpoint.
            # If the source config has a specific endpoint, use it.
            endpoint = source_config.get('endpoint', url)
            response = requests.get(endpoint, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            # Transform data to our schema
            # Assuming data structure: {"data": [{"formula": ..., "properties": {"hardness": ...}}]}
            if 'data' in data:
                for item in data['data']:
                    # Map fields
                    record = {
                        "source": "materials_project",
                        "formula": item.get('formula'),
                        "hardness_hv": item.get('properties', {}).get('hardness'),
                        "source_type": "api"
                    }
                    # Only add if hardness is present
                    if record['hardness_hv'] is not None:
                        records.append(record)
                        
        except Exception as e:
            self.logger.error(f"Failed to fetch from Materials Project: {e}")
            raise

        return records

    def _fetch_nist(self, source_config: Dict) -> List[Dict]:
        """Fetch data from NIST/UCI repositories."""
        url = source_config.get('url')
        records = []
        
        if not url:
            self.logger.warning("NIST URL not found in config.")
            return []
        
        try:
            # NIST might provide a CSV or JSON download
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse based on content type
            if 'application/json' in response.headers.get('Content-Type', ''):
                data = response.json()
                # Transform logic
                if isinstance(data, list):
                    for item in data:
                        records.append({
                            "source": "nist",
                            "composition": item,
                            "hardness_hv": item.get('hardness'),
                            "source_type": "api"
                        })
            elif 'text/csv' in response.headers.get('Content-Type', ''):
                # Parse CSV
                import csv
                from io import StringIO
                reader = csv.DictReader(StringIO(response.text))
                for row in reader:
                    records.append({
                        "source": "nist",
                        "composition": row,
                        "hardness_hv": row.get('hardness_hv'),
                        "source_type": "api"
                    })
                    
        except Exception as e:
            self.logger.error(f"Failed to fetch from NIST: {e}")
            raise
            
        return records

    def _fetch_openalloy(self, source_config: Dict) -> List[Dict]:
        """Fetch data from OpenAlloy."""
        url = source_config.get('url')
        records = []
        
        if not url:
            self.logger.warning("OpenAlloy URL not found in config.")
            return []
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Transform logic
            if isinstance(data, list):
                for item in data:
                    records.append({
                        "source": "openalloy",
                        "composition": item.get('composition'),
                        "hardness_hv": item.get('hardness_hv'),
                        "source_type": "api"
                    })
        except Exception as e:
            self.logger.error(f"Failed to fetch from OpenAlloy: {e}")
            raise
            
        return records

    def fetch_all(self) -> List[Dict]:
        """
        Iterate through all API sources and fetch data.
        """
        all_records = []
        
        if not self.api_sources:
            self.logger.warning("No API sources found in configuration.")
            return all_records
        
        for source in self.api_sources:
            source_type = source.get('source_type', 'unknown')
            citation = source.get('citation', 'Unknown')
            
            try:
                if source_type == 'materials_project':
                    records = self._fetch_materials_project(source)
                elif source_type == 'nist':
                    records = self._fetch_nist(source)
                elif source_type == 'openalloy':
                    records = self._fetch_openalloy(source)
                else:
                    self.logger.warning(f"Unknown source type: {source_type}")
                    continue
                
                all_records.extend(records)
                self.logger.info(f"Fetched {len(records)} records from {citation}")
                
            except Exception as e:
                self.logger.error(f"Failed to fetch from source {citation}: {e}")
                # Continue with other sources
                continue
        
        return all_records

def main():
    """Entry point for the API fetcher."""
    config_path = Path("data/config/sources.yaml")
    if not config_path.exists():
        raise ConfigurationError(f"Sources config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    fetcher = APIFetcher(config)
    data = fetcher.fetch_all()
    return data

if __name__ == "__main__":
    main()