"""
verify_resources.py

This script performs a HEAD request to verify external resources required for the
pipeline:

* Dataset URL: https://huggingface.co/datasets/omnineura/Omni-Doc-1
* Model URL:   https://huggingface.co/Qwen/Qwen-Image-VAE-2.0

If both URLs are reachable (HTTP status 2xx) a JSON status file is written to
``data/raw/download_status.json`` containing the verification result.
The script always exits with status 0 after writing the status file, allowing the
pipeline to proceed regardless of reachability (the status file records any
failures).

The script is intended to be run as:
    python -m code.boot.verify_resources
"""

import json
import sys
from pathlib import Path

import requests

from llmxive_toolkit import paths, get_logger

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
DATASET_URL = "https://huggingface.co/datasets/omnineura/Omni-Doc-1"
# The required VAE model URL (CPU‑compatible verification)
MODEL_URL = "https://huggingface.co/Qwen/Qwen-Image-VAE-2.0"

# Output file (the `paths.data` helper creates the necessary directories)
OUTPUT_PATH = paths.data("raw", "download_status.json")

logger = get_logger(__name__)

def _head_check(url: str) -> bool:
    """
    Perform a HEAD request to ``url`` and return True if the response status
    indicates success (2xx). Any exception or non‑2xx status is treated as
    failure.
    """
    try:
        logger.info(f"Checking URL: {url}")
        response = requests.head(url, allow_redirects=True, timeout=10)
        if 200 <= response.status_code < 300:
            logger.info(f"URL reachable: {url} (status {response.status_code})")
            return True
        else:
            logger.error(
                f"URL returned non‑successful status {response.status_code}: {url}"
            )
            return False
    except requests.RequestException as exc:
        logger.error(f"HEAD request failed for {url}: {exc}")
        return False

def main() -> None:
    """Run the verification checks and write a JSON status file."""
    dataset_ok = _head_check(DATASET_URL)
    model_ok = _head_check(MODEL_URL)

    status = {
        "dataset_url": DATASET_URL,
        "dataset_status": "reachable" if dataset_ok else "unreachable",
        "model_url": MODEL_URL,
        "model_status": "reachable" if model_ok else "unreachable",
    }

    # Write the JSON file; ensure parent directory exists (handled by paths)
    OUTPUT_PATH.write_text(json.dumps(status, indent=2))
    logger.info(f"Wrote verification status to {OUTPUT_PATH}")

    # Always exit with code 0; the status JSON records any failures.
    sys.exit(0)

if __name__ == "__main__":
    main()
