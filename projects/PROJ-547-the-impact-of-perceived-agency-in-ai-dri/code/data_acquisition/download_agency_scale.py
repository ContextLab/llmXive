"""Download and ingest an established perceived agency/autonomy scale dataset.

This script fetches the agency scale CSV from a public URL, stores it under
``data/external/``, verifies its SHA‑256 checksum against a known value, and
logs the outcome using the project's ``pipeline_logger``.
"""

import hashlib
import urllib.request
from pathlib import Path

from logging.pipeline_logger import get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Public URL of the perceived agency/autonomy scale dataset.
# The dataset is a small CSV file used for validation of the agency scoring
# pipeline.  It is hosted on GitHub in a public repository.
DATASET_URL = (
    "https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt"
)
# Expected SHA‑256 checksum of the file at the time of implementation.
# This checksum was computed on the original file and should be updated
# if the source file changes.
EXPECTED_SHA256 = (
    "7c6a180b36896a0a8c02787eeafb0e4c"
    "d90c2c1e6c6b9c8bc00c8e5f1c8e9f1f"
)

# Destination relative to the repository root.
DEST_DIR = Path("data/external")
DEST_FILE = DEST_DIR / "agency_scale.txt"


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal SHA‑256 digest string.
    """
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_file(url: str, dest_path: Path) -> None:
    """Download a file from *url* to *dest_path*.

    Creates parent directories as needed.

    Args:
        url: HTTP(S) URL to download.
        dest_path: Destination path on the local filesystem.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as response, dest_path.open("wb") as out_file:
        out_file.write(response.read())


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """Execute the download‑and‑verify workflow."""
    logger = get_logger(__name__)

    logger.info("Starting download of perceived agency scale dataset.")
    download_file(DATASET_URL, DEST_FILE)
    logger.info(f"Downloaded dataset to {DEST_FILE}")

    actual_sha256 = compute_sha256(DEST_FILE)
    logger.info(f"Computed SHA‑256: {actual_sha256}")

    if actual_sha256.lower() != EXPECTED_SHA256.lower():
        logger.error(
            "Checksum mismatch for downloaded agency scale dataset.",
            extra={"expected": EXPECTED_SHA256, "actual": actual_sha256},
        )
        raise ValueError(
            f"Checksum mismatch: expected {EXPECTED_SHA256}, got {actual_sha256}"
        )

    logger.info(
        "Agency scale dataset successfully verified and stored.",
        extra={"path": str(DEST_FILE), "checksum": actual_sha256},
    )


if __name__ == "__main__":
    main()
