import os
import ftplib
import csv
import io
import requests
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Constants
SWPC_BASE_URL = "https://services.swpc.noaa.gov/json"
KP_INDEX_URL = f"{SWPC_BASE_URL}/kp-3-day.json"
Dst_URL = f"{SWPC_BASE_URL}/kp-3-day.json" # Placeholder, actual Dst logic handled in fetch_dst_indices

def ensure_directories():
    """Ensure required data directories exist."""
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("results").mkdir(parents=True, exist_ok=True)
    Path("code").mkdir(parents=True, exist_ok=True)

def log_message(msg: str, level: str = "INFO"):
    """Log a message to stdout with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}")

def load_manifest(manifest_path: str = "data/source_manifest.yaml") -> Dict[str, Any]:
    """Load the source manifest YAML file."""
    if not os.path.exists(manifest_path):
        return {"sources": {}}
    with open(manifest_path, 'r') as f:
        return yaml.safe_load(f) or {"sources": {}}

def save_manifest(data: Dict[str, Any], manifest_path: str = "data/source_manifest.yaml"):
    """Save the manifest to YAML."""
    with open(manifest_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False)

def update_manifest_entry(source_name: str, entry: Dict[str, Any], manifest_path: str = "data/source_manifest.yaml"):
    """Update or add an entry in the manifest."""
    manifest = load_manifest(manifest_path)
    manifest["sources"][source_name] = entry
    save_manifest(manifest, manifest_path)

def connect_to_swpc() -> bool:
    """Test connectivity to NOAA SWPC services."""
    try:
        # Test a lightweight endpoint
        resp = requests.get("https://services.swpc.noaa.gov/json/planetary-k-index-3-day.json", timeout=10)
        return resp.status_code == 200
    except Exception as e:
        log_message(f"SWPC connection failed: {e}", "ERROR")
        return False

def fetch_dst_indices() -> List[Dict[str, Any]]:
    """Fetch Dst indices (placeholder for T013 implementation)."""
    # This is a placeholder to satisfy the import surface for T013
    # The actual implementation for Dst is assumed to be in T013
    return []

def write_dst_data(data: List[Dict[str, Any]], filename: str):
    """Write Dst data to CSV (placeholder for T013)."""
    pass

def fetch_kp_indices() -> List[Dict[str, Any]]:
    """
    Fetch Kp indices from NOAA SWPC.
    
    Source: https://services.swpc.noaa.gov/json/planetary-k-index-3-day.json
    Returns a list of dictionaries with timestamp, kp_index, ap_index, etc.
    """
    ensure_directories()
    url = "https://services.swpc.noaa.gov/json/planetary-k-index-3-day.json"
    
    log_message(f"Fetching Kp indices from {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, list):
            # Some endpoints return a dict with a 'data' key
            if isinstance(data, dict) and 'data' in data:
                data = data['data']
            else:
                raise ValueError("Unexpected JSON structure for Kp indices")
        
        log_message(f"Successfully fetched {len(data)} Kp records")
        return data
    
    except requests.exceptions.RequestException as e:
        log_message(f"Failed to fetch Kp indices: {e}", "ERROR")
        raise RuntimeError(f"Data fetch failed: {e}")
    except json.JSONDecodeError as e:
        log_message(f"Failed to parse Kp indices JSON: {e}", "ERROR")
        raise ValueError(f"Invalid JSON response: {e}")

def validate_kp_schema(data: List[Dict[str, Any]]) -> bool:
    """
    Validate Kp data against basic schema requirements.
    Checks for presence of required fields: time_tag, kp_index, ap_index.
    """
    required_fields = ['time_tag', 'kp_index', 'ap_index']
    
    if not data:
        log_message("Validation failed: No data provided", "ERROR")
        return False
    
    valid_count = 0
    for idx, record in enumerate(data):
        if not isinstance(record, dict):
            continue
        
        if all(field in record for field in required_fields):
            # Basic type check
            try:
                float(record['kp_index'])
                float(record['ap_index'])
                valid_count += 1
            except (ValueError, TypeError):
                continue
        else:
            log_message(f"Record {idx} missing required fields", "WARNING")
    
    if valid_count == 0:
        log_message("Validation failed: No valid records found", "ERROR")
        return False
    
    log_message(f"Validation passed: {valid_count}/{len(data)} records valid")
    return True

def write_kp_data(data: List[Dict[str, Any]], filename: str = "data/raw/kp_indices.csv"):
    """
    Write Kp indices to a CSV file.
    
    Args:
        data: List of dictionaries containing Kp data
        filename: Output path relative to project root
    """
    ensure_directories()
    
    if not data:
        log_message("No data to write", "WARNING")
        return
    
    # Determine columns from the first record
    # We flatten the structure to ensure standard CSV format
    # Standard fields: time_tag, kp_index, ap_index
    # Additional fields might exist, we'll capture them if present
    fieldnames = ['time_tag', 'kp_index', 'ap_index']
    
    # Check for additional keys in the first record to include
    first_record = data[0]
    if isinstance(first_record, dict):
        for key in first_record.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for record in data:
            if isinstance(record, dict):
                # Ensure time_tag is formatted consistently if it's a nested object
                # SWPC JSON usually returns time_tag as string, but let's be safe
                if 'time_tag' in record:
                    # If it's a dict (e.g., {'date': '...', 'time': '...'}), flatten or stringify
                    if isinstance(record['time_tag'], dict):
                        record['time_tag'] = f"{record['time_tag'].get('date', '')} {record['time_tag'].get('time', '')}"
                writer.writerow(record)
    
    log_message(f"Wrote Kp data to {filename}")

def main():
    """
    Main entry point for downloading Kp indices.
    Orchestrates fetch, validate, and write steps.
    """
    log_message("Starting Kp indices ingestion (T013b)")
    
    # 1. Fetch
    try:
        kp_data = fetch_kp_indices()
    except Exception as e:
        log_message(f"Ingestion failed at fetch: {e}", "ERROR")
        return 1
    
    # 2. Validate
    if not validate_kp_schema(kp_data):
        log_message("Ingestion failed at validation", "ERROR")
        return 1
    
    # 3. Write
    output_path = "data/raw/kp_indices.csv"
    try:
        write_kp_data(kp_data, output_path)
    except Exception as e:
        log_message(f"Ingestion failed at write: {e}", "ERROR")
        return 1
    
    # 4. Update Manifest
    try:
        manifest_entry = {
            "source": "NOAA SWPC Kp Index",
            "url": "https://services.swpc.noaa.gov/json/planetary-k-index-3-day.json",
            "retrieved_at": datetime.now().isoformat(),
            "output_file": output_path,
            "record_count": len(kp_data),
            "status": "verified"
        }
        update_manifest_entry("kp_indices", manifest_entry)
        log_message("Manifest updated successfully")
    except Exception as e:
        log_message(f"Failed to update manifest: {e}", "WARNING")
    
    log_message("Kp indices ingestion completed successfully")
    return 0

if __name__ == "__main__":
    exit(main())
