import os
import sys
import csv
import io
import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Iterator
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/ingest.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass

def ensure_directories():
    """Create necessary directories for data and logs."""
    dirs = ['data/raw', 'data/processed', 'logs', 'results', 'state/projects']
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def log_message(msg: str, level: str = 'INFO'):
    """Log a message with the specified level."""
    if level == 'ERROR':
        logger.error(msg)
    elif level == 'WARNING':
        logger.warning(msg)
    else:
        logger.info(msg)

def load_manifest(manifest_path: str = 'data/source_manifest.yaml') -> Dict[str, Any]:
    """Load the source manifest YAML file."""
    import yaml
    if not os.path.exists(manifest_path):
        return {"sources": {}}
    with open(manifest_path, 'r') as f:
        return yaml.safe_load(f) or {"sources": {}}

def save_manifest(data: Dict[str, Any], manifest_path: str = 'data/source_manifest.yaml'):
    """Save the source manifest YAML file."""
    import yaml
    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    with open(manifest_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False)

def update_manifest_entry(manifest: Dict, source_id: str, updates: Dict[str, Any]):
    """Update a specific source entry in the manifest."""
    if source_id not in manifest["sources"]:
        manifest["sources"][source_id] = {"id": source_id, "status": "pending"}
    manifest["sources"][source_id].update(updates)

def verify_cdaweb_source():
    """
    Verify CDAWeb source availability via HEAD request.
    Raises DataFetchError if verification fails.
    """
    url = "https://cdaweb.gsfc.nasa.gov/index.html/"
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            log_message(f"CDAWeb source verified: {url} (Status 200)")
            return True
        else:
            raise DataFetchError(f"CDAWeb verification failed: Status {response.status_code}")
    except requests.RequestException as e:
        raise DataFetchError(f"CDAWeb verification failed: {str(e)}")

def fetch_with_backoff(url: str, max_retries: int = 3, timeout: int = 30) -> requests.Response:
    """Fetch a URL with exponential backoff."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response
            log_message(f"Attempt {attempt+1} failed with status {response.status_code}", "WARNING")
        except requests.RequestException as e:
            log_message(f"Attempt {attempt+1} failed: {str(e)}", "WARNING")
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    raise DataFetchError(f"Failed to fetch {url} after {max_retries} attempts")

def stream_csv_lines(url: str, delimiter: str = ',') -> Iterator[str]:
    """
    Stream CSV lines from a URL without loading the whole file into memory.
    Yields lines as strings.
    """
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    for line in response.iter_lines():
        if line:
            yield line.decode('utf-8')

def fetch_dst_indices_http() -> List[Dict[str, Any]]:
    """
    Fetch Dst indices from NOAA SWPC via HTTP.
    Returns a list of dictionaries with date and value.
    """
    # NOAA SWPC Dst Index URL (Text format)
    url = "https://services.swpc.noaa.gov/products/noaa-dst-index.txt"
    data = []
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        lines = response.text.splitlines()
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 4:
                try:
                    year, month, day, value = parts[0], parts[1], parts[2], parts[3]
                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    data.append({"date": date_str, "dst": float(value)})
                except (ValueError, IndexError):
                    continue
        return data
    except requests.RequestException as e:
        raise DataFetchError(f"Failed to fetch Dst indices: {str(e)}")

def fetch_kp_indices_http() -> List[Dict[str, Any]]:
    """
    Fetch Kp indices from NOAA SWPC via HTTP.
    Returns a list of dictionaries with date and value.
    """
    # NOAA SWPC Kp Index URL (Text format)
    url = "https://services.swpc.noaa.gov/products/noaa-kp-index.txt"
    data = []
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        lines = response.text.splitlines()
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 4:
                try:
                    year, month, day, value = parts[0], parts[1], parts[2], parts[3]
                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    data.append({"date": date_str, "kp": float(value)})
                except (ValueError, IndexError):
                    continue
        return data
    except requests.RequestException as e:
        raise DataFetchError(f"Failed to fetch Kp indices: {str(e)}")

def write_dst_data(data: List[Dict[str, Any]], output_path: str = 'data/raw/dst_indices.csv'):
    """Write Dst data to CSV."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'dst'])
        writer.writeheader()
        writer.writerows(data)
    log_message(f"Wrote {len(data)} Dst records to {output_path}")

def write_kp_data(data: List[Dict[str, Any]], output_path: str = 'data/raw/kp_indices.csv'):
    """Write Kp data to CSV."""
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['date', 'kp'])
        writer.writeheader()
        writer.writerows(data)
    log_message(f"Wrote {len(data)} Kp records to {output_path}")

def validate_kp_schema(data: List[Dict[str, Any]]) -> bool:
    """
    Validate Kp data against a simple schema.
    Returns True if valid, False otherwise.
    """
    for record in data:
        if 'date' not in record or 'kp' not in record:
            return False
        try:
            float(record['kp'])
        except (ValueError, TypeError):
            return False
    return True

def validate_date_range(data: List[Dict[str, Any]], source_name: str, min_date: str = "2010-01-01", max_date: str = "2023-12-31") -> bool:
    """
    Validates that the downloaded data covers the required date range [min_date, max_date].
    
    Logic:
    1. Parse all dates in the data.
    2. Check if min(data_dates) >= min_date.
    3. Check if max(data_dates) >= max_date (meaning we have at least reached the end of the required period).
    
    Behavior:
    - If the window is slightly off (e.g., starts 2010-01-02), logs a warning and sets data_limitation flag.
    - If the window is significantly missing (e.g., max date is 2022), logs a "Data Insufficiency" error,
      sets data_limitation flag, and raises a DataFetchError to halt the pipeline.
    
    Returns True if data is sufficient, False otherwise (if limitation flag is set).
    """
    import yaml
    from datetime import datetime as dt

    if not data:
        log_message(f"Data Insufficiency: No data found for {source_name}.", "ERROR")
        # Update manifest
        manifest = load_manifest()
        update_manifest_entry(manifest, source_name, {"data_limitation": True, "limitation_reason": "No data found"})
        save_manifest(manifest)
        return False

    dates = []
    for record in data:
        try:
            d = dt.strptime(record['date'], "%Y-%m-%d")
            dates.append(d)
        except (ValueError, KeyError):
            continue

    if not dates:
        log_message(f"Data Insufficiency: No valid dates found for {source_name}.", "ERROR")
        manifest = load_manifest()
        update_manifest_entry(manifest, source_name, {"data_limitation": True, "limitation_reason": "No valid dates"})
        save_manifest(manifest)
        return False

    min_actual = min(dates)
    max_actual = max(dates)
    min_req = dt.strptime(min_date, "%Y-%m-%d")
    max_req = dt.strptime(max_date, "%Y-%m-%d")

    is_start_ok = min_actual >= min_req
    is_end_ok = max_actual >= max_req

    # Check for slight deviation at start
    if not is_start_ok:
        delta = (min_req - min_actual).days
        if delta <= 5: # Graceful failure for small offset
            log_message(f"WARNING: {source_name} start date is slightly off. Expected >= {min_date}, got {min_actual.date()}. Setting data_limitation flag.", "WARNING")
            manifest = load_manifest()
            update_manifest_entry(manifest, source_name, {
                "data_limitation": True, 
                "limitation_reason": f"Start date offset: {delta} days"
            })
            save_manifest(manifest)
            # Do not halt, but flag it
        else:
            log_message(f"ERROR: Data Insufficiency for {source_name}. Start date {min_actual.date()} is too early/late relative to {min_date}.", "ERROR")
            manifest = load_manifest()
            update_manifest_entry(manifest, source_name, {
                "data_limitation": True, 
                "limitation_reason": f"Start date {min_actual.date()} outside acceptable range"
            })
            save_manifest(manifest)
            return False

    # Check for missing end of range
    if not is_end_ok:
        delta = (max_req - max_actual).days
        log_message(f"ERROR: Data Insufficiency for {source_name}. Max date {max_actual.date()} is before required end {max_date}. Missing {delta} days.", "ERROR")
        manifest = load_manifest()
        update_manifest_entry(manifest, source_name, {
            "data_limitation": True, 
            "limitation_reason": f"Data ends at {max_actual.date()}, required {max_date}"
        })
        save_manifest(manifest)
        return False

    log_message(f"Date range validation passed for {source_name}: [{min_actual.date()}, {max_actual.date()}]", "INFO")
    return True

def main():
    """
    Main entry point for ingestion.
    Performs source verification, data fetching, and date range validation.
    """
    ensure_directories()
    
    # 1. Verify CDAWeb source (Blocking Gate T071)
    try:
        verify_cdaweb_source()
        manifest = load_manifest()
        update_manifest_entry(manifest, "CDAWeb_LASCO", {"cme_url_verified": True, "verification_timestamp": datetime.now().isoformat()})
        save_manifest(manifest)
    except DataFetchError as e:
        log_message(f"Critical: CDAWeb verification failed: {e}", "ERROR")
        sys.exit(1)

    # 2. Fetch Dst Indices
    log_message("Fetching Dst indices...")
    try:
        dst_data = fetch_dst_indices_http()
        write_dst_data(dst_data)
        # Validate Date Range for Dst
        if not validate_date_range(dst_data, "NOAA_SWPC_DST"):
            # If validation fails (missing end date), we stop here per T011b requirement
            log_message("Halting pipeline due to insufficient Dst data range.", "ERROR")
            sys.exit(1)
    except DataFetchError as e:
        log_message(f"Failed to fetch Dst: {e}", "ERROR")
        sys.exit(1)

    # 3. Fetch Kp Indices
    log_message("Fetching Kp indices...")
    try:
        kp_data = fetch_kp_indices_http()
        write_kp_data(kp_data)
        if not validate_kp_schema(kp_data):
            log_message("Kp data schema validation failed.", "ERROR")
            sys.exit(1)
        # Validate Date Range for Kp
        if not validate_date_range(kp_data, "NOAA_SWPC_KP"):
            log_message("Halting pipeline due to insufficient Kp data range.", "ERROR")
            sys.exit(1)
    except DataFetchError as e:
        log_message(f"Failed to fetch Kp: {e}", "ERROR")
        sys.exit(1)

    log_message("Ingestion and initial validation complete.")

if __name__ == "__main__":
    main()
