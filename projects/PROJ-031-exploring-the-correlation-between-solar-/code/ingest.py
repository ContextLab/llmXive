import os
import ftplib
import csv
import io
import requests
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Configuration
SWPC_FTP_HOST = "ftp.swpc.noaa.gov"
SWPC_HTTP_BASE = "https://www.swpc.noaa.gov/products"
KP_URL_TEMPLATE = "https://www.swpc.noaa.gov/products/kp-index"
KP_DATA_URL = "https://www.swpc.noaa.gov/indices/kp.csv" # Direct data link if available, otherwise scrape
# Fallback to the specific known data file structure often used by SWPC for indices
# SWPC typically hosts Kp in text files like 'kp.csv' or similar in the indices directory
KP_RAW_URL = "https://www.swpc.noaa.gov/indices/kp.csv"

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure required data directories exist."""
    dirs = ['data/raw', 'data/processed', 'results', 'results/figures']
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def log_message(msg: str):
    logger.info(msg)

def load_manifest() -> Dict[str, Any]:
    manifest_path = "data/source_manifest.yaml"
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            import yaml
            return yaml.safe_load(f) or {}
    return {"sources": {}}

def save_manifest(manifest: Dict[str, Any]):
    manifest_path = "data/source_manifest.yaml"
    with open(manifest_path, 'w') as f:
        import yaml
        yaml.dump(manifest, f)

def update_manifest_entry(name: str, url: str, status: str, timestamp: str = None):
    manifest = load_manifest()
    if "sources" not in manifest:
        manifest["sources"] = {}
    
    entry = {
        "url": url,
        "status": status,
        "last_updated": timestamp or datetime.now().isoformat(),
        "file": f"data/raw/{name}.csv"
    }
    manifest["sources"][name] = entry
    save_manifest(manifest)
    log_message(f"Updated manifest for {name}: {status}")

def connect_to_swpc():
    """Attempt to connect to SWPC FTP to verify connectivity."""
    try:
        ftp = ftplib.FTP(SWPC_FTP_HOST)
        ftp.login()
        ftp.quit()
        return True
    except Exception as e:
        log_message(f"FTP connection failed: {e}")
        return False

# --- Dst Indices (Existing Implementation) ---

def fetch_dst_indices_http() -> List[Dict[str, Any]]:
    """Fetch Dst indices via HTTP."""
    # SWPC Dst data URL
    url = "https://www.swpc.noaa.gov/indices/dst.csv"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # Parse CSV content
        lines = response.text.strip().split('\n')
        data = []
        # Skip header if present, usually first line is comments or header
        # Format: Date, Time, Dst, Error
        for line in lines[1:]: # Skip header
            if not line.strip():
                continue
            parts = line.split(',')
            if len(parts) >= 3:
                try:
                    # Date format: YYYY-MM-DD, Time: HH:MM
                    date_str = parts[0].strip()
                    time_str = parts[1].strip()
                    dst_val = int(parts[2].strip())
                    data.append({
                        "timestamp": f"{date_str} {time_str}:00",
                        "dst": dst_val
                    })
                except (ValueError, IndexError):
                    continue
        return data
    except Exception as e:
        log_message(f"Failed to fetch Dst indices: {e}")
        return []

def write_dst_data(data: List[Dict[str, Any]]):
    output_path = "data/raw/dst_indices.csv"
    if not data:
        log_message("No Dst data to write.")
        return
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "dst"])
        writer.writeheader()
        writer.writerows(data)
    log_message(f"Wrote {len(data)} Dst records to {output_path}")

# --- Kp Indices (Task T013b Implementation) ---

def fetch_kp_indices_http() -> List[Dict[str, Any]]:
    """
    Fetch Kp indices from NOAA SWPC.
    Kp is a 3-hour index. The standard format is often a text file with columns:
    Date, Time, Kp, Ap, etc.
    Source: https://www.swpc.noaa.gov/indices/kp.csv
    """
    url = KP_RAW_URL
    data = []
    
    try:
        log_message(f"Fetching Kp indices from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        lines = response.text.strip().split('\n')
        
        # Parse lines. SWPC kp.csv usually has headers or starts with data.
        # Format often: YYYY/MM/DD, HH, Kp, Ap, ...
        # We need to handle potential header rows.
        
        start_index = 0
        if lines and 'Year' in lines[0] or 'Date' in lines[0]:
            start_index = 1
        
        for line in lines[start_index:]:
            if not line.strip():
                continue
            parts = line.split(',')
            # Expected: Date, Time, Kp, Ap, ...
            # Kp is often a float like 0.0, 0.3, 0.7, 1.0...
            if len(parts) >= 3:
                try:
                    date_str = parts[0].strip().replace('/', '-') # Normalize to YYYY-MM-DD
                    time_str = parts[1].strip()
                    # Time is often 00, 03, 06, 09, etc. Format as HH:00
                    if time_str.isdigit() and len(time_str) == 2:
                        time_str = f"{time_str}:00"
                    
                    kp_val = float(parts[2].strip())
                    
                    data.append({
                        "timestamp": f"{date_str} {time_str}:00",
                        "kp": kp_val
                    })
                except (ValueError, IndexError) as e:
                    # Skip malformed lines
                    continue
        
        if not data:
            log_message("No valid Kp data found in response.")
        else:
            log_message(f"Successfully parsed {len(data)} Kp records.")
            
        return data

    except requests.exceptions.RequestException as e:
        log_message(f"Failed to fetch Kp indices via HTTP: {e}")
        return []
    except Exception as e:
        log_message(f"Unexpected error fetching Kp indices: {e}")
        return []

def validate_kp_schema(data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
    """
    Validate Kp data against basic schema requirements:
    - Must have 'timestamp' and 'kp' keys
    - 'kp' must be a float between 0.0 and 9.0
    - 'timestamp' must be a valid string format (YYYY-MM-DD HH:MM:SS)
    """
    errors = []
    if not data:
        errors.append("No data provided for validation.")
        return False, errors
    
    valid_count = 0
    for i, row in enumerate(data):
        if 'timestamp' not in row or 'kp' not in row:
            errors.append(f"Row {i}: Missing 'timestamp' or 'kp' key.")
            continue
        
        try:
            kp_val = float(row['kp'])
            if not (0.0 <= kp_val <= 9.0):
                errors.append(f"Row {i}: Kp value {kp_val} out of range [0.0, 9.0].")
            else:
                valid_count += 1
        except (ValueError, TypeError):
            errors.append(f"Row {i}: Invalid Kp value '{row['kp']}'.")
    
    if valid_count == 0:
        return False, errors
    
    return True, errors

def write_kp_data(data: List[Dict[str, Any]]):
    """Write Kp indices to data/raw/kp_indices.csv."""
    output_path = "data/raw/kp_indices.csv"
    if not data:
        log_message("No Kp data to write.")
        return
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "kp"])
        writer.writeheader()
        writer.writerows(data)
    log_message(f"Wrote {len(data)} Kp records to {output_path}")

def main():
    """Main entry point for Kp index ingestion (T013b)."""
    log_message("Starting Kp index ingestion (Task T013b)...")
    ensure_directories()
    
    # Fetch data
    kp_data = fetch_kp_indices_http()
    
    if not kp_data:
        log_message("Failed to retrieve Kp data. Updating manifest with 'Failed' status.")
        update_manifest_entry("kp_indices", KP_RAW_URL, "Failed")
        # Do not write file if fetch failed, to avoid empty/placeholder files
        return 1
    
    # Validate
    is_valid, errors = validate_kp_schema(kp_data)
    if not is_valid:
        log_message(f"Kp data validation failed with {len(errors)} errors. Aborting write.")
        for err in errors[:5]: # Log first 5 errors
            log_message(f"  - {err}")
        update_manifest_entry("kp_indices", KP_RAW_URL, "Validation Failed")
        return 1
    
    # Write
    write_kp_data(kp_data)
    
    # Update Manifest
    update_manifest_entry("kp_indices", KP_RAW_URL, "Success")
    
    log_message("Task T013b completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
