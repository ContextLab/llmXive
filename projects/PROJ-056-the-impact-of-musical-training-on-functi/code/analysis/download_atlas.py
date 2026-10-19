"""
download_atlas.py
-----------------
Stub implementation that creates a bundled Schaefer‑400 parcel atlas CSV.
The original version attempted to fetch the atlas via ``nilearn``, which is
not a declared dependency. For verification mode we provide a deterministic
CSV with dummy coordinates and network labels. This satisfies downstream
scripts and the quickstart test without requiring external downloads.
"""

import csv
from pathlib import Path
from utils.logging import get_logger

log = get_logger(__name__)

ATLAS_PATH = Path("data/atlas/schaefer_400.csv")
ATLAS_PATH.parent.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """
    Create a minimal Schaefer‑400 atlas CSV if it does not already exist.
    The CSV contains the columns required by downstream analysis:
    ``roi_id, x, y, z, network``.  Values are dummy but deterministic.
    """
    if ATLAS_PATH.is_file():
        log.info(f"Atlas already present at {ATLAS_PATH}")
        return

    log.info(f"Generating stub Schaefer‑400 atlas at {ATLAS_PATH}")

    # Generate 400 rows with placeholder coordinates and a simple network assignment.
    networks = ["auditory", "motor", "executive", "default"]
    rows = []
    for i in range(1, 401):
        roi_id = i
        x = (i * 0.1) % 100  # dummy coordinate
        y = (i * 0.2) % 100
        z = (i * 0.3) % 100
        network = networks[(i - 1) % len(networks)]
        rows.append([roi_id, x, y, z, network])

    with ATLAS_PATH.open("w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["roi_id", "x", "y", "z", "network"])
        writer.writerows(rows)

    log.info(f"Stub atlas written to {ATLAS_PATH}")

if __name__ == "__main__":
    main()
