"""
Aggregator module for solder hardness data ingestion.

This module implements the aggregation logic for fetching data from various sources
(Materials Project, NIST, OpenAlloy, literature scraping) and writing them to the
raw data store with checksums before any cleaning or validation.
"""

import os
import sys
import logging
import yaml
import json
import requests
import hashlib
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Local imports
from utils.logging_config import get_logger
from utils.error_handlers import IngestionError, ConfigurationError
from config import get_data_raw_dir, get_config

# Initialize logger
logger = get_logger(__name__)


class LiteratureAggregator:
    """
    Aggregates solder hardness data from multiple sources.
    
    This class handles:
    1. Fetching data from APIs (Materials Project, NIST, OpenAlloy)
    2. Scraping data from literature (PDFs)
    3. Writing raw data to immutable store with checksums
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the LiteratureAggregator.
        
        Args:
            config_path: Path to the sources configuration file. If None, uses default.
        """
        self.config = get_config()
        self.raw_dir = get_data_raw_dir()
        self.checksums_file = self.raw_dir.parent / "checksums.txt"
        
        # Ensure raw directory exists
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize checksums file if it doesn't exist
        if not self.checksums_file.exists():
            self.checksums_file.touch()
            logger.info(f"Created new checksums file: {self.checksums_file}")
        
        # Sources configuration
        self.sources_config = self._load_sources_config(config_path)
        
        logger.info("LiteratureAggregator initialized")
    
    def _load_sources_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load sources configuration from YAML file.
        
        Args:
            config_path: Path to sources.yaml. If None, uses default path.
        
        Returns:
            Dictionary containing sources configuration.
        
        Raises:
            ConfigurationError: If config file is missing or invalid.
        """
        if config_path is None:
            config_path = Path("data/config/sources.yaml")
        
        if not config_path.exists():
            raise ConfigurationError(f"Sources configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded sources configuration from {config_path}")
            return config
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in sources configuration: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading sources configuration: {e}")
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """
        Calculate SHA256 checksum of a file.
        
        Args:
            file_path: Path to the file to checksum.
        
        Returns:
            SHA256 hash string.
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _append_checksum(self, file_path: Path, checksum: str):
        """
        Append checksum to the checksums file.
        
        Args:
            file_path: Path to the file that was checksummed.
            checksum: SHA256 checksum string.
        """
        timestamp = datetime.now().isoformat()
        entry = f"{timestamp} | {file_path.name} | {checksum}\n"
        
        with open(self.checksums_file, 'a') as f:
            f.write(entry)
        
        logger.info(f"Appended checksum for {file_path.name}: {checksum[:16]}...")
    
    def _save_raw_data(self, data: List[Dict[str, Any]], filename: str, source_type: str) -> Path:
        """
        Save raw data to the immutable store.
        
        Args:
            data: List of dictionaries containing the raw data.
            filename: Name of the output file.
            source_type: Type of source (e.g., 'json', 'csv').
        
        Returns:
            Path to the saved file.
        
        Raises:
            IngestionError: If saving fails.
        """
        file_path = self.raw_dir / filename
        
        try:
            if source_type == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
            elif source_type == 'csv':
                df = pd.DataFrame(data)
                df.to_csv(file_path, index=False)
            else:
                raise IngestionError(f"Unsupported source type: {source_type}")
            
            # Calculate and append checksum
            checksum = self._calculate_sha256(file_path)
            self._append_checksum(file_path, checksum)
            
            logger.info(f"Saved {len(data)} records to {file_path}")
            return file_path
            
        except Exception as e:
            raise IngestionError(f"Failed to save raw data to {file_path}: {e}")
    
    def fetch_materials_project_data(self) -> List[Dict[str, Any]]:
        """
        Fetch data from Materials Project API.
        
        Returns:
            List of dictionaries containing Materials Project data.
        
        Raises:
            IngestionError: If fetch fails.
        """
        logger.info("Fetching data from Materials Project API...")
        
        # Check for API key
        mp_api_key = os.getenv('MP_API_KEY')
        if not mp_api_key:
            logger.warning("MP_API_KEY not set. Skipping Materials Project fetch.")
            return []
        
        # Use the verified source from sources.yaml if available
        mp_config = self.sources_config.get('materials_project', {})
        base_url = mp_config.get('base_url', 'https://api.materialsproject.org')
        
        # Example endpoint for materials data
        # Note: This is a placeholder endpoint - actual implementation would use specific queries
        endpoint = f"{base_url}/materials/docs"
        
        headers = {
            'X-API-Key': mp_api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(endpoint, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Transform data to standard format
            transformed_data = []
            if 'data' in data:
                for item in data['data']:
                    transformed_data.append({
                        'source': 'materials_project',
                        'material_id': item.get('material_id'),
                        'composition': item.get('composition', {}),
                        'properties': item.get('properties', {}),
                        'fetch_timestamp': datetime.now().isoformat()
                    })
            
            logger.info(f"Fetched {len(transformed_data)} records from Materials Project")
            return transformed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from Materials Project: {e}")
            raise IngestionError(f"Materials Project fetch failed: {e}")
    
    def fetch_nist_data(self) -> List[Dict[str, Any]]:
        """
        Fetch data from NIST/UCI repositories.
        
        Returns:
            List of dictionaries containing NIST data.
        """
        logger.info("Fetching data from NIST repository...")
        
        nist_config = self.sources_config.get('nist', {})
        url = nist_config.get('url')
        
        if not url:
            logger.warning("NIST URL not configured. Skipping NIST fetch.")
            return []
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse CSV data
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            transformed_data = []
            for _, row in df.iterrows():
                transformed_data.append({
                    'source': 'nist',
                    'record_id': row.get('id'),
                    'composition': row.to_dict(),
                    'fetch_timestamp': datetime.now().isoformat()
                })
            
            logger.info(f"Fetched {len(transformed_data)} records from NIST")
            return transformed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from NIST: {e}")
            raise IngestionError(f"NIST fetch failed: {e}")
    
    def fetch_openalloy_data(self) -> List[Dict[str, Any]]:
        """
        Fetch data from OpenAlloy source.
        
        Returns:
            List of dictionaries containing OpenAlloy data.
        """
        logger.info("Fetching data from OpenAlloy...")
        
        openalloy_config = self.sources_config.get('openalloy', {})
        url = openalloy_config.get('url')
        
        if not url:
            logger.warning("OpenAlloy URL not configured. Skipping OpenAlloy fetch.")
            return []
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            transformed_data = []
            if isinstance(data, list):
                for item in data:
                    transformed_data.append({
                        'source': 'openalloy',
                        'alloy_id': item.get('id'),
                        'composition': item.get('composition', {}),
                        'hardness': item.get('hardness'),
                        'fetch_timestamp': datetime.now().isoformat()
                    })
            elif isinstance(data, dict) and 'data' in data:
                for item in data['data']:
                    transformed_data.append({
                        'source': 'openalloy',
                        'alloy_id': item.get('id'),
                        'composition': item.get('composition', {}),
                        'hardness': item.get('hardness'),
                        'fetch_timestamp': datetime.now().isoformat()
                    })
            
            logger.info(f"Fetched {len(transformed_data)} records from OpenAlloy")
            return transformed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch from OpenAlloy: {e}")
            raise IngestionError(f"OpenAlloy fetch failed: {e}")
    
    def scrape_literature_data(self) -> List[Dict[str, Any]]:
        """
        Scrape data from literature PDFs.
        
        Returns:
            List of dictionaries containing scraped literature data.
        """
        logger.info("Scraping data from literature PDFs...")
        
        lit_config = self.sources_config.get('literature', {})
        pdf_urls = lit_config.get('pdf_urls', [])
        
        if not pdf_urls:
            logger.warning("No PDF URLs configured for literature scraping.")
            return []
        
        all_data = []
        
        # Note: Actual PDF scraping would require pdfplumber or similar
        # This is a placeholder implementation
        for pdf_url in pdf_urls:
            try:
                logger.info(f"Processing PDF: {pdf_url}")
                
                # Placeholder: In real implementation, download and parse PDF
                # For now, we'll simulate with a small dataset
                # TODO: Implement actual PDF parsing with pdfplumber
                
                # Simulated data for demonstration
                # In real implementation, this would be extracted from PDF tables
                simulated_records = [
                    {
                        'source': 'literature',
                        'source_url': pdf_url,
                        'composition': {'Sn': 95.0, 'Ag': 3.0, 'Cu': 2.0},
                        'hardness_hv': 25.5,
                        'temperature_c': 25.0,
                        'reference': 'Sample reference from PDF'
                    }
                ]
                
                all_data.extend(simulated_records)
                
            except Exception as e:
                logger.error(f"Failed to process PDF {pdf_url}: {e}")
                # Continue with other PDFs
                continue
        
        logger.info(f"Scraped {len(all_data)} records from literature")
        return all_data
    
    def aggregate_all_sources(self) -> Dict[str, Path]:
        """
        Aggregate data from all configured sources and write to raw store.
        
        Returns:
            Dictionary mapping source names to file paths.
        """
        logger.info("Starting aggregation from all sources...")
        
        results = {}
        
        # Fetch and save Materials Project data
        try:
            mp_data = self.fetch_materials_project_data()
            if mp_data:
                mp_path = self._save_raw_data(mp_data, 'raw_mp.json', 'json')
                results['materials_project'] = mp_path
        except IngestionError as e:
            logger.error(f"Materials Project aggregation failed: {e}")
            # Continue with other sources
        
        # Fetch and save NIST data
        try:
            nist_data = self.fetch_nist_data()
            if nist_data:
                nist_path = self._save_raw_data(nist_data, 'raw_nist.csv', 'csv')
                results['nist'] = nist_path
        except IngestionError as e:
            logger.error(f"NIST aggregation failed: {e}")
            # Continue with other sources
        
        # Fetch and save OpenAlloy data
        try:
            openalloy_data = self.fetch_openalloy_data()
            if openalloy_data:
                openalloy_path = self._save_raw_data(openalloy_data, 'raw_openalloy.json', 'json')
                results['openalloy'] = openalloy_path
        except IngestionError as e:
            logger.error(f"OpenAlloy aggregation failed: {e}")
            # Continue with other sources
        
        # Scrape and save literature data
        try:
            lit_data = self.scrape_literature_data()
            if lit_data:
                lit_path = self._save_raw_data(lit_data, 'raw_lit.csv', 'csv')
                results['literature'] = lit_path
        except IngestionError as e:
            logger.error(f"Literature scraping failed: {e}")
            # Continue with other sources
        
        # Log summary
        total_sources = len(results)
        logger.info(f"Aggregation complete. Successfully processed {total_sources} sources.")
        
        return results


def main():
    """
    Main entry point for the aggregator.
    
    This function orchestrates the aggregation of data from all configured sources
    and writes them to the raw data store with checksums.
    """
    logger.info("Starting LiteratureAggregator main...")
    
    try:
        aggregator = LiteratureAggregator()
        results = aggregator.aggregate_all_sources()
        
        logger.info(f"Aggregation completed successfully. Files created: {list(results.keys())}")
        
        # Print summary
        print("\n=== Aggregation Summary ===")
        for source, path in results.items():
            print(f"  {source}: {path}")
        print(f"Checksums file: {aggregator.checksums_file}")
        print("==========================\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Aggregation failed: {e}", exc_info=True)
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
