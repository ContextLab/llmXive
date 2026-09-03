import json
import os
import re
import shutil
import tarfile
import zipfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import yaml
import requests
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """
    Load the manifest file (YAML or JSON).
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported manifest format: {path.suffix}")

def validate_manifest(manifest: Dict[str, Any], schema_path: str) -> Tuple[bool, List[str]]:
    """
    Validate the manifest against a JSON Schema (loaded from YAML).
    Returns (is_valid, list_of_errors).
    """
    try:
        import jsonschema
    except ImportError:
        logger.error("jsonschema library is required for validation. Install with: pip install jsonschema")
        return False, ["jsonschema library missing"]

    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    errors = []
    try:
        jsonschema.validate(instance=manifest, schema=schema)
        logger.info("Manifest validation successful.")
        return True, []
    except jsonschema.exceptions.ValidationError as e:
        errors.append(f"Validation Error: {e.message} at path: {list(e.path)}")
        return False, errors

def fetch_dataset(dataset_url: str, output_dir: str) -> str:
    """
    Fetch a dataset from a URL and save it to the output directory.
    Returns the path to the downloaded file.
    """
    if not dataset_url:
        raise ValueError("Dataset URL is required.")

    os.makedirs(output_dir, exist_ok=True)
    filename = dataset_url.split('/')[-1]
    local_path = os.path.join(output_dir, filename)

    logger.info(f"Downloading {dataset_url} to {local_path}...")
    try:
        response = requests.get(dataset_url, stream=True)
        response.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logger.info(f"Downloaded successfully: {local_path}")
        return local_path
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to download dataset: {e}")

def find_supplementary_files(base_dir: str, patterns: List[str]) -> List[str]:
    """
    Find supplementary files in the base directory matching given patterns.
    """
    found_files = []
    base = Path(base_dir)
    if not base.exists():
        return found_files

    for pattern in patterns:
        # Simple glob matching
        files = list(base.glob(pattern))
        found_files.extend([str(f) for f in files])
    
    return found_files

def parse_pdf_for_metadata(pdf_path: str) -> Dict[str, Any]:
    """
    Extract metadata (temperature, solvent, etc.) from a PDF file.
    Requires PyPDF2 or pdfplumber.
    """
    metadata = {}
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            
            # Regex patterns for extraction
            temp_match = re.search(r'Temperature:\s*([\d.]+)\s*°C', text)
            if temp_match:
                metadata['temperature'] = float(temp_match.group(1))
            
            solvent_match = re.search(r'Solvent:\s*(\w+)', text)
            if solvent_match:
                metadata['solvent'] = solvent_match.group(1)
                
            yield_match = re.search(r'Yield.*?([\d.]+)%', text)
            if yield_match:
                metadata['yield'] = float(yield_match.group(1))
                
    except ImportError:
        logger.warning("PyPDF2 not installed. Skipping PDF parsing.")
    except Exception as e:
        logger.error(f"Error parsing PDF {pdf_path}: {e}")
    
    return metadata

def parse_csv_for_metadata(csv_path: str) -> List[Dict[str, Any]]:
    """
    Parse a CSV file for experimental data.
    Returns a list of row dictionaries.
    """
    try:
        df = pd.read_csv(csv_path)
        return df.to_dict(orient='records')
    except Exception as e:
        logger.error(f"Error parsing CSV {csv_path}: {e}")
        return []

def process_manifest_entry(entry: Dict[str, Any], data_dir: str) -> Dict[str, Any]:
    """
    Process a single entry from the manifest: fetch data, find supplements, parse metadata.
    """
    result = {
        'doi': entry.get('doi'),
        'status': 'pending',
        'data_path': None,
        'supplementary_files': [],
        'extracted_metadata': {}
    }

    if 'dataset_url' in entry and entry['dataset_url']:
        try:
            data_path = fetch_dataset(entry['dataset_url'], data_dir)
            result['data_path'] = data_path
            result['status'] = 'fetched'
        except Exception as e:
            result['status'] = 'fetch_failed'
            result['error'] = str(e)
    
    if 'supplementary_files' in entry:
        if result['data_path']:
            base_dir = os.path.dirname(result['data_path'])
        else:
            base_dir = data_dir
        
        supplements = find_supplementary_files(base_dir, entry['supplementary_files'])
        result['supplementary_files'] = supplements

    # Try to parse PDF if available
    for supp in result['supplementary_files']:
        if supp.endswith('.pdf'):
            meta = parse_pdf_for_metadata(supp)
            if meta:
                result['extracted_metadata'].update(meta)
                break

    return result

def verify_dataset_variables(df: pd.DataFrame, required_vars: List[str]) -> Tuple[bool, List[str]]:
    """
    Verify that the dataset contains all required variables (columns).
    """
    missing = [var for var in required_vars if var not in df.columns]
    if missing:
        logger.warning(f"Missing variables in dataset: {missing}")
        return False, missing
    return True, []

def ingest_pipeline(manifest_path: str, schema_path: str, data_dir: str, output_path: str):
    """
    Main pipeline: Load manifest, validate, process entries, save results.
    """
    logger.info(f"Starting ingest pipeline. Manifest: {manifest_path}, Schema: {schema_path}")
    
    # 1. Load Manifest
    try:
        manifest = load_manifest(manifest_path)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return

    # 2. Validate Manifest
    is_valid, errors = validate_manifest(manifest, schema_path)
    if not is_valid:
        logger.error("Manifest validation failed:")
        for err in errors:
            logger.error(f"  - {err}")
        raise RuntimeError("Manifest validation failed. Halting pipeline.")
    
    logger.info("Manifest validation passed.")

    # 3. Process Entries
    results = []
    for entry in manifest.get('papers', []):
        logger.info(f"Processing paper: {entry.get('doi')}")
        processed = process_manifest_entry(entry, data_dir)
        results.append(processed)

    # 4. Save Results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Ingest pipeline complete. Results saved to {output_path}")

def main():
    """
    Entry point for running the ingest pipeline from command line or script.
    """
    # Default paths relative to project root
    manifest_path = "data/manifest.yaml"
    schema_path = "contracts/PaperManifest.schema.yaml"
    data_dir = "data/processed"
    output_path = "artifacts/logs/ingest_results.json"

    # Allow overrides via environment or args if needed
    import sys
    if len(sys.argv) > 1:
        manifest_path = sys.argv[1]
    if len(sys.argv) > 2:
        schema_path = sys.argv[2]

    try:
        ingest_pipeline(manifest_path, schema_path, data_dir, output_path)
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
