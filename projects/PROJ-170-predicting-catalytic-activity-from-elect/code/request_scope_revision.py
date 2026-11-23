"""
Request Scope Revision Script (T015)

This script generates a JSON request describing the missing experimental TOF dataset,
records its SHA‑256 checksum, and writes both artifacts to the appropriate locations.
It is intended to be invoked when the experimental TOF dataset cannot be obtained
automatically (see T014). The generated JSON file is placed under the ``outputs/``
directory, and its checksum is recorded in ``data/checksums.txt``.
"""

import json
import uuid
import hashlib
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def update_checksum_file(checksum_path: Path, filename: str, checksum: str) -> None:
    """
    Record (or replace) a checksum entry in the checksum file.

    The checksum file is a simple whitespace‑separated text file where each line
    contains ``<filename> <checksum>``.
    """
    # Ensure the parent directory exists
    checksum_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing entries
    entries = {}
    if checksum_path.is_file():
        with open(checksum_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 2:
                    entries[parts[0]] = parts[1]

    # Update or add the entry
    entries[filename] = checksum

    # Write back the whole file (overwrites previous content)
    with open(checksum_path, "w", encoding="utf-8") as f:
        for name, val in sorted(entries.items()):
            f.write(f"{name} {val}\\n")

    log.info(f"Checksum for '{filename}' recorded in {checksum_path}")

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> int:
    """
    Generate the scope‑revision request JSON and record its checksum.

    Returns:
        int: 0 on success, non‑zero on failure.
    """
    try:
        # 1. Build the request payload
        request_payload = {
            "request_id": str(uuid.uuid4()),
            "missing_dataset": "Experimental TOF dataset for the 2025 CO₂ hydrogenation study (Doe et al., 2025).",
            "impact": (
                "FR‑001 cannot be satisfied without an open experimental TOF dataset. "
                "The downstream modeling pipeline (training, evaluation, SHAP analysis) is halted."
            ),
            "proposed_action": (
                "Provide a publicly accessible CSV file containing the experimental TOF values, "
                "or make the dataset available via a stable DOI/URL. "
                "Once the data are available, re‑run the acquisition step (T014) and continue the pipeline."
            )
        }

        # 2. Write JSON to the outputs folder
        output_path: Path = paths.outputs("scope_revision_request.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(request_payload, f, indent=2, sort_keys=True)

        log.info(f"Scope‑revision request written to {output_path}")

        # 3. Compute and record checksum
        checksum = compute_sha256(output_path)
        checksum_file = paths.data("checksums.txt")  # data/checksums.txt as required by the spec
        update_checksum_file(checksum_file, output_path.name, checksum)

        log.info("Scope‑revision request checksum recorded successfully")
        return 0

    except Exception as exc:
        log.error("Failed to generate scope‑revision request", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
