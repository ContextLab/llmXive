"""
Download bulk configuration records from OQMD with retry logic,
sample exactly 600 records (200 each of Fe‑Cr, Ni‑Al, Cu‑Zn),
write them to ``data/raw/oqmd_records/`` and record SHA‑256 checksums
and metadata in ``data/metadata.yaml``.
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
from datasets import load_dataset

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
def _write_record(record: Dict, out_path: Path) -> str:
    """Write a record as JSON and return its SHA-256 checksum."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(record, fp, indent=2, sort_keys=True)

    sha256 = hashlib.sha256()
    with open(out_path, "rb") as fp:
        for chunk in iter(lambda: fp.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def _write_manifest(manifest_path: Path, url: str, reason: str) -> None:
    """Append a failure entry to the inaccessible manifest."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"failed_urls": []}
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pass
    data["failed_urls"].append({"url": url, "reason": reason})
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

def _update_metadata(checksums: Dict[str, str], sampling_rule: str, waiver_status: str = "DATA_UNAVAILABLE") -> None:
    """Update data/metadata.yaml with OQMD download provenance."""
    data_paths = get_data_paths()
    metadata_path: Path = data_paths["metadata"]
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    metadata = {}
    if metadata_path.exists():
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = yaml.safe_load(f) or {}

    metadata.setdefault("oqmd_download", {})
    oqmd_entry = metadata["oqmd_download"]
    oqmd_entry["sampling_rule"] = sampling_rule
    oqmd_entry["materials_project_status"] = waiver_status
    oqmd_entry["checksums"] = checksums

    with open(metadata_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(metadata, f, sort_keys=False)
    logger.info(f"Metadata updated at {metadata_path}")

# -------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------
def download_bulk_configs(url: str, max_retries: int = 3, metadata_path: Path = None) -> Dict:
    """Generic download helper with retry logic for unit tests."""
    if metadata_path is None:
        metadata_path = get_data_paths()["metadata"]

    attempt = 0
    while attempt < max_retries:
        attempt += 1
        val = validate_citations(url, str(metadata_path))
        if val.get("success"):
            break
        if attempt < max_retries:
            time.sleep(2 ** attempt)
        else:
            logger.error("[DATA_UNAVAILABLE] URL validation exhausted.")
            _write_manifest(metadata_path.parent / "inaccessible_manifest.json", url, val.get("error_code", "UNKNOWN"))
            return {"success": False, "error_code": "DATA_UNAVAILABLE"}

    try:
        head_resp = requests.head(url, timeout=10)
        if head_resp.status_code != 200:
            raise RuntimeError(f"HEAD {head_resp.status_code}")
    except Exception as e:
        _write_manifest(metadata_path.parent / "inaccessible_manifest.json", url, "HEAD_FAILED")
        return {"success": False, "error_code": "DATA_UNAVAILABLE"}

    raw_dir = paths.data("raw", "oqmd_records")
    raw_dir.mkdir(parents=True, exist_ok=True)
    filename = url.split("/")[-1] or f"download_{int(time.time())}.bin"
    out_path = raw_dir / filename

    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(out_path, "wb") as f:
                shutil.copyfileobj(r.raw, f)
    except Exception as e:
        _write_manifest(metadata_path.parent / "inaccessible_manifest.json", url, "DOWNLOAD_FAILED")
        return {"success": False, "error_code": "DATA_UNAVAILABLE"}

    sha256 = hashlib.sha256()
    with open(out_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    
    rel_path = str(out_path.relative_to(get_project_root()))
    _update_metadata({rel_path: sha256.hexdigest()}, "direct_download")
    return {"success": True, "error_code": None}

def download_oqmd_records(max_retries: int = 3, seed: int = 20231023) -> None:
    """Download and sample 600 OQMD records (200 each of Fe-Cr, Ni-Al, Cu-Zn)."""
    random.seed(seed)
    raw_oqmd_dir = paths.data("raw", "oqmd_records")
    raw_oqmd_dir.mkdir(parents=True, exist_ok=True)

    attempt = 0
    while attempt < max_retries:
        attempt += 1
        try:
            logger.info(f"Attempt {attempt}/{max_retries}: Loading OQMD dataset (streaming).")
            dataset = load_dataset("jablonkagroup/oqmd", name="raw_data", streaming=True)
            
            target_systems = {"Fe-Cr": ["Fe", "Cr"], "Ni-Al": ["Ni", "Al"], "Cu-Zn": ["Cu", "Zn"]}
            collected = {sys: [] for sys in target_systems}
            
            # Stream and filter
            for rec in dataset:
                for sys, elements in target_systems.items():
                    comp = rec.get("composition", "").lower()
                    if all(el.lower() in comp for el in elements):
                        collected[sys].append(rec)
                # Optimization: stop if we have plenty for sampling
                if all(len(v) >= 2000 for v in collected.values()):
                    break
            
            # Check if we have enough for each
            for sys, recs in collected.items():
                if len(recs) < 200:
                    raise ValueError(f"Insufficient records for {sys}: found {len(recs)}, need 200")
            
            # Sampling
            checksums = {}
            total_sampled = 0
            for sys, recs in collected.items():
                chosen = random.sample(recs, 200)
                for idx, rec in enumerate(chosen, 1):
                    fname = f"{sys.replace('-', '_')}_record_{idx:03d}.json"
                    out_path = raw_oqmd_dir / fname
                    checksums[str(out_path.relative_to(get_project_root()))] = _write_record(rec, out_path)
                    total_sampled += 1
            
            _update_metadata(checksums, "200 records each of Fe‑Cr, Ni‑Al, Cu‑Zn (total 600 records)")
            logger.info(f"Successfully sampled {total_sampled} OQMD records.")
            return
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(2 ** attempt)
            else:
                logger.error("[DATA_UNAVAILABLE] OQMD download failed after retries.")
                _update_metadata({}, "", "DATA_UNAVAILABLE")
                raise e

def main() -> None:
    """CLI entry point."""
    try:
        download_oqmd_records()
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()
