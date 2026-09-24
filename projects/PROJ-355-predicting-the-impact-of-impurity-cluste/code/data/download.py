import os
import json
import logging
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import yaml
import requests
from jsonschema import validate, ValidationError as JsonSchemaValidationError

# Import from project config
from config import get_project_root, get_data_paths
from validators import validate_citations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON/YAML schema from disk."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        if schema_path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif schema_path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {schema_path.suffix}")

def validate_dataset(data_path: Path, schema_path: Path) -> bool:
    """
    Validate a dataset file against a JSON Schema.
    
    Args:
        data_path: Path to the data file (JSON or YAML) to validate.
        schema_path: Path to the schema file (JSON or YAML).
        
    Returns:
        True if validation passes.
        
    Raises:
        JsonSchemaValidationError: If data fails schema validation.
        FileNotFoundError: If data or schema files are missing.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Load data
    with open(data_path, 'r', encoding='utf-8') as f:
        if data_path.suffix in ['.yaml', '.yml']:
            data = yaml.safe_load(f)
        elif data_path.suffix == '.json':
            data = json.load(f)
        else:
            raise ValueError(f"Unsupported data format: {data_path.suffix}")
    
    # Validate
    try:
        validate(instance=data, schema=schema)
        logger.info(f"Dataset validation successful: {data_path}")
        return True
    except JsonSchemaValidationError as e:
        logger.error(f"Dataset validation failed for {data_path}: {e.message}")
        logger.error(f"Error path: {list(e.path)}")
        raise

def download_bulk_configs(url: str, max_retries: int = 3) -> Path:
    """
    Download bulk configurations from a URL with retry logic and citation validation.
    
    Args:
        url: URL to the dataset.
        max_retries: Maximum number of retry attempts.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        FileNotFoundError: If the URL is invalid or data is unavailable after retries.
    """
    # Validate citations before attempting download
    metadata_path = get_project_root() / 'data' / 'metadata.yaml'
    validation_result = validate_citations(url, str(metadata_path))
    
    if not validation_result.get('success', False):
        logger.error(f"[DATA_UNAVAILABLE] URL={url} attempts={max_retries} reason={validation_result.get('message')}")
        # Write to inaccessible manifest
        manifest_path = get_project_root() / 'data' / 'inaccessible_manifest.json'
        manifest_entry = {
            'url': url,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'reason': validation_result.get('message')
        }
        
        manifest_data = []
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)
        
        manifest_data.append(manifest_entry)
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest_data, f, indent=2)
        
        raise FileNotFoundError(f"[DATA_UNAVAILABLE] URL={url} after {max_retries} attempts")
    
    # Attempt download with retries
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Downloading {url} (attempt {attempt}/{max_retries})")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to data/raw
            data_paths = get_data_paths()
            raw_dir = data_paths['raw']
            raw_dir.mkdir(parents=True, exist_ok=True)
            
            filename = url.split('/')[-1] or 'downloaded_data.json'
            output_path = raw_dir / filename
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded to {output_path}")
            
            # Validate against schema BEFORE returning
            schema_path = get_project_root() / 'contracts' / 'dataset.schema.yaml'
            if schema_path.exists():
                validate_dataset(output_path, schema_path)
            else:
                logger.warning(f"Schema file not found at {schema_path}, skipping validation")
            
            return output_path
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Download attempt {attempt} failed: {e}")
            if attempt == max_retries:
                logger.error(f"[DATA_UNAVAILABLE] URL={url} attempts={max_retries}")
                
                # Write to inaccessible manifest
                manifest_path = get_project_root() / 'data' / 'inaccessible_manifest.json'
                manifest_entry = {
                    'url': url,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'reason': str(e)
                }
                
                manifest_data = []
                if manifest_path.exists():
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest_data = json.load(f)
                
                manifest_data.append(manifest_entry)
                
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    json.dump(manifest_data, f, indent=2)
                
                # Attempt backup
                backup_path = get_project_root() / 'data' / 'raw' / 'backup' / filename
                if backup_path.exists():
                    logger.info(f"Using backup from {backup_path}")
                    return backup_path
                
                raise FileNotFoundError(f"[DATA_UNAVAILABLE] URL={url} after {max_retries} attempts")
            time.sleep(2 ** attempt)  # Exponential backoff

def main():
    """CLI entry point for download module."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download bulk configurations')
    parser.add_argument('--url', type=str, required=True, help='URL to download from')
    parser.add_argument('--max-retries', type=int, default=3, help='Max retry attempts')
    
    args = parser.parse_args()
    
    try:
        output_path = download_bulk_configs(args.url, args.max_retries)
        print(f"Success: {output_path}")
    except FileNotFoundError as e:
        print(f"Failed: {e}")
        exit(1)

if __name__ == '__main__':
    main()
