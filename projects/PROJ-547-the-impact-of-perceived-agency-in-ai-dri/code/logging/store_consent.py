"""
Store consent documentation and record its SHA-256 checksum.

This script downloads a sample consent PDF, saves it under ``data/consent/``,
computes its SHA‑256 checksum, writes the checksum into ``data/metadata.yaml``,
and logs the association using the project's ``pipeline_logger``.
"""
import hashlib
import json
import urllib.request
from pathlib import Path

# Import the project's logger utilities.  This script lives in the same
# directory as ``pipeline_logger.py`` so a direct import works.
from pipeline_logger import get_logger, log_dict

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CONSENT_URL = (
    "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
)
CONSENT_DIR = Path("data/consent")
CONSENT_PATH = CONSENT_DIR / "consent_document.pdf"
METADATA_PATH = Path("data/metadata.yaml")

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def download_consent(url: str, destination: Path) -> None:
    """Download the consent PDF to ``destination``."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    # ``urlretrieve`` writes directly to the given path.
    urllib.request.urlretrieve(url, destination)

def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 checksum of ``file_path`` as a hex string."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def update_metadata(metadata_path: Path, checksum: str) -> None:
    """Write/overwrite the consent checksum in ``metadata_path``."""
    import yaml

    metadata = {}
    if metadata_path.is_file():
        with metadata_path.open("r", encoding="utf-8") as f:
            metadata = yaml.safe_load(f) or {}
    metadata["consent_checksum"] = checksum
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with metadata_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(metadata, f)

def log_consent_association(checksum: str) -> None:
    """Log a structured entry linking the current run to the consent file."""
    logger = get_logger()
    entry = {
        "event": "consent_stored",
        "checksum": checksum,
        "consent_path": str(CONSENT_PATH),
    }
    # ``log_dict`` writes a JSON‑line using the project's logger configuration.
    log_dict(logger, entry)

# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def main() -> None:
    """Execute the consent‑storage workflow."""
    # 1. Download the consent PDF.
    download_consent(CONSENT_URL, CONSENT_PATH)

    # 2. Compute its SHA‑256 checksum.
    checksum = compute_sha256(CONSENT_PATH)

    # 3. Record the checksum in ``data/metadata.yaml``.
    update_metadata(METADATA_PATH, checksum)

    # 4. Log the association.
    log_consent_association(checksum)

    # Inform the user (useful when run from the command line).
    print(f"Consent document stored at: {CONSENT_PATH}")
    print(f"SHA‑256 checksum recorded in {METADATA_PATH}: {checksum}")

if __name__ == "__main__":
    main()
