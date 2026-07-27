import os
import ftplib
import csv
import io
import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SWPC_FTP_HOST = "ftp.swpc.noaa.gov"
SWPC_FTP_DIR = "pub/lists/indices/"
KP_URL_TEMPLATE = "https://services.swpc.noaa.gov/products/noaa-planetary-k-indices.csv"
KP_DATA_PATH = "data/raw/kp_indices.csv"
MANIFEST_PATH = "data/source_manifest.yaml"

def ensure_directories():
    """Ensure required directories exist."""
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("results", exist_ok=True)

def log_message(msg: str):
    """Log a message with timestamp."""
    logger.info(msg)

def load_manifest() -> Dict[str, Any]:
    """Load the source manifest YAML file."""
    if not os.path.exists(MANIFEST_PATH):
        return {"sources": {}}
    try:
        with open(MANIFEST_PATH, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        return {"sources": {}}

def save_manifest(manifest: Dict[str, Any]):
    """Save the source manifest YAML file."""
    with open(MANIFEST_PATH, 'w') as f:
        yaml.dump(manifest, f, default_flow_style=False)

def update_manifest_entry(source_name: str, status: str, details: str = None, checksum: str = None):
    """Update a specific entry in the source manifest."""
    manifest = load_manifest()
    if "sources" not in manifest:
        manifest["sources"] = {}
    
    manifest["sources"][source_name] = {
        "status": status,
        "last_updated": datetime.now().isoformat(),
        "details": details or "",
        "checksum": checksum or ""
    }
    save_manifest(manifest)

def connect_to_swpc() -> Optional[ftplib.FTP]:
    """Connect to NOAA SWPC FTP server."""
    try:
        ftp = ftplib.FTP(SWPC_FTP_HOST)
        ftp.login()
        logger.info(f"Successfully connected to {SWPC_FTP_HOST}")
        return ftp
    except Exception as e:
        logger.error(f"Failed to connect to SWPC FTP: {e}")
        return None

def fetch_dst_indices() -> List[Dict[str, Any]]:
    """
    Fetch Dst indices from NOAA SWPC.
    This is a stub implementation as per task T013 requirements.
    """
    log_message("Fetching Dst indices...")
    # Placeholder: In a real implementation, this would download from FTP
    # For now, return empty list to indicate no data
    return []

def fetch_dst_indices_http() -> List[Dict[str, Any]]:
    """
    Fetch Dst indices via HTTP as a fallback.
    """
    log_message("Attempting to fetch Dst indices via HTTP...")
    # Placeholder: In a real implementation, this would use requests
    return []

def write_dst_data(data: List[Dict[str, Any]], path: str = "data/raw/dst_indices.csv"):
    """
    Write Dst data to CSV.
    This is a stub implementation as per task T013 requirements.
    """
    log_message(f"Writing Dst data to {path}...")
    # Placeholder: In a real implementation, this would write to CSV
    pass

def fetch_kp_indices() -> List[Dict[str, Any]]:
    """
    Fetch Kp indices from NOAA SWPC.
    
    Retrieves the latest Kp index data from the official NOAA SWPC product
    URL. The data is returned as a list of dictionaries with keys:
    'time', 'kp', 'ap'.
    
    Returns:
        List[Dict[str, Any]]: List of Kp index records.
        
    Raises:
        RuntimeError: If the fetch fails and no data can be retrieved.
    """
    log_message("Fetching Kp indices from NOAA SWPC...")
    
    try:
        response = requests.get(KP_URL_TEMPLATE, timeout=30)
        response.raise_for_status()
        
        # Parse CSV content
        reader = csv.DictReader(io.StringIO(response.text))
        data = []
        
        for row in reader:
            # Clean up the data
            clean_row = {
                'time': row.get('Time', '').strip(),
                'kp': row.get('Kp', '').strip(),
                'ap': row.get('Ap', '').strip()
            }
            
            # Only include rows with valid data
            if clean_row['time'] and clean_row['kp']:
                data.append(clean_row)
        
        if not data:
            raise ValueError("No valid data found in response")
        
        log_message(f"Successfully fetched {len(data)} Kp records")
        return data
        
    except requests.exceptions.RequestException as e:
        log_message(f"Failed to fetch Kp indices via HTTP: {e}")
        raise RuntimeError(f"Failed to fetch Kp indices: {e}")
    except Exception as e:
        log_message(f"Error parsing Kp indices: {e}")
        raise RuntimeError(f"Error parsing Kp indices: {e}")

def fetch_kp_indices_http() -> List[Dict[str, Any]]:
    """
    Alias for fetch_kp_indices to maintain API consistency.
    """
    return fetch_kp_indices()

def validate_kp_schema(data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate Kp data against expected schema.
    
    Args:
        data: List of Kp index dictionaries
        
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors = []
    required_fields = ['time', 'kp', 'ap']
    
    if not data:
        errors.append("Data list is empty")
        return False, errors
    
    for i, row in enumerate(data):
        for field in required_fields:
            if field not in row:
                errors.append(f"Row {i}: Missing required field '{field}'")
            elif not row[field]:
                errors.append(f"Row {i}: Empty value for required field '{field}'")
        
        # Validate Kp is a number (or 'x' for extreme values)
        if 'kp' in row and row['kp']:
            kp_val = row['kp']
            if kp_val != 'x':
                try:
                    float(kp_val)
                except ValueError:
                    errors.append(f"Row {i}: Invalid Kp value '{kp_val}'")
    
    return len(errors) == 0, errors

def write_kp_data(data: List[Dict[str, Any]], path: str = KP_DATA_PATH):
    """
    Write Kp indices to CSV file.
    
    Args:
        data: List of Kp index dictionaries
        path: Output file path
    """
    if not data:
        log_message("No data to write for Kp indices")
        return
    
    ensure_directories()
    
    fieldnames = ['time', 'kp', 'ap']
    with open(path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    log_message(f"Successfully wrote {len(data)} Kp records to {path}")

def main():
    """
    Main entry point for Kp index ingestion.
    
    This function:
    1. Fetches Kp indices from NOAA SWPC
    2. Validates the data against the schema
    3. Writes the data to data/raw/kp_indices.csv
    4. Updates the source manifest with status and checksum
    """
    log_message("Starting Kp index ingestion...")
    
    # Fetch data
    try:
        kp_data = fetch_kp_indices()
    except RuntimeError as e:
        log_message(f"CRITICAL: Failed to fetch Kp data: {e}")
        update_manifest_entry("kp_indices", "Failed", str(e))
        return
    
    # Validate schema
    is_valid, errors = validate_kp_schema(kp_data)
    if not is_valid:
        log_message(f"Schema validation failed: {errors}")
        update_manifest_entry("kp_indices", "Validation Failed", "; ".join(errors))
        return
    
    # Write data
    write_kp_data(kp_data)
    
    # Calculate checksum
    import hashlib
    with open(KP_DATA_PATH, 'rb') as f:
        checksum = hashlib.sha256(f.read()).hexdigest()
    
    # Update manifest
    update_manifest_entry(
        "kp_indices", 
        "Success", 
        f"Fetched {len(kp_data)} records", 
        checksum
    )
    
    log_message("Kp index ingestion completed successfully")

if __name__ == "__main__":
    main()
