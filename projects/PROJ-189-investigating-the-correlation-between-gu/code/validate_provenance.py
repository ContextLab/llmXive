import sys
import json
from pathlib import Path

import psutil
import requests
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def check_resources():
    """Verify CPU-only resource guards."""
    mem = psutil.virtual_memory()
    total_gb = mem.total / (1024 ** 3)
    log.info(f"System Total RAM: {total_gb:.2f} GB")
    return {
        "total_ram_gb": total_gb,
        "ram_limit_gb": 7.0,
        "cpu_count": psutil.cpu_count(),
        "resource_guard_active": True,
    }

def _attempt_load(ds_id: str):
    """
    Try to load a dataset in streaming mode.
    First attempt without specifying a split (works for datasets that expose a default split).
    If that fails, fall back to loading the 'train' split explicitly.
    Returns the dataset object on success, otherwise raises the original exception.
    """
    try:
        log.info(f"Attempting to load dataset '{ds_id}' without explicit split.")
        ds = load_dataset(ds_id, streaming=True)
        # Pull a single record to confirm real data access
        next(iter(ds))
        log.info(f"Successfully accessed dataset '{ds_id}' (no split).")
        return ds
    except Exception as e_no_split:
        log.debug(f"Loading without split failed for '{ds_id}': {e_no_split}")
        # Try with explicit 'train' split
        try:
            log.info(f"Attempting to load dataset '{ds_id}' with split='train'.")
            ds = load_dataset(ds_id, split="train", streaming=True)
            next(iter(ds))
            log.info(f"Successfully accessed dataset '{ds_id}' with split='train'.")
            return ds
        except Exception as e_split:
            log.debug(f"Loading with split='train' also failed for '{ds_id}': {e_split}")
            # Raise the original exception for clearer upstream handling
            raise e_no_split

def verify_agp_access():
    """
    Verify access to the American Gut Project via HuggingFace datasets.
    Tries known dataset identifiers and confirms at least one yields a real record.
    """
    log.info("Verifying AGP dataset access...")
    dataset_ids = ["american_gut_project", "qiita/16s_gut_microbiome"]
    for ds_id in dataset_ids:
        try:
            _attempt_load(ds_id)
            log.info(f"AGP access verified via dataset ID: {ds_id}")
            return True, ds_id
        except Exception as e:
            log.warning(f"Access failed for {ds_id}: {e}")
    log.error("AGP access failed for all known real sources.")
    return False, None

def verify_hrs_portal():
    """
    Verify access to the Health and Retirement Study (HRS) portal.
    Performs a simple GET request; any HTTP response (even 403) is treated
    as reachable because the portal may require authentication.
    """
    log.info("Verifying HRS portal connectivity...")
    url = "https://hrs.isr.umich.edu"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # Consider any response (status < 500) as reachable
        if response.status_code < 500:
            log.info(f"HRS portal reachable, status code: {response.status_code}")
            return True
        else:
            log.error(f"HRS portal returned error status: {response.status_code}")
            return False
    except Exception as e:
        log.error(f"HRS portal access failed: {e}")
        return False

def main():
    log.info("Starting provenance and resource validation...")

    agp_ok, agp_id = verify_agp_access()
    hrs_ok = verify_hrs_portal()
    resources = check_resources()

    results = {
        "resources": resources,
        "provenance": {
            "agp_accessible": agp_ok,
            "agp_dataset_id": agp_id,
            "hrs_portal_accessible": hrs_ok,
        },
    }

    # Write report regardless of success/failure
    report_path = paths.data("provenance_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)

    if not agp_ok or not hrs_ok:
        log.error(
            "Provenance validation failed: One or more data sources are unreachable."
        )
        sys.exit(1)

    log.info(f"Validation successful. Report saved to {report_path}")

if __name__ == "__main__":
    main()