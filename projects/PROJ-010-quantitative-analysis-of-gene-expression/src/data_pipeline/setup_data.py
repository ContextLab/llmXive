import os
import hashlib
import yaml
import datetime
import requests
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def calculate_sha256(file_path: os.PathLike) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Parameters
    ----------
    file_path : PathLike
        Path to the file.

    Returns
    -------
    str
        Hexadecimal SHA-256 digest.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def verify_dataset_accessibility(geo_accession: str) -> bool:
    """
    Verify that a GEO dataset is reachable via HTTP.

    Parameters
    ----------
    geo_accession : str
        GEO Series accession (e.g., "GSE131928").

    Returns
    -------
    bool
        True if the GEO page returns HTTP 200.
    """
    url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={geo_accession}"
    try:
        response = requests.head(url, timeout=30)
        if response.status_code == 200:
            log.info(f"GEO dataset {geo_accession} is accessible.")
            return True
        else:
            log.error(f"GEO dataset {geo_accession} returned status {response.status_code}.")
            return False
    except requests.RequestException as e:
        log.error(f"Failed to reach GEO dataset {geo_accession}: {e}")
        return False

# ----------------------------------------------------------------------
# Main routine
# ----------------------------------------------------------------------
def main() -> None:
    """
    Project setup entry point.

    - Ensures required directory layout exists.
    - Verifies accessibility of a reference fetal brain atlas dataset.
    - Computes SHA-256 checksums for all files under ``data/raw``.
    - Writes a ``project_state.yaml`` file documenting the above.
    """
    # 1. Ensure directory layout
    required_dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("processed"),
        paths.figures(),
        paths.results(),
    ]
    for d in required_dirs:
        d.mkdir(parents=True, exist_ok=True)
        log.debug(f"Ensured directory: {d}")

    # 2. Verify dataset accessibility (using a known human fetal brain atlas GEO accession)
    # NOTE: This is a lightweight HTTP HEAD request; it does not download large files.
    GEO_ACCESSION = "GSE131928"  # Example fetal brain scRNA‑seq atlas
    dataset_accessible = verify_dataset_accessibility(GEO_ACCESSION)

    # 3. Compute SHA‑256 checksums for raw files
    raw_dir = paths.data("raw")
    checksums = {}
    if raw_dir.exists():
        for root, _, files in os.walk(raw_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    checksum = calculate_sha256(fpath)
                    rel_path = os.path.relpath(fpath, raw_dir)
                    checksums[rel_path] = checksum
                    log.debug(f"Checksum for {rel_path}: {checksum}")
                except Exception as e:
                    log.error(f"Failed to checksum {fpath}: {e}")

    # 4. Write project_state.yaml
    state = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "raw_checksums": checksums,
        "dataset_accessible": dataset_accessible,
        "geo_accession": GEO_ACCESSION,
    }
    state_path = paths.data("project_state.yaml")
    with open(state_path, "w") as f:
        yaml.safe_dump(state, f, sort_keys=False)
    log.info(f"Project state written to {state_path}")

    # Exit status
    if not dataset_accessible:
        raise RuntimeError(
            f"Dataset {GEO_ACCESSION} is not accessible; aborting setup."
        )

if __name__ == "__main__":
    main()
