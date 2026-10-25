"""
Download bulk configuration records from OQMD with retry logic,
sample exactly 600 records (200 each of Fe‑Cr, Ni‑Al, Cu‑Zn),
write them to ``data/raw/oqmd_records/`` and record SHA‑256 checksums
and metadata in ``data/metadata.yaml``.

This module also provides a generic ``download_bulk_configs`` function
used by unit tests to verify retry logic, citation validation, and
manifest handling.
"""
import json
import hashlib
import logging
import random
import time
from pathlib import Path
from typing import List, Dict

import yaml
import requests
import shutil

from llmxive_toolkit import paths
from config import get_data_paths, get_project_root
from validators import validate_citations

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def _filter_records_by_elements(
    records: List[Dict], elements: List[str]
) -> List[Dict]:
    """
    Keep records whose ``composition`` field contains **all** elements
    in ``elements`` (case‑insensitive). The OQMD dataset stores the
    composition as a string like ``Fe2 Cr1`` or ``Ni Al``.
    """
    filtered = []
    for rec in records:
        comp = rec.get("composition", "")
        comp_lower = comp.lower()
        if all(el.lower() in comp_lower for el in elements):
            filtered.append(rec)
    return filtered

def _write_record(record: Dict, out_path: Path) -> str:
    """
    Write a single record as pretty‑printed JSON and return its SHA‑256 checksum.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(record, fp, indent=2, sort_keys=True)

    sha256 = hashlib.sha256()
    with open(out_path, "rb") as fp:
        for chunk in iter(lambda: fp.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def _write_manifest(manifest_path: Path, url: str, reason: str) -> None:
    """
    Append a failure entry to the inaccessible manifest.
    The manifest format is::

        {
            "failed_urls": [
                {"url": "<url>", "reason": "<reason>"}
            ]
        }
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"failed_urls": []}

    data["failed_urls"].append({"url": url, "reason": reason})
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

def _update_metadata(
    checksums: Dict[str, str],
    sampling_rule: str,
    waiver_status: str = "DATA_UNAVAILABLE",
) -> None:
    """
    Load ``data/metadata.yaml`` (create if missing), update it with the
    OQMD download information and write it back.
    """
    data_paths = get_data_paths()
    metadata_path: Path = data_paths["metadata"]
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = yaml.safe_load(f) or {}
    else:
        metadata = {}

    metadata.setdefault("oqmd_download", {})
    oqmd_entry = metadata["oqmd_download"]
    oqmd_entry["sampling_rule"] = sampling_rule
    oqmd_entry["materials_project_status"] = waiver_status
    oqmd_entry["checksums"] = checksums

    with open(metadata_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(metadata, f, sort_keys=False)

    logger.info(f"Metadata written to {metadata_path}")

# -------------------------------------------------------------------------
# Public API expected by unit tests
# -------------------------------------------------------------------------
def download_bulk_configs(
    url: str,
    max_retries: int = 3,
    metadata_path: Path = None,
) -> Dict:
    """
    Generic download helper used by the test suite.

    Steps:
    1. Validate the URL via ``validators.validate_citations``.
    2. Retry up to ``max_retries`` times on validation failure.
    3. Perform a HEAD request to ensure the resource exists.
    4. Stream the content to a file under ``data/raw/oqmd_records``.
    5. Record a SHA‑256 checksum and update ``data/metadata.yaml``.
    6. On permanent failure, write an ``inaccessible_manifest.json`` file
       and return a failure dict with ``error_code: "DATA_UNAVAILABLE"``.

    Returns a dict with at least ``"success"`` (bool) and optionally
    ``"error_code"``.
    """
    if metadata_path is None:
        metadata_path = get_data_paths()["metadata"]

    # -----------------------------------------------------------------
    # Validation with retry
    # -----------------------------------------------------------------
    attempt = 0
    while attempt < max_retries:
        attempt += 1
        validation_result = validate_citations(url, str(metadata_path))
        if validation_result.get("success"):
            logger.info(f"URL validation succeeded on attempt {attempt}")
            break
        else:
            logger.warning(
                f"Validation failed (attempt {attempt}/{max_retries}): "
                f"{validation_result.get('error_code')}"
            )
            if attempt < max_retries:
                backoff = 2 ** attempt
                logger.info(f"Retrying after {backoff}s...")
                time.sleep(backoff)
            else:
                logger.error("[DATA_UNAVAILABLE] URL validation exhausted.")
                manifest_path = metadata_path.parent / "inaccessible_manifest.json"
                _write_manifest(
                    manifest_path,
                    url,
                    validation_result.get("error_code", "UNKNOWN"),
                )
                return {"success": False, "error_code": "DATA_UNAVAILABLE"}

    # -----------------------------------------------------------------
    # HEAD request to confirm availability
    # -----------------------------------------------------------------
    try:
        head_resp = requests.head(url, timeout=10)
        if head_resp.status_code != 200:
            raise RuntimeError(f"HEAD request returned {head_resp.status_code}")
    except Exception as exc:
        logger.error(f"HEAD request failed: {exc}")
        manifest_path = metadata_path.parent / "inaccessible_manifest.json"
        _write_manifest(manifest_path, url, "HEAD_FAILED")
        return {"success": False, "error_code": "DATA_UNAVAILABLE"}

    # -----------------------------------------------------------------
    # Download the content
    # -----------------------------------------------------------------
    raw_dir: Path = paths.data("raw", "oqmd_records")
    raw_dir.mkdir(parents=True, exist_ok=True)
    # Derive a deterministic filename from the URL
    filename = url.split("/")[-1] or f"download_{int(time.time())}.bin"
    out_path = raw_dir / filename

    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                shutil.copyfileobj(r.raw, f)
    except Exception as exc:
        logger.error(f"Download failed: {exc}")
        manifest_path = metadata_path.parent / "inaccessible_manifest.json"
        _write_manifest(manifest_path, url, "DOWNLOAD_FAILED")
        return {"success": False, "error_code": "DATA_UNAVAILABLE"}

    # Compute checksum
    sha256 = hashlib.sha256()
    with open(out_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()

    # Record checksum in metadata
    rel_path = str(out_path.relative_to(get_project_root()))
    _update_metadata(
        checksums={rel_path: checksum},
        sampling_rule="direct_download",
        waiver_status="DATA_UNAVAILABLE",
    )

    logger.info(f"Successfully downloaded {url} to {out_path}")
    return {"success": True, "error_code": None}

# -------------------------------------------------------------------------
# OQMD specific bulk download (used by the pipeline)
# -------------------------------------------------------------------------
def download_oqmd_records(
    max_retries: int = 3,
    seed: int = 20231023,
) -> None:
    """
    Download OQMD bulk configuration records, sample the required
    600 records, write them to disk and record provenance metadata.
    If the dataset cannot be loaded after the permitted retries,
    the function records an empty checksum map and exits gracefully,
    leaving a ``DATA_UNAVAILABLE`` flag in the metadata.
    """
    random.seed(seed)

    # Destination directory for the raw OQMD JSON files
    raw_oqmd_dir: Path = paths.data("raw", "oqmd_records")
    raw_oqmd_dir.mkdir(parents=True, exist_ok=True)

    attempt = 0
    all_records: List[Dict] = []
    while attempt < max_retries:
        attempt += 1
        try:
            logger.info(
                f"Attempt {attempt}/{max_retries}: loading OQMD dataset (streaming)."
            )
            dataset = load_dataset(
                "jablonkagroup/oqmd", name="raw_data", streaming=True
            )
            # Convert streaming dataset to a list for sampling.
            all_records = list(dataset)
            logger.info(f"Successfully loaded OQMD dataset with {len(all_records)} records.")
            break  # success
        except Exception as exc:
            logger.warning(
                f"OQMD dataset load failed on attempt {attempt}: {exc}"
            )
            if attempt < max_retries:
                backoff = 2 ** attempt
                logger.info(f"Retrying after {backoff}s...")
                time.sleep(backoff)
            else:
                logger.error("[DATA_UNAVAILABLE] OQMD dataset could not be loaded after retries.")
                _update_metadata(
                    checksums={},
                    sampling_rule="",
                    waiver_status="DATA_UNAVAILABLE",
                )
                return  # graceful exit; no exception propagated

    # -----------------------------------------------------------------
    # Filtering / sampling
    # -----------------------------------------------------------------
    target_systems = {
        "Fe-Cr": ["Fe", "Cr"],
        "Ni-Al": ["Ni", "Al"],
        "Cu-Zn": ["Cu", "Zn"],
    }
    sampled_records: List[Dict] = []
    checksums: Dict[str, str] = {}

    for system_name, elements in target_systems.items():
        filtered = _filter_records_by_elements(all_records, elements)
        if len(filtered) < 200:
            raise ValueError(
                f"Not enough records for system {system_name}: required 200, found {len(filtered)}"
            )
        chosen = random.sample(filtered, 200)
        for idx, rec in enumerate(chosen, start=1):
            # Deterministic filename: <system>_record_<idx>.json
            filename = f"{system_name.replace('-', '_')}_record_{idx:03d}.json"
            out_path = raw_oqmd_dir / filename
            checksum = _write_record(rec, out_path)
            # Store checksum keyed by path relative to project root for provenance
            checksums[str(out_path.relative_to(get_project_root()))] = checksum
            sampled_records.append(rec)

    # -----------------------------------------------------------------
    # Write provenance metadata
    # -----------------------------------------------------------------
    sampling_rule_desc = (
        "200 records each of Fe‑Cr, Ni‑Al, Cu‑Zn (total 600 records)"
    )
    _update_metadata(
        checksums=checksums,
        sampling_rule=sampling_rule_desc,
        waiver_status="DATA_UNAVAILABLE",
    )
    logger.info(
        f"Successfully downloaded and sampled {len(sampled_records)} OQMD records."
    )

# -------------------------------------------------------------------------
# Script entry point
# -------------------------------------------------------------------------
def main() -> None:
    """
    Entry point used by the pipeline runner.
    """
    try:
        download_oqmd_records()
    except Exception as exc:
        logger.error(f"Download failed: {exc}")
        raise

if __name__ == "__main__":
    main()