"""
Data download module for T003.
Downloads QM9 and IR spectra, aligns them via InChIKey, computes SHA‑256 checksums,
and writes a verification JSON file.
"""

import logging
import sys
import json
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pandas as pd
import requests
from scipy import stats

# External libraries
import qm9pack

# llmxive utilities for path handling
from llmxive_toolkit import paths

logger = logging.getLogger(__name__)

def _ensure_dir(path: Path) -> Path:
    """Make sure the parent directory of *path* exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def _sha256_of_file(file_path: Path, chunk_size: int = 8192) -> str:
    """Compute SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

# ----------------------------------------------------------------------
# Download helpers
# ----------------------------------------------------------------------
def download_qm9(output_dir: Optional[Path] = None) -> Path:
    """Download the QM9 dataset using ``qm9pack`` and store as Parquet."""
    if output_dir is None:
        output_dir = Path("data/raw")
    _ensure_dir(output_dir / "placeholder")  # ensure the directory exists

    logger.info("Downloading QM9 dataset via qm9pack")
    df = qm9pack.get_data("qm9")
    out_path = output_dir / "qm9.parquet"
    df.to_parquet(out_path, engine="pyarrow")
    logger.info(f"QM9 saved to {out_path}")
    return out_path

def download_ir_spectra(output_dir: Optional[Path] = None) -> Path:
    """Download the IR‑spectra dataset from the verified HuggingFace URL and store as Parquet."""
    if output_dir is None:
        output_dir = Path("data/raw")
    _ensure_dir(output_dir / "placeholder")

    # Verified real source URL (direct parquet file)
    url = "https://huggingface.co/datasets/lamblador/QM9-IR/resolve/main/data/qm9_ir.parquet"
    logger.info(f"Downloading IR spectra dataset from {url}")

    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()  # Fail fast on HTTP errors

    out_path = output_dir / "ir_spectra.parquet"
    # Write streamed content to file
    with open(out_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    logger.info(f"IR spectra saved to {out_path}")
    return out_path

# ----------------------------------------------------------------------
# Alignment & bias helpers (unchanged logic, only column‑name normalisation)
# ----------------------------------------------------------------------
def align_datasets(
    qm9_df: pd.DataFrame, ir_df: pd.DataFrame, key: str = "InChIKey"
) -> Tuple[pd.DataFrame, int]:
    """Align QM9 and IR spectra datasets on *key* (default ``InChIKey``)."""
    # Normalise possible variations of the column name
    rename_map = {
        col: col.replace("inchikey", "InChIKey")
        .replace("InchiKey", "InChIKey")
        for col in qm9_df.columns
    }
    qm9_df = qm9_df.rename(columns=rename_map)

    rename_map = {
        col: col.replace("inchikey", "InChIKey")
        .replace("InchiKey", "InChIKey")
        for col in ir_df.columns
    }
    ir_df = ir_df.rename(columns=rename_map)

    if key not in qm9_df.columns or key not in ir_df.columns:
        raise KeyError(
            f"Alignment key {key!r} not found. QM9 cols: {list(qm9_df.columns)}, IR cols: {list(ir_df.columns)}"
        )

    merged = pd.merge(qm9_df, ir_df, on=key, how="inner")
    discarded = len(qm9_df) - len(merged)
    return merged, discarded

def compute_selection_bias(
    full_df: pd.DataFrame, aligned_df: pd.DataFrame, properties: list
) -> Dict[str, Any]:
    """KS‑test based bias assessment for each *property*."""
    bias_stats = {}
    for prop in properties:
        if prop not in full_df.columns or prop not in aligned_df.columns:
            continue
        s, p = stats.ks_2samp(full_df[prop], aligned_df[prop])
        bias_stats[prop] = {"statistic": float(s), "p_value": float(p)}
    return bias_stats

def save_aligned_data(
    aligned_df: pd.DataFrame, output_path: Optional[Path] = None
) -> Path:
    """Persist the aligned DataFrame as Parquet."""
    if output_path is None:
        output_path = Path("data/processed") / "aligned_data.parquet"
    _ensure_dir(output_path)
    aligned_df.to_parquet(output_path, engine="pyarrow")
    logger.info(f"Aligned dataset written to {output_path}")
    return output_path

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main() -> None:
    """Entry point used by ``code/main.py download``."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting data download and alignment")

    try:
        # 1. Download raw files
        qm9_path = download_qm9()
        ir_path = download_ir_spectra()
        logger.info(f"Downloaded QM9 → {qm9_path}, IR spectra → {ir_path}")

        # 2. Load Parquet files
        qm9_df = pd.read_parquet(qm9_path, engine="pyarrow")
        ir_df = pd.read_parquet(ir_path, engine="pyarrow")

        # 3. Align on InChIKey
        aligned_df, discarded = align_datasets(qm9_df, ir_df)
        matched = len(aligned_df)
        logger.info(f"Alignment complete: matched={matched}, discarded={discarded}")

        # 4. Verify sufficient matches (acceptance scenario)
        if matched < 129_000:
            raise RuntimeError(
                f"Insufficient matches: {matched} < 129,000 required"
            )

        # 5. Selection‑bias KS‑tests for target properties
        target_props = [
            "Dipole_debye",
            "Polarizability_bohr3",
            "HOMO_LUMO_gap_au",
        ]
        available = [p for p in target_props if p in qm9_df.columns]
        if not available:
            # Fallback to common short names used by qm9pack
            fallback = {"mu": "Dipole_debye", "alpha": "Polarizability_bohr3", "gap": "HOMO_LUMO_gap_au"}
            for short, long_name in fallback.items():
                if short in qm9_df.columns:
                    available.append(short)

        bias_stats = compute_selection_bias(qm9_df, aligned_df, available)
        logger.info(f"Selection‑bias stats computed for: {available}")

        # 6. Write alignment report (JSON)
        report = {
            "matched": matched,
            "discarded": discarded,
            "selection_bias_stats": bias_stats,
        }
        report_path = Path("data/processed/alignment_report.json")
        _ensure_dir(report_path)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info(f"Alignment report saved to {report_path}")

        # 7. Persist the aligned dataset for downstream stages
        save_aligned_data(aligned_df)

        # 8. Compute SHA‑256 checksums and write verification file
        checksums = {
            "qm9.parquet": _sha256_of_file(qm9_path),
            "ir_spectra.parquet": _sha256_of_file(ir_path),
        }
        checksums_path = paths.results("checksums.json")
        _ensure_dir(checksums_path)
        checksums_json = {"files": checksums, "status": "ok"}
        with open(checksums_path, "w") as f:
            json.dump(checksums_json, f, indent=2)
        logger.info(f"Checksums written to {checksums_path}")

    except Exception as exc:
        logger.error(f"Data ingestion failed: {exc}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
