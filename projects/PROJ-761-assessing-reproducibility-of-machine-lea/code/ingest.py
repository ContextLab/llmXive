import json
import os
import re
import shutil
import tarfile
import zipfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Ensure logging is configured if not already
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for required dataset variables
REQUIRED_VARIABLES = ['smiles', 'yield', 'covariates']
# Common variations for yield column
YIELD_VARIATIONS = ['yield', 'yield_pct', 'percent_yield', 'yield_percent', 'product_yield']

def load_manifest(manifest_path: str) -> Dict[str, Any]:
    """
    Load a YAML manifest file and return its contents as a dictionary.
    """
    import yaml
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_manifest(manifest: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the manifest structure and required fields.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Check top-level required fields
    required_top_level = ['doi', 'repo_url', 'dataset_name', 'reported_metrics']
    for field in required_top_level:
        if field not in manifest:
            errors.append(f"Missing required top-level field: {field}")
    
    # Check dataset section
    if 'dataset' not in manifest:
        errors.append("Missing 'dataset' section in manifest")
        return False, errors
    
    dataset = manifest['dataset']
    
    # Check for required dataset variables in schema or column list
    # The schema might be defined in 'schema' or 'columns'
    schema = dataset.get('schema', dataset.get('columns', {}))
    
    # Normalize schema to a list of column names if it's a dict
    if isinstance(schema, dict):
        columns = list(schema.keys())
    elif isinstance(schema, list):
        columns = schema
    else:
        errors.append("Dataset schema must be a list of columns or a dict of column definitions")
        return False, errors
    
    # Check for SMILES
    smiles_found = False
    smiles_variations = ['smiles', 'smile', 'mol', 'molecule', 'compound_smiles']
    for var in smiles_variations:
        if any(var.lower() == col.lower() for col in columns):
            smiles_found = True
            break
    
    if not smiles_found:
        errors.append("Missing required variable: SMILES (or variations: smiles, smile, mol, molecule, compound_smiles)")
    
    # Check for Yield
    yield_found = False
    for var in YIELD_VARIATIONS:
        if any(var.lower() == col.lower() for col in columns):
            yield_found = True
            break
    
    if not yield_found:
        errors.append(f"Missing required variable: yield (or variations: {', '.join(YIELD_VARIATIONS)})")
    
    # Check for covariates (reaction conditions)
    # Covariates might be a single column or multiple condition columns
    covariate_keywords = ['temperature', 'solvent', 'catalyst', 'loading', 'time', 'pressure', 'condition', 'reagent']
    covariate_found = False
    
    for col in columns:
        col_lower = col.lower()
        if 'covariate' in col_lower or 'condition' in col_lower:
            covariate_found = True
            break
        if any(kw in col_lower for kw in covariate_keywords):
            covariate_found = True
            break
    
    # Also check if there's a specific 'covariates' column
    if any('covariate' in col.lower() for col in columns):
        covariate_found = True
    
    if not covariate_found:
        errors.append("Missing required variable: covariates (reaction conditions like temperature, solvent, catalyst, etc.)")
    
    return len(errors) == 0, errors

def fetch_dataset(dataset_info: Dict[str, Any], target_dir: str) -> str:
    """
    Fetch dataset from URL or local path specified in manifest.
    Returns path to downloaded/extracted data.
    """
    source_type = dataset_info.get('source_type', 'url')
    source_path = dataset_info.get('source_path')
    
    if not source_path:
        raise ValueError("Dataset source path not specified in manifest")
    
    os.makedirs(target_dir, exist_ok=True)
    
    if source_type == 'url':
        logger.info(f"Fetching dataset from URL: {source_path}")
        import requests
        filename = os.path.basename(source_path.split('?')[0])
        if not filename:
            filename = 'dataset.zip'
        
        local_path = os.path.join(target_dir, filename)
        
        response = requests.get(source_path, stream=True)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded dataset to {local_path}")
        return local_path
    
    elif source_type == 'local':
        logger.info(f"Using local dataset: {source_path}")
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Local dataset not found: {source_path}")
        
        # Copy to target directory
        dest_path = os.path.join(target_dir, os.path.basename(source_path))
        shutil.copy2(source_path, dest_path)
        return dest_path
    
    else:
        raise ValueError(f"Unknown source type: {source_type}")

def find_supplementary_files(base_dir: str, patterns: Optional[List[str]] = None) -> List[str]:
    """
    Find supplementary data files matching patterns.
    Default patterns: *_supp.csv, *_data.parquet, *_supplemental.*
    """
    if patterns is None:
        patterns = [
            '*_supp.csv',
            '*_supp.parquet',
            '*_data.parquet',
            '*_supplemental.*',
            '*_raw.csv',
            '*_raw.parquet'
        ]
    
    found_files = []
    base_path = Path(base_dir)
    
    for pattern in patterns:
        matches = list(base_path.rglob(pattern))
        found_files.extend([str(m) for m in matches])
    
    return found_files

def process_manifest_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single manifest entry to extract and validate dataset.
    Returns a dictionary with dataset info and validation results.
    """
    result = {
        'doi': entry.get('doi'),
        'dataset_name': entry.get('dataset_name'),
        'validation_status': 'unknown',
        'missing_variables': [],
        'data_path': None,
        'errors': []
    }
    
    try:
        # Validate manifest structure
        is_valid, errors = validate_manifest(entry)
        
        if not is_valid:
            result['validation_status'] = 'failed'
            result['errors'] = errors
            
            # Extract missing variables from errors
            for error in errors:
                if 'Missing required variable' in error:
                    # Extract the variable name from the error message
                    match = re.search(r'Missing required variable:\s*([^(]+)', error)
                    if match:
                        var_name = match.group(1).strip()
                        result['missing_variables'].append(var_name)
            
            logger.warning(f"Manifest validation failed for {entry.get('doi')}: {errors}")
            return result
        
        result['validation_status'] = 'passed'
        
        # Fetch dataset if validation passed
        if 'dataset' in entry:
            dataset_info = entry['dataset']
            target_dir = os.path.join('data', 'raw', entry.get('dataset_name', 'unknown'))
            
            data_path = fetch_dataset(dataset_info, target_dir)
            result['data_path'] = data_path
            
            # Find supplementary files
            supp_files = find_supplementary_files(target_dir)
            if supp_files:
                result['supplementary_files'] = supp_files
                logger.info(f"Found {len(supp_files)} supplementary files for {entry.get('doi')}")
        
        return result
        
    except Exception as e:
        result['validation_status'] = 'error'
        result['errors'].append(str(e))
        logger.error(f"Error processing manifest entry for {entry.get('doi')}: {e}")
        return result

def verify_dataset_variables(data_path: str, required_vars: List[str]) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Verify that the dataset at data_path contains all required variables.
    Returns (all_present, list_of_missing, detailed_info).
    
    This function attempts to load the dataset and check for required columns.
    It supports CSV, Parquet, and JSON formats.
    """
    import pandas as pd
    import json
    
    missing_vars = []
    detailed_info = {
        'file_type': None,
        'columns_found': [],
        'row_count': 0
    }
    
    try:
        # Determine file type and load
        path = Path(data_path)
        suffix = path.suffix.lower()
        
        if suffix == '.csv':
            df = pd.read_csv(data_path)
            detailed_info['file_type'] = 'csv'
        elif suffix in ['.parquet', '.pq']:
            df = pd.read_parquet(data_path)
            detailed_info['file_type'] = 'parquet'
        elif suffix == '.json':
            df = pd.read_json(data_path)
            detailed_info['file_type'] = 'json'
        elif suffix in ['.zip', '.tar', '.gz']:
            # Try to extract and find CSV/Parquet inside
            extract_dir = data_path + '_extracted'
            os.makedirs(extract_dir, exist_ok=True)
            
            if suffix == '.zip':
                with zipfile.ZipFile(data_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            elif suffix in ['.tar', '.gz']:
                with tarfile.open(data_path, 'r:*') as tar_ref:
                    tar_ref.extractall(extract_dir)
            
            # Look for data files in extracted directory
            data_files = list(Path(extract_dir).rglob('*.csv')) + list(Path(extract_dir).rglob('*.parquet'))
            
            if data_files:
                df = pd.read_csv(str(data_files[0])) if str(data_files[0]).endswith('.csv') else pd.read_parquet(str(data_files[0]))
                detailed_info['file_type'] = 'extracted'
            else:
                raise ValueError("No supported data files found in archive")
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
        
        # Get column names (normalize to lowercase for comparison)
        columns = [str(col).lower() for col in df.columns]
        detailed_info['columns_found'] = list(df.columns)
        detailed_info['row_count'] = len(df)
        
        # Check for required variables
        for var in required_vars:
            var_lower = var.lower()
            
            if var_lower == 'smiles':
                # Check for SMILES variations
                smiles_found = any(
                    any(v.lower() == col for v in ['smiles', 'smile', 'mol', 'molecule', 'compound_smiles'])
                    for col in columns
                )
                if not smiles_found:
                    missing_vars.append('SMILES')
            
            elif var_lower == 'yield':
                # Check for yield variations
                yield_found = any(
                    any(v.lower() == col for v in YIELD_VARIATIONS)
                    for col in columns
                )
                if not yield_found:
                    missing_vars.append('yield')
            
            elif var_lower == 'covariates':
                # Check for covariate keywords
                covariate_keywords = ['temperature', 'solvent', 'catalyst', 'loading', 'time', 'pressure', 'condition', 'reagent', 'covariate']
                covariate_found = any(
                    any(kw in col for kw in covariate_keywords)
                    for col in columns
                )
                if not covariate_found:
                    missing_vars.append('covariates')
            else:
                # Direct match for other variables
                if not any(var_lower == col for col in columns):
                    missing_vars.append(var)
        
        all_present = len(missing_vars) == 0
        return all_present, missing_vars, detailed_info
        
    except Exception as e:
        logger.error(f"Error verifying dataset variables for {data_path}: {e}")
        return False, required_vars, {'error': str(e)}

def ingest_pipeline(manifest_path: str, output_dir: str = 'artifacts/reports') -> Dict[str, Any]:
    """
    Main ingestion pipeline that:
    1. Loads and validates the manifest
    2. For each entry, verifies dataset variables against the manifest schema
    3. Generates detailed flags for missing variables
    4. Records results in ReproResult format with "Data Unavailable" status if needed
    
    Returns a summary dictionary of all processed entries.
    """
    import json
    from datetime import datetime
    
    # Load manifest
    logger.info(f"Loading manifest from {manifest_path}")
    manifest = load_manifest(manifest_path)
    
    # Prepare results
    results = {
        'pipeline_run': {
            'timestamp': datetime.now().isoformat(),
            'manifest_path': manifest_path,
            'total_entries': 0,
            'valid_entries': 0,
            'failed_entries': 0,
            'data_unavailable_entries': 0
        },
        'entries': []
    }
    
    # Process each entry in the manifest
    entries = manifest.get('entries', []) if isinstance(manifest, dict) else manifest
    if not isinstance(entries, list):
        entries = [entries] if isinstance(entries, dict) else []
    
    results['pipeline_run']['total_entries'] = len(entries)
    
    for entry in entries:
        doi = entry.get('doi', 'unknown')
        logger.info(f"Processing entry: {doi}")
        
        # Process manifest entry
        processed = process_manifest_entry(entry)
        
        # If validation passed, verify actual dataset variables
        if processed['validation_status'] == 'passed' and processed.get('data_path'):
            all_present, missing_vars, details = verify_dataset_variables(
                processed['data_path'], 
                REQUIRED_VARIABLES
            )
            
            if not all_present:
                processed['validation_status'] = 'data_unavailable'
                processed['missing_variables'] = missing_vars
                processed['data_details'] = details
                results['pipeline_run']['data_unavailable_entries'] += 1
                logger.warning(f"Data unavailable for {doi}: missing {missing_vars}")
            else:
                processed['data_details'] = details
                results['pipeline_run']['valid_entries'] += 1
        elif processed['validation_status'] == 'failed':
            results['pipeline_run']['failed_entries'] += 1
        else:
            results['pipeline_run']['failed_entries'] += 1
        
        # Add to results
        results['entries'].append({
            'doi': doi,
            'dataset_name': entry.get('dataset_name'),
            'status': processed['validation_status'],
            'missing_variables': processed.get('missing_variables', []),
            'errors': processed.get('errors', []),
            'data_path': processed.get('data_path'),
            'data_details': processed.get('data_details', {})
        })
    
    # Save results to output directory
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'ingestion_results.json')
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Ingestion pipeline complete. Results saved to {output_path}")
    return results

def main():
    """
    Entry point for the ingestion pipeline.
    Usage: python -m code.ingest --manifest data/manifest.yaml --output artifacts/reports
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Ingest and validate research datasets')
    parser.add_argument('--manifest', type=str, default='data/manifest.yaml',
                      help='Path to the manifest file')
    parser.add_argument('--output', type=str, default='artifacts/reports',
                      help='Output directory for results')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.manifest):
        logger.error(f"Manifest file not found: {args.manifest}")
        return 1
    
    try:
        results = ingest_pipeline(args.manifest, args.output)
        
        # Print summary
        print(f"\nIngestion Pipeline Summary:")
        print(f"  Total entries: {results['pipeline_run']['total_entries']}")
        print(f"  Valid entries: {results['pipeline_run']['valid_entries']}")
        print(f"  Failed entries: {results['pipeline_run']['failed_entries']}")
        print(f"  Data unavailable entries: {results['pipeline_run']['data_unavailable_entries']}")
        
        if results['pipeline_run']['data_unavailable_entries'] > 0:
            print(f"\n⚠️  WARNING: {results['pipeline_run']['data_unavailable_entries']} entries have missing required variables.")
            print("These are flagged as 'Data Unavailable' in the results.")
        
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())