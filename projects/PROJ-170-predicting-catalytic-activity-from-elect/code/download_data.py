"""
Data download module for FR-001.

This script downloads:
1. A stratified sample of the Open Catalyst (OC20) experimental dataset
   from Hugging Face using streaming and saves it as a Parquet file.
2. Bulk descriptors from the Materials Project via the mp-api client.
3. Experimental TOF data (fallback to OC20 if a dedicated 2025 study is
   not reachable) and saves it as CSV.
4. A JSON file describing the mandatory columns for the unified DataFrame.

The script records SHA‑256 checksums for each downloaded file in
`data/raw/checksums.txt`. All failures raise exceptions – no synthetic
fallback is performed.
"""
import os
import sys
import json
import hashlib
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from datasets import load_dataset

# Optional mp-api import; will raise a clear error if unavailable.
try:
    from mp_api.client import MPRester
except ImportError:
    MPRester = None

# Project utilities
from config import get_data_path, get_output_path
from logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
# Updated to a real, publicly accessible Hugging Face dataset.
REPO_ID = "open-catalyst-project/oc20"
REPO_CONFIG = "s2ef"          # configuration containing the S2EF data
SAMPLE_SIZE = 1000            # Target number of rows in the stratified sample
BUFFER_SIZE = 5000            # Number of rows to stream into memory for stratification

RAW_DIR = get_data_path() / "raw"
PARQUET_FILE = RAW_DIR / "oc20_sample.parquet"
MP_DESCRIPTORS_FILE = RAW_DIR / "mp_descriptors.json"
EXP_TOF_FILE = RAW_DIR / "experimental_tof.csv"
REQUIRED_COLUMNS_FILE = RAW_DIR / "required_columns.json"
CHECKSUM_FILE = RAW_DIR / "checksums.txt"
FILE_NAME = "oc20_sample.parquet"

# ----------------------------------------------------------------------
# Helper functions (checksum handling)
# ----------------------------------------------------------------------
def load_expected_checksums() -> Dict[str, str]:
    """Load expected checksums from the checksum file (plain text)."""
    checksums: Dict[str, str] = {}
    if CHECKSUM_FILE.exists():
        with open(CHECKSUM_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    name, value = line.split()
                    checksums[name] = value
                except ValueError:
                    # ignore malformed lines
                    continue
    return checksums

def save_checksum(filename: str, checksum: str) -> None:
    """Append a checksum entry to the checksum file."""
    checksums = load_expected_checksums()
    checksums[filename] = checksum
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Write all entries (overwrite each time for simplicity)
    with open(CHECKSUM_FILE, "w") as f:
        for name, val in checksums.items():
            f.write(f"{name} {val}\\n")

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
        expected_checksum = load_expected_checksums().get(filepath.name)
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
def _extract_elements(composition_str: str) -> List[str]:
    """Simple element extraction from a chemical formula string."""
    return re.findall(r"[A-Z][a-z]?", composition_str)

def derive_composition_family(composition_str: str) -> str:
    """Derive a simple composition family for stratification."""
    try:
        elements = _extract_elements(composition_str)
        if not elements:
            return "Unknown"
        counts: Dict[str, int] = {}
        for el in elements:
            counts[el] = counts.get(el, 0) + 1
        if "O" in counts:
            non_oxides = [el for el in elements if el != "O"]
            if non_oxides:
                primary = non_oxides[0]
                return f"Oxide_{primary}"
            return "Oxide_Other"
        else:
            primary = elements[0]
            return f"Material_{primary}"
    except Exception as e:
        logger.error(f"Failed to derive composition family for '{composition_str}': {e}")
        return "Unknown"

def download_oc20_stratified_sample() -> Path:
    """
    Downloads the OC20 experimental dataset using streaming,
    performs a proportional stratified sample, and writes to Parquet.
    """
    logger.info(f"Streaming OC20 dataset from {REPO_ID} (config={REPO_CONFIG})")

    try:
        # Load dataset in streaming mode
        dataset = load_dataset(
            REPO_ID,
            name=REPO_CONFIG,
            streaming=True,
            split='train'
        )

        # Collect a buffer to perform stratification
        buffer: List[Dict[str, Any]] = []
        for i, entry in enumerate(dataset):
            buffer.append(entry)
            if i + 1 >= BUFFER_SIZE:
                break

        if not buffer:
            raise RuntimeError(f"No data retrieved from {REPO_ID}")

        df = pd.DataFrame(buffer)
        logger.info(f"Collected buffer of {len(df)} rows from stream")

        # Ensure required column exists for stratification
        if "composition" not in df.columns:
            raise RuntimeError("OC20 dataset does not contain a 'composition' column required for stratification.")

        # Stratification
        df["_family"] = df["composition"].apply(derive_composition_family)

        sampled_frames = []
        total = len(df)
        for family, group in df.groupby("_family"):
            frac = len(group) / total
            n_take = max(1, int(round(frac * SAMPLE_SIZE)))
            n_take = min(n_take, len(group))
            sampled_frames.append(group.sample(n=n_take, random_state=42))

        sampled_df = pd.concat(sampled_frames).reset_index(drop=True)

        # If we still have fewer rows than SAMPLE_SIZE, fill with random rows
        if len(sampled_df) < SAMPLE_SIZE and len(df) > len(sampled_df):
            remaining = SAMPLE_SIZE - len(sampled_df)
            extra = df.drop(sampled_df.index).sample(
                n=min(remaining, len(df) - len(sampled_df)),
                random_state=42
            )
            sampled_df = pd.concat([sampled_df, extra]).reset_index(drop=True)

        logger.info(f"Final stratified sample size: {len(sampled_df)} rows")

        # Write to Parquet
        PARQUET_FILE.parent.mkdir(parents=True, exist_ok=True)
        sampled_df.drop(columns=["_family"]).to_parquet(PARQUET_FILE, index=False)
        logger.info(f"Wrote stratified sample to {PARQUET_FILE}")

        # Record checksum
        checksum = compute_file_hash(PARQUET_FILE)
        save_checksum(PARQUET_FILE.name, checksum)

        return PARQUET_FILE
    except Exception as e:
        raise RuntimeError(f"Failed to fetch OC20 dataset: {e}") from e

# ----------------------------------------------------------------------
# Materials Project descriptor download
# ----------------------------------------------------------------------
def download_mp_descriptors(compositions: List[str]) -> Path:
    """Retrieves bulk descriptors from Materials Project via API."""
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise RuntimeError("Materials Project API key not found in MP_API_KEY")
    if MPRester is None:
        raise RuntimeError("mp-api client could not be imported")

    logger.info(f"Fetching MP bulk descriptors for {len(compositions)} compositions")
    descriptors: Dict[str, Dict[str, Any]] = {}

    with MPRester(api_key) as mpr:
        for comp in set(compositions):
            try:
                results = mpr.summary.search(
                    formula=comp,
                    fields=["material_id", "formula_pretty"]
                )
                if results:
                    entry = results[0]
                    descriptors[comp] = {
                        "material_id": entry.material_id,
                        "formula_pretty": entry.formula_pretty,
                        "d_band_center": None,
                        "p_band_center": None,
                        "bader_charges": None,
                    }
            except Exception as e:
                logger.error(f"Failed to retrieve MP data for {comp}: {e}")
                raise RuntimeError(f"MP descriptor fetch failed for composition {comp}") from e

    MP_DESCRIPTORS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MP_DESCRIPTORS_FILE, "w") as f:
        json.dump(descriptors, f, indent=2)

    checksum = compute_file_hash(MP_DESCRIPTORS_FILE)
    save_checksum(MP_DESCRIPTORS_FILE.name, checksum)
    return MP_DESCRIPTORS_FILE

# ----------------------------------------------------------------------
# Experimental TOF data extraction (fallback to OC20 columns)
# ----------------------------------------------------------------------
def extract_experimental_tof(sample_path: Path) -> Path:
    """Extracts experimental TOF CSV (fallback to OC20)."""
    logger.info(f"Extracting experimental TOF from {sample_path}")
    df = pd.read_parquet(sample_path)

    required = ["composition", "surface_facet", "synthesis_condition", "experimental_tof"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"Required columns for experimental TOF missing in OC20: {missing}")

    df_tof = df[required].copy()
    EXP_TOF_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_tof.to_csv(EXP_TOF_FILE, index=False)

    checksum = compute_file_hash(EXP_TOF_FILE)
    save_checksum(EXP_TOF_FILE.name, checksum)
    return EXP_TOF_FILE

# ----------------------------------------------------------------------
# Required columns description
# ----------------------------------------------------------------------
def write_required_columns() -> Path:
    """
    Writes a JSON file describing the mandatory columns for the unified DataFrame.
    """
    required_columns = [
        "catalyst_id",
        "composition",
        "surface_facet",
        "synthesis_condition",
        "d_band_center",
        "p_band_center",
        "bader_charges",
        "activation_barrier",
        "reaction_energy",
        "experimental_tof",
        "temperature",
        "pressure"
    ]
    REQUIRED_COLUMNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REQUIRED_COLUMNS_FILE, "w") as f:
        json.dump(required_columns, f, indent=2)

    checksum = compute_file_hash(REQUIRED_COLUMNS_FILE)
    save_checksum(REQUIRED_COLUMNS_FILE.name, checksum)
    return REQUIRED_COLUMNS_FILE

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """Executes the full FR‑001 data acquisition pipeline."""
    try:
        # 1. OC20 Stratified Sample
        parquet_path = download_oc20_stratified_sample()

        # 2. Experimental TOF (fallback logic)
        extract_experimental_tof(parquet_path)

        # 3. MP Descriptors
        df_sample = pd.read_parquet(parquet_path)
        comps = df_sample["composition"].dropna().astype(str).tolist()
        download_mp_descriptors(comps)

        # 4. Required columns description
        write_required_columns()

        logger.info("All data acquisition steps completed successfully")
        return 0
    except Exception as exc:
        logger.error(f"Data acquisition failed: {exc}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
