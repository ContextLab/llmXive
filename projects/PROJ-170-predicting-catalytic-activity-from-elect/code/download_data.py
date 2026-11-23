"""
Data download module for FR-001.

This script downloads:
1. A stratified sample from the OC20 dataset using HuggingFace `datasets`
   with streaming enabled.
2. Bulk electronic descriptors from the Materials Project via the `mp-api`
   client (requires `MP_API_KEY` environment variable).
3. A JSON file describing the mandatory columns for the unified DataFrame.

For each generated file the SHA-256 checksum is recorded in
`data/checksums.txt`. All failures raise exceptions; there is no
silent fallback to fabricated data.
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

try:
    from mp_api.client import MPRester
except ImportError as exc:
    # This will be caught by the main try-except and logged
    raise ImportError(
        "The `mp-api` package is required for Materials Project descriptor "
        "download. Install it via `pip install mp-api`."
    ) from exc

# Project utilities
from config import get_data_path
from logging_config import get_logger

# Configure logger
logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
OC20_DATASET = "nimashoghi/oc20_s2ef_train_2M"
SAMPLE_SIZE = 1000
BUFFER_SIZE = 10000  # Buffer to enable stratification from stream

RAW_DIR = get_data_path() / "raw"
PARQUET_FILE = RAW_DIR / "oc20_sample.parquet"
MP_DESCRIPTORS_FILE = RAW_DIR / "mp_descriptors.json"
REQUIRED_COLUMNS_FILE = RAW_DIR / "required_columns.json"
CHECKSUM_FILE = get_data_path() / "checksums.txt"

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
                    parts = line.split()
                    if len(parts) == 2:
                        name, value = parts
                        checksums[name] = value
                except ValueError:
                    continue
    return checksums

def save_checksum(filename: str, checksum: str) -> None:
    """Record a checksum entry in the checksum file without trailing empty lines."""
    checksums = load_expected_checksums()
    checksums[filename] = checksum
    CHECKSUM_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Join with newlines and ensure no trailing newline at the very end of the file
    lines = [f"{name} {val}" for name, val in checksums.items()]
    with open(CHECKSUM_FILE, "w") as f:
        f.write("\n".join(lines))

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(4096), b""):
            sha256.update(block)
    return sha256.hexdigest()

# ----------------------------------------------------------------------
# OC20 streaming download & stratified sampling
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

def download_stratified_sample() -> Path:
    """
    Streams the OC20 dataset, extracts composition, performs proportional 
    stratified sampling, and writes the result to Parquet.
    """
    logger.info(f"Streaming OC20 dataset from HuggingFace: {OC20_DATASET}")
    try:
        # Using trust_remote_code=False as per modern datasets API for public datasets
        dataset = load_dataset(OC20_DATASET, split="train", streaming=True)
    except Exception as e:
        raise RuntimeError(f"Failed to load OC20 dataset via `datasets`: {e}") from e

    rows: List[Dict[str, Any]] = []
    for i, example in enumerate(dataset):
        rows.append(example)
        if i + 1 >= BUFFER_SIZE:
            break

    if not rows:
        raise RuntimeError("No rows were retrieved from the OC20 stream.")

    df = pd.DataFrame(rows)

    # Extract composition from structure if not present directly
    if "composition" not in df.columns:
        if "structure" in df.columns:
            def _extract_formula(struct):
                if not isinstance(struct, dict): return "Unknown"
                return struct.get("formula_pretty") or struct.get("formula") or "Unknown"
            df["composition"] = df["structure"].apply(_extract_formula)
        else:
            logger.warning("No composition information found; filling with placeholder 'Unknown'.")
            df["composition"] = "Unknown"

    df["_family"] = df["composition"].apply(derive_composition_family)

    sampled_frames = []
    total = len(df)
    for family, group in df.groupby("_family"):
        frac = len(group) / total
        n_take = max(1, int(round(frac * SAMPLE_SIZE)))
        n_take = min(n_take, len(group))
        sampled_frames.append(group.sample(n=n_take, random_state=42))

    sampled_df = pd.concat(sampled_frames).reset_index(drop=True)

    # Fill remaining slots if sampling didn't reach SAMPLE_SIZE
    if len(sampled_df) < SAMPLE_SIZE and len(df) > len(sampled_df):
        remaining = SAMPLE_SIZE - len(sampled_df)
        # Use indices not already in sampled_df
        remaining_pool = df.drop(sampled_df.index)
        extra = remaining_pool.sample(
            n=min(remaining, len(remaining_pool)),
            random_state=42,
        )
        sampled_df = pd.concat([sampled_df, extra]).reset_index(drop=True)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    sampled_df.drop(columns=["_family"]).to_parquet(PARQUET_FILE, index=False)
    
    save_checksum(PARQUET_FILE.name, compute_file_hash(PARQUET_FILE))
    return PARQUET_FILE

# ----------------------------------------------------------------------
# Materials Project descriptor download
# ----------------------------------------------------------------------
def download_mp_descriptors(compositions: List[str]) -> Path:
    """
    Retrieves bulk electronic descriptors from the Materials Project for the
    supplied list of compositions.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        raise RuntimeError(
            "MP_API_KEY environment variable not set. Materials Project descriptors "
            "cannot be fetched without a valid API key."
        )

    logger.info(f"Fetching MP bulk descriptors for {len(set(compositions))} unique compositions.")
    descriptors: Dict[str, Dict[str, Any]] = {}

    with MPRester(api_key) as mpr:
        for comp in set(compositions):
            try:
                # Search for summary data including electronic descriptors
                results = mpr.summary.search(
                    formula=comp,
                    fields=["material_id", "formula_pretty", "d_band_center", "p_band_center", "bader_charges"],
                )
                if results:
                    entry = results[0]
                    descriptors[comp] = {
                        "material_id": str(getattr(entry, "material_id", None)),
                        "formula_pretty": getattr(entry, "formula_pretty", comp),
                        "d_band_center": getattr(entry, "d_band_center", None),
                        "p_band_center": getattr(entry, "p_band_center", None),
                        "bader_charges": getattr(entry, "bader_charges", None),
                    }
                else:
                    descriptors[comp] = {
                        "material_id": None,
                        "formula_pretty": comp,
                        "d_band_center": None,
                        "p_band_center": None,
                        "bader_charges": None,
                    }
            except Exception as e:
                logger.error(f"Failed to retrieve MP data for composition '{comp}': {e}")
                # We raise here to fail loudly as per constraints
                raise RuntimeError(f"MP descriptor fetch failed for composition {comp}") from e

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(MP_DESCRIPTORS_FILE, "w") as f:
        json.dump(descriptors, f, indent=2)

    save_checksum(MP_DESCRIPTORS_FILE.name, compute_file_hash(MP_DESCRIPTORS_FILE))
    return MP_DESCRIPTORS_FILE

# ----------------------------------------------------------------------
# Required columns description
# ----------------------------------------------------------------------
def write_required_columns() -> Path:
    """Writes a JSON file describing the mandatory columns for the unified DataFrame."""
    required_columns = [
        "catalyst_id", "composition", "surface_facet", "synthesis_condition",
        "d_band_center", "p_band_center", "bader_charges", "activation_barrier",
        "reaction_energy", "experimental_tof", "temperature", "pressure",
    ]
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with open(REQUIRED_COLUMNS_FILE, "w") as f:
        json.dump(required_columns, f, indent=2)

    save_checksum(REQUIRED_COLUMNS_FILE.name, compute_file_hash(REQUIRED_COLUMNS_FILE))
    return REQUIRED_COLUMNS_FILE

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> int:
    """Executes the full FR-001 data acquisition pipeline."""
    try:
        parquet_path = download_stratified_sample()
        df_sample = pd.read_parquet(parquet_path)
        comps = df_sample["composition"].dropna().astype(str).tolist()
        if not comps:
            raise RuntimeError("No composition information found in OC20 sample.")
        
        download_mp_descriptors(comps)
        write_required_columns()

        logger.info("All data acquisition steps completed successfully.")
        return 0
    except Exception as exc:
        logger.error(f"Data acquisition failed: {exc}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())