import os
import sys
import pandas as pd
import hashlib
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

# Ensure imports work relative to project root if run as script
if __name__ == '__main__' and 'code' not in sys.path[0]:
    sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

# Verified sources as per project constraints
# Primary: MoleculeNet S3 (as per task description)
PRIMARY_SOURCE_URL = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/delaney-processed.csv"
# Fallback: HuggingFace direct file resolve (verified mirror)
FALLBACK_SOURCE_URL = "https://huggingface.co/datasets/deepchem/delaney-processed/resolve/main/delaney-processed.csv"

def fetch_esol_dataset(output_dir: str) -> pd.DataFrame:
    """
    Fetches the ESOL dataset from verified real sources.
    Tries Primary URL, then Fallback URL.
    Fails loudly if both sources are unreachable.
    No synthetic fallbacks allowed.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    csv_path = output_path / "delaney-processed.csv"

    if csv_path.exists():
        logger.info(f"Found existing raw CSV at {csv_path}")
        # Validate content minimally
        try:
            df = pd.read_csv(csv_path)
            if "logS" in df.columns:
                return df
            else:
                logger.warning("Existing CSV missing 'logS' column, re-fetching...")
        except Exception:
            logger.warning("Existing CSV corrupted, re-fetching...")

    # Attempt Primary Source
    logger.info(f"Attempting to fetch from Primary Source: {PRIMARY_SOURCE_URL}")
    try:
        df = _download_csv(PRIMARY_SOURCE_URL, output_path)
        return df
    except Exception as e:
        logger.warning(f"Primary source failed: {e}. Attempting fallback...")

    # Attempt Fallback Source
    logger.info(f"Attempting to fetch from Fallback Source: {FALLBACK_SOURCE_URL}")
    try:
        df = _download_csv(FALLBACK_SOURCE_URL, output_path)
        return df
    except Exception as e:
        logger.error(f"Fallback source failed: {e}")
        # CRITICAL: Fail loudly. No synthetic fallback.
        raise RuntimeError(
            f"CRITICAL: Could not fetch real data from any verified source. "
            f"Primary: {PRIMARY_SOURCE_URL}, Fallback: {FALLBACK_SOURCE_URL}. "
            f"Aborting."
        ) from e

def _download_csv(url: str, output_path: Path) -> pd.DataFrame:
    """Helper to download CSV from a URL and return as DataFrame."""
    try:
        # Use urllib to fetch the file directly
        with urllib.request.urlopen(url, timeout=30) as response:
            if response.status != 200:
                raise ConnectionError(f"HTTP {response.status}")
            
            # Save raw content
            raw_path = output_path / "delaney-processed.csv"
            with open(raw_path, "wb") as f:
                f.write(response.read())
        
        # Load and validate
        df = pd.read_csv(raw_path)
        
        # Validate required columns
        if "logS" not in df.columns:
            raise ValueError("Invalid dataset format: 'logS' column missing.")
        if "smiles" not in df.columns:
            # Handle case sensitivity if needed
            cols_lower = {c.lower(): c for c in df.columns}
            if "smiles" in cols_lower:
                df = df.rename(columns={cols_lower["smiles"]: "smiles"})
            else:
                raise ValueError("Invalid dataset format: 'smiles' column missing.")
        
        logger.info(f"Successfully downloaded and validated CSV from {url}")
        return df

    except urllib.error.URLError as e:
        raise ConnectionError(f"Network error fetching {url}: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to process CSV from {url}: {e}")

def save_raw_csv(df: pd.DataFrame, output_path: str):
    """Saves the dataframe to a CSV file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved raw CSV to {output_path}")

def verify_checksum(file_path: str) -> str:
    """Computes SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state_manifest(checksum: str, csv_path: str):
    """Updates the project state manifest with the artifact checksum."""
    import yaml
    from config.seeds import get_seed # Just to ensure config imports work if needed elsewhere, though not strictly used here
    
    project_id = "PROJ-351-predicting-the-solubility-of-pharmaceuti"
    state_dir = Path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = state_dir / f"{project_id}.yaml"
    
    # Load existing or create new
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            try:
                state = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state = {}
    else:
        state = {}
    
    # Ensure structure
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    # Update specific hash
    relative_path = csv_path
    if not relative_path.startswith("data/"):
        relative_path = f"data/{csv_path}"
        
    state["artifact_hashes"][relative_path] = f"sha256:{checksum}"
    
    # Write back
    with open(manifest_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated state manifest at {manifest_path}")

def main():
    """Main entry point for downloading ESOL dataset."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    output_dir = os.environ.get("DATA_RAW_DIR", "data/raw")
    os.makedirs(output_dir, exist_ok=True)
    
    df = fetch_esol_dataset(output_dir)
    csv_path = os.path.join(output_dir, "delaney-processed.csv")
    checksum = verify_checksum(csv_path)
    logger.info(f"Dataset checksum: {checksum}")
    
    # Update state manifest
    update_state_manifest(checksum, csv_path)

if __name__ == "__main__":
    main()