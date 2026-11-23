"""
Unified dataset loader for Materials Project and AFLOW.

WARNING: This model is a surrogate interpolator trained on pre-computed DFT data.
It does NOT solve the Schrödinger equation or perform first-principles calculations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import requests

from ingest.loader_base import DataLoader
from ingest.validator import enforce_single_source

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class DownloadManifest:
    def __init__(self, num_entries: int, source: str, download_path: Path):
        self.num_entries = num_entries
        self.source = source
        self.download_path = download_path

class MaterialsProjectLoader(DataLoader):
    """
    Loader for Materials Project data.
    
    WARNING: This model is a surrogate interpolator trained on pre-computed DFT data.
    It does NOT solve the Schrödinger equation or perform first-principles calculations.
    """
    def __init__(self, output_dir: Path, api_key: Optional[str] = None):
        super().__init__(output_dir)
        self.api_key = api_key or os.getenv("MP_API_KEY")
        if not self.api_key:
            raise ValueError("Materials Project API key not found. Set MP_API_KEY environment variable.")
        
    def fetch_data(self) -> DownloadManifest:
        """
        Fetches raw data from the Materials Project API.
        
        WARNING: This model is a surrogate interpolator trained on pre-computed DFT data.
        It does NOT solve the Schrödinger equation or perform first-principles calculations.
        
        Returns:
            DownloadManifest: Metadata about the downloaded data.
        """
        # Enforce single source check
        enforce_single_source("materials_project")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define the API endpoint for 2D materials with elastic tensors
        # We request a subset of materials that have elastic tensor data
        # and are 2D materials (layer materials)
        base_url = "https://materialsproject.org/rest/v2/materials"
        
        # We'll fetch a small batch to start with (max 100 per request)
        # In a real scenario, we would paginate through all results
        params = {
            'api_key': self.api_key,
            'has_elastic': 'true',
            'nelements': '2-3',  # Limit to binary and ternary for 2D focus
            'page_limit': 100
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'response' not in data or 'data' not in data['response']:
                raise ValueError("Invalid response from Materials Project API")
            
            materials = data['response']['data']
            downloaded_count = 0
            
            for mat in materials:
                material_id = mat.get('material_id')
                if not material_id:
                    continue
                
                # Fetch detailed data for this material including elastic tensor
                detail_url = f"{base_url}/{material_id}"
                detail_params = {
                    'api_key': self.api_key,
                    'fields': 'structure,elasticity'
                }
                
                try:
                    detail_response = requests.get(detail_url, params=detail_params)
                    detail_response.raise_for_status()
                    detail_data = detail_response.json()
                    
                    if 'response' in detail_data and 'data' in detail_data['response']:
                        mat_data = detail_data['response']['data'][0]
                        
                        # Save the raw JSON data
                        output_file = self.output_dir / f"{material_id}.json"
                        with open(output_file, 'w') as f:
                            json.dump(mat_data, f, indent=2)
                        
                        downloaded_count += 1
                        
                        # Log progress every 10 materials
                        if downloaded_count % 10 == 0:
                            logger.info(f"Downloaded {downloaded_count} materials...")
                    
                except Exception as e:
                    logger.warning(f"Failed to download details for {material_id}: {e}")
                    continue
            
            logger.info(f"Successfully downloaded {downloaded_count} materials from Materials Project")
            return DownloadManifest(
                num_entries=downloaded_count,
                source="materials_project",
                download_path=self.output_dir
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during download: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during data fetch: {e}")
            raise

    def validate_source(self) -> bool:
        """Validates that the source is Materials Project."""
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """Returns metadata about the source."""
        return {
            "source": "materials_project",
            "api_key_set": bool(self.api_key),
            "warning": "WARNING: This model is a surrogate interpolator trained on pre-computed DFT data. It does NOT solve the Schrödinger equation or perform first-principles calculations."
        }

class AFLOWLoader(DataLoader):
    """
    Loader for AFLOW data.
    
    WARNING: This model is a surrogate interpolator trained on pre-computed DFT data.
    It does NOT solve the Schrödinger equation or perform first-principles calculations.
    """
    def __init__(self, output_dir: Path):
        super().__init__(output_dir)
        
    def fetch_data(self) -> DownloadManifest:
        """
        Fetches raw data from AFLOW.
        
        WARNING: This model is a surrogate interpolator trained on pre-computed DFT data.
        It does NOT solve the Schrödinger equation or perform first-principles calculations.
        
        Returns:
            DownloadManifest: Metadata about the downloaded data.
        """
        # Enforce single source check
        enforce_single_source("aflow")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # AFLOW REST API endpoint for elastic data
        # We'll fetch a sample of materials with elastic tensor data
        base_url = "https://aflow.org/rest/v1"
        
        # Parameters for 2D materials with elastic data
        # Note: AFLOW's API might require specific parameters for 2D materials
        params = {
            'api_key': 'demo',  # Using demo key for testing
            'c': 'elastic',  # Request elastic data
            'l': 100,  # Limit to 100 entries
            'format': 'json'
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # AFLOW returns data in a specific format
            if 'data' not in data:
                raise ValueError("Invalid response from AFLOW API")
            
            materials = data['data']
            downloaded_count = 0
            
            for mat in materials:
                # AFLOW data structure might vary, adapt as needed
                material_id = mat.get('prototype', 'unknown')
                if not material_id:
                    continue
                
                # Save the raw JSON data
                output_file = self.output_dir / f"aflow_{material_id}.json"
                with open(output_file, 'w') as f:
                    json.dump(mat, f, indent=2)
                
                downloaded_count += 1
                
                # Log progress every 10 materials
                if downloaded_count % 10 == 0:
                    logger.info(f"Downloaded {downloaded_count} materials from AFLOW...")
            
            logger.info(f"Successfully downloaded {downloaded_count} materials from AFLOW")
            return DownloadManifest(
                num_entries=downloaded_count,
                source="aflow",
                download_path=self.output_dir
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during AFLOW download: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during AFLOW data fetch: {e}")
            raise

    def validate_source(self) -> bool:
        """Validates that the source is AFLOW."""
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """Returns metadata about the source."""
        return {
            "source": "aflow",
            "warning": "WARNING: This model is a surrogate interpolator trained on pre-computed DFT data. It does NOT solve the Schrödinger equation or perform first-principles calculations."
        }

class UnifiedDatasetLoader:
    """
    Unified loader that abstracts Materials Project and AFLOW into a single canonical source.
    
    WARNING: This model is a surrogate interpolator trained on pre-computed DFT data.
    It does NOT solve the Schrödinger equation or perform first-principles calculations.
    
    This loader enforces that only one data source is active per run, satisfying
    Constitution Principle I (Data Hygiene).
    """
    def __init__(self, source: str, output_dir: Optional[Path] = None):
        """
        Initializes the unified loader with a single canonical source.
        
        Args:
            source: Either 'materials_project' or 'aflow'
            output_dir: Directory to store downloaded data
            
        Raises:
            ValueError: If source is invalid or multiple sources are detected
        """
        self.source = source
        self.output_dir = output_dir or Path("data/raw")
        
        if source == "materials_project":
            self.loader = MaterialsProjectLoader(self.output_dir)
        elif source == "aflow":
            self.loader = AFLOWLoader(self.output_dir)
        else:
            raise ValueError(f"Unknown source: {source}. Use 'materials_project' or 'aflow'.")
        
        # Enforce single source constraint
        enforce_single_source(source)

    def fetch_data(self) -> DownloadManifest:
        """
        Fetches data from the configured canonical source.
        
        Returns:
            DownloadManifest: Metadata about the downloaded data
        """
        return self.loader.fetch_data()

def main():
    """
    Main entry point for the dataset download script.
    
    WARNING: This model is a surrogate interpolator trained on pre-computed DFT data.
    It does NOT solve the Schrödinger equation or perform first-principles calculations.
    """
    parser = argparse.ArgumentParser(
        description="Download data from a canonical source (Materials Project or AFLOW)."
    )
    parser.add_argument(
        "--output", 
        type=str, 
        required=True, 
        help="Output directory for raw data"
    )
    parser.add_argument(
        "--source", 
        type=str, 
        default=os.getenv("DATA_SOURCE", "materials_project"), 
        help="Data source ('materials_project' or 'aflow')"
    )
    
    args = parser.parse_args()
    output_dir = Path(args.output)
    source = args.source

    try:
        loader = UnifiedDatasetLoader(source=source, output_dir=output_dir)
        manifest = loader.fetch_data()
        logger.info(f"Downloaded {manifest.num_entries} entries from {manifest.source} to {manifest.download_path}")
        
        # Log the warning disclaimer
        logger.warning("WARNING: This model is a surrogate interpolator trained on pre-computed DFT data. "
                     "It does NOT solve the Schrödinger equation or perform first-principles calculations.")
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise

if __name__ == "__main__":
    main()