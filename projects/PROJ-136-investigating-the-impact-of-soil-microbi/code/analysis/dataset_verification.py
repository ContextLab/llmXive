"""
Dataset Verification Module for PROJ-136.

This module implements the BLOCKING GATE task T012.
It attempts to verify the accessibility of EMP, MG-RAST, and Disease Incidence dataset URLs.
If no verified sources exist, it reports a FAIL status, halting downstream tasks (T013+).
"""
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from .logging_config import get_logger

# Configuration for dataset URLs
# These are read from environment variables as per T008, with fallbacks for verification
DEFAULT_EMP_URL = "https://qiita.ucsd.edu/study/description/10317"  # Example agricultural study ID
DEFAULT_MGRAST_URL = "https://api.mg-rast.org/mgrest"
DEFAULT_DISEASE_URL = "https://figshare.com/ndownloader/files/placeholder"  # Placeholder for real dataset

# Output paths
OUTPUT_DIR = Path("data/processed")
OUTPUT_FILE = OUTPUT_DIR / "dataset_verification.json"

# Timeouts
URL_TIMEOUT = 10  # seconds

def check_url_accessibility(url: str, timeout: int = URL_TIMEOUT) -> Tuple[bool, str]:
    """
    Attempts to verify if a URL is accessible.
    Returns (is_accessible, status_message).
    """
    if not url or url.strip() == "":
        return False, "URL is empty or not configured"

    try:
        # Create a request to avoid some basic bot blocking, though we just want a 200/302
        req = Request(url, headers={'User-Agent': 'llmXive-Research-Agent/1.0'})
        with urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            if 200 <= status_code < 300:
                return True, f"Accessible (Status {status_code})"
            elif status_code == 301 or status_code == 302:
                return True, f"Redirects (Status {status_code})"
            else:
                return False, f"Unexpected status code: {status_code}"
    except HTTPError as e:
        return False, f"HTTP Error: {e.code} {e.reason}"
    except URLError as e:
        return False, f"URL Error: {e.reason}"
    except Exception as e:
        return False, f"General Error: {str(e)}"

def verify_datasets() -> Dict[str, Any]:
    """
    Verifies the accessibility of all configured dataset sources.
    Returns a dictionary with verification results and overall status.
    """
    logger = get_logger(__name__)
    logger.info("Starting dataset verification for T012 blocking gate.")

    # Retrieve URLs from environment or use defaults
    emp_url = os.getenv("DATASET_EMP_URL", DEFAULT_EMP_URL)
    mg_rast_url = os.getenv("DATASET_MGRAST_URL", DEFAULT_MGRAST_URL)
    disease_url = os.getenv("DATASET_DISEASE_URL", DEFAULT_DISEASE_URL)

    results = []
    all_pass = True

    sources = [
        {"name": "EMP Agricultural Subset", "url": emp_url, "id": "emp"},
        {"name": "MG-RAST Soil Microbiome", "url": mg_rast_url, "id": "mg-rast"},
        {"name": "Disease Incidence Records", "url": disease_url, "id": "disease"}
    ]

    for source in sources:
        logger.info(f"Verifying {source['name']}: {source['url']}")
        is_accessible, message = check_url_accessibility(source['url'])
        
        result_entry = {
            "source_id": source['id'],
            "source_name": source['name'],
            "url": source['url'],
            "accessible": is_accessible,
            "message": message
        }
        results.append(result_entry)

        if not is_accessible:
            all_pass = False
            logger.warning(f"Verification failed for {source['name']}: {message}")
        else:
            logger.info(f"Verification passed for {source['name']}: {message}")

    # Determine overall status
    status = "PASS" if all_pass else "FAIL"
    verification_report = {
        "task_id": "T012",
        "status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sources_verified": results,
        "action_required": "HALT_T013_PLUS" if status == "FAIL" else "PROCEED_TO_T013"
    }

    logger.info(f"Dataset verification complete. Status: {status}")
    return verification_report

def save_report(report: Dict[str, Any]) -> Path:
    """
    Saves the verification report to the specified output file.
    """
    if not OUTPUT_DIR.exists():
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(report, f, indent=2)
    
    return OUTPUT_FILE

def main():
    """
    Main entry point for the dataset verification task.
    """
    report = verify_datasets()
    output_path = save_report(report)
    print(f"Verification report saved to: {output_path}")
    print(f"Overall Status: {report['status']}")
    
    if report['status'] == 'FAIL':
        print("CRITICAL: Dataset verification failed. Downstream tasks (T013+) are halted.")
        print("Action: Review spec for dataset sources or update environment variables.")
        # We exit with 0 here to allow the pipeline to inspect the JSON file, 
        # but the status is clearly FAIL for the orchestrator to read.
        # In a real pipeline, this would trigger a halt.
    
    return report

if __name__ == "__main__":
    main()
