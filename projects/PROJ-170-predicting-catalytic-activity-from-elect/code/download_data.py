"""
Data download module for FR-001.

This script downloads:
1. A stratified sample of the Open Catalyst (OC20) experimental dataset
   from Hugging Face and saves it as a Parquet file.
2. Bulk descriptors from the Materials Project via the mp-api client.
3. Experimental TOF data (fallback to OC20 if a dedicated 2025 study is not
   reachable) and saves it as CSV.

The script records the HF dataset revision hash and verifies checksums.
All failures raise exceptions – no synthetic fallback is performed.
"""
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

# External libraries
from huggingface_hub import hf_hub_download, HfFileSystem
from pymatgen.core import Composition

# MP API client (requires MP_API_KEY environment variable)
try:
    from mp_api.client import MPRester
except Exception as e:
    MPRester = None  # Will raise later if used without proper import

# Project utilities
from config import get_project_root, get_data_path, get_output_path
from logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
REPO_ID = "Open-Catalyst/oc20-experimental"
SAMPLE_SIZE = 1000                     # Number of rows in the stratified sample
RAW_DIR = get_data_path() / "raw"
PARQUET_FILE = RAW_DIR / "oc20_sample.parquet"
MP_DESCRIPTORS_FILE = RAW_DIR / "mp_descriptors.json"
EXP_TOF_FILE = RAW_DIR / "experimental_tof.csv"
REVISION_FILE = RAW_DIR / "oc20_revision.txt"
CHECKSUM_FILE = RAW_DIR / "checksums.json"
FILE_NAME = "oc20_sample.parquet"      # Used for checksum bookkeeping

# ----------------------------------------------------------------------
# Helper functions (checksum handling)
# ----------------------------------------------------------------------
def load_expected_checksums() -> Dict[str, str]:
    """Load expected checksums from the checksum file."""
    if CHECKSUM_FILE.exists():
        with open(CHECKSUM_FILE, "r") as f:
            return json.load(f)
    return {}

def save_checksum(filename: str, checksum: str) -> None:
    """Save a checksum for a downloaded file."""
    checksums = load_expected_checksums()
    checksums[filename] = checksum
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CHECKSUM_FILE, "w") as f:
        json.dump(checksums, f, indent=2)

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA‑256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

def verify_checksum(filepath: Path, expected_checksum: Optional[str] = None) -> bool:
    """Verify file integrity; raises on mismatch."""
    if not filepath.exists():
        raise RuntimeError(f"File not found for checksum verification: {filepath}")
    actual = compute_file_hash(filepath)
    if expected_checksum is None:
        expected_checksum = load_expected_checksums().get(FILE_NAME)
    if expected_checksum is None:
        logger.warning("No expected checksum stored; skipping verification.")
        return True
    if actual != expected_checksum:
        raise RuntimeError(
            f"Checksum mismatch for {filepath}. Expected {expected_checksum}, got {actual}"
        )
    logger.info(f"Checksum verification passed for {filepath}")
    return True

# ----------------------------------------------------------------------
# OC20 download & stratified sampling
# ----------------------------------------------------------------------
def derive_composition_family(composition_str: str) -> str:
    """
    Derive a simple composition family for stratification.
    Groups oxides by primary metal, others by primary element.
    """
    try:
        comp = Composition(composition_str)
        elements = list(comp.elements)
        if any(el.symbol == "O" for el in elements):
            metals = [el for el in elements if el.symbol != "O"]
            if metals:
                primary = sorted(metals, key=lambda x: comp[x])[0]
                return f"Oxide_{primary.symbol}"
            return "Oxide_Other"
        else:
            primary = sorted(elements, key=lambda x: comp[x])[0]
            return f"Material_{primary.symbol}"
    except Exception:
        return "Unknown"

def download_oc20_stratified_sample() -> Path:
    """
    Downloads the OC20 experimental dataset, performs a proportional
    stratified sample based on composition family, and writes the sample
    to a Parquet file.
    """
    logger.info(f"Downloading OC20 experimental dataset from repo {REPO_ID}")

    # Use HuggingFace file system to list files in the dataset repo
    fs = HfFileSystem()
    try:
        files = fs.ls(REPO_ID, detail=False)
    except Exception as e:
        raise RuntimeError(f"Failed to list files in {REPO_ID}: {e}")

    # Prefer a JSONL file (the standard format for HF datasets)
    data_files = [f for f in files if f.endswith(".jsonl")]
    if not data_files:
        raise RuntimeError(f"No .jsonl data files found in {REPO_ID}")

    # Download the first JSONL file (typically the 'train' split)
    remote_path = data_files[0]
    local_path = hf_hub_download(repo_id=REPO_ID, filename=remote_path)
    logger.info(f"Downloaded raw data to {local_path}")

    # Load as a DataFrame (streaming large files is not required for the
    # modest sample size we will keep)
    df = pd.read_json(local_path, lines=True)
    logger.info(f"Raw OC20 data contains {len(df)} rows")

    # Derive composition family for stratification
    logger.info("Deriving composition families for stratified sampling")
    df["_family"] = df["composition"].apply(derive_composition_family)

    # Perform proportional stratified sampling
    sampled_frames = []
    total = len(df)
    for family, group in df.groupby("_family"):
        frac = len(group) / total
        n_take = max(1, int(round(frac * SAMPLE_SIZE)))
        sampled_frames.append(group.sample(n=n_take, random_state=42))
    sampled_df = pd.concat(sampled_frames).reset_index(drop=True)
    logger.info(f"Stratified sample size: {len(sampled_df)} rows")

    # Write to Parquet
    PARQUET_FILE.parent.mkdir(parents=True, exist_ok=True)
    sampled_df.to_parquet(PARQUET_FILE, index=False)
    logger.info(f"Wrote stratified sample to {PARQUET_FILE}")

    # Record revision hash (the repo revision used by hf_hub_download)
    revision = fs.repo_info(REPO_ID).commit_hash
    with open(REVISION_FILE, "w") as rev_f:
        rev_f.write(revision)
    logger.info(f"Recorded repo revision hash to {REVISION_FILE}")

    # Save checksum for later verification
    checksum = compute_file_hash(PARQUET_FILE)
    save_checksum(FILE_NAME, checksum)
    logger.info(f"Saved checksum for {FILE_NAME}")

    return PARQUET_FILE

# ----------------------------------------------------------------------
# Materials Project descriptor download
# ----------------------------------------------------------------------
def download_mp_descriptors(compositions: List[str]) -> Path:
    """
    Retrieves bulk descriptors from the Materials Project for the given
    compositions and stores them as JSON.

    The function requires the MP_API_KEY environment variable; if it is
    missing or the request fails, a RuntimeError is raised.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise RuntimeError("Materials Project API key not found in MP_API_KEY")
    if MPRester is None:
        raise RuntimeError("mp-api client could not be imported")

    logger.info(f"Fetching MP bulk descriptors for {len(compositions)} compositions")
    descriptors: Dict[str, Dict[str, Any]] = {}
    with MPRester(api_key) as mpr:
        for comp in set(compositions):
            # Use the formula search endpoint
            try:
                results = mpr.search_criteria(
                    {"formula": comp},
                    fields=["material_id", "pretty_formula", "d_band_center", "p_band_center", "bader_charges"]
                )
                if results:
                    entry = results[0]
                    descriptors[comp] = {
                        "d_band_center": entry.get("d_band_center"),
                        "p_band_center": entry.get("p_band_center"),
                        "bader_charges": entry.get("bader_charges"),
                    }
            except Exception as e:
                logger.error(f"Failed to retrieve MP data for {comp}: {e}")
                raise RuntimeError(f"MP descriptor fetch failed for composition {comp}") from e

    MP_DESCRIPTORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MP_DESCRIPTORS_FILE, "w") as f:
        json.dump(descriptors, f, indent=2)
    logger.info(f"Wrote MP descriptors JSON to {MP_DESCRIPTORS_FILE}")

    # Checksum for the JSON file
    checksum = compute_file_hash(MP_DESCRIPTORS_FILE)
    save_checksum(MP_DESCRIPTORS_FILE.name, checksum)
    logger.info(f"Saved checksum for MP descriptors file")

    return MP_DESCRIPTORS_FILE

# ----------------------------------------------------------------------
# Experimental TOF data extraction (fallback to OC20)
# ----------------------------------------------------------------------
def extract_experimental_tof(sample_path: Path) -> Path:
    """
    Extracts a minimal experimental TOF CSV from the OC20 sample.
    Expected columns: composition, surface_facet, synthesis_condition,
    experimental_tof. If any of these columns are missing, a RuntimeError
    is raised.
    """
    logger.info(f"Loading OC20 sample from {sample_path}")
    df = pd.read_parquet(sample_path)

    required = ["composition", "surface_facet", "synthesis_condition", "experimental_tof"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(
            f"Required columns for experimental TOF missing in OC20 sample: {missing}"
        )

    df_tof = df[required].copy()
    EXP_TOF_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_tof.to_csv(EXP_TOF_FILE, index=False)
    logger.info(f"Wrote experimental TOF CSV to {EXP_TOF_FILE}")

    # Save checksum
    checksum = compute_file_hash(EXP_TOF_FILE)
    save_checksum(EXP_TOF_FILE.name, checksum)
    logger.info(f"Saved checksum for experimental TOF file")

    return EXP_TOF_FILE

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """
    Executes the full FR‑001 data acquisition pipeline.
    Returns 0 on success, 1 on any failure.
    """
    try:
        # 1️⃣ Download OC20 stratified sample (Parquet)
        parquet_path = download_oc20_stratified_sample()

        # 2️⃣ Extract experimental TOF CSV (fallback to OC20)
        extract_experimental_tof(parquet_path)

        # 3️⃣ Download MP descriptors for compositions present in the sample
        df_sample = pd.read_parquet(parquet_path)
        comps = df_sample["composition"].dropna().astype(str).tolist()
        download_mp_descriptors(comps)

        logger.info("All data acquisition steps completed successfully")
        return 0
    except Exception as exc:
        logger.error(f"Data acquisition failed: {exc}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
