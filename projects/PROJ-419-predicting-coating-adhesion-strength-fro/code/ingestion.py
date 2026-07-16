import os
import time
import logging
from typing import Optional, List, Dict, Any
import requests
import pandas as pd
from urllib.parse import urlparse, parse_qs
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
ALLOWED_HOSTS = ['api.materialsproject.org', 'srdata.nist.gov']
VALID_SCHEMES = {'http', 'https'}

def validate_url_parameter(url: str) -> bool:
    """
    Validate API URL parameters for security and correctness.
    
    Args:
        url: The URL string to validate.
        
    Returns:
        bool: True if valid, False otherwise.
        
    Raises:
        ValueError: If the URL is invalid or contains unsafe parameters.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string.")
    
    try:
        parsed = urlparse(url)
        
        # Check scheme
        if parsed.scheme not in VALID_SCHEMES:
            raise ValueError(f"Invalid URL scheme: {parsed.scheme}. Must be one of {VALID_SCHEMES}.")
        
        # Check host
        if parsed.netloc not in ALLOWED_HOSTS:
            raise ValueError(f"Unauthorized host: {parsed.netloc}. Allowed hosts: {ALLOWED_HOSTS}.")
        
        # Check for SQL injection patterns in query parameters
        query_params = parse_qs(parsed.query)
        sql_injection_patterns = [
            r";\s*drop\s+",
            r";\s*delete\s+",
            r";\s*update\s+",
            r";\s*insert\s+",
            r"--\s*",
            r"/\*.*\*/",
            r"'\s*or\s+'1'\s*=\s*'1",
            r"'\s*or\s+1\s*=\s*1"
        ]
        
        for param_values in query_params.values():
            for value in param_values:
                for pattern in sql_injection_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        raise ValueError(f"Potential SQL injection detected in URL parameter: {value}")
        
        # Check for path traversal
        if '..' in parsed.path:
            raise ValueError("Path traversal detected in URL.")
        
        return True
        
    except Exception as e:
        raise ValueError(f"URL validation failed: {str(e)}")

def fetch_materials_project_data(api_key: str, formula: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch data from Materials Project API with strict input validation.
    
    Args:
        api_key: API key for authentication.
        formula: Optional chemical formula filter.
        
    Returns:
        List of material data dictionaries.
    """
    base_url = "https://api.materialsproject.org/v2/materials"
    
    # Validate API key format (basic sanity check)
    if not api_key or not isinstance(api_key, str) or len(api_key) < 10:
        raise ValueError("Invalid API key format.")
    
    # Validate formula if provided
    if formula:
        # Simple chemical formula validation (letters, numbers, parentheses, spaces)
        if not re.match(r'^[A-Za-z0-9\s\(\)]+$', formula):
            raise ValueError(f"Invalid chemical formula format: {formula}")
    
    url = f"{base_url}?api_key={api_key}"
    if formula:
        url += f"&formula={formula}"
    
    # Validate the constructed URL
    validate_url_parameter(url)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Failed to fetch Materials Project data after {MAX_RETRIES} attempts: {e}")
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
    
    return []

def fetch_nist_surface_metrology_data(dataset_id: str) -> List[Dict[str, Any]]:
    """
    Fetch data from NIST Surface Metrology Repository with input validation.
    
    Args:
        dataset_id: Identifier for the dataset.
        
    Returns:
        List of surface metrology data dictionaries.
    """
    base_url = "https://srdata.nist.gov/surface-metrology/api/v1/datasets"
    
    # Validate dataset_id (alphanumeric + hyphen/underscore)
    if not dataset_id or not isinstance(dataset_id, str):
        raise ValueError("Dataset ID must be a non-empty string.")
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', dataset_id):
        raise ValueError(f"Invalid dataset ID format: {dataset_id}")
    
    url = f"{base_url}/{dataset_id}"
    
    # Validate the constructed URL
    validate_url_parameter(url)
    
    headers = {
        "Accept": "application/json"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            # Assuming NIST returns a list or a dict with a 'data' key
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'data' in data:
                return data['data']
            else:
                logger.warning(f"Unexpected NIST response format: {data}")
                return []
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Failed to fetch NIST data after {MAX_RETRIES} attempts: {e}")
                raise
            time.sleep(2 ** attempt)
    
    return []

def fetch_open_access_literature_data(source_url: str, query_params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """
    Fetch data from open-access literature sources with input validation.
    
    Args:
        source_url: Base URL of the literature source.
        query_params: Optional dictionary of query parameters.
        
    Returns:
        List of literature data dictionaries.
    """
    if not source_url or not isinstance(source_url, str):
        raise ValueError("Source URL must be a non-empty string.")
    
    # Validate base URL
    validate_url_parameter(source_url)
    
    # Build final URL with parameters
    final_url = source_url
    if query_params:
        # Validate parameter values
        for key, value in query_params.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(f"Query parameter {key} must be string key-value pairs.")
            # Check for injection in values
            sql_patterns = [r";", r"--", r"/\*"]
            for pattern in sql_patterns:
                if pattern in value:
                    raise ValueError(f"Potential injection detected in query parameter: {key}={value}")
        
        # Safe URL encoding
        import urllib.parse
        query_string = urllib.parse.urlencode(query_params)
        final_url = f"{source_url}?{query_string}"
    
    # Validate final URL
    validate_url_parameter(final_url)
    
    headers = {
        "Accept": "application/json",
        "User-Agent": "llmXive-CoatingAdhesion/1.0"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(final_url, headers=headers, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            # Handle different response formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Try common keys
                for key in ['data', 'results', 'items', 'records']:
                    if key in data and isinstance(data[key], list):
                        return data[key]
                return [data]
            else:
                return []
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Failed to fetch literature data after {MAX_RETRIES} attempts: {e}")
                raise
            time.sleep(2 ** attempt)
    
    return []

def filter_astm_d4541_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter records to strictly ASTM D4541 pull-off test results.
    
    Args:
        records: List of raw data records.
        
    Returns:
        Filtered list of ASTM D4541 records.
    """
    filtered = []
    astm_keywords = ['astm d4541', 'd4541', 'pull-off', 'pull off']
    
    for record in records:
        test_method = str(record.get('test_method', '')).lower()
        test_type = str(record.get('test_type', '')).lower()
        
        if any(keyword in test_method for keyword in astm_keywords) or \
           any(keyword in test_type for keyword in astm_keywords):
            filtered.append(record)
    
    logger.info(f"Filtered {len(records)} records to {len(filtered)} ASTM D4541 records.")
    return filtered

def exclude_missing_target_records(records: List[Dict[str, Any]], target_column: str = 'adhesion_strength') -> List[Dict[str, Any]]:
    """
    Exclude records with missing target variables.
    
    Args:
        records: List of data records.
        target_column: Name of the target column.
        
    Returns:
        List of records with valid target values.
    """
    valid_records = []
    missing_count = 0
    
    for record in records:
        target_val = record.get(target_column)
        if target_val is not None and pd.notna(target_val):
            try:
                float(target_val)
                valid_records.append(record)
            except (ValueError, TypeError):
                missing_count += 1
        else:
            missing_count += 1
    
    logger.info(f"Excluded {missing_count} records with missing target values.")
    return valid_records

def resolve_duplicates(records: List[Dict[str, Any]], date_column: str = 'date', sample_count_column: str = 'sample_count') -> List[Dict[str, Any]]:
    """
    Resolve duplicates by keeping the most recent or highest sample count.
    
    Args:
        records: List of data records.
        date_column: Column name for date comparison.
        sample_count_column: Column name for sample count comparison.
        
    Returns:
        Deduplicated list of records.
    """
    unique_map = {}
    
    for record in records:
        # Create a simple hash key based on composition and surface features
        key_parts = []
        for field in ['composition', 'surface_roughness', 'material_type']:
            if field in record:
                key_parts.append(str(record[field]))
        key = "|".join(key_parts)
        
        if key not in unique_map:
            unique_map[key] = record
        else:
            existing = unique_map[key]
            
            # Compare dates
            existing_date = pd.to_datetime(existing.get(date_column, '1900-01-01'), errors='coerce')
            new_date = pd.to_datetime(record.get(date_column, '1900-01-01'), errors='coerce')
            
            if pd.notna(new_date) and (pd.isna(existing_date) or new_date > existing_date):
                unique_map[key] = record
            elif pd.notna(new_date) and pd.notna(existing_date) and new_date == existing_date:
                # Compare sample counts
                existing_count = int(existing.get(sample_count_column, 0) or 0)
                new_count = int(record.get(sample_count_column, 0) or 0)
                if new_count > existing_count:
                    unique_map[key] = record
    
    logger.info(f"Resolved duplicates: {len(records)} -> {len(unique_map)} records.")
    return list(unique_map.values())

def sample_dataset_to_memory_limit(records: List[Dict[str, Any]], max_rows: int = 5000) -> List[Dict[str, Any]]:
    """
    Sample dataset to memory limit if raw volume exceeds limit.
    
    Args:
        records: List of data records.
        max_rows: Maximum number of rows to keep.
        
    Returns:
        Sampled list of records.
    """
    if len(records) <= max_rows:
        return records
    
    sampled = records[:max_rows]
    logger.warning(f"Dataset exceeded memory limit. Sampled {len(records)} -> {max_rows} rows.")
    return sampled

def exclude_missing_surface_roughness(records: List[Dict[str, Any]], roughness_column: str = 'surface_roughness_rms') -> List[Dict[str, Any]]:
    """
    Exclude records with missing surface roughness data.
    
    Args:
        records: List of data records.
        roughness_column: Column name for surface roughness.
        
    Returns:
        List of records with valid surface roughness.
    """
    valid_records = []
    missing_count = 0
    
    for record in records:
        roughness_val = record.get(roughness_column)
        if roughness_val is not None and pd.notna(roughness_val):
            try:
                float(roughness_val)
                valid_records.append(record)
            except (ValueError, TypeError):
                missing_count += 1
        else:
            missing_count += 1
    
    logger.info(f"Excluded {missing_count} records with missing surface roughness.")
    return valid_records

def process_ingestion_data(input_dir: str, output_path: str) -> None:
    """
    Main ingestion pipeline: fetch, filter, clean, and save data.
    
    Args:
        input_dir: Directory containing raw data (if applicable).
        output_path: Path to save the processed dataset.
    """
    logger.info("Starting data ingestion pipeline...")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Example: Fetch from Materials Project (requires API key in environment)
    # In a real scenario, this would be configured via a config file
    api_key = os.getenv("MATERIALS_PROJECT_API_KEY")
    if api_key:
        try:
            mp_data = fetch_materials_project_data(api_key, formula="TiO2")
            logger.info(f"Fetched {len(mp_data)} records from Materials Project.")
        except Exception as e:
            logger.error(f"Failed to fetch Materials Project data: {e}")
            mp_data = []
    else:
        logger.warning("MATERIALS_PROJECT_API_KEY not set. Skipping Materials Project fetch.")
        mp_data = []
    
    # Combine all sources (placeholder for NIST and Literature)
    all_records = mp_data
    
    if not all_records:
        logger.warning("No data fetched from any source. Pipeline cannot proceed.")
        return
    
    # Apply filters
    filtered = filter_astm_d4541_records(all_records)
    filtered = exclude_missing_target_records(filtered)
    filtered = resolve_duplicates(filtered)
    filtered = exclude_missing_surface_roughness(filtered)
    filtered = sample_dataset_to_memory_limit(filtered)
    
    # Convert to DataFrame
    df = pd.DataFrame(filtered)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed dataset to {output_path} with {len(df)} rows.")

def main():
    """Main entry point for ingestion script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest and process coating adhesion data.")
    parser.add_argument("--input-dir", type=str, default="data/raw", help="Input directory for raw data.")
    parser.add_argument("--output", type=str, default="data/processed/coating_adhesion_dataset.csv", help="Output path for processed dataset.")
    
    args = parser.parse_args()
    
    try:
        process_ingestion_data(args.input_dir, args.output)
        logger.info("Ingestion pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
