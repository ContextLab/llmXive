"""
Project‑setup script for the gene‑expression dynamics pipeline.

This script is invoked via the quick‑start command
``python src/data_pipeline/setup_data.py``.  It performs three essential
actions required by task **T001**:

1. **Directory layout** – ensures that ``code/``, ``data/raw/``,
   ``data/processed/`` and ``figures/`` exist (using the ``paths`` helper
   from ``llmxive_toolkit``).
2. **Dataset accessibility check** – verifies that a representative GEO
   series (``GSE131928`` – a human fetal brain scRNA‑seq dataset) can be
   reached over HTTP.
3. **Checksum generation & state recording** – downloads a small,
   real scRNA‑seq file (the 3 k PBMC dataset from Scanpy) into
   ``data/raw/``, computes SHA‑256 digests for every file under that
   directory and writes a ``project_state.yaml`` file that records the
   timestamp, GEO accessibility flag and the checksum map.

The script writes all artefacts under the project’s ``data/`` folder;
no external state is modified.
"""
import os
import hashlib
import yaml
import datetime
import requests
import scanpy as sc
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants – these are the real identifiers used for verification.
# ----------------------------------------------------------------------
GEO_ACCESSION = "GSE131928"  # Human fetal brain scRNA‑seq atlas (public)
RAW_FILENAME = "pbmc3k.h5ad"

# ----------------------------------------------------------------------
def calculate_sha256(file_path: os.PathLike) -> str:
    """
    Compute the SHA‑256 checksum of a file.

    Parameters
    ----------
    file_path : PathLike
        Path to the file.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ----------------------------------------------------------------------
def verify_dataset_accessibility(geo_accession: str) -> bool:
    """
    Verify that a GEO dataset page returns HTTP 200.

    Parameters
    ----------
    geo_accession : str
        GEO Series accession (e.g., ``GSE131928``).

    Returns
    -------
    bool
        True if the GEO page is reachable.
    """
    url = f"https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={geo_accession}"
    try:
        response = requests.head(url, timeout=10)
        reachable = response.status_code == 200
    except Exception as exc:
        log.error("Error checking GEO accessibility: %s", exc)
        reachable = False
    log.info("GEO accession %s reachable: %s", geo_accession, reachable)
    return reachable

# ----------------------------------------------------------------------
def _download_raw_dataset(dest_path):
    """
    Download a small, real scRNA‑seq dataset (PBMC 3k) and store it under
    ``data/raw/``.  The file is modest (~12 MB) and suitable for checksum
    generation.
    """
    log.info("Downloading PBMC 3k dataset via Scanpy")
    # Scanpy provides a reliable downloader for this dataset.
    adata = sc.datasets.pbmc3k()
    adata.write_h5ad(dest_path)
    log.info("Raw dataset saved to %s", dest_path)

# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for the project‑setup step.
    """
    # 1. Ensure directory layout exists
    for folder_func in (
        paths.code,
        paths.data,
        paths.results,
        paths.figures,
    ):
        # ``paths.<folder>()`` creates the folder if missing.
        folder_func()

    # Ensure sub‑folders under ``data/``
    paths.data("raw")
    paths.data("processed")

    # 2. Verify GEO accessibility
    geo_ok = verify_dataset_accessibility(GEO_ACCESSION)

    # 3. Download a real raw file (if not already present)
    raw_path = paths.data("raw", RAW_FILENAME)
    if not raw_path.is_file():
        _download_raw_dataset(raw_path)
    else:
        log.info("Raw file already exists at %s", raw_path)

    # 4. Compute SHA‑256 checksums for everything under ``data/raw/``
    checksums = {}
    raw_dir = paths.data("raw")
    for root, _, files in os.walk(raw_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, raw_dir)
            checksums[rel_path] = calculate_sha256(fpath)

    # 5. Write project state YAML
    state = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "geo_accessible": geo_ok,
        "raw_checksums": checksums,
    }
    state_path = paths.data("project_state.yaml")
    with open(state_path, "w") as fh:
        yaml.safe_dump(state, fh, sort_keys=False)
    log.info("Project state written to %s", state_path)

if __name__ == "__main__":
    main()
