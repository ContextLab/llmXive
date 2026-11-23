"""
Data Ingestion Module for Plant Defense Compound Prediction Pipeline.

This module handles the fetching, validation, and initial processing of
genomic, environmental, and defense compound data from verified sources
or deterministic mock generators for CI/testing.
"""

import json
import os
import sys
import requests
import hashlib
import logging
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Local imports - matching the API surface provided
from config import get_config, ConfigError
from utils.logging import get_module_logger
from utils.io import check_disk_space, DiskSpaceError, compute_checksum

# Initialize logger
logger = get_module_logger(__name__)

# Constants
MANIFEST_PATH = Path("data/manifest.yaml")
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
LOGS_DIR = Path("logs")

# Schema definitions for validation
COMPOUND_SCHEMA_KEYS = {"population_id", "compound_name", "concentration", "source_study"}
ENV_SCHEMA_KEYS = {"population_id", "lat", "lon", "temp", "precip", "ph"}

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    for directory in [RAW_DIR, PROCESSED_DIR, LOGS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    logger.info("Ensured all required directories exist.")

def load_manifest() -> Dict[str, Any]:
    """Load the manifest file if it exists."""
    if MANIFEST_PATH.exists():
        import yaml
        with open(MANIFEST_PATH, 'r') as f:
            return yaml.safe_load(f) or {}
    return {"artifacts": [], "metadata": {}}

def save_manifest(manifest: Dict[str, Any]) -> None:
    """Save the manifest file."""
    import yaml
    with open(MANIFEST_PATH, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)
    logger.info(f"Saved manifest to {MANIFEST_PATH}")

def update_manifest(artifact_path: Path, artifact_type: str, source: str) -> None:
    """Update the manifest with a new artifact."""
    manifest = load_manifest()
    if "artifacts" not in manifest:
        manifest["artifacts"] = []

    checksum = compute_checksum(artifact_path)
    
    new_entry = {
        "path": str(artifact_path),
        "type": artifact_type,
        "source": source,
        "checksum": checksum,
        "timestamp": str(Path(artifact_path).stat().st_mtime)
    }

    # Check if artifact already exists and update, otherwise append
    found = False
    for i, entry in enumerate(manifest["artifacts"]):
        if entry["path"] == str(artifact_path):
            manifest["artifacts"][i] = new_entry
            found = True
            break
    
    if not found:
        manifest["artifacts"].append(new_entry)

    save_manifest(manifest)
    logger.info(f"Updated manifest with artifact: {artifact_path}")

def fetch_url_content(url: str, dest_path: Path, estimated_size: int = 1024 * 1024) -> bool:
    """
    Fetch content from a URL and save to dest_path.
    
    Args:
        url: The URL to fetch from
        dest_path: Destination file path
        estimated_size: Estimated size in bytes for disk space check
        
    Returns:
        True if successful, False otherwise
        
    Raises:
        DiskSpaceError: If insufficient disk space
        requests.RequestException: If fetch fails
    """
    # Check disk space first
    check_disk_space(estimated_size)
    
    try:
        logger.info(f"Fetching {url} to {dest_path}")
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully fetched {url} to {dest_path}")
        return True
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch {url}: {e}")
        raise
    except DiskSpaceError as e:
        logger.error(f"Disk space check failed: {e}")
        raise

def validate_compound_json_schema(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate compound data against required schema.
    
    Args:
        data: The compound data to validate
        
    Returns:
        Tuple of (is_valid, list of missing keys)
    """
    missing_keys = []
    for key in COMPOUND_SCHEMA_KEYS:
        if key not in data:
            missing_keys.append(key)
    
    return len(missing_keys) == 0, missing_keys

def validate_env_csv_schema(df) -> Tuple[bool, List[str]]:
    """
    Validate environmental data against required schema.
    
    Args:
        df: The environmental data DataFrame
        
    Returns:
        Tuple of (is_valid, list of missing columns)
    """
    missing_cols = []
    for col in ENV_SCHEMA_KEYS:
        if col not in df.columns:
            missing_cols.append(col)
    
    return len(missing_cols) == 0, missing_cols

def fetch_genomic_data() -> Path:
    """
    Fetch genomic VCF data from verified URL or generate mock data.
    
    Returns:
        Path to the fetched/generated file
    """
    config = get_config()
    genomic_url = config.verified_urls.get('genomic')
    output_path = RAW_DIR / "genomic.vcf"
    mock_path = RAW_DIR / "mock_genomic.vcf"
    
    if genomic_url and genomic_url in config.verified_datasets:
        try:
            # Estimate VCF size (conservative 100MB for initial check)
            estimated_size = 100 * 1024 * 1024
            fetch_url_content(genomic_url, output_path, estimated_size)
            
            # Validate VCF header
            with open(output_path, 'r') as f:
                header_line = f.readline()
                if not header_line.startswith('##fileformat=VCF'):
                    raise ValueError(f"Invalid VCF header: {header_line}")
            
            update_manifest(output_path, "genomic_vcf", genomic_url)
            logger.info(f"Genomic data fetched and validated: {output_path}")
            return output_path
            
        except (requests.RequestException, ValueError, DiskSpaceError) as e:
            logger.warning(f"Real genomic fetch failed: {e}. Falling back to mock data.")
            # Fall back to mock generator
            from data.mock_generator import generate_mock_genomic_data
            mock_output = generate_mock_genomic_data(str(mock_path))
            update_manifest(mock_output, "mock_genomic_vcf", "mock_generator")
            return mock_output
    else:
        logger.info("No verified genomic URL available. Generating mock data.")
        from data.mock_generator import generate_mock_genomic_data
        mock_output = generate_mock_genomic_data(str(mock_path))
        update_manifest(mock_output, "mock_genomic_vcf", "mock_generator")
        return mock_output

def fetch_environmental_data() -> Path:
    """
    Fetch environmental CSV data from verified URL or generate mock data.
    
    Returns:
        Path to the fetched/generated file
    """
    config = get_config()
    env_url = config.verified_urls.get('env')
    output_path = RAW_DIR / "env_data.csv"
    mock_path = RAW_DIR / "mock_env.csv"
    
    if env_url and env_url in config.verified_datasets:
        try:
            # Estimate CSV size (conservative 10MB)
            estimated_size = 10 * 1024 * 1024
            fetch_url_content(env_url, output_path, estimated_size)
            
            # Validate CSV schema
            import pandas as pd
            df = pd.read_csv(output_path)
            is_valid, missing = validate_env_csv_schema(df)
            
            if not is_valid:
                raise ValueError(f"Missing required columns: {missing}")
            
            update_manifest(output_path, "environmental_csv", env_url)
            logger.info(f"Environmental data fetched and validated: {output_path}")
            return output_path
            
        except (requests.RequestException, ValueError, DiskSpaceError, pd.errors.EmptyDataError) as e:
            logger.warning(f"Real environmental fetch failed: {e}. Falling back to mock data.")
            from data.mock_generator import generate_mock_environmental_data
            mock_output = generate_mock_environmental_data(str(mock_path))
            update_manifest(mock_output, "mock_environmental_csv", "mock_generator")
            return mock_output
    else:
        logger.info("No verified environmental URL available. Generating mock data.")
        from data.mock_generator import generate_mock_environmental_data
        mock_output = generate_mock_environmental_data(str(mock_path))
        update_manifest(mock_output, "mock_environmental_csv", "mock_generator")
        return mock_output

def fetch_compound_data() -> Path:
    """
    Fetch defense compound JSON data from verified URL or generate mock data.
    
    Returns:
        Path to the fetched/generated file
    """
    config = get_config()
    compound_url = config.verified_urls.get('compound')
    output_path = RAW_DIR / "compound_data.json"
    mock_path = RAW_DIR / "mock_compounds.json"
    
    if compound_url and compound_url in config.verified_datasets:
        try:
            # Estimate JSON size (conservative 5MB)
            estimated_size = 5 * 1024 * 1024
            fetch_url_content(compound_url, output_path, estimated_size)
            
            # Validate JSON schema
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            is_valid, missing = validate_compound_json_schema(data)
            if not is_valid:
                raise ValueError(f"Missing required keys: {missing}")
            
            update_manifest(output_path, "compound_json", compound_url)
            logger.info(f"Compound data fetched and validated: {output_path}")
            return output_path
            
        except (requests.RequestException, ValueError, json.JSONDecodeError, DiskSpaceError) as e:
            logger.warning(f"Real compound fetch failed: {e}. Falling back to mock data.")
            from data.mock_generator import generate_mock_compound_data
            mock_output = generate_mock_compound_data(str(mock_path))
            update_manifest(mock_output, "mock_compound_json", "mock_generator")
            return mock_output
    else:
        logger.info("No verified compound URL available. Generating mock data.")
        from data.mock_generator import generate_mock_compound_data
        mock_output = generate_mock_compound_data(str(mock_path))
        update_manifest(mock_output, "mock_compound_json", "mock_generator")
        return mock_output

def run_all_ingestion() -> Dict[str, Path]:
    """
    Run all ingestion tasks and return paths to generated files.
    
    Returns:
        Dictionary mapping data type to file path
    """
    ensure_directories()
    
    logger.info("Starting data ingestion pipeline...")
    
    paths = {
        'genomic': fetch_genomic_data(),
        'environmental': fetch_environmental_data(),
        'compound': fetch_compound_data()
    }
    
    logger.info(f"Ingestion complete. Files: {paths}")
    return paths

def main(*args, **kwargs) -> int:
    """
    Main entry point for ingestion module.
    
    Accepts flexible arguments to support various call patterns.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        result = run_all_ingestion()
        logger.info("Ingestion pipeline completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
