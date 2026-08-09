import os
import sys
import hashlib
import logging
from pathlib import Path
from urllib.request import urlopen, urlretrieve

# Add parent directory to path to resolve imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from errors import DataLoadError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verified source from T006a: pycalphad's open thermodynamic database repository
# TCFE9 is proprietary, but we use the open proxy TCFE.tdb from pycalphad/thermo-data
# URL: https://github.com/pycalphad/thermo-data/raw/main/TCFE.tdb
TCFE_URL = "https://github.com/pycalphad/thermo-data/raw/main/TCFE.tdb"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "raw" / "thermo"
OUTPUT_FILE = OUTPUT_DIR / "TCFE.tdb"
EXPECTED_SHA256 = "e8e8333f19054154444044943812333433444343344334434433443344334433"  # Placeholder, will be computed

def calculate_sha256(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_thermo_proxy() -> Path:
    """
    Download the open thermodynamic proxy (TCFE.tdb) from pycalphad's open data repository.
    
    This implements the substitution of proprietary TCFE9 with an open proxy as per plan.md.
    If fetch fails or file is missing, raises DataLoadError (NO synthetic fallbacks).
    If ternary parameters are missing for specific systems, the file is still saved,
    and the gap is flagged during validation (handled by T047).
    
    Returns:
        Path: Path to the downloaded TCFE.tdb file.
    
    Raises:
        DataLoadError: If the download fails or the file cannot be verified.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if OUTPUT_FILE.exists():
        logger.info(f"Thermodynamic proxy already exists at {OUTPUT_FILE}. Skipping download.")
        # Verify checksum if we had a known hash, but for now just return
        return OUTPUT_FILE

    logger.info(f"Fetching thermodynamic proxy from {TCFE_URL}...")
    try:
        # Use urlretrieve for direct download
        urlretrieve(TCFE_URL, OUTPUT_FILE)
    except Exception as e:
        logger.error(f"Failed to download thermodynamic proxy: {e}")
        raise DataLoadError(f"Failed to download thermodynamic proxy from {TCFE_URL}: {e}")

    if not OUTPUT_FILE.exists():
        raise DataLoadError(f"Downloaded file not found at {OUTPUT_FILE}")

    # Verify file is not empty
    if OUTPUT_FILE.stat().st_size == 0:
        OUTPUT_FILE.unlink()
        raise DataLoadError(f"Downloaded thermodynamic proxy is empty at {OUTPUT_FILE}")

    sha256 = calculate_sha256(OUTPUT_FILE)
    logger.info(f"Downloaded TCFE.tdb successfully. SHA256: {sha256}")
    logger.info(f"File saved to: {OUTPUT_FILE}")
    
    # Note: We do not enforce a specific checksum here as the open source may update.
    # Instead, we rely on the file existence and non-empty check.
    # If a specific version checksum is required, it should be hardcoded and validated.
    
    return OUTPUT_FILE

def main():
    """Entry point for fetching the thermodynamic proxy."""
    try:
        output_path = fetch_thermo_proxy()
        print(f"SUCCESS: Thermodynamic proxy downloaded to {output_path}")
        # Log a note about missing ternary parameters if applicable
        # This is a placeholder; actual validation of parameters happens in T047
        print("NOTE: Validation of ternary interaction parameters will be performed by T047.")
    except DataLoadError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()