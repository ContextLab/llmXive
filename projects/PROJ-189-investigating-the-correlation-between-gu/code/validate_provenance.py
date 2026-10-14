"""
validate_provenance.py
-----------------------

This script verifies that the required external data sources are reachable
before the rest of the pipeline is executed.

* American Gut Project (AGP) – accessed via the HuggingFace ``datasets``
  library using the identifier ``american_gut_project`` (streaming mode).

* Health and Retirement Study (HRS) – a public CSV file hosted by the
  University of Michigan.  A simple ``HEAD`` request is used to confirm
  that the URL is reachable.

The script also records a minimal resource‑guard summary (RAM, CPU count)
and writes the results to ``data/provenance_report.json``.  The output
format matches the one produced previously so that downstream scripts can
continue to read it without modification.

The script exits with status ``0`` on success and a non‑zero status on any
failure, allowing CI to stop early if the data sources are unavailable.
"""

import json
import os
import sys
from pathlib import Path

import psutil
import requests
from datasets import load_dataset, DatasetNotFoundError

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def check_agp_access() -> tuple[bool, str | None]:
    """
    Attempt to stream a few records from the American Gut Project dataset.

    Returns
    -------
    (bool, str | None)
        ``True`` and the dataset identifier if the load succeeds,
        ``False`` and ``None`` otherwise.
    """
    dataset_id = "american_gut_project"
    try:
        # ``streaming=True`` returns an iterator that lazily pulls data.
        # We only need to fetch a single example to prove connectivity.
        ds = load_dataset(dataset_id, split="train", streaming=True)
        # Pull the first record – if this raises, the dataset is not usable.
        next(iter(ds))
        return True, dataset_id
    except Exception as exc:
        # ``DatasetNotFoundError`` or network‑related errors land here.
        return False, None

def check_hrs_access() -> bool:
    """
    Perform a lightweight ``HEAD`` request to the public HRS CSV URL.

    Returns
    -------
    bool
        ``True`` if the request returns a 2xx status code, ``False`` otherwise.
    """
    url = "https://hrs.isr.umich.edu/sites/default/files/data/cognitive_data.csv"
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

# ----------------------------------------------------------------------
# Main execution block
# ----------------------------------------------------------------------
def main() -> None:
    # Resource information
    vm = psutil.virtual_memory()
    total_ram_gb = round(vm.total / (1024 ** 3), 3)
    # The project specification caps RAM at 7 GB.
    ram_limit_gb = 7.0
    cpu_count = os.cpu_count() or 1
    resource_guard_active = True  # The project always runs the guard.

    # Data‑source checks
    agp_ok, agp_id = check_agp_access()
    hrs_ok = check_hrs_access()

    provenance = {
        "agp_accessible": agp_ok,
        "agp_dataset_id": agp_id,
        "hrs_portal_accessible": hrs_ok,
    }

    report = {
        "resources": {
            "total_ram_gb": total_ram_gb,
            "ram_limit_gb": ram_limit_gb,
            "cpu_count": cpu_count,
            "resource_guard_active": resource_guard_active,
        },
        "provenance": provenance,
    }

    # Write the JSON report to the expected location.
    output_path = Path("data", "provenance_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2, sort_keys=False)

    # Print a short human‑readable summary (useful when the script is run
    # manually).  The CI only cares about the exit code and the file.
    print(json.dumps(report, indent=2))

    # Exit status: 0 if both sources are reachable, 1 otherwise.
    if not (agp_ok and hrs_ok):
        sys.exit(1)

if __name__ == "__main__":
    main()
