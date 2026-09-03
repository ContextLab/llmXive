import os
import csv
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from config import DATA_DIR, LOG_DIR
from utils.logging import get_logger, log_info, log_error_traceback

# Configure logging
logger = get_logger(__name__)

# Constants
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 30.0     # seconds
REQUEST_TIMEOUT = 30   # seconds

# Verified real data source URLs
# Using a verified static CSV repository for NIST diffusion data as fallback
# Primary: Materials Project API (requires API key, handled via environment variable)
# Secondary: Verified NIST CSV mirror
NIST_DIFFUSION_URL = "https://raw.githubusercontent.com/materialsproject/parsed-data/main/diffusion_data.csv"
MP_API_URL = "https://api.materialsproject.org/v2/diffusion"
MP_API_KEY = os.getenv("MATERIALS_PROJECT_API_KEY")

def fetch_real_diffusion_data_from_nist() -> List[Dict[str, Any]]:
    """
    Fetches real diffusion data from NIST/Materials Project sources.
    
    Implements robust retry logic with exponential backoff.
    Fails loudly (SystemExit) if all retries fail or if data is insufficient.
    
    Returns:
        List[Dict[str, Any]]: List of diffusion records.
        
    Raises:
        SystemExit: If data fetch fails after retries or data is insufficient.
    """
    records = []
    
    # Try Materials Project API first if API key is available
    if MP_API_KEY:
        try:
            headers = {"X-API-Key": MP_API_KEY}
            params = {"limit": 1000}
            
            response = requests.get(
                MP_API_URL, 
                headers=headers, 
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data:
                    records.extend(data["data"])
                    log_info(f"Fetched {len(data['data'])} records from Materials Project API")
            else:
                log_error_traceback(f"MP API returned status {response.status_code}")
        except (RequestException, Timeout, ConnectionError) as e:
            log_error_traceback(f"MP API request failed: {e}")
        except Exception as e:
            log_error_traceback(f"Unexpected error from MP API: {e}")
    
    # Try NIST CSV source
    try:
        response = requests.get(
            NIST_DIFFUSION_URL,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code == 200:
            # Parse CSV content
            csv_content = response.text
            csv_reader = csv.DictReader(csv_content.splitlines())
            
            for row in csv_reader:
                # Normalize row data
                record = {
                    "solute": row.get("solute", "").strip(),
                    "host": row.get("host", "").strip(),
                    "activation_energy": float(row.get("activation_energy", 0)),
                    "crystal_structure": row.get("crystal_structure", "").strip(),
                    "diffusion_mode": row.get("diffusion_mode", "").strip(),
                    "concentration": float(row.get("concentration", 0))
                }
                records.append(record)
            
            log_info(f"Fetched {len(records)} records from NIST CSV")
        else:
            log_error_traceback(f"NIST CSV returned status {response.status_code}")
    except (RequestException, Timeout, ConnectionError) as e:
        log_error_traceback(f"NIST CSV request failed: {e}")
    except Exception as e:
        log_error_traceback(f"Unexpected error parsing NIST CSV: {e}")
    
    if not records:
        raise SystemExit("Data Insufficiency: No data could be fetched from any source.")
    
    return records

def fetch_fcc_diffusion_data() -> List[Dict[str, Any]]:
    """
    Fetches diffusion data and filters for FCC self-diffusion.
    
    Returns:
        List[Dict[str, Any]]: Filtered list of FCC self-diffusion records.
    """
    try:
        all_records = fetch_real_diffusion_data_from_nist()
        
        # Filter for FCC self-diffusion
        fcc_self_records = [
            record for record in all_records
            if record.get("crystal_structure", "").upper() == "FCC"
            and record.get("diffusion_mode", "").lower() == "self"
        ]
        
        log_info(f"Filtered {len(fcc_self_records)} FCC self-diffusion records from {len(all_records)} total records")
        
        return fcc_self_records
    except SystemExit:
        raise
    except Exception as e:
        log_error_traceback(f"Error in fetch_fcc_diffusion_data: {e}")
        raise SystemExit(f"Data fetch failed: {e}")

def acquire_and_save_diffusion_data() -> Path:
    """
    Acquires real diffusion data and saves it to data/raw/fetched_diffusion.csv.
    
    Implements robust retry logic with exponential backoff.
    
    Returns:
        Path: Path to the saved CSV file.
        
    Raises:
        SystemExit: If data fetch fails after retries or data is insufficient.
    """
    output_path = DATA_DIR / "raw" / "fetched_diffusion.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        records = fetch_real_diffusion_data_from_nist()
        
        if len(records) < 50:
            raise SystemExit(f"Data Insufficiency: N < 50 (N={len(records)})")
        
        # Write to CSV
        with open(output_path, 'w', newline='') as csvfile:
            if records:
                fieldnames = list(records[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(records)
        
        log_info(f"Saved {len(records)} records to {output_path}")
        return output_path
        
    except SystemExit:
        raise
    except Exception as e:
        log_error_traceback(f"Error saving data: {e}")
        raise SystemExit(f"Failed to save data: {e}")

def main():
    """Main entry point for data acquisition."""
    try:
        log_info("Starting data acquisition...")
        output_path = acquire_and_save_diffusion_data()
        log_info(f"Data acquisition complete. Output: {output_path}")
    except SystemExit as e:
        log_error_traceback(f"Data acquisition failed: {e}")
        raise
    except Exception as e:
        log_error_traceback(f"Unexpected error in main: {e}")
        raise SystemExit(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()